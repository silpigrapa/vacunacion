import sqlite3
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

from modelos.ampolla import obtener_stock_por_vacunatorio
from modelos.stock import obtener_resumen_stock, listar_stock_por_vacunatorio


def conectar_a(ruta):
    conexion = sqlite3.connect(ruta)
    conexion.execute("PRAGMA foreign_keys = ON")
    conexion.row_factory = sqlite3.Row
    return conexion


class PruebasStockPorVacunatorio(unittest.TestCase):
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
            conexion.executemany(
                """
                INSERT INTO VACUNATORIO (nombre, direccion, es_central)
                VALUES (?, ?, ?)
                """,
                [
                    ("Central", "Dirección central", 1),
                    ("Sucursal", "Dirección sucursal", 0),
                ],
            )
            conexion.execute(
                "INSERT INTO VACUNA (nombre, dosis_por_ampolla) VALUES (?, ?)",
                ("Vacuna de prueba", 5),
            )
            id_vacuna = conexion.execute(
                "SELECT id_vacuna FROM VACUNA WHERE nombre = ?",
                ("Vacuna de prueba",),
            ).fetchone()[0]
            hoy = date.today().isoformat()
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
                    ("CENTRAL", futuro, 2, id_vacuna, 1),
                    ("SUCURSAL", hoy, 1, id_vacuna, 1),
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
                INSERT INTO AMPOLLA (
                    dosis_disponibles, id_lote, id_vacunatorio_actual
                ) VALUES (?, ?, ?)
                """,
                [
                    (1, id_lotes["VENCIDO"], 1),
                    (4, id_lotes["CENTRAL"], 1),
                    (3, id_lotes["CENTRAL"], 1),
                    (2, id_lotes["SUCURSAL"], 2),
                ],
            )
            conexion.commit()
        finally:
            conexion.close()

        self.parches = (
            patch(
                "modelos.stock.obtener_conexion",
                side_effect=lambda: conectar_a(self.base),
            ),
            patch(
                "modelos.ampolla.obtener_conexion",
                side_effect=lambda: conectar_a(self.base),
            ),
        )
        for parche in self.parches:
            parche.start()
            self.addCleanup(parche.stop)
        self.addCleanup(self.directorio.cleanup)
        self.id_vacuna = id_vacuna

    def test_resumen_y_listado_cuentan_solo_stock_vigente(self):
        resumen = obtener_resumen_stock(1)
        listado = listar_stock_por_vacunatorio(1)

        self.assertEqual(resumen["vacunas_con_stock"], 1)
        self.assertEqual(resumen["ampollas_con_stock"], 2)
        self.assertEqual(resumen["dosis_disponibles"], 7)
        self.assertEqual(resumen["dosis_vencidas"], 1)
        self.assertEqual(len(listado), 1)
        self.assertEqual(listado[0]["cantidad_ampollas"], 2)
        self.assertEqual(listado[0]["dosis_disponibles"], 7)
        self.assertEqual(listado[0]["dosis_vencidas"], 1)

    def test_comparativa_muestra_ampollas_y_dosis_por_centro(self):
        filas = obtener_stock_por_vacunatorio(self.id_vacuna)
        por_centro = {fila["nombre"]: fila for fila in filas}

        self.assertEqual(por_centro["Central"]["ampollas_disponibles"], 2)
        self.assertEqual(por_centro["Central"]["dosis_disponibles"], 7)
        self.assertEqual(por_centro["Sucursal"]["ampollas_disponibles"], 1)
        self.assertEqual(por_centro["Sucursal"]["dosis_disponibles"], 2)


if __name__ == "__main__":
    unittest.main()
