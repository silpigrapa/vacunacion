"""
Módulo de conexión a la base de datos del Sistema de Vacunación.

En SQLite no existe el comando CREATE DATABASE: la base de datos
es directamente el archivo .db. Este módulo se encarga de:
  1) Crear el archivo si no existe.
  2) Ejecutar el script de creación de tablas la primera vez.
  3) Entregar conexiones ya configuradas (con foreign keys activadas).
"""

import sqlite3
import os

# Rutas del proyecto
CARPETA_BASE = os.path.dirname(os.path.abspath(__file__))
RUTA_BD = os.path.join(CARPETA_BASE, "sistema_vacunacion.db")
RUTA_SCRIPT_SQL = os.path.join(CARPETA_BASE, "sistema_vacunacion.sql")
TABLA_CONTEXTO_ESCRITURA = "CONTEXTO_ESCRITURA_APP"
ADVERTENCIAS_AUDITORIA_INICIO = []


class _CursorAplicacion(sqlite3.Cursor):
    def execute(self, sql, parametros=()):
        if _es_escritura(sql) and not getattr(self.connection, "_actualizando_contexto", False):
            self.connection._marcar_escritura_app()
        return super().execute(sql, parametros)

    def executemany(self, sql, secuencia_parametros):
        if _es_escritura(sql) and not getattr(self.connection, "_actualizando_contexto", False):
            self.connection._marcar_escritura_app()
        return super().executemany(sql, secuencia_parametros)


def _es_escritura(sql):
    instruccion = sql.lstrip().split(None, 1)[0].upper() if sql.strip() else ""
    return instruccion in {"INSERT", "UPDATE", "DELETE", "REPLACE"}


class _ConexionAplicacion(sqlite3.Connection):
    def cursor(self, factory=None):
        return super().cursor(factory or _CursorAplicacion)

    def _actualizar_contexto(self, activa):
        self._actualizando_contexto = True
        try:
            sqlite3.Connection.execute(
                self,
                f"UPDATE {TABLA_CONTEXTO_ESCRITURA} SET activa = ? WHERE id = 1",
                (1 if activa else 0,),
            )
        except sqlite3.OperationalError as error:
            if "no such table" not in str(error).lower():
                raise
        finally:
            self._actualizando_contexto = False

    def _marcar_escritura_app(self):
        self._actualizar_contexto(True)

    def commit(self):
        if self.in_transaction:
            self._actualizar_contexto(False)
        return super().commit()


def obtener_conexion():
    """
    Devuelve una conexión a la base de datos con las foreign keys
    activadas (SQLite las trae desactivadas por defecto en cada conexión).
    """
    conexion = sqlite3.connect(RUTA_BD, factory=_ConexionAplicacion)
    conexion.execute("PRAGMA foreign_keys = ON;")
    conexion.execute("PRAGMA busy_timeout = 5000;")  # espera hasta 5s si la base está ocupada
    conexion.row_factory = sqlite3.Row  # permite acceder a columnas por nombre
    return conexion


def inicializar_base_de_datos():
    """
    Crea el archivo de base de datos (si no existe) y ejecuta el script
    de creación de tablas. Se debe llamar una sola vez, al arrancar la
    aplicación por primera vez.

    Si el archivo .db ya existe, no vuelve a ejecutar el script
    (evita el error de "la tabla ya existe").
    """
    bd_ya_existia = os.path.exists(RUTA_BD)
    ADVERTENCIAS_AUDITORIA_INICIO.clear()

    conexion = sqlite3.connect(RUTA_BD)
    conexion.execute("PRAGMA foreign_keys = ON;")
    conexion.execute("PRAGMA busy_timeout = 5000;")

    if not bd_ya_existia:
        with open(RUTA_SCRIPT_SQL, "r", encoding="utf-8") as archivo:
            script = archivo.read()
        conexion.executescript(script)
        print(f"Base de datos creada en: {RUTA_BD}")
    else:
        print(f"Base de datos ya existente en: {RUTA_BD}")

    conexion.execute(
        """
        CREATE TABLE IF NOT EXISTS OPCION_VACUNA_CSV (
            nombre TEXT PRIMARY KEY
        )
        """
    )
    from database.auditoria import (
        detectar_elementos_auditoria_faltantes,
        instalar_auditoria,
    )

    if bd_ya_existia:
        ADVERTENCIAS_AUDITORIA_INICIO.extend(
            detectar_elementos_auditoria_faltantes(conexion)
        )
    instalar_auditoria(conexion)
    conexion.commit()
    conexion.close()


def consumir_advertencias_auditoria_inicio():
    """Entrega una sola vez las faltas detectadas antes de reparar la auditoría."""
    advertencias = ADVERTENCIAS_AUDITORIA_INICIO.copy()
    ADVERTENCIAS_AUDITORIA_INICIO.clear()
    return advertencias


if __name__ == "__main__":
    # Permite correr este archivo directamente para inicializar la BD:
    #   python conexion.py
    inicializar_base_de_datos()