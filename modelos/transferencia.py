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
    lista_id_ampollas: list,
    observaciones: str = None,
):
    """
    Registra una nueva transferencia en la BD:
    1. Inserta la cabecera en TRANSFERENCIA.
    2. Valida cada ampolla (existe y pertenece al origen) ANTES de tocarla.
    3. Inserta cada ampolla en TRANSFERENCIA_DETALLE.
    4. Actualiza el vacunatorio_actual de las ampollas en la tabla AMPOLLA.

    Usa una transacción (commit al final o rollback si falla algo)
    para garantizar la integridad de los datos.

    Nota: la validación previa (paso 2) evita que una ampolla
    inexistente dispare un sqlite3.IntegrityError (por la FOREIGN KEY
    de TRANSFERENCIA_DETALLE hacia AMPOLLA) en vez del ValueError
    claro que se quiere mostrar en la interfaz.
    """
    if id_vacunatorio_origen == id_vacunatorio_destino:
        raise ValueError(
            "El vacunatorio de origen y destino no pueden ser el mismo."
        )

    if not lista_id_ampollas:
        raise ValueError("Debe incluir al menos una ampolla en la transferencia.")

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        # 1) Insertar cabecera de la transferencia
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

        # 2) Insertar detalles y actualizar stock/ubicación de cada ampolla
        for id_ampolla in lista_id_ampollas:
            # Validar ANTES de insertar/actualizar, para distinguir
            # "no existe" de "existe pero está en otro vacunatorio" y
            # dar siempre un ValueError claro (nunca un error crudo de SQLite).
            cursor.execute(
                "SELECT id_vacunatorio_actual FROM AMPOLLA WHERE id_ampolla = ?",
                (id_ampolla,),
            )
            fila_ampolla = cursor.fetchone()

            if fila_ampolla is None:
                raise ValueError(f"La ampolla ID {id_ampolla} no existe.")

            if fila_ampolla["id_vacunatorio_actual"] != id_vacunatorio_origen:
                raise ValueError(
                    f"La ampolla ID {id_ampolla} no pertenece al vacunatorio de origen."
                )

            # Insertar detalle
            cursor.execute(
                """
                INSERT INTO TRANSFERENCIA_DETALLE (id_transferencia, id_ampolla)
                VALUES (?, ?)
                """,
                (id_transferencia, id_ampolla),
            )

            # Cambiar de lugar la ampolla al vacunatorio destino
            cursor.execute(
                """
                UPDATE AMPOLLA
                SET id_vacunatorio_actual = ?
                WHERE id_ampolla = ? AND id_vacunatorio_actual = ?
                """,
                (id_vacunatorio_destino, id_ampolla, id_vacunatorio_origen),
            )

        # Confirmar la transacción
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
    Incluye nombres del vacunatorio origen, destino y usuario que la realizó.

    Si se pasa id_vacunatorio, filtra aquellas donde ese centro haya sido
    origen o destino.
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


def obtener_transferencia_por_id(id_transferencia: int):
    """
    Devuelve la cabecera completa de una transferencia dada por su ID.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute(
        """
        SELECT 
            t.id_transferencia,
            t.numero_remito,
            t.fecha,
            t.observaciones,
            t.id_vacunatorio_origen,
            t.id_vacunatorio_destino,
            t.id_usuario,
            vo.nombre AS origen,
            vd.nombre AS destino,
            (u.nombre || ' ' || u.apellido) AS usuario
        FROM TRANSFERENCIA t
        INNER JOIN VACUNATORIO vo ON t.id_vacunatorio_origen = vo.id_vacunatorio
        INNER JOIN VACUNATORIO vd ON t.id_vacunatorio_destino = vd.id_vacunatorio
        INNER JOIN USUARIO u ON t.id_usuario = u.id_usuario
        WHERE t.id_transferencia = ?
        """,
        (id_transferencia,),
    )

    fila = cursor.fetchone()
    conexion.close()
    return fila


def obtener_detalle_transferencia(id_transferencia: int):
    """
    Devuelve la lista de ampollas/vacunas asociadas a un remito de transferencia.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute(
        """
        SELECT 
            td.id_ampolla,
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