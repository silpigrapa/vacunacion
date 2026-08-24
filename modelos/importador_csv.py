"""
Importador del CSV (SISA).

El archivo trae algunas líneas de metadata antes del encabezado real
(título, fecha de creación, usuario que lo generó), separador ';', y
fechas en formato DD/MM/YYYY. Este módulo:

  1) Encuentra la fila de encabezado real dentro del archivo.
  2) Por cada fila de datos:
       - Matchea 'Establecimiento' contra VACUNATORIO.nombre (exacto).
         Si no matchea, la fila se descarta (no sabemos a qué
         vacunatorio pertenece).
       - Matchea 'Lote' contra LOTE.numero_lote dentro de ese
         vacunatorio. Si no matchea, se guarda igual la aplicación
         (para historial), pero sin descuento de stock.
       - Evita duplicados: si la aplicación ya se había importado
         antes (mismo DNI, vacuna, dosis, fecha y vacunatorio), la
         omite. Esto permite volver a importar el mismo archivo (o uno
         más nuevo que incluya filas viejas) sin duplicar el consumo
         de stock.
       - Si matcheó lote y hay una ampolla con stock, descuenta 1
         dosis con ampolla.descontar_dosis().
  3) Devuelve un resumen con contadores, para mostrar en la interfaz.
"""

import csv
from datetime import datetime

from database.conexion import obtener_conexion
from modelos.vacunatorio import obtener_vacunatorio_por_nombre
from modelos.lote import obtener_lote_por_numero
from modelos.ampolla import obtener_ampolla_con_stock_por_lote, descontar_dosis

COLUMNAS_ESPERADAS = [
    "Fecha de aplicación", "Vacuna", "Esquema", "Dosis",
    "Apellido y nombre", "Sexo", "NroDoc", "Establecimiento",
    "Región sanitaria del establecimiento", "Departamento del establecimiento",
    "Lote", "Tipo de Edad", "Edad", "Fecha de registro", "Excepción",
    "Cuenta del usuario",
]


def _convertir_fecha(fecha_ddmmyyyy):
    """Convierte 'DD/MM/YYYY' a 'YYYY-MM-DD'. Devuelve None si viene vacío o inválido."""
    if not fecha_ddmmyyyy or fecha_ddmmyyyy.strip().lower() == "null":
        return None
    try:
        return datetime.strptime(fecha_ddmmyyyy.strip(), "%d/%m/%Y").strftime("%Y-%m-%d")
    except ValueError:
        return None


def _limpiar_valor(valor):
    """Convierte el texto 'null' del CSV (y strings vacíos) a None."""
    if valor is None:
        return None
    valor = valor.strip()
    if valor == "" or valor.lower() == "null":
        return None
    return valor


def _encontrar_encabezado_y_filas(ruta_archivo):
    """
    Busca dentro del archivo la línea que contiene el encabezado real
    (la que empieza con 'Fecha de aplicación') y devuelve un DictReader
    posicionado a partir de ahí.
    """
    archivo = open(ruta_archivo, encoding="cp1252")
    for linea in archivo:
        if linea.startswith("Fecha de aplicación"):
            encabezados = [c.strip() for c in linea.strip().split(";")]
            return archivo, csv.DictReader(archivo, fieldnames=encabezados, delimiter=";")
    archivo.close()
    raise ValueError("No se encontró la fila de encabezado esperada en el archivo CSV.")


def _ya_existe_aplicacion(cursor, fecha_aplicacion, dni, vacuna_nombre, dosis, id_vacunatorio):
    """
    Verifica si esta aplicación puntual ya fue importada antes,
    para evitar duplicados al reimportar un archivo.
    """
    cursor.execute(
        """
        SELECT 1 FROM APLICACION
        WHERE fecha_aplicacion IS ? AND dni IS ? AND vacuna_nombre IS ?
          AND dosis IS ? AND id_vacunatorio = ?
        LIMIT 1
        """,
        (fecha_aplicacion, dni, vacuna_nombre, dosis, id_vacunatorio),
    )
    return cursor.fetchone() is not None


