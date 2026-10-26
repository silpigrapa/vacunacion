"""
Modelo de TRANSFERENCIA y TRANSFERENCIA_DETALLE.
Maneja el registro de remitos de envío entre centros/vacunatorios
y la consulta de transferencias con su detalle de ampollas.
Aadaptado dinámicamente para soportar esquemas con o sin columna 'cantidad'.
"""

from database.conexion import obtener_conexion


def registrar_transferencia(
    numero_remito: str,
    fecha: str,
    id_vacunatorio_origen: int,
    id_vacunatorio_destino: int,
    id_usuario: int,
    lista_ampollas_con_cantidad: list,
    observaciones: str = None,
):
    """
    Registra una nueva transferencia en la BD:
    1. Inserta la cabecera en TRANSFERENCIA.
    2. Inserta el detalle en TRANSFERENCIA_DETALLE (detecta si existe la columna 'cantidad').
    3. Actualiza la ubicación de la ampolla en AMPOLLA (descuenta del origen y suma al destino).
    """
    if id_vacunatorio_origen == id_vacunatorio_destino:
        raise ValueError("El vacunatorio de origen y destino no pueden ser el mismo.")

    if not lista_ampollas_con_cantidad:
        raise ValueError("Debe incluir al menos una ampolla en la transferencia.")

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        # 1) Detectar si la tabla TRANSFERENCIA_DETALLE tiene la columna 'cantidad'
        cursor.execute("PRAGMA table_info(TRANSFERENCIA_DETALLE);")
        columnas = [col["name"] if isinstance(col, dict) else col[1] for col in cursor.fetchall()]
        tiene_columna_cantidad = "cantidad" in columnas

        # 2) Insertar cabecera de la transferencia
        cursor.execute(
            """
            INSERT INTO TRANSFERENCIA (
                numero_remito, fecha, id_vacunatorio_origen,
                id_vacunatorio_destino, id_usuario, observaciones
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                numero_remito,
                fecha,
                id_vacunatorio_origen,
                id_vacunatorio_destino,
                id_usuario,
                observaciones,
            ),
        )
        id_transferencia = cursor.lastrowid

        # 3) Insertar en detalle según las columnas disponibles
        for item in lista_ampollas_con_cantidad:
            if isinstance(item, (list, tuple)):
                id_ampolla, cantidad = item[0], item[1]
            else:
                id_ampolla, cantidad = item, 1

            if tiene_columna_cantidad:
                cursor.execute(
                    """
                    INSERT INTO TRANSFERENCIA_DETALLE (id_transferencia, id_ampolla, cantidad)
                    VALUES (?, ?, ?)
                    """,
                    (id_transferencia, id_ampolla, cantidad),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO TRANSFERENCIA_DETALLE (id_transferencia, id_ampolla)
                    VALUES (?, ?)
                    """,
                    (id_transferencia, id_ampolla),
                )

            # Resta del stock de origen y suma al de destino actualizando la ubicación física
            cursor.execute(
                """
                UPDATE AMPOLLA
                SET id_vacunatorio_actual = ?
                WHERE id_ampolla = ? AND id_vacunatorio_actual = ?
                """,
                (id_vacunatorio_destino, id_ampolla, id_vacunatorio_origen),
            )

        conexion.commit()
        return id_transferencia

    except Exception as e:
        conexion.rollback()
        raise e
    finally:
        conexion.close()


def listar_transferencias(id_vacunatorio: int = None):
    """
    Devuelve la lista de transferencias ordenadas por fecha descendente.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    sql = """
        SELECT 
            t.id_transferencia,
            t.numero_remito,
            t.fecha,
            t.observaciones,
            vo.nombre AS origen,
            vd.nombre AS destino,
            (u.nombre || ' ' || u.apellido) AS usuario
        FROM TRANSFERENCIA t
        INNER JOIN VACUNATORIO vo ON t.id_vacunatorio_origen = vo.id_vacunatorio
        INNER JOIN VACUNATORIO vd ON t.id_vacunatorio_destino = vd.id_vacunatorio
        INNER JOIN USUARIO u ON t.id_usuario = u.id_usuario
    """

    parametros = []
    if id_vacunatorio is not None:
        sql += " WHERE t.id_vacunatorio_origen = ? OR t.id_vacunatorio_destino = ?"
        parametros.extend([id_vacunatorio, id_vacunatorio])

    sql += " ORDER BY t.fecha DESC"

    cursor.execute(sql, parametros)
    filas = cursor.fetchall()
    conexion.close()

    return filas


def obtener_detalle_transferencia(id_transferencia: int):
    """
    Devuelve las ampollas asociadas a una transferencia.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    # Verificar si existe la columna 'cantidad' para incluirla en la consulta
    cursor.execute("PRAGMA table_info(TRANSFERENCIA_DETALLE);")
    columnas = [col["name"] if isinstance(col, dict) else col[1] for col in cursor.fetchall()]
    col_cant = "td.cantidad" if "cantidad" in columnas else "1 AS cantidad"

    cursor.execute(
        f"""
        SELECT 
            td.id_ampolla,
            {col_cant},
            a.dosis_disponibles,
            a.fecha_apertura,
            l.numero_lote,
            l.fecha_vencimiento,
            v.nombre AS vacuna_nombre
        FROM TRANSFERENCIA_DETALLE td
        INNER JOIN AMPOLLA a ON td.id_ampolla = a.id_ampolla
        INNER JOIN LOTE l ON a.id_lote = l.id_lote
        INNER JOIN VACUNA v ON l.id_vacuna = v.id_vacuna
        WHERE td.id_transferencia = ?
        """,
        (id_transferencia,),
    )

    filas = cursor.fetchall()
    conexion.close()
    return filas