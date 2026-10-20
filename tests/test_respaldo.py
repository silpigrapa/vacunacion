import sqlite3
import tempfile
import unittest
from pathlib import Path

from database.respaldo import TABLAS_REQUERIDAS, crear_respaldo, restaurar_respaldo


def crear_base_prueba(ruta, valor):
    conexion = sqlite3.connect(ruta)
    try:
        for tabla in sorted(TABLAS_REQUERIDAS):
            conexion.execute(f'CREATE TABLE "{tabla}" (id INTEGER PRIMARY KEY)')
        conexion.execute("CREATE TABLE PRUEBA (valor TEXT NOT NULL)")
        conexion.execute("INSERT INTO PRUEBA (valor) VALUES (?)", (valor,))
        conexion.commit()
    finally:
        conexion.close()


class PruebasRespaldo(unittest.TestCase):
    def test_crea_copia_consistente_de_la_base(self):
        with tempfile.TemporaryDirectory() as directorio:
            base = Path(directorio) / "activa.sqlite3"
            copia = Path(directorio) / "copia.sqlite3"
            crear_base_prueba(base, "original")

            self.assertEqual(crear_respaldo(copia, base), copia)

            conexion = sqlite3.connect(copia)
            try:
                valor = conexion.execute("SELECT valor FROM PRUEBA").fetchone()[0]
            finally:
                conexion.close()
            self.assertEqual(valor, "original")

    def test_restaurar_crea_respaldo_previo_y_reemplaza_la_base(self):
        with tempfile.TemporaryDirectory() as directorio:
            base = Path(directorio) / "activa.sqlite3"
            copia = Path(directorio) / "copia.sqlite3"
            crear_base_prueba(base, "actual")
            crear_base_prueba(copia, "respaldado")

            respaldo_previo = restaurar_respaldo(copia, base)

            self.assertTrue(respaldo_previo.is_file())
            for ruta, valor_esperado in (
                (base, "respaldado"),
                (respaldo_previo, "actual"),
            ):
                conexion = sqlite3.connect(ruta)
                try:
                    valor = conexion.execute("SELECT valor FROM PRUEBA").fetchone()[0]
                finally:
                    conexion.close()
                self.assertEqual(valor, valor_esperado)

    def test_restaurar_base_en_modo_wal(self):
        with tempfile.TemporaryDirectory() as directorio:
            base = Path(directorio) / "activa.sqlite3"
            copia = Path(directorio) / "copia.sqlite3"
            crear_base_prueba(base, "actual")
            crear_base_prueba(copia, "respaldado")

            conexion = sqlite3.connect(base)
            try:
                conexion.execute("PRAGMA journal_mode = WAL")
            finally:
                conexion.close()

            restaurar_respaldo(copia, base)

            conexion = sqlite3.connect(base)
            try:
                modo = conexion.execute("PRAGMA journal_mode").fetchone()[0]
                valor = conexion.execute("SELECT valor FROM PRUEBA").fetchone()[0]
            finally:
                conexion.close()
            self.assertEqual(modo.lower(), "delete")
            self.assertEqual(valor, "respaldado")

    def test_rechaza_archivo_ajeno_sin_modificar_base(self):
        with tempfile.TemporaryDirectory() as directorio:
            base = Path(directorio) / "activa.sqlite3"
            archivo_ajeno = Path(directorio) / "ajeno.sqlite3"
            crear_base_prueba(base, "actual")
            sqlite3.connect(archivo_ajeno).close()

            with self.assertRaises(ValueError):
                restaurar_respaldo(archivo_ajeno, base)

            conexion = sqlite3.connect(base)
            try:
                valor = conexion.execute("SELECT valor FROM PRUEBA").fetchone()[0]
            finally:
                conexion.close()
            self.assertEqual(valor, "actual")


if __name__ == "__main__":
    unittest.main()
