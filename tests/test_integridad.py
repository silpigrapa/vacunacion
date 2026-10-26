import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import database.conexion as modulo_conexion
from database.auditoria import (
    detectar_elementos_auditoria_faltantes,
    instalar_auditoria,
    marcar_cambios_externos_notificados,
    obtener_cambios_externos_pendientes,
    verificar_auditoria,
)
from database.integridad import auditar_integridad
from modelos.vacuna import registrar_ingreso_central


def crear_base(ruta):
    sql_path = Path(__file__).resolve().parents[1] / "database" / "sistema_vacunacion.sql"
    conexion = sqlite3.connect(ruta)
    try:
        conexion.executescript(sql_path.read_text(encoding="utf-8"))
        conexion.execute(
            """
            INSERT INTO VACUNATORIO (nombre, direccion, es_central)
            VALUES ('Central', 'Dirección de prueba', 1)
            """
        )
        instalar_auditoria(conexion)
        conexion.commit()
    finally:
        conexion.close()


def conectar_a(ruta):
    conexion = sqlite3.connect(ruta)
    conexion.execute("PRAGMA foreign_keys = ON")
    conexion.row_factory = sqlite3.Row
    return conexion


class PruebasIntegridad(unittest.TestCase):
    def test_base_vacia_pasa_auditoria(self):
        with tempfile.TemporaryDirectory() as directorio:
            base = Path(directorio) / "base.sqlite3"
            crear_base(base)

            self.assertEqual(auditar_integridad(base), [])

    def test_ingreso_central_registra_lote_y_todas_sus_ampollas(self):
        with tempfile.TemporaryDirectory() as directorio:
            base = Path(directorio) / "base.sqlite3"
            crear_base(base)

            with patch(
                "modelos.vacuna.obtener_conexion",
                side_effect=lambda: conectar_a(base),
            ):
                id_lote, id_vacuna, vacuna_nueva = registrar_ingreso_central(
                    nombre="Vacuna de prueba",
                    numero_lote="L1",
                    fecha_vencimiento="2027-01-01",
                    cantidad_ampollas=3,
                    id_vacunatorio=1,
                    dosis_por_ampolla=5,
                )

            self.assertTrue(vacuna_nueva)
            conexion = sqlite3.connect(base)
            try:
                cantidad_lote = conexion.execute(
                    "SELECT cantidad_ampollas FROM LOTE WHERE id_lote = ?",
                    (id_lote,),
                ).fetchone()[0]
                cantidad_ampollas = conexion.execute(
                    "SELECT COUNT(*) FROM AMPOLLA WHERE id_lote = ?",
                    (id_lote,),
                ).fetchone()[0]
                vacuna = conexion.execute(
                    "SELECT id_vacuna, dosis_disponibles FROM VACUNA "
                    "JOIN LOTE USING (id_vacuna) "
                    "JOIN AMPOLLA USING (id_lote) WHERE id_vacuna = ? LIMIT 1",
                    (id_vacuna,),
                ).fetchone()
            finally:
                conexion.close()

            self.assertEqual(cantidad_lote, 3)
            self.assertEqual(cantidad_ampollas, 3)
            self.assertEqual(vacuna[0], id_vacuna)
            self.assertEqual(vacuna[1], 5)
            self.assertEqual(auditar_integridad(base), [])

    def test_auditoria_detecta_dosis_negativas_y_cantidad_inconsistente(self):
        with tempfile.TemporaryDirectory() as directorio:
            base = Path(directorio) / "base.sqlite3"
            crear_base(base)
            conexion = conectar_a(base)
            try:
                conexion.execute(
                    "INSERT INTO VACUNA (nombre) VALUES ('Prueba')"
                )
                id_vacuna = conexion.execute(
                    "SELECT id_vacuna FROM VACUNA WHERE nombre = 'Prueba'"
                ).fetchone()[0]
                conexion.execute(
                    """
                    INSERT INTO LOTE (
                        numero_lote, fecha_vencimiento, cantidad_ampollas,
                        id_vacuna, id_vacunatorio
                    ) VALUES ('L1', '31-12-2027', 2, ?, 1)
                    """,
                    (id_vacuna,),
                )
                id_lote = conexion.execute(
                    "SELECT id_lote FROM LOTE WHERE numero_lote = 'L1'"
                ).fetchone()[0]
                conexion.execute(
                    """
                    INSERT INTO AMPOLLA (
                        dosis_disponibles, id_lote, id_vacunatorio_actual
                    ) VALUES (-1, ?, 1)
                    """,
                    (id_lote,),
                )
                conexion.commit()
            finally:
                conexion.close()

            hallazgos = auditar_integridad(base)

            self.assertTrue(any("dosis disponibles negativas" in h for h in hallazgos))
            self.assertTrue(any("declara 2 ampollas" in h for h in hallazgos))
            self.assertTrue(any("fecha inválida" in h for h in hallazgos))

    def test_ingreso_central_es_atomico_si_falla_al_crear_ampolla(self):
        with tempfile.TemporaryDirectory() as directorio:
            base = Path(directorio) / "base.sqlite3"
            crear_base(base)
            conexion = conectar_a(base)
            try:
                conexion.execute(
                    """
                    CREATE TRIGGER fallar_ampolla
                    BEFORE INSERT ON AMPOLLA
                    BEGIN
                        SELECT RAISE(ABORT, 'fallo simulado');
                    END
                    """
                )
                conexion.commit()
            finally:
                conexion.close()

            with patch(
                "modelos.vacuna.obtener_conexion",
                side_effect=lambda: conectar_a(base),
            ):
                with self.assertRaises(sqlite3.IntegrityError):
                    registrar_ingreso_central(
                        nombre="Vacuna de prueba",
                        numero_lote="L1",
                        fecha_vencimiento="2027-01-01",
                        cantidad_ampollas=2,
                        id_vacunatorio=1,
                    )

            conexion = sqlite3.connect(base)
            try:
                for tabla in ("VACUNA", "LOTE", "AMPOLLA"):
                    cantidad = conexion.execute(
                        f"SELECT COUNT(*) FROM {tabla}"
                    ).fetchone()[0]
                    self.assertEqual(cantidad, 0, tabla)
            finally:
                conexion.close()

    def test_rechaza_fecha_o_cantidades_invalidas_antes_de_escribir(self):
        with tempfile.TemporaryDirectory() as directorio:
            base = Path(directorio) / "base.sqlite3"
            crear_base(base)

            with patch(
                "modelos.vacuna.obtener_conexion",
                side_effect=lambda: conectar_a(base),
            ):
                with self.assertRaises(ValueError):
                    registrar_ingreso_central(
                        nombre="Vacuna",
                        numero_lote="L1",
                        fecha_vencimiento="31/12/2027",
                        cantidad_ampollas=1,
                        id_vacunatorio=1,
                    )

            self.assertEqual(auditar_integridad(base), [])

    def test_cambio_externo_genera_un_evento_de_auditoria(self):
        with tempfile.TemporaryDirectory() as directorio:
            base = Path(directorio) / "base.sqlite3"
            crear_base(base)
            conexion = sqlite3.connect(base)
            try:
                conexion.execute(
                    "INSERT INTO VACUNA (nombre) VALUES ('Editada afuera')"
                )
                conexion.commit()
                cambios = conexion.execute(
                    """
                    SELECT tabla, operacion, id_registro, notificado
                    FROM CAMBIOS_EXTERNOS
                    """
                ).fetchall()
            finally:
                conexion.close()

            self.assertEqual(len(cambios), 1)
            self.assertEqual(cambios[0], ("VACUNA", "INSERT", "1", 0))

    def test_alerta_de_cambio_externo_se_consulta_y_puede_confirmarse(self):
        with tempfile.TemporaryDirectory() as directorio:
            base = Path(directorio) / "base.sqlite3"
            crear_base(base)
            conexion = sqlite3.connect(base)
            try:
                conexion.execute(
                    "INSERT INTO VACUNA (nombre) VALUES ('Editada afuera')"
                )
                conexion.commit()
                id_cambio = conexion.execute(
                    "SELECT id_cambio FROM CAMBIOS_EXTERNOS"
                ).fetchone()[0]
            finally:
                conexion.close()

            with patch("database.auditoria.RUTA_BD", str(base)):
                pendientes = obtener_cambios_externos_pendientes()
                marcar_cambios_externos_notificados([id_cambio])
                despues = obtener_cambios_externos_pendientes()

            self.assertEqual(len(pendientes), 1)
            self.assertEqual(pendientes[0]["tabla"], "VACUNA")
            self.assertEqual(despues, [])

    def test_escritura_de_la_aplicacion_no_se_reporta_como_externa(self):
        with tempfile.TemporaryDirectory() as directorio:
            base = Path(directorio) / "base.sqlite3"
            crear_base(base)

            with patch.object(modulo_conexion, "RUTA_BD", str(base)):
                conexion = modulo_conexion.obtener_conexion()
                try:
                    conexion.execute(
                        "INSERT INTO VACUNA (nombre) VALUES ('Creada en app')"
                    )
                    conexion.commit()
                finally:
                    conexion.close()

            conexion = sqlite3.connect(base)
            try:
                cantidad = conexion.execute(
                    "SELECT COUNT(*) FROM CAMBIOS_EXTERNOS"
                ).fetchone()[0]
            finally:
                conexion.close()
            self.assertEqual(cantidad, 0)

    def test_detecta_triggers_de_auditoria_eliminados(self):
        with tempfile.TemporaryDirectory() as directorio:
            base = Path(directorio) / "base.sqlite3"
            crear_base(base)
            nombre_trigger = "trg_cambio_externo_vacuna_insert"
            conexion = sqlite3.connect(base)
            try:
                conexion.execute(f'DROP TRIGGER "{nombre_trigger}"')
                conexion.commit()
                faltantes = detectar_elementos_auditoria_faltantes(conexion)
            finally:
                conexion.close()

            self.assertIn(f"Falta el trigger {nombre_trigger}.", faltantes)
            self.assertIn(
                f"Falta el trigger {nombre_trigger}.",
                verificar_auditoria(base),
            )

    def test_inicio_avisa_si_auditoria_faltaba_antes_de_reinstalarla(self):
        with tempfile.TemporaryDirectory() as directorio:
            base = Path(directorio) / "base.sqlite3"
            crear_base(base)
            conexion = sqlite3.connect(base)
            try:
                conexion.execute(
                    'DROP TRIGGER "trg_cambio_externo_vacuna_insert"'
                )
                conexion.commit()
            finally:
                conexion.close()

            with patch.object(modulo_conexion, "RUTA_BD", str(base)):
                modulo_conexion.inicializar_base_de_datos()
                advertencias = (
                    modulo_conexion.consumir_advertencias_auditoria_inicio()
                )
                repetidas = (
                    modulo_conexion.consumir_advertencias_auditoria_inicio()
                )

            self.assertTrue(
                any("trg_cambio_externo_vacuna_insert" in a for a in advertencias)
            )
            self.assertEqual(repetidas, [])
            self.assertEqual(verificar_auditoria(base), [])


if __name__ == "__main__":
    unittest.main()
