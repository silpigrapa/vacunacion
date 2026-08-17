"""
Modelo de VACUNATORIO.
CRUD básico: crear, obtener por id, listar todos, actualizar.
"""

from database.conexion import obtener_conexion


def crear_vacunatorio(nombre, direccion, telefono=None, es_central=False):
    """
    Crea un nuevo vacunatorio. Devuelve el id_vacunatorio generado.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """
        INSERT INTO VACUNATORIO (nombre, direccion, telefono, es_central)
        VALUES (?, ?, ?, ?)
        """,
        (nombre, direccion, telefono, 1 if es_central else 0),
    )
    conexion.commit()
    id_vacunatorio = cursor.lastrowid
    conexion.close()
    return id_vacunatorio


def obtener_vacunatorio_por_id(id_vacunatorio):
    """
    Devuelve el registro (sqlite3.Row) de un vacunatorio, o None si no existe.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT * FROM VACUNATORIO WHERE id_vacunatorio = ?",
        (id_vacunatorio,),
    )
    fila = cursor.fetchone()
    conexion.close()
    return fila


def listar_vacunatorios():
    """
    Devuelve la lista de todos los vacunatorios, ordenados por nombre.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM VACUNATORIO ORDER BY nombre")
    filas = cursor.fetchall()
    conexion.close()
    return filas


def obtener_vacunatorio_central():
    """
    Devuelve el vacunatorio marcado como central, o None si todavía
    no se cargó ninguno.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM VACUNATORIO WHERE es_central = 1 LIMIT 1")
    fila = cursor.fetchone()
    conexion.close()
    return fila


def actualizar_vacunatorio(id_vacunatorio, nombre, direccion, telefono=None):
    """
    Actualiza los datos de un vacunatorio existente.
    (es_central no se modifica acá para evitar cambios accidentales)
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """
        UPDATE VACUNATORIO
        SET nombre = ?, direccion = ?, telefono = ?
        WHERE id_vacunatorio = ?
        """,
        (nombre, direccion, telefono, id_vacunatorio),
    )
    conexion.commit()
    filas_afectadas = cursor.rowcount
    conexion.close()
    return filas_afectadas > 0  # True si encontró y actualizó el registro