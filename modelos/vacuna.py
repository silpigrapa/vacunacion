"""
Modelo de VACUNA (el catálogo se genera dinámicamente).
CRUD básico: crear, buscar por id, buscar por nombre, listar, actualizar.
"""

from database.conexion import obtener_conexion
from modelos.lote import crear_lote
from modelos.ampolla import crear_ampolla


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


def registrar_ingreso_central(
    nombre,
    numero_lote,
    fecha_vencimiento,
    cantidad_ampollas,
    id_vacunatorio,
    fabricante=None,
    dosis_requeridas=1,
    dosis_por_ampolla=1,
):
    """
    Registra la llegada de un lote al hospital central: reutiliza la
    vacuna del catálogo si ya existe (por nombre) o la crea si es
    nueva, da de alta el lote y genera una AMPOLLA por cada unidad
    física indicada en cantidad_ampollas (cada una arranca con
    dosis_disponibles = dosis_por_ampolla de la vacuna).

    Devuelve una tupla (id_lote, id_vacuna, vacuna_nueva), donde
    vacuna_nueva es True si la vacuna se creó en este llamado y False
    si ya existía en el catálogo.
    """
    vacuna_existente = obtener_vacuna_por_nombre(nombre)

    if vacuna_existente is not None:
        id_vacuna = vacuna_existente["id_vacuna"]
        dosis_por_ampolla_efectiva = vacuna_existente["dosis_por_ampolla"]
        vacuna_nueva = False
    else:
        id_vacuna = crear_vacuna(
            nombre=nombre,
            fabricante=fabricante,
            dosis_requeridas=dosis_requeridas,
            dosis_por_ampolla=dosis_por_ampolla,
        )
        dosis_por_ampolla_efectiva = dosis_por_ampolla
        vacuna_nueva = True

    id_lote = crear_lote(
        numero_lote=numero_lote,
        fecha_vencimiento=fecha_vencimiento,
        cantidad_ampollas=cantidad_ampollas,
        id_vacuna=id_vacuna,
        id_vacunatorio=id_vacunatorio,
    )

    for _ in range(cantidad_ampollas):
        crear_ampolla(
            id_lote=id_lote,
            id_vacunatorio_actual=id_vacunatorio,
            dosis_disponibles=dosis_por_ampolla_efectiva,
        )

    return id_lote, id_vacuna, vacuna_nueva