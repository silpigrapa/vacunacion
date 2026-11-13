"""
Modelo de TRANSFERENCIA y TRANSFERENCIA_DETALLE.
Maneja el registro de remitos de envío entre centros/vacunatorios
y la consulta de transferencias con su detalle de ampollas.
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
    2. Inserta el detalle en TRANSFERENCIA_DETALLE.
    3. Mueve la ampolla física en la tabla AMPOLLA del vacunatorio origen al destino.
    """
    id_origen = int(id_vacunatorio_origen)
    id_destino = int(id_vacunatorio_destino)
    id_usr = int(id_usuario)

    if id_origen == id_destino:
        raise ValueError("El vacunatorio de origen y destino no pueden ser el mismo.")

    if not lista_ampollas_con_cantidad:
        raise ValueError("Debe incluir al menos una ampolla en la transferencia.")

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        # 1) Detectar columnas de TRANSFERENCIA_DETALLE
        cursor.execute("PRAGMA table_info(TRANSFERENCIA_DETALLE);")
        cols_det = [col["name"] if isinstance(col, dict) else col[1] for col in cursor.fetchall()]
        tiene_columna_cantidad = "cantidad" in cols_det

        # 2) Detectar el nombre exacto de la columna de ubicación en AMPOLLA
        cursor.execute("PRAGMA table_info(AMPOLLA);")
        cols_amp = [col["name"] if isinstance(col, dict) else col[1] for col in cursor.fetchall()]
        col_ubicacion = "id_vacunatorio_actual" if "id_vacunatorio_actual" in cols_amp else "id_vacunatorio"

        # 3) Insertar cabecera de la transferencia
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
                id_origen,
                id_destino,
                id_usr,
                observaciones,
            ),
        )
        id_transferencia = cursor.lastrowid

        # 4) Insertar en detalle y actualizar ubicación de cada ampolla
        for item in lista_ampollas_con_cantidad:
            if isinstance(item, (list, tuple)):
                id_ampolla = int(item[0])
                cantidad = int(item[1])
            else:
                id_ampolla = int(item)
                cantidad = 1

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

            # Mover la ampolla del CAP origen al CAP destino
            cursor.execute(
                f"""
                UPDATE AMPOLLA
                SET {col_ubicacion} = ?
                WHERE id_ampolla = ? AND {col_ubicacion} = ?
                """,
                (id_destino, id_ampolla, id_origen),
            )

            if cursor.rowcount == 0:
                raise RuntimeError(
                    f"No se pudo mover la ampolla #{id_ampolla}: no se encontró disponible en el centro de origen."
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
        parametros.extend([int(id_vacunatorio), int(id_vacunatorio)])

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
        (int(id_transferencia),),
    )

    filas = cursor.fetchall()
    conexion.close()
    return filas