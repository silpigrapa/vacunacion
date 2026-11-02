import sqlite3
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

from database.auditoria import instalar_auditoria
from modelos.notificaciones import (
    listar_stock_bajo,
    listar_stock_con_umbral,
    listar_umbrales_vacunas,
    guardar_umbral,
)


def conectar_a(ruta):
    conexion = sqlite3.connect(ruta)
    conexion.execute("PRAGMA foreign_keys = ON")
    conexion.row_factory = sqlite3.Row
    return conexion


class PruebasUmbralStock(unittest.TestCase):
    def setUp(self):
        self.directorio = tempfile.TemporaryDirectory()
        self.base = Path(self.directorio.name) / "base.sqlite3"
        ruta_sql = (
            Path(__file__).resolve().parents[1]
            / "database"
            / "sistema_vacunacion.sql"
        )
        conexion = sqlite3.connect(self.base)
        try:
            conexion.executescript(ruta_sql.read_text(encoding="utf-8"))
            conexion.execute(
                """
                INSERT INTO VACUNATORIO (nombre, direccion, es_central)
                VALUES ('Central', 'Dirección de prueba', 1)
                """
            )
            conexion.execute(
                """
                INSERT INTO VACUNATORIO (nombre, direccion)
                VALUES ('Sucursal', 'Otra dirección de prueba')
                """
            )
            conexion.execute(
                "INSERT INTO VACUNA (nombre, dosis_por_ampolla) VALUES (?, ?)",
                ("Vacuna de prueba", 5),
            )
            id_vacuna = conexion.execute(
                "SELECT id_vacuna FROM VACUNA WHERE nombre = ?",
                ("Vacuna de prueba",),
            ).fetchone()[0]
            ayer = (date.today() - timedelta(days=1)).isoformat()
            futuro = (date.today() + timedelta(days=30)).isoformat()
            conexion.executemany(
                """
                INSERT INTO LOTE (
                    numero_lote, fecha_vencimiento, cantidad_ampollas,
                    id_vacuna, id_vacunatorio
                ) VALUES (?, ?, ?, ?, ?)
                """,
                [
                    ("VENCIDO", ayer, 1, id_vacuna, 1),
                    ("CENTRAL", futuro, 1, id_vacuna, 1),
                    ("SUCURSAL", futuro, 3, id_vacuna, 2),
                ],
            )
            id_lotes = {
                numero: id_lote
                for id_lote, numero in conexion.execute(
                    "SELECT id_lote, numero_lote FROM LOTE"
                )
            }
            conexion.executemany(
                """
                INSERT INTO AMPOLLA (dosis_disponibles, id_lote, id_vacunatorio_actual)
                VALUES (?, ?, ?)
                """,
                [
                    (5, id_lotes["VENCIDO"], 1),
                    (1, id_lotes["CENTRAL"], 1),
                    (1, id_lotes["SUCURSAL"], 2),
                    (1, id_lotes["SUCURSAL"], 2),
                    (1, id_lotes["SUCURSAL"], 2),
                ],
            )
            instalar_auditoria(conexion)
            conexion.commit()
        finally:
            conexion.close()

        self.parche_conexion = patch(
            "modelos.notificaciones.obtener_conexion",
            side_effect=lambda: conectar_a(self.base),
        )
        self.parche_conexion.start()
        self.addCleanup(self.parche_conexion.stop)
        self.addCleanup(self.directorio.cleanup)

    def test_lista_stock_vigente_separado_por_vacunatorio(self):
        filas = listar_stock_con_umbral()

        self.assertEqual(
            [(fila["vacunatorio"], fila["stock"]) for fila in filas],
            [("Central", 1), ("Sucursal", 3)],
        )

    def test_alerta_incluye_otro_vacunatorio_y_aplica_umbral_por_vacuna(self):
        id_vacuna = listar_stock_con_umbral()[0]["id_vacuna"]
        guardar_umbral(id_vacuna, 2)

        alertas = listar_stock_bajo()

        self.assertEqual(len(alertas), 1)
        self.assertEqual(alertas[0]["vacunatorio"], "Central")
        self.assertEqual(alertas[0]["stock"], 1)
        self.assertEqual(alertas[0]["umbral"], 2)
        self.assertEqual(len(listar_stock_bajo(2)), 0)

    def test_configuracion_de_umbral_muestra_cada_vacuna_una_vez(self):
        id_vacuna = listar_stock_con_umbral()[0]["id_vacuna"]
        guardar_umbral(id_vacuna, 4)

        umbrales = listar_umbrales_vacunas()

        self.assertEqual(len(umbrales), 1)
        self.assertEqual(umbrales[0]["id_vacuna"], id_vacuna)
        self.assertEqual(umbrales[0]["umbral"], 4)


if __name__ == "__main__":
    unittest.main()
