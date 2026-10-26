"""
Modelo de VACUNA (el catálogo se genera dinámicamente).
CRUD básico: crear, buscar por id, buscar por nombre, listar, actualizar.
"""

from datetime import date

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


def guardar_opciones_vacuna_csv(nombres):
    """Agrega al banco los nombres de vacuna encontrados en un CSV."""
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor()
        cursor.executemany(
            "INSERT OR IGNORE INTO OPCION_VACUNA_CSV (nombre) VALUES (?)",
            [(nombre,) for nombre in nombres],
        )
        conexion.commit()
        return cursor.rowcount
    finally:
        conexion.close()


def listar_opciones_vacuna_csv():
    """Lista los nombres únicos detectados en los CSV seleccionados."""
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT nombre FROM OPCION_VACUNA_CSV ORDER BY nombre COLLATE NOCASE")
        return [fila["nombre"] for fila in cursor.fetchall()]
    finally:
        conexion.close()


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
    Registra la llegada de un lote al vacunatorio central: reutiliza la
    vacuna del catálogo si ya existe (por nombre) o la crea si es
    nueva, da de alta el lote y genera una AMPOLLA por cada unidad
    física indicada en cantidad_ampollas (cada una arranca con
    dosis_disponibles = dosis_por_ampolla de la vacuna).

    Devuelve una tupla (id_lote, id_vacuna, vacuna_nueva), donde
    vacuna_nueva es True si la vacuna se creó en este llamado y False
    si ya existía en el catálogo.
    """
    if not nombre or not nombre.strip():
        raise ValueError("El nombre de la vacuna es obligatorio.")
    if not numero_lote or not numero_lote.strip():
        raise ValueError("El número de lote es obligatorio.")
    if not all(
        isinstance(valor, int) and not isinstance(valor, bool) and valor > 0
        for valor in (dosis_requeridas, dosis_por_ampolla, cantidad_ampollas)
    ):
        raise ValueError("Dosis y cantidad de ampollas deben ser enteros positivos.")
    try:
        fecha_validada = date.fromisoformat(fecha_vencimiento)
        if fecha_validada.isoformat() != fecha_vencimiento:
            raise ValueError
    except (TypeError, ValueError) as error:
        raise ValueError("La fecha de vencimiento debe tener formato AAAA-MM-DD.") from error

    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT id_vacuna, dosis_por_ampolla FROM VACUNA WHERE nombre = ?",
            (nombre,),
        )
        vacuna_existente = cursor.fetchone()

        if vacuna_existente is None:
            cursor.execute(
                """
                INSERT INTO VACUNA (
                    nombre, fabricante, dosis_requeridas, dosis_por_ampolla
                ) VALUES (?, ?, ?, ?)
                """,
                (nombre, fabricante, dosis_requeridas, dosis_por_ampolla),
            )
            id_vacuna = cursor.lastrowid
            dosis_por_ampolla_efectiva = dosis_por_ampolla
            vacuna_nueva = True
        else:
            id_vacuna = vacuna_existente["id_vacuna"]
            dosis_por_ampolla_efectiva = vacuna_existente["dosis_por_ampolla"]
            vacuna_nueva = False

        cursor.execute(
            """
            INSERT INTO LOTE (
                numero_lote, fecha_vencimiento, cantidad_ampollas,
                id_vacuna, id_vacunatorio
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                numero_lote,
                fecha_vencimiento,
                cantidad_ampollas,
                id_vacuna,
                id_vacunatorio,
            ),
        )
        id_lote = cursor.lastrowid

        cursor.executemany(
            """
            INSERT INTO AMPOLLA (
                id_lote, id_vacunatorio_actual, dosis_disponibles
            ) VALUES (?, ?, ?)
            """,
            (
                (id_lote, id_vacunatorio, dosis_por_ampolla_efectiva)
                for _ in range(cantidad_ampollas)
            ),
        )
        conexion.commit()
        return id_lote, id_vacuna, vacuna_nueva
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()