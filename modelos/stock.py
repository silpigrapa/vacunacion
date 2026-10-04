"""
Modelo de STOCK / AMPOLLAS.
Permite consultar las ampollas registradas en un vacunatorio,
registrar la apertura de ampollas, descontar dosis aplicadas y ver resúmenes.
"""

from database.conexion import obtener_conexion
from datetime import datetime


def obtener_stock_por_vacunatorio(id_vacunatorio: int = None):
    """
    Devuelve el inventario detallado de ampollas.
    Si se especifica id_vacunatorio, filtra por ese centro de salud.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    sql = """
        SELECT 
            a.id_ampolla,
            v.nombre AS vacuna,
            v.nombre AS vacuna_nombre,
            l.numero_lote,
            l.fecha_vencimiento,
            a.dosis_disponibles,
            v.dosis_por_ampolla,
            a.fecha_apertura,
            vc.nombre AS vacunatorio
        FROM AMPOLLA a
        INNER JOIN LOTE l ON a.id_lote = l.id_lote
        INNER JOIN VACUNA v ON l.id_vacuna = v.id_vacuna
        INNER JOIN VACUNATORIO vc ON a.id_vacunatorio_actual = vc.id_vacunatorio
        WHERE a.dosis_disponibles > 0
    """

    parametros = []
    if id_vacunatorio is not None:
        sql += " AND a.id_vacunatorio_actual = ?"
        parametros.append(id_vacunatorio)

    sql += " ORDER BY l.fecha_vencimiento ASC, a.id_ampolla ASC"

    cursor.execute(sql, parametros)
    filas = cursor.fetchall()
    conexion.close()
    return filas


def obtener_resumen_stock(id_vacunatorio: int = None):
    """
    Devuelve un resumen consolidado del stock agrupado por vacuna y lote,
    calculando la cantidad de ampollas y el total de dosis disponibles.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    sql = """
        SELECT 
            v.nombre AS vacuna,
            l.numero_lote,
            l.fecha_vencimiento,
            COUNT(a.id_ampolla) AS total_ampollas,
            SUM(a.dosis_disponibles) AS total_dosis,
            vc.nombre AS vacunatorio
        FROM AMPOLLA a
        INNER JOIN LOTE l ON a.id_lote = l.id_lote
        INNER JOIN VACUNA v ON l.id_vacuna = v.id_vacuna
        INNER JOIN VACUNATORIO vc ON a.id_vacunatorio_actual = vc.id_vacunatorio
        WHERE a.dosis_disponibles > 0
    """

    parametros = []
    if id_vacunatorio is not None:
        sql += " AND a.id_vacunatorio_actual = ?"
        parametros.append(id_vacunatorio)

    sql += " GROUP BY v.id_vacuna, l.id_lote, a.id_vacunatorio_actual ORDER BY l.fecha_vencimiento ASC"

    cursor.execute(sql, parametros)
    filas = cursor.fetchall()
    conexion.close()
    return filas


def descontar_dosis_ampolla(id_ampolla: int, dosis_a_descontar: int = 1):
    """
    Descuenta una o más dosis de una ampolla específica.
    Si la ampolla no estaba abierta, registra automáticamente la fecha de apertura.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute(
        "SELECT dosis_disponibles, fecha_apertura FROM AMPOLLA WHERE id_ampolla = ?",
        (id_ampolla,)
    )
    ampolla = cursor.fetchone()

    if not ampolla:
        conexion.close()
        raise ValueError("La ampolla especificada no existe.")

    dosis_actuales = ampolla["dosis_disponibles"]

    if dosis_actuales < dosis_a_descontar:
        conexion.close()
        raise ValueError(f"No hay suficientes dosis. Disponibles: {dosis_actuales}")

    nuevas_dosis = dosis_actuales - dosis_a_descontar
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if ampolla["fecha_apertura"] is None:
        cursor.execute(
            """
            UPDATE AMPOLLA
            SET dosis_disponibles = ?, fecha_apertura = ?
            WHERE id_ampolla = ?
            """,
            (nuevas_dosis, fecha_actual, id_ampolla)
        )
    else:
        cursor.execute(
            """
            UPDATE AMPOLLA
            SET dosis_disponibles = ?
            WHERE id_ampolla = ?
            """,
            (nuevas_dosis, id_ampolla)
        )

    conexion.commit()
    conexion.close()
    return nuevas_dosis


# --- ALIAS DE COMPATIBILIDAD ---
def listar_ampollas_detalle(id_vacunatorio: int = None):
    return obtener_stock_por_vacunatorio(id_vacunatorio)

def listar_stock_por_vacunatorio(id_vacunatorio: int = None):
    return obtener_stock_por_vacunatorio(id_vacunatorio)

def registrar_descuento_dosis(id_ampolla: int, dosis: int = 1):
    return descontar_dosis_ampolla(id_ampolla, dosis)