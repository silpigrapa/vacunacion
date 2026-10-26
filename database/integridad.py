"""Auditoría de integridad física, relacional y de dominio de la base."""

import sqlite3
from datetime import datetime
from pathlib import Path

from database.conexion import RUTA_BD
from database.respaldo import TABLAS_REQUERIDAS


def _fecha_valida(valor, incluir_hora=False):
    if valor is None:
        return False
    try:
        if incluir_hora:
            datetime.strptime(valor, "%Y-%m-%d %H:%M:%S")
        else:
            fecha = datetime.strptime(valor, "%Y-%m-%d")
            if fecha.strftime("%Y-%m-%d") != valor:
                return False
        return True
    except (TypeError, ValueError):
        return False


def auditar_integridad(ruta_base=RUTA_BD):
    """Devuelve hallazgos; una lista vacía indica que las comprobaciones pasaron."""
    ruta = Path(ruta_base).expanduser().resolve(strict=True)
    conexion = sqlite3.connect(f"{ruta.as_uri()}?mode=ro", uri=True)
    try:
        hallazgos = []

        for resultado, in conexion.execute("PRAGMA integrity_check"):
            if resultado != "ok":
                hallazgos.append(f"Integridad física de SQLite: {resultado}")

        tablas = {
            fila[0]
            for fila in conexion.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        faltantes = TABLAS_REQUERIDAS - tablas
        if faltantes:
            return [
                "Faltan tablas requeridas: " + ", ".join(sorted(faltantes))
            ]

        for tabla, fila, padre, clave in conexion.execute(
            "PRAGMA foreign_key_check"
        ):
            hallazgos.append(
                f"Clave foránea inválida en {tabla}, fila {fila}, "
                f"tabla relacionada {padre}, clave {clave}."
            )

        validaciones_numericas = (
            (
                "VACUNA",
                "SELECT id_vacuna FROM VACUNA "
                "WHERE dosis_requeridas <= 0 OR dosis_por_ampolla <= 0",
                "dosis requeridas o dosis por ampolla no positivas",
            ),
            (
                "LOTE",
                "SELECT id_lote FROM LOTE WHERE cantidad_ampollas <= 0",
                "cantidad de ampollas no positiva",
            ),
            (
                "AMPOLLA",
                "SELECT id_ampolla FROM AMPOLLA WHERE dosis_disponibles < 0",
                "dosis disponibles negativas",
            ),
            (
                "TRANSFERENCIA",
                "SELECT id_transferencia FROM TRANSFERENCIA "
                "WHERE id_vacunatorio_origen = id_vacunatorio_destino",
                "origen y destino iguales",
            ),
        )
        for tabla, consulta, descripcion in validaciones_numericas:
            for (id_registro,) in conexion.execute(consulta):
                hallazgos.append(
                    f"{tabla} ID {id_registro}: {descripcion}."
                )

        for id_lote, cantidad, cantidad_registrada in conexion.execute(
            """
            SELECT l.id_lote, l.cantidad_ampollas, COUNT(a.id_ampolla)
            FROM LOTE l
            LEFT JOIN AMPOLLA a ON a.id_lote = l.id_lote
            GROUP BY l.id_lote
            HAVING l.cantidad_ampollas != COUNT(a.id_ampolla)
            """
        ):
            hallazgos.append(
                f"LOTE ID {id_lote}: declara {cantidad} ampollas pero "
                f"tiene {cantidad_registrada} registradas."
            )

        for tabla, columna, identificador, incluir_hora in (
            ("LOTE", "fecha_vencimiento", "id_lote", False),
            ("APLICACION", "fecha_aplicacion", "id_aplicacion", False),
            ("APLICACION", "fecha_registro", "id_aplicacion", False),
            ("AMPOLLA", "fecha_apertura", "id_ampolla", True),
            ("TRANSFERENCIA", "fecha", "id_transferencia", True),
        ):
            consulta = (
                f"SELECT {identificador}, {columna} FROM {tabla} "
                f"WHERE {columna} IS NOT NULL"
            )
            for id_registro, valor in conexion.execute(consulta):
                if not _fecha_valida(valor, incluir_hora):
                    hallazgos.append(
                        f"{tabla} ID {id_registro}: fecha inválida en {columna}."
                    )

        cantidad_centrales = conexion.execute(
            "SELECT COUNT(*) FROM VACUNATORIO WHERE es_central = 1"
        ).fetchone()[0]
        if cantidad_centrales > 1:
            hallazgos.append(
                f"Hay {cantidad_centrales} vacunatorios marcados como centrales."
            )

        return hallazgos
    finally:
        conexion.close()
