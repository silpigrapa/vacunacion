import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from modelos.stock import obtener_stock_por_vacunatorio
from modelos.transferencia import registrar_transferencia


def conectar_a(ruta):
    conexion = sqlite3.connect(ruta)
    conexion.row_factory = sqlite3.Row
    return conexion


class PruebasTransferencia(unittest.TestCase):
    def setUp(self):
        self.directorio = tempfile.TemporaryDirectory()
        self.base = Path(self.directorio.name) / "base.sqlite3"
        conexion = sqlite3.connect(self.base)
        conexion.executescript(
            """
            CREATE TABLE VACUNATORIO (
                id_vacunatorio INTEGER PRIMARY KEY,
                nombre TEXT NOT NULL
            );
            CREATE TABLE VACUNA (
                id_vacuna INTEGER PRIMARY KEY,
                nombre TEXT NOT NULL,
                dosis_por_ampolla INTEGER NOT NULL
            );
            CREATE TABLE LOTE (
                id_lote INTEGER PRIMARY KEY,
                numero_lote TEXT NOT NULL,
                fecha_vencimiento TEXT NOT NULL,
                id_vacuna INTEGER NOT NULL
            );
            CREATE TABLE AMPOLLA (
                id_ampolla INTEGER PRIMARY KEY,
                fecha_apertura TEXT,
                dosis_disponibles INTEGER NOT NULL,
                id_lote INTEGER NOT NULL,
                id_vacunatorio_actual INTEGER NOT NULL
            );
            CREATE TABLE TRANSFERENCIA (
                id_transferencia INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_remito TEXT NOT NULL,
                fecha TEXT NOT NULL,
                id_vacunatorio_origen INTEGER NOT NULL,
                id_vacunatorio_destino INTEGER NOT NULL,
                id_usuario INTEGER NOT NULL,
                observaciones TEXT
            );
            CREATE TABLE TRANSFERENCIA_DETALLE (
                id_transferencia INTEGER NOT NULL,
                id_ampolla INTEGER NOT NULL
            );
            INSERT INTO VACUNATORIO VALUES (1, 'Origen'), (2, 'Destino');
            INSERT INTO VACUNA VALUES (1, 'Vacuna de prueba', 5);
            INSERT INTO LOTE VALUES
                (1, 'VIGENTE', date('now', 'localtime', '+30 days'), 1),
                (2, 'VENCIDO', date('now', 'localtime', '-1 day'), 1);
            INSERT INTO AMPOLLA VALUES
                (1, NULL, 5, 1, 1),
                (2, NULL, 5, 2, 1);
            """
        )
        conexion.commit()
        conexion.close()
        self.addCleanup(self.directorio.cleanup)

    def test_listado_para_transferencia_excluye_ampollas_vencidas(self):
        with patch(
            "modelos.stock.obtener_conexion",
            side_effect=lambda: conectar_a(self.base),
        ):
            ampollas = obtener_stock_por_vacunatorio(id_vacunatorio=1)

        self.assertEqual([ampolla["id_ampolla"] for ampolla in ampollas], [1])

    def test_transferencia_mueve_ampolla_vigente_al_destino(self):
        with patch(
            "modelos.transferencia.obtener_conexion",
            side_effect=lambda: conectar_a(self.base),
        ):
            registrar_transferencia(
                numero_remito="R-1",
                fecha="2026-01-01",
                id_vacunatorio_origen=1,
                id_vacunatorio_destino=2,
                id_usuario=1,
                lista_ampollas_con_cantidad=[(1, 1)],
            )

        conexion = sqlite3.connect(self.base)
        try:
            ubicacion = conexion.execute(
                "SELECT id_vacunatorio_actual FROM AMPOLLA WHERE id_ampolla = 1"
            ).fetchone()[0]
            self.assertEqual(ubicacion, 2)
        finally:
            conexion.close()

    def test_ampolla_vencida_no_crea_remito_ni_cambia_de_ubicacion(self):
        with patch(
            "modelos.transferencia.obtener_conexion",
            side_effect=lambda: conectar_a(self.base),
        ):
            with self.assertRaisesRegex(RuntimeError, "está vencida"):
                registrar_transferencia(
                    numero_remito="R-2",
                    fecha="2026-01-01",
                    id_vacunatorio_origen=1,
                    id_vacunatorio_destino=2,
                    id_usuario=1,
                    lista_ampollas_con_cantidad=[(2, 1)],
                )

        conexion = sqlite3.connect(self.base)
        try:
            self.assertEqual(
                conexion.execute("SELECT COUNT(*) FROM TRANSFERENCIA").fetchone()[0],
                0,
            )
            ubicacion = conexion.execute(
                "SELECT id_vacunatorio_actual FROM AMPOLLA WHERE id_ampolla = 2"
            ).fetchone()[0]
            self.assertEqual(ubicacion, 1)
        finally:
            conexion.close()


if __name__ == "__main__":
    unittest.main()
