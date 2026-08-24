"""
Modelo de VACUNA (el catálogo se genera dinámicamente).
CRUD básico: crear, buscar por id, buscar por nombre, listar, actualizar.
"""

from database.conexion import obtener_conexion


def crear_vacuna(nombre, fabricante=None, dosis_requeridas=1, dosis_por_ampolla=1):
    """
    Da de alta una vacuna en el catálogo.
    dosis_requeridas: cuántas dosis necesita UN paciente (esquema completo).
    dosis_por_ampolla: cuántos pacientes puede cubrir UNA ampolla.
    Devuelve el id_vacuna generado.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """
        INSERT INTO VACUNA (nombre, fabricante, dosis_requeridas, dosis_por_ampolla)
        VALUES (?, ?, ?, ?)
        """,
        (nombre, fabricante, dosis_requeridas, dosis_por_ampolla),
    )
    conexion.commit()
    id_vacuna = cursor.lastrowid
    conexion.close()
    return id_vacuna


def obtener_vacuna_por_id(id_vacuna):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM VACUNA WHERE id_vacuna = ?", (id_vacuna,))
    fila = cursor.fetchone()
    conexion.close()
    return fila


def obtener_vacuna_por_nombre(nombre):
    """
    Busca una vacuna por nombre exacto. Se usa, por ejemplo, durante la
    importación del CSV para relacionar la columna 'Vacuna' del archivo
    con el catálogo interno.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM VACUNA WHERE nombre = ?", (nombre,))
    fila = cursor.fetchone()
    conexion.close()
    return fila


def listar_vacunas():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM VACUNA ORDER BY nombre")
    filas = cursor.fetchall()
    conexion.close()
    return filas


def actualizar_vacuna(id_vacuna, nombre, fabricante=None, dosis_requeridas=1, dosis_por_ampolla=1):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """
        UPDATE VACUNA
        SET nombre = ?, fabricante = ?, dosis_requeridas = ?, dosis_por_ampolla = ?
        WHERE id_vacuna = ?
        """,
        (nombre, fabricante, dosis_requeridas, dosis_por_ampolla, id_vacuna),
    )
    conexion.commit()
    filas_afectadas = cursor.rowcount
    conexion.close()
    return filas_afectadas > 0