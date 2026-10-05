"""
Modelo de STOCK.s
"""

from database.conexion import obtener_conexion


def listar_stock_por_vacunatorio(id_vacunatorio):
    """
    Devuelve el stock 
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """
        SELECT
            v.id_vacuna,
            v.nombre AS nombre_vacuna,
            v.fabricante,
            COUNT(a.id_ampolla) AS cantidad_ampollas,
            COALESCE(SUM(a.dosis_disponibles), 0) AS dosis_disponibles,
            MIN(l.fecha_vencimiento) AS proximo_vencimiento
        FROM AMPOLLA a
        JOIN LOTE l ON a.id_lote = l.id_lote
        JOIN VACUNA v ON l.id_vacuna = v.id_vacuna
        WHERE a.id_vacunatorio_actual = ?
          AND a.dosis_disponibles > 0
        GROUP BY v.id_vacuna
        ORDER BY v.nombre
        """,
        (id_vacunatorio,),
    )
    filas = cursor.fetchall()
    conexion.close()
    return filas


def listar_stock_general():
    """
    Devuelve el stock agrupado por vacunatorio + vacuna
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """
        SELECT
            vt.id_vacunatorio,
            vt.nombre AS nombre_vacunatorio,
            v.id_vacuna,
            v.nombre AS nombre_vacuna,
            COUNT(a.id_ampolla) AS cantidad_ampollas,
            COALESCE(SUM(a.dosis_disponibles), 0) AS dosis_disponibles,
            MIN(l.fecha_vencimiento) AS proximo_vencimiento
        FROM AMPOLLA a
        JOIN LOTE l ON a.id_lote = l.id_lote
        JOIN VACUNA v ON l.id_vacuna = v.id_vacuna
        JOIN VACUNATORIO vt ON a.id_vacunatorio_actual = vt.id_vacunatorio
        WHERE a.dosis_disponibles > 0
        GROUP BY vt.id_vacunatorio, v.id_vacuna
        ORDER BY vt.nombre, v.nombre
        """
    )
    filas = cursor.fetchall()
    conexion.close()
    return filas


def listar_ampollas_detalle(id_vacunatorio=None, id_vacuna=None, incluir_agotadas=False):
    """
    Devuelve el detalle ampolla por ampolla 
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    condiciones = ["1 = 1"]
    parametros = []

    if id_vacunatorio is not None:
        condiciones.append("a.id_vacunatorio_actual = ?")
        parametros.append(id_vacunatorio)

    if id_vacuna is not None:
        condiciones.append("l.id_vacuna = ?")
        parametros.append(id_vacuna)

    if not incluir_agotadas:
        condiciones.append("a.dosis_disponibles > 0")

    cursor.execute(
        f"""
        SELECT
            a.id_ampolla,
            a.dosis_disponibles,
            a.fecha_apertura,
            l.numero_lote,
            l.fecha_vencimiento,
            v.id_vacuna,
            v.nombre AS nombre_vacuna,
            vt.nombre AS nombre_vacunatorio
        FROM AMPOLLA a
        JOIN LOTE l ON a.id_lote = l.id_lote
        JOIN VACUNA v ON l.id_vacuna = v.id_vacuna
        JOIN VACUNATORIO vt ON a.id_vacunatorio_actual = vt.id_vacunatorio
        WHERE {" AND ".join(condiciones)}
        ORDER BY l.fecha_vencimiento ASC, a.id_ampolla ASC
        """,
        parametros,
    )
    filas = cursor.fetchall()
    conexion.close()
    return filas


def obtener_resumen_stock(id_vacunatorio=None):
    """
    Devuelve un resumen numérico rápido
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    condicion = ""
    parametros = []
    if id_vacunatorio is not None:
        condicion = "AND a.id_vacunatorio_actual = ?"
        parametros.append(id_vacunatorio)

    cursor.execute(
        f"""
        SELECT
            COUNT(DISTINCT l.id_vacuna) AS vacunas_con_stock,
            COUNT(a.id_ampolla) AS ampollas_con_stock,
            COALESCE(SUM(a.dosis_disponibles), 0) AS dosis_disponibles
        FROM AMPOLLA a
        JOIN LOTE l ON a.id_lote = l.id_lote
        WHERE a.dosis_disponibles > 0
        {condicion}
        """,
        parametros,
    )
    fila = cursor.fetchone()
    conexion.close()
    return fila
