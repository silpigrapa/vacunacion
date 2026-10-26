"""Registro y consulta de cambios hechos fuera de la aplicación."""

import sqlite3
from pathlib import Path

from database.conexion import RUTA_BD, TABLA_CONTEXTO_ESCRITURA

TABLA_CAMBIOS_EXTERNOS = "CAMBIOS_EXTERNOS"

TABLAS_AUDITADAS = {
    "VACUNATORIO": "id_vacunatorio",
    "USUARIO": "id_usuario",
    "VACUNA": "id_vacuna",
    "LOTE": "id_lote",
    "AMPOLLA": "id_ampolla",
    "TRANSFERENCIA": "id_transferencia",
    "TRANSFERENCIA_DETALLE": "id_transferencia || ':' || id_ampolla",
    "APLICACION": "id_aplicacion",
    "OPCION_VACUNA_CSV": "nombre",
    "UMBRAL_STOCK": "id_vacuna",
}


def _crear_trigger(tabla, clave, operacion):
    referencia = "OLD" if operacion == "DELETE" else "NEW"

    # Si la clave tiene partes separadas por || (concatenación)
    if " || " in clave:
        partes = []
        for token in clave.split("||"):
            token_limpio = token.strip()
            # Si el token es una cadena literal entre comillas (ej: ':'), no se le antecede OLD/NEW
            if (token_limpio.startswith("'") and token_limpio.endswith("'")) or (
                token_limpio.startswith('"') and token_limpio.endswith('"')
            ):
                partes.append(token_limpio)
            elif token_limpio:
                partes.append(f"{referencia}.{token_limpio}")
        expresion_clave = " || ".join(partes)
    else:
        clave_limpia = clave.strip()
        if (clave_limpia.startswith("'") and clave_limpia.endswith("'")) or (
            clave_limpia.startswith('"') and clave_limpia.endswith('"')
        ):
            expresion_clave = clave_limpia
        else:
            expresion_clave = f"{referencia}.{clave_limpia}"

    nombre = f"trg_cambio_externo_{tabla.lower()}_{operacion.lower()}"
    return f"""
        CREATE TRIGGER IF NOT EXISTS "{nombre}"
        AFTER {operacion} ON "{tabla}"
        WHEN (SELECT activa FROM "{TABLA_CONTEXTO_ESCRITURA}" WHERE id = 1) = 0
        BEGIN
            INSERT INTO "{TABLA_CAMBIOS_EXTERNOS}" (tabla, operacion, id_registro)
            VALUES ('{tabla}', '{operacion}', CAST({expresion_clave} AS TEXT));
        END
    """


def _limpiar_triggers_viejos(conexion):
    """Elimina triggers de auditoría previos para asegurar que se reconstruyan correctamente."""
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type = 'trigger' AND name LIKE 'trg_cambio_externo_%'"
    )
    triggers = [row[0] for row in cursor.fetchall()]
    for trg in triggers:
        cursor.execute(f'DROP TRIGGER IF EXISTS "{trg}"')


