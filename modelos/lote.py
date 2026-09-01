"""
Modelo de LOTE.
CRUD básico + consultas de vencimiento, útiles para el control de stock.
"""

from database.conexion import obtener_conexion


def crear_lote(numero_lote, fecha_vencimiento, cantidad_ampollas, id_vacuna, id_vacunatorio):
    """
    Da de alta un lote. fecha_vencimiento en formato 'YYYY-MM-DD'.
    Devuelve el id_lote generado.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """
        INSERT INTO LOTE (numero_lote, fecha_vencimiento, cantidad_ampollas, id_vacuna, id_vacunatorio)
        VALUES (?, ?, ?, ?, ?)
        """,
        (numero_lote, fecha_vencimiento, cantidad_ampollas, id_vacuna, id_vacunatorio),
    )
    conexion.commit()
    id_lote = cursor.lastrowid
    conexion.close()
    return id_lote


def obtener_lote_por_id(id_lote):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM LOTE WHERE id_lote = ?", (id_lote,))
    fila = cursor.fetchone()
    conexion.close()
    return fila


def obtener_lote_por_numero(numero_lote, id_vacunatorio):
    """
    Busca un lote por su número dentro de un vacunatorio puntual.
    Se usa durante la importación del CSV para relacionar la columna
    'Lote' del archivo con un lote cargado en el sistema.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT * FROM LOTE WHERE numero_lote = ? AND id_vacunatorio = ?",
        (numero_lote, id_vacunatorio),
    )
    fila = cursor.fetchone()
    conexion.close()
    return fila


def listar_lotes():
    """
    Devuelve todos los lotes registrados en el sistema, sin importar el
    vacunatorio, con el nombre de la vacuna y del vacunatorio incluidos
    (JOIN). Se usa en la vista de Vacunas para mostrar el listado
    general de lotes ingresados en el hospital central.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """
        SELECT l.*, v.nombre AS nombre_vacuna, vt.nombre AS nombre_vacunatorio
        FROM LOTE l
        JOIN VACUNA v ON l.id_vacuna = v.id_vacuna
        JOIN VACUNATORIO vt ON l.id_vacunatorio = vt.id_vacunatorio
        ORDER BY l.fecha_vencimiento ASC
        """
    )
    filas = cursor.fetchall()
    conexion.close()
    return filas


def listar_lotes_por_vacunatorio(id_vacunatorio):
    """
    Devuelve todos los lotes de un vacunatorio, con el nombre de la
    vacuna incluido (JOIN), ordenados por fecha de vencimiento
    (los que vencen antes, primero — útil para consumo FIFO).
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """
        SELECT l.*, v.nombre AS nombre_vacuna
        FROM LOTE l
        JOIN VACUNA v ON l.id_vacuna = v.id_vacuna
        WHERE l.id_vacunatorio = ?
        ORDER BY l.fecha_vencimiento ASC
        """,
        (id_vacunatorio,),
    )
    filas = cursor.fetchall()
    conexion.close()
    return filas


def listar_lotes_vencidos(id_vacunatorio=None):
    """
    Devuelve los lotes cuya fecha_vencimiento ya pasó.
    Si se pasa id_vacunatorio, filtra solo los de ese vacunatorio.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    if id_vacunatorio is not None:
        cursor.execute(
            """
            SELECT l.*, v.nombre AS nombre_vacuna
            FROM LOTE l
            JOIN VACUNA v ON l.id_vacuna = v.id_vacuna
            WHERE l.fecha_vencimiento < date('now') AND l.id_vacunatorio = ?
            ORDER BY l.fecha_vencimiento ASC
            """,
            (id_vacunatorio,),
        )
    else:
        cursor.execute(
            """
            SELECT l.*, v.nombre AS nombre_vacuna
            FROM LOTE l
            JOIN VACUNA v ON l.id_vacuna = v.id_vacuna
            WHERE l.fecha_vencimiento < date('now')
            ORDER BY l.fecha_vencimiento ASC
            """
        )
    filas = cursor.fetchall()
    conexion.close()
    return filas