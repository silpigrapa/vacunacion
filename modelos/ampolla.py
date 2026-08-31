"""
Modelo de AMPOLLA.
Maneja las unidades físicas de stock: alta desde un lote, consulta de
disponibilidad (en stock y no vencida) y descuento de dosis al aplicar
una vacuna o al importar aplicaciones desde el CSV.
"""

from database.conexion import obtener_conexion


def crear_ampolla(id_lote, id_vacunatorio_actual, dosis_disponibles, fecha_apertura=None):
    """
    Da de alta una ampolla física, asociada a un lote y ubicada en un
    vacunatorio. dosis_disponibles normalmente arranca en el valor de
    VACUNA.dosis_por_ampolla.
    Devuelve el id_ampolla generado.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """
        INSERT INTO AMPOLLA (fecha_apertura, dosis_disponibles, id_lote, id_vacunatorio_actual)
        VALUES (?, ?, ?, ?)
        """,
        (fecha_apertura, dosis_disponibles, id_lote, id_vacunatorio_actual),
    )
    conexion.commit()
    id_ampolla = cursor.lastrowid
    conexion.close()
    return id_ampolla


def obtener_ampolla_por_id(id_ampolla):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM AMPOLLA WHERE id_ampolla = ?", (id_ampolla,))
    fila = cursor.fetchone()
    conexion.close()
    return fila


def listar_ampollas_utilizables(id_vacunatorio, id_vacuna=None):
    """
    Devuelve las ampollas de un vacunatorio que están:
      - en stock (dosis_disponibles > 0)
      - no vencidas (LOTE.fecha_vencimiento >= hoy)
    Ordenadas por fecha de vencimiento (consumo FIFO: se gasta primero
    lo que vence antes).

    Si se pasa id_vacuna, filtra además por esa vacuna puntual.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    condiciones = """
        a.id_vacunatorio_actual = ?
        AND a.dosis_disponibles > 0
        AND l.fecha_vencimiento >= date('now')
    """
    parametros = [id_vacunatorio]

    if id_vacuna is not None:
        condiciones += " AND l.id_vacuna = ?"
        parametros.append(id_vacuna)

    cursor.execute(
        f"""
        SELECT a.*, l.numero_lote, l.fecha_vencimiento, l.id_vacuna
        FROM AMPOLLA a
        JOIN LOTE l ON a.id_lote = l.id_lote
        WHERE {condiciones}
        ORDER BY l.fecha_vencimiento ASC
        """,
        parametros,
    )
    filas = cursor.fetchall()
    conexion.close()
    return filas


def obtener_stock_total(id_vacunatorio, id_vacuna):
    """
    Devuelve la suma de dosis_disponibles utilizables (en stock y no
    vencidas) para una vacuna puntual en un vacunatorio. Es la consulta
    clave para saber "cuánto stock queda" de una vacuna.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """
        SELECT COALESCE(SUM(a.dosis_disponibles), 0) AS stock_total
        FROM AMPOLLA a
        JOIN LOTE l ON a.id_lote = l.id_lote
        WHERE a.id_vacunatorio_actual = ?
          AND l.id_vacuna = ?
          AND a.dosis_disponibles > 0
          AND l.fecha_vencimiento >= date('now')
        """,
        (id_vacunatorio, id_vacuna),
    )
    fila = cursor.fetchone()
    conexion.close()
    return fila["stock_total"]


def obtener_ampolla_con_stock_por_lote(id_lote):
    """
    Devuelve una ampolla con dosis_disponibles > 0 dentro de un lote
    puntual (la primera que encuentra), o None si no queda stock en
    ese lote. Se usa durante la importación del CSV: una vez que se
    identifica a qué LOTE corresponde una aplicación, hay que
    descontar la dosis de alguna ampolla de ese lote.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """
        SELECT * FROM AMPOLLA
        WHERE id_lote = ? AND dosis_disponibles > 0
        ORDER BY id_ampolla ASC
        LIMIT 1
        """,
        (id_lote,),
    )
    fila = cursor.fetchone()
    conexion.close()
    return fila


def descontar_dosis(id_ampolla, cantidad=1):
    """
    Descuenta 'cantidad' dosis de una ampolla puntual (por defecto, 1).
    Si es la primera vez que se usa (fecha_apertura vacía), la marca
    como abierta ahora.
    No permite que dosis_disponibles quede en negativo.
    Devuelve True si se pudo descontar, False si no había stock suficiente.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("SELECT dosis_disponibles, fecha_apertura FROM AMPOLLA WHERE id_ampolla = ?", (id_ampolla,))
    fila = cursor.fetchone()

    if fila is None or fila["dosis_disponibles"] < cantidad:
        conexion.close()
        return False

    nueva_fecha_apertura = fila["fecha_apertura"] or "CURRENT_TIMESTAMP"

    if fila["fecha_apertura"] is None:
        cursor.execute(
            """
            UPDATE AMPOLLA
            SET dosis_disponibles = dosis_disponibles - ?,
                fecha_apertura = datetime('now')
            WHERE id_ampolla = ?
            """,
            (cantidad, id_ampolla),
        )
    else:
        cursor.execute(
            """
            UPDATE AMPOLLA
            SET dosis_disponibles = dosis_disponibles - ?
            WHERE id_ampolla = ?
            """,
            (cantidad, id_ampolla),
        )

    conexion.commit()
    conexion.close()
    return True