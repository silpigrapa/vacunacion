"""
Modelo de USUARIO.
Contiene las funciones de acceso a datos relacionadas al login
y a la gestión del usuario del sistema.
"""

import hashlib
from database.conexion import obtener_conexion


def hashear_contrasena(contrasena_plana: str) -> str:
    """
    Convierte una contraseña en texto plano a su hash SHA-256.
    Nunca se guarda ni se compara la contraseña en texto plano.
    """
    return hashlib.sha256(contrasena_plana.encode("utf-8")).hexdigest()


def crear_usuario(nombre, apellido, usuario, contrasena_plana, id_vacunatorio):
    """
    Crea un nuevo usuario en la base, guardando la contraseña ya hasheada.
    Devuelve el id_usuario generado.
    """
    contrasena_hash = hashear_contrasena(contrasena_plana)

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """
        INSERT INTO USUARIO (nombre, apellido, usuario, contrasena, id_vacunatorio)
        VALUES (?, ?, ?, ?, ?)
        """,
        (nombre, apellido, usuario, contrasena_hash, id_vacunatorio),
    )
    conexion.commit()
    id_usuario = cursor.lastrowid
    conexion.close()
    return id_usuario


def validar_login(usuario: str, contrasena_plana: str):
    """
    Verifica las credenciales contra la base de datos.

    Devuelve el registro del usuario (sqlite3.Row) si las credenciales
    son correctas, o None si el usuario no existe o la contraseña es incorrecta.
    """
    contrasena_hash = hashear_contrasena(contrasena_plana)

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """
        SELECT id_usuario, nombre, apellido, usuario, id_vacunatorio
        FROM USUARIO
        WHERE usuario = ? AND contrasena = ?
        """,
        (usuario, contrasena_hash),
    )
    fila = cursor.fetchone()
    conexion.close()

    return fila  # None si no coincide usuario/contraseña