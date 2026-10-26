"""Creación y restauración segura de copias de la base SQLite."""

import os
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

from database.conexion import RUTA_BD


TABLAS_REQUERIDAS = {
    "VACUNATORIO",
    "USUARIO",
    "VACUNA",
    "LOTE",
    "AMPOLLA",
    "TRANSFERENCIA",
    "TRANSFERENCIA_DETALLE",
    "APLICACION",
    "OPCION_VACUNA_CSV",
}


def _validar_base(ruta):
    uri = f"{ruta.as_uri()}?mode=ro"
    conexion = sqlite3.connect(uri, uri=True)
    try:
        resultado = conexion.execute("PRAGMA integrity_check").fetchone()[0]
        if resultado != "ok":
            raise ValueError(f"La base de datos no pasó la verificación: {resultado}")

        tablas = {
            fila[0]
            for fila in conexion.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        faltantes = TABLAS_REQUERIDAS - tablas
        if faltantes:
            raise ValueError(
                "El archivo no tiene el esquema del sistema; faltan las tablas: "
                + ", ".join(sorted(faltantes))
            )

        violaciones = conexion.execute("PRAGMA foreign_key_check").fetchmany(5)
        if violaciones:
            raise ValueError(
                "La base contiene registros con referencias inválidas; "
                "no se puede usar como copia válida."
            )
    finally:
        conexion.close()


def _crear_archivo_temporal(carpeta, prefijo):
    descriptor, nombre = tempfile.mkstemp(
        prefix=prefijo,
        suffix=".sqlite3",
        dir=carpeta,
    )
    os.close(descriptor)
    return Path(nombre)


def _copiar_base(ruta_origen, ruta_destino):
    origen = sqlite3.connect(f"{ruta_origen.as_uri()}?mode=ro", uri=True)
    try:
        destino = sqlite3.connect(ruta_destino)
        try:
            origen.backup(destino)
        finally:
            destino.close()
    finally:
        origen.close()
    _validar_base(ruta_destino)


def crear_respaldo(ruta_destino, ruta_base=RUTA_BD):
    """Crea una copia consistente de la base de datos en la ruta indicada."""
    origen = Path(ruta_base).expanduser().resolve(strict=True)
    destino = Path(ruta_destino).expanduser().resolve()
    if origen == destino:
        raise ValueError("El destino de la copia no puede ser la base activa.")
    if not origen.is_file():
        raise ValueError(f"No se encontró la base de datos: {origen}")
    if not destino.parent.is_dir():
        raise FileNotFoundError(f"No existe la carpeta de destino: {destino.parent}")

    _validar_base(origen)
    temporal = _crear_archivo_temporal(destino.parent, f".{destino.name}.")
    try:
        _copiar_base(origen, temporal)
        os.replace(temporal, destino)
    finally:
        temporal.unlink(missing_ok=True)

    return destino


def _preparar_base_para_reemplazo(ruta_base):
    conexion = sqlite3.connect(ruta_base)
    try:
        modo = conexion.execute("PRAGMA journal_mode").fetchone()[0].lower()
        if modo == "wal":
            checkpoint = conexion.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
            if checkpoint[0]:
                raise RuntimeError(
                    "No se pudo cerrar el registro WAL. Cerrá otras instancias "
                    "del sistema e intentá de nuevo."
                )
            modo = (
                conexion.execute("PRAGMA journal_mode = DELETE").fetchone()[0].lower()
            )
            if modo != "delete":
                raise RuntimeError(
                    "No se pudo preparar la base para restaurar la copia."
                )
    finally:
        conexion.close()

    archivos_auxiliares = (
        Path(f"{ruta_base}-wal"),
        Path(f"{ruta_base}-shm"),
        Path(f"{ruta_base}-journal"),
    )
    existentes = [str(ruta) for ruta in archivos_auxiliares if ruta.exists()]
    if existentes:
        raise RuntimeError(
            "La base todavía tiene archivos auxiliares abiertos. Cerrá todas "
            "las instancias del sistema e intentá de nuevo."
        )


def restaurar_respaldo(ruta_respaldo, ruta_base=RUTA_BD):
    """Restaura una copia válida y conserva automáticamente la base actual."""
    respaldo = Path(ruta_respaldo).expanduser().resolve(strict=True)
    base = Path(ruta_base).expanduser().resolve(strict=True)
    if respaldo == base:
        raise ValueError("Seleccioná una copia distinta de la base activa.")
    if not respaldo.is_file() or not base.is_file():
        raise FileNotFoundError("No se encontró la copia o la base de datos activa.")

    _validar_base(respaldo)
    _validar_base(base)

    marca_tiempo = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    respaldo_previo = base.with_name(
        f"{base.stem}_pre_restauracion_{marca_tiempo}{base.suffix}"
    )
    temporal = _crear_archivo_temporal(base.parent, f".{base.name}.restauracion.")
    try:
        _copiar_base(respaldo, temporal)
        crear_respaldo(respaldo_previo, ruta_base=base)
        _preparar_base_para_reemplazo(base)
        os.replace(temporal, base)
        from database.auditoria import instalar_auditoria

        conexion = sqlite3.connect(base)
        try:
            instalar_auditoria(conexion)
            conexion.commit()
        finally:
            conexion.close()
    finally:
        temporal.unlink(missing_ok=True)

    return respaldo_previo