def instalar_auditoria(conexion):
    """Crea el contexto y los triggers de auditoría de forma idempotente."""
    conexion.execute(
        f"""
        CREATE TABLE IF NOT EXISTS "{TABLA_CONTEXTO_ESCRITURA}" (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            activa INTEGER NOT NULL CHECK (activa IN (0, 1))
        )
        """
    )
    conexion.execute(
        f"""
        INSERT OR IGNORE INTO "{TABLA_CONTEXTO_ESCRITURA}" (id, activa)
        VALUES (1, 0)
        """
    )
    conexion.execute(
        f"""
        CREATE TABLE IF NOT EXISTS "{TABLA_CAMBIOS_EXTERNOS}" (
            id_cambio INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            tabla TEXT NOT NULL,
            operacion TEXT NOT NULL CHECK (operacion IN ('INSERT', 'UPDATE', 'DELETE')),
            id_registro TEXT,
            notificado INTEGER NOT NULL DEFAULT 0 CHECK (notificado IN (0, 1))
        )
        """
    )

    # Limpiar cualquier trigger mal formado guardado previamente en SQLite
    _limpiar_triggers_viejos(conexion)

    tablas_existentes = {
        fila[0]
        for fila in conexion.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    for tabla, clave in TABLAS_AUDITADAS.items():
        if tabla not in tablas_existentes:
            continue
        for operacion in ("INSERT", "UPDATE", "DELETE"):
            conexion.execute(_crear_trigger(tabla, clave, operacion))


def detectar_elementos_auditoria_faltantes(conexion):
    """Devuelve los elementos de auditoría requeridos que no están instalados."""
    objetos = {
        (tipo, nombre): tabla
        for tipo, nombre, tabla in conexion.execute(
            """
            SELECT type, name, tbl_name
            FROM sqlite_master
            WHERE type IN ('table', 'trigger')
            """
        )
    }
    tablas = {
        nombre.upper()
        for (tipo, nombre), _ in objetos.items()
        if tipo == "table"
    }
    faltantes = []

    for tabla_requerida in (TABLA_CAMBIOS_EXTERNOS, TABLA_CONTEXTO_ESCRITURA):
        if tabla_requerida.upper() not in tablas:
            faltantes.append(f"Falta la tabla {tabla_requerida}.")

    if all(
        tabla.upper() in tablas
        for tabla in (TABLA_CAMBIOS_EXTERNOS, TABLA_CONTEXTO_ESCRITURA)
    ):
        for tabla, clave in TABLAS_AUDITADAS.items():
            if tabla.upper() not in tablas:
                continue
            for operacion in ("INSERT", "UPDATE", "DELETE"):
                nombre = f"trg_cambio_externo_{tabla.lower()}_{operacion.lower()}"
                trigger_tabla = objetos.get(("trigger", nombre))
                if trigger_tabla is None or trigger_tabla.upper() != tabla.upper():
                    faltantes.append(f"Falta el trigger {nombre}.")

    return faltantes


def verificar_auditoria(ruta_base=RUTA_BD):
    """Comprueba, en modo de solo lectura, que la auditoría siga instalada."""
    ruta = Path(ruta_base).resolve()
    conexion = sqlite3.connect(f"{ruta.as_uri()}?mode=ro", uri=True)
    try:
        return detectar_elementos_auditoria_faltantes(conexion)
    finally:
        conexion.close()


def obtener_cambios_externos_pendientes():
    ruta = Path(RUTA_BD).resolve()
    conexion = sqlite3.connect(f"{ruta.as_uri()}?mode=ro", uri=True)
    conexion.row_factory = sqlite3.Row
    try:
        return conexion.execute(
            f"""
            SELECT id_cambio, fecha, tabla, operacion, id_registro
            FROM "{TABLA_CAMBIOS_EXTERNOS}"
            WHERE notificado = 0
            ORDER BY id_cambio
            """
        ).fetchall()
    finally:
        conexion.close()


def marcar_cambios_externos_notificados(ids_cambios):
    ids = tuple(ids_cambios)
    if not ids:
        return
    conexion = sqlite3.connect(RUTA_BD)
    try:
        placeholders = ",".join("?" for _ in ids)
        conexion.execute(
            f"""
            UPDATE "{TABLA_CAMBIOS_EXTERNOS}"
            SET notificado = 1
            WHERE id_cambio IN ({placeholders})
            """,
            ids,
        )
        conexion.commit()
    finally:
        conexion.close()


def asegurar_trigger_umbral(conexion):
    """Instala triggers si la tabla opcional de umbrales ya fue creada."""
    for operacion in ("INSERT", "UPDATE", "DELETE"):
        conexion.execute(_crear_trigger("UMBRAL_STOCK", "id_vacuna", operacion))