def importar_csv(ruta_archivo):
    """
    Importa el archivo CSV indicado. Devuelve un diccionario resumen:
        {
            "total_filas": int,
            "importadas": int,
            "duplicadas": int,
            "sin_vacunatorio": int,   # Establecimiento no matcheó
            "sin_lote": int,          # se importó, pero sin descuento de stock
            "sin_stock": int,         # matcheó lote, pero no había ampolla con stock
            "establecimientos_no_encontrados": set(),
        }
    """
    archivo, lector = _encontrar_encabezado_y_filas(ruta_archivo)

    resumen = {
        "total_filas": 0,
        "importadas": 0,
        "duplicadas": 0,
        "sin_vacunatorio": 0,
        "sin_lote": 0,
        "sin_stock": 0,
        "establecimientos_no_encontrados": set(),
    }

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        for fila in lector:
            # Filas vacías o de cierre del archivo (sin datos reales)
            if not fila.get("Fecha de aplicación"):
                continue

            resumen["total_filas"] += 1

            establecimiento = _limpiar_valor(fila.get("Establecimiento"))
            vacunatorio = obtener_vacunatorio_por_nombre(establecimiento) if establecimiento else None

            if vacunatorio is None:
                resumen["sin_vacunatorio"] += 1
                if establecimiento:
                    resumen["establecimientos_no_encontrados"].add(establecimiento)
                continue

            id_vacunatorio = vacunatorio["id_vacunatorio"]

            fecha_aplicacion = _convertir_fecha(fila.get("Fecha de aplicación"))
            fecha_registro = _convertir_fecha(fila.get("Fecha de registro"))
            dni = _limpiar_valor(fila.get("NroDoc"))
            vacuna_nombre = _limpiar_valor(fila.get("Vacuna"))
            dosis = _limpiar_valor(fila.get("Dosis"))
            numero_lote = _limpiar_valor(fila.get("Lote"))

            # Evitar duplicados si el archivo ya se importó antes
            if _ya_existe_aplicacion(cursor, fecha_aplicacion, dni, vacuna_nombre, dosis, id_vacunatorio):
                resumen["duplicadas"] += 1
                continue

            # Intentar matchear el lote dentro de este vacunatorio
            id_lote = None
            if numero_lote:
                lote = obtener_lote_por_numero(numero_lote, id_vacunatorio)
                if lote is not None:
                    id_lote = lote["id_lote"]
                else:
                    resumen["sin_lote"] += 1

            edad_texto = _limpiar_valor(fila.get("Edad"))
            edad = int(edad_texto) if edad_texto and edad_texto.isdigit() else None

            cursor.execute(
                """
                INSERT INTO APLICACION (
                    fecha_aplicacion, vacuna_nombre, esquema, dosis,
                    paciente_nombre, sexo, dni, id_vacunatorio,
                    region_sanitaria, departamento, id_lote, tipo_edad,
                    edad, fecha_registro, excepcion, usuario_sisa
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    fecha_aplicacion,
                    vacuna_nombre,
                    _limpiar_valor(fila.get("Esquema")),
                    dosis,
                    _limpiar_valor(fila.get("Apellido y nombre")),
                    _limpiar_valor(fila.get("Sexo")),
                    dni,
                    id_vacunatorio,
                    _limpiar_valor(fila.get("Región sanitaria del establecimiento")),
                    _limpiar_valor(fila.get("Departamento del establecimiento")),
                    id_lote,
                    _limpiar_valor(fila.get("Tipo de Edad")),
                    edad,
                    fecha_registro,
                    _limpiar_valor(fila.get("Excepción")),
                    _limpiar_valor(fila.get("Cuenta del usuario")),
                ),
            )

            resumen["importadas"] += 1
            conexion.commit()  # liberar el lock antes de usar otras conexiones (descontar_dosis, etc.)

            # Descontar stock si se pudo identificar el lote
            if id_lote is not None:
                ampolla_con_stock = obtener_ampolla_con_stock_por_lote(id_lote)
                if ampolla_con_stock is not None:
                    descontar_dosis(ampolla_con_stock["id_ampolla"], 1)
                else:
                    resumen["sin_stock"] += 1

        conexion.commit()
    finally:
        conexion.close()
        archivo.close()

    return resumen