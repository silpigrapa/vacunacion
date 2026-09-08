"""
Modelo de VACUNATORIO.
CRUD básico: crear, obtener por id, listar todos, actualizar.
"""

from database.conexion import obtener_conexion


def crear_vacunatorio(nombre, direccion, telefono=None, es_central=False):
    """
    Crea un nuevo vacunatorio. Devuelve el id_vacunatorio generado.
    Si es_central=True, se desmarca cualquier otro vacunatorio que
    fuera central antes (garantiza que exista uno solo a la vez).
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        if es_central:
            cursor.execute("UPDATE VACUNATORIO SET es_central = 0 WHERE es_central = 1")
        cursor.execute(
            """
            INSERT INTO VACUNATORIO (nombre, direccion, telefono, es_central)
            VALUES (?, ?, ?, ?)
            """,
            (nombre, direccion, telefono, 1 if es_central else 0),
        )
        conexion.commit()
        return cursor.lastrowid
    finally:
        conexion.close()


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


def obtener_vacunatorio_por_nombre(nombre):
    """
    Busca un vacunatorio por su nombre exacto. Se usa durante la
    importación del CSV para relacionar la columna 'Establecimiento'
    del archivo con un vacunatorio cargado en el sistema.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM VACUNATORIO WHERE nombre = ?", (nombre,))
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


def marcar_como_central(id_vacunatorio):
    """
    Marca el vacunatorio indicado como el central, y desmarca
    cualquier otro que lo fuera antes (garantiza que exista como
    máximo un único vacunatorio central a la vez).
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute("UPDATE VACUNATORIO SET es_central = 0 WHERE es_central = 1")
        cursor.execute(
            "UPDATE VACUNATORIO SET es_central = 1 WHERE id_vacunatorio = ?",
            (id_vacunatorio,),
        )
        conexion.commit()
    finally:
        conexion.close()


def eliminar_vacunatorio(id_vacunatorio):
    """
    Elimina un vacunatorio. Si tiene datos asociados (usuarios, lotes,
    ampollas, aplicaciones o transferencias que lo referencian), la
    base rechaza el borrado por la restricción de clave foránea
    (PRAGMA foreign_keys = ON) — en ese caso se relanza un ValueError
    con un mensaje claro para mostrar en la interfaz
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute("DELETE FROM VACUNATORIO WHERE id_vacunatorio = ?", (id_vacunatorio,))
        conexion.commit()
        return cursor.rowcount > 0
    except Exception as error:
        conexion.rollback()
        raise ValueError(
            "No se puede eliminar: este vacunatorio tiene datos asociados "
            "(usuarios, lotes, ampollas, aplicaciones o transferencias)."
        ) from error
    finally:
        conexion.close()