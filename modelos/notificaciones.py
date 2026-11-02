"""
Modelo de NOTIFICACIONES de la pantalla principal.

Genera dos tipos de avisos para un vacunatorio:
  1) Lotes con ampollas en stock que vencen en un mes o menos (o que ya vencieron).
  2) Vacunas cuyo stock (en ampollas con dosis disponibles) es menor o igual
     al umbral de alerta configurado para esa vacuna.

El umbral es independiente por vacuna y se guarda en la tabla
UMBRAL_STOCK. Si una vacuna no tiene umbral propio se usa
UMBRAL_POR_DEFECTO. La tabla se crea sola si no existe, por lo que
funciona también con bases de datos ya creadas.
"""

from database.conexion import obtener_conexion
from database.auditoria import asegurar_trigger_umbral

UMBRAL_POR_DEFECTO = 10


def _asegurar_tabla(conexion):
    conexion.execute(
        """
        CREATE TABLE IF NOT EXISTS UMBRAL_STOCK (
            id_vacuna  INTEGER PRIMARY KEY,
            umbral     INTEGER NOT NULL CHECK (umbral >= 0),
            FOREIGN KEY (id_vacuna) REFERENCES VACUNA(id_vacuna)
        )
        """
    )
    asegurar_trigger_umbral(conexion)


def guardar_umbral(id_vacuna: int, umbral: int):
    """Crea o actualiza el umbral de alerta de una vacuna."""
    if umbral < 0:
        raise ValueError("El umbral no puede ser negativo.")
    conexion = obtener_conexion()
    try:
        _asegurar_tabla(conexion)
        conexion.execute(
            """
            INSERT INTO UMBRAL_STOCK (id_vacuna, umbral) VALUES (?, ?)
            ON CONFLICT(id_vacuna) DO UPDATE SET umbral = excluded.umbral
            """,
            (id_vacuna, umbral),
        )
        conexion.commit()
    finally:
        conexion.close()


# Vacunas relevantes por vacunatorio: las que tienen ampollas allí o cuyos
# lotes ingresaron allí. Así no se generan alertas de "0" en todos los centros.
_SQL_STOCK_POR_VACUNA = """
    SELECT
        v.id_vacuna,
        v.nombre AS vacuna,
        c.id_vacunatorio,
        c.nombre AS vacunatorio,
        COALESCE((
            SELECT COUNT(*)
            FROM AMPOLLA a
            JOIN LOTE l ON a.id_lote = l.id_lote
            WHERE l.id_vacuna = v.id_vacuna
              AND a.id_vacunatorio_actual = c.id_vacunatorio
              AND a.dosis_disponibles > 0
              AND l.fecha_vencimiento >= date('now', 'localtime')
        ), 0) AS stock,
        COALESCE(u.umbral, :defecto) AS umbral
    FROM VACUNA v
    JOIN VACUNATORIO c ON (:vac IS NULL OR c.id_vacunatorio = :vac)
    LEFT JOIN UMBRAL_STOCK u ON u.id_vacuna = v.id_vacuna
    WHERE EXISTS (
            SELECT 1 FROM AMPOLLA a JOIN LOTE l ON a.id_lote = l.id_lote
            WHERE l.id_vacuna = v.id_vacuna
              AND a.id_vacunatorio_actual = c.id_vacunatorio
          )
       OR EXISTS (
            SELECT 1 FROM LOTE l
            WHERE l.id_vacuna = v.id_vacuna
              AND l.id_vacunatorio = c.id_vacunatorio
          )
"""


def listar_stock_con_umbral(id_vacunatorio: int = None):
    """Vacunas relevantes por centro, con stock vigente y umbral configurado."""
    conexion = obtener_conexion()
    try:
        _asegurar_tabla(conexion)
        cursor = conexion.execute(
            _SQL_STOCK_POR_VACUNA
            + " ORDER BY v.nombre COLLATE NOCASE, c.nombre COLLATE NOCASE",
            {"vac": id_vacunatorio, "defecto": UMBRAL_POR_DEFECTO},
        )
        return cursor.fetchall()
    finally:
        conexion.close()


def listar_stock_bajo(id_vacunatorio: int = None):
    """Centros cuya vacuna tiene stock menor o igual al umbral (más escasos primero)."""
    return sorted(
        (f for f in listar_stock_con_umbral(id_vacunatorio) if f["stock"] <= f["umbral"]),
        key=lambda f: (f["stock"] - f["umbral"], f["vacuna"].lower()),
    )


def listar_umbrales_vacunas():
    """Lista una vez cada vacuna para configurar su umbral común por centro."""
    conexion = obtener_conexion()
    try:
        _asegurar_tabla(conexion)
        return conexion.execute(
            """
            SELECT
                v.id_vacuna,
                v.nombre AS vacuna,
                COALESCE(u.umbral, ?) AS umbral
            FROM VACUNA v
            LEFT JOIN UMBRAL_STOCK u ON u.id_vacuna = v.id_vacuna
            ORDER BY v.nombre COLLATE NOCASE
            """,
            (UMBRAL_POR_DEFECTO,),
        ).fetchall()
    finally:
        conexion.close()


def listar_lotes_por_vencer(id_vacunatorio: int):
    """
    Lotes con ampollas aún con dosis en el vacunatorio cuyo vencimiento es
    dentro de un mes o menos. Incluye los ya vencidos (dias_restantes < 0).
    """
    conexion = obtener_conexion()
    try:
        cursor = conexion.execute(
            """
            SELECT
                v.nombre AS vacuna,
                l.numero_lote,
                l.fecha_vencimiento,
                COUNT(a.id_ampolla) AS ampollas,
                CAST(julianday(l.fecha_vencimiento)
                     - julianday(date('now', 'localtime')) AS INTEGER) AS dias_restantes
            FROM AMPOLLA a
            JOIN LOTE l  ON a.id_lote = l.id_lote
            JOIN VACUNA v ON l.id_vacuna = v.id_vacuna
            WHERE a.id_vacunatorio_actual = ?
              AND a.dosis_disponibles > 0
              AND l.fecha_vencimiento <= date('now', 'localtime', '+1 month')
            GROUP BY l.id_lote
            ORDER BY l.fecha_vencimiento ASC, v.nombre
            """,
            (id_vacunatorio,),
        )
        return cursor.fetchall()
    finally:
        conexion.close()