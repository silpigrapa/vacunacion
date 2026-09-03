"""
Script para crear un usuario en el Sistema de Vacunación.

Usalo cuando la base de datos no tiene ningún usuario todavía
(por ejemplo, la primera vez que armás el proyecto, o si la
base se recreó vacía).

Uso:
    python crear_usuario_inicial.py

IMPORTANTE: copiá este archivo dentro de la carpeta
'sistema_vacunacion' (al mismo nivel que main.py) antes de
ejecutarlo.
"""

import hashlib
import sqlite3
import os

CARPETA_BASE = os.path.dirname(os.path.abspath(__file__))
RUTA_BD = os.path.join(CARPETA_BASE, "database", "sistema_vacunacion.db")


def hashear_contrasena(contrasena_plana: str) -> str:
    return hashlib.sha256(contrasena_plana.encode("utf-8")).hexdigest()


def main():
    if not os.path.exists(RUTA_BD):
        print(f"No encontré la base de datos en: {RUTA_BD}")
        print("Corré primero database/conexion.py para crearla (o main.py).")
        return

    conexion = sqlite3.connect(RUTA_BD)
    cursor = conexion.cursor()

    # Mostrar usuarios existentes, si hay
    cursor.execute("SELECT usuario FROM USUARIO")
    existentes = cursor.fetchall()
    if existentes:
        print("\nYa existen estos usuarios:")
        for u in existentes:
            print(f"  - {u[0]}")
        print()
    else:
        print("\nLa tabla USUARIO está vacía. Vamos a crear el primer usuario.\n")

    # Necesitamos un vacunatorio para asociar el usuario (clave foránea NOT NULL)
    cursor.execute("SELECT id_vacunatorio, nombre FROM VACUNATORIO")
    vacunatorios = cursor.fetchall()

    if not vacunatorios:
        print("No hay ningún vacunatorio cargado en la base.")
        print("Creo uno genérico llamado 'Central' para poder asociar el usuario...")
        cursor.execute(
            "INSERT INTO VACUNATORIO (nombre, direccion, es_central) VALUES (?, ?, 1)",
            ("Central", "Sin especificar"),
        )
        conexion.commit()
        id_vacunatorio = cursor.lastrowid
    elif len(vacunatorios) == 1:
        id_vacunatorio = vacunatorios[0][0]
    else:
        print("Vacunatorios disponibles:")
        for v in vacunatorios:
            print(f"  - id {v[0]}: {v[1]}")
        id_vacunatorio = int(input("ID del vacunatorio a asociar al usuario: "))

    nombre = input("Nombre: ").strip()
    apellido = input("Apellido: ").strip()
    usuario = input("Usuario (para loguearse, ej: admin): ").strip()
    contrasena_plana = input("Contraseña: ")

    contrasena_hash = hashear_contrasena(contrasena_plana)

    try:
        cursor.execute(
            """
            INSERT INTO USUARIO (nombre, apellido, usuario, contrasena, id_vacunatorio)
            VALUES (?, ?, ?, ?, ?)
            """,
            (nombre, apellido, usuario, contrasena_hash, id_vacunatorio),
        )
        conexion.commit()
        print(f"\nUsuario '{usuario}' creado correctamente. Ya podés iniciar sesión.")
    except sqlite3.IntegrityError:
        print(f"\nYa existe un usuario con el nombre '{usuario}'. Elegí otro o usá el script de reseteo de contraseña.")
    finally:
        conexion.close()


if __name__ == "__main__":
    main()