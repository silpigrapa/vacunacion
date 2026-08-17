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


def obtener_conexion():
    """
    Devuelve una conexión a la base de datos con las foreign keys
    activadas (SQLite las trae desactivadas por defecto en cada conexión).
    """
    conexion = sqlite3.connect(RUTA_BD)
    conexion.execute("PRAGMA foreign_keys = ON;")
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

    conexion = obtener_conexion()

    if not bd_ya_existia:
        with open(RUTA_SCRIPT_SQL, "r", encoding="utf-8") as archivo:
            script = archivo.read()
        conexion.executescript(script)
        conexion.commit()
        print(f"Base de datos creada en: {RUTA_BD}")
    else:
        print(f"Base de datos ya existente en: {RUTA_BD}")

    conexion.close()


if __name__ == "__main__":
    # Permite correr este archivo directamente para inicializar la BD:
    #   python conexion.py
    inicializar_base_de_datos()