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


# Vacunas "relevantes" para un vacunatorio: las que tienen o tuvieron
# ampollas ahí, o cuyos lotes ingresaron ahí (caso del vacunatorio central).
# Así una vacuna que nunca pasó por un vacunatorio no genera alertas de "0".
_SQL_STOCK_POR_VACUNA = """
    SELECT
        v.id_vacuna,
        v.nombre AS vacuna,
        COALESCE((
            SELECT COUNT(*)
            FROM AMPOLLA a
            JOIN LOTE l ON a.id_lote = l.id_lote
            WHERE l.id_vacuna = v.id_vacuna
              AND a.id_vacunatorio_actual = :vac
              AND a.dosis_disponibles > 0
        ), 0) AS stock,
        COALESCE(u.umbral, :defecto) AS umbral
    FROM VACUNA v
    LEFT JOIN UMBRAL_STOCK u ON u.id_vacuna = v.id_vacuna
    WHERE EXISTS (
            SELECT 1 FROM AMPOLLA a JOIN LOTE l ON a.id_lote = l.id_lote
            WHERE l.id_vacuna = v.id_vacuna AND a.id_vacunatorio_actual = :vac
          )
       OR EXISTS (
            SELECT 1 FROM LOTE l
            WHERE l.id_vacuna = v.id_vacuna AND l.id_vacunatorio = :vac
          )
"""


def listar_stock_con_umbral(id_vacunatorio: int):
    """Todas las vacunas relevantes del vacunatorio con su stock y su umbral."""
    conexion = obtener_conexion()
    try:
        _asegurar_tabla(conexion)
        cursor = conexion.execute(
            _SQL_STOCK_POR_VACUNA + " ORDER BY v.nombre COLLATE NOCASE",
            {"vac": id_vacunatorio, "defecto": UMBRAL_POR_DEFECTO},
        )
        return cursor.fetchall()
    finally:
        conexion.close()


def listar_stock_bajo(id_vacunatorio: int):
    """Vacunas cuyo stock es menor o igual a su umbral (las más escasas primero)."""
    return sorted(
        (f for f in listar_stock_con_umbral(id_vacunatorio) if f["stock"] <= f["umbral"]),
        key=lambda f: (f["stock"] - f["umbral"], f["vacuna"].lower()),
    )


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