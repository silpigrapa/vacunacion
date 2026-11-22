"""
Generación de PDFs de remitos de transferencia.

No requiere instalar librerías externas: el PDF se arma directamente con la
biblioteca estándar de Python (fuentes Helvetica incorporadas en todo lector PDF).
"""

import os
import re
import unicodedata
from datetime import datetime

from modelos.transferencia import obtener_detalle_transferencia, obtener_transferencia

# Carpeta donde se guardan los remitos: <proyecto>/remitos
CARPETA_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA_REMITOS = os.path.join(CARPETA_PROYECTO, "remitos")

# Página A4 en puntos (1 pt = 1/72 pulgada)
ANCHO_PAG, ALTO_PAG = 595.28, 841.89
MARGEN = 57.0  # ~2 cm
ANCHO_UTIL = ANCHO_PAG - 2 * MARGEN
LIMITE_INFERIOR = ALTO_PAG - MARGEN - 20  # deja lugar al pie de página

AZUL = (0.17, 0.34, 0.59)
GRIS = (0.35, 0.35, 0.35)
GRIS_CLARO = (0.6, 0.6, 0.6)
NEGRO = (0, 0, 0)
BLANCO = (1, 1, 1)
FILA_ALTERNA = (0.95, 0.96, 0.98)

# Anchos de los caracteres ASCII (32 a 126) de Helvetica, en milésimas de em.
_ANCHOS_HELVETICA = dict(zip(range(32, 127), [
    278, 278, 355, 556, 556, 889, 667, 191, 333, 333, 389, 584, 278, 333, 278, 278,
    556, 556, 556, 556, 556, 556, 556, 556, 556, 556, 278, 278, 584, 584, 584, 556,
    1015, 667, 667, 722, 722, 667, 611, 778, 722, 278, 500, 667, 556, 833, 722, 778,
    667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 278, 278, 278, 469, 556,
    333, 556, 556, 500, 556, 556, 278, 556, 556, 222, 222, 500, 222, 833, 556, 556,
    556, 556, 333, 500, 278, 556, 500, 722, 500, 500, 500, 334, 260, 334, 584,
]))


def _ancho(texto, tam, negrita=False):
    """Ancho aproximado de un texto en puntos."""
    total = 0
    for c in str(texto):
        codigo = ord(c)
        if codigo not in _ANCHOS_HELVETICA:
            base = unicodedata.normalize("NFD", c)[0]  # á -> a
            codigo = ord(base) if ord(base) in _ANCHOS_HELVETICA else 0
        total += _ANCHOS_HELVETICA.get(codigo, 556)
    return total * tam / 1000 * (1.07 if negrita else 1)


def _ajustar(texto, ancho_max, tam, negrita=False):
    """Parte un texto en líneas que entren en ancho_max."""
    texto = "-" if texto in (None, "") else str(texto)
    lineas = []
    for parrafo in texto.splitlines() or [""]:
        actual = ""
        for palabra in parrafo.split():
            while _ancho(palabra, tam, negrita) > ancho_max:
                corte = 1
                while corte < len(palabra) and _ancho(palabra[:corte + 1], tam, negrita) <= ancho_max:
                    corte += 1
                if actual:
                    lineas.append(actual)
                    actual = ""
                lineas.append(palabra[:corte])
                palabra = palabra[corte:]
            candidato = palabra if not actual else f"{actual} {palabra}"
            if _ancho(candidato, tam, negrita) <= ancho_max:
                actual = candidato
            else:
                lineas.append(actual)
                actual = palabra
        lineas.append(actual)
    return lineas or ["-"]


def _escapar(texto):
    texto = str(texto).replace("\n", " ").replace("\r", " ").replace("\t", " ")
    texto = texto.encode("cp1252", "replace").decode("latin-1")
    return texto.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


class _Pagina:
    """Acumula las instrucciones de dibujo de una página (origen arriba a la izquierda)."""

    def __init__(self):
        self.ops = []

    def texto(self, x, y, s, tam=10, negrita=False, color=NEGRO):
        fuente = "F2" if negrita else "F1"
        r, g, b = color
        self.ops.append(
            f"BT /{fuente} {tam} Tf {r} {g} {b} rg {x:.2f} {ALTO_PAG - y:.2f} Td ({_escapar(s)}) Tj ET"
        )

    def linea(self, x1, y1, x2, y2, grosor=0.5, color=GRIS_CLARO):
        r, g, b = color
        self.ops.append(
            f"{grosor} w {r} {g} {b} RG {x1:.2f} {ALTO_PAG - y1:.2f} m {x2:.2f} {ALTO_PAG - y2:.2f} l S"
        )

    def rect(self, x, y, ancho, alto, relleno=None, borde=None, grosor=0.4):
        yb = ALTO_PAG - y - alto
        if relleno:
            r, g, b = relleno
            self.ops.append(f"{r} {g} {b} rg {x:.2f} {yb:.2f} {ancho:.2f} {alto:.2f} re f")
        if borde:
            r, g, b = borde
            self.ops.append(f"{grosor} w {r} {g} {b} RG {x:.2f} {yb:.2f} {ancho:.2f} {alto:.2f} re S")

    def contenido(self):
        return "\n".join(self.ops)


def _armar_pdf(paginas):
    """Convierte una lista de contenidos de página en los bytes de un PDF."""
    n = len(paginas)
    objetos = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        ("<< /Type /Pages /Kids [%s] /Count %d >>"
         % (" ".join(f"{5 + 2 * i} 0 R" for i in range(n)), n)).encode(),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
    ]
    for i, contenido in enumerate(paginas):
        datos = contenido.encode("latin-1")
        objetos.append(
            ("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %.2f %.2f] "
             "/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents %d 0 R >>"
             % (ANCHO_PAG, ALTO_PAG, 6 + 2 * i)).encode()
        )
        objetos.append(b"<< /Length %d >>\nstream\n" % len(datos) + datos + b"\nendstream")

    salida = bytearray(b"%PDF-1.4\n")
    posiciones = []
    for numero, cuerpo in enumerate(objetos, 1):
        posiciones.append(len(salida))
        salida += b"%d 0 obj\n" % numero + cuerpo + b"\nendobj\n"

    inicio_xref = len(salida)
    salida += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objetos) + 1)
    for pos in posiciones:
        salida += b"%010d 00000 n \n" % pos
    salida += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objetos) + 1, inicio_xref
    )
    return bytes(salida)


def _valor(fila, clave, defecto=None):
    try:
        return fila[clave]
    except (KeyError, IndexError, TypeError):
        return defecto


def _nombre_archivo_seguro(numero_remito):
    limpio = re.sub(r"[^A-Za-z0-9._-]+", "_", str(numero_remito)).strip("._")
    return limpio or "remito"


def generar_remito_pdf(id_transferencia, ruta_destino=None):
    """
    Genera el PDF del remito de una transferencia ya registrada.

    Si no se indica ruta_destino, se guarda en la carpeta "remitos" del
    proyecto con el nombre <numero_remito>.pdf. Devuelve la ruta del archivo.
    """
    cabecera = obtener_transferencia(id_transferencia)
    if cabecera is None:
        raise ValueError(f"No existe la transferencia #{id_transferencia}.")
    detalle = obtener_detalle_transferencia(id_transferencia)

    if ruta_destino is None:
        os.makedirs(CARPETA_REMITOS, exist_ok=True)
        ruta_destino = os.path.join(
            CARPETA_REMITOS, _nombre_archivo_seguro(cabecera["numero_remito"]) + ".pdf"
        )
    else:
        os.makedirs(os.path.dirname(os.path.abspath(ruta_destino)), exist_ok=True)

    paginas = []

    def nueva_pagina():
        pagina = _Pagina()
        paginas.append(pagina)
        return pagina

    pagina = nueva_pagina()
    y = MARGEN

    # --- Título ---
    titulo = "REMITO DE TRANSFERENCIA"
    pagina.texto((ANCHO_PAG - _ancho(titulo, 20, True)) / 2, y + 18, titulo, 20, True)
    y += 36
    subtitulo = f"N° {cabecera['numero_remito']}"
    pagina.texto((ANCHO_PAG - _ancho(subtitulo, 12)) / 2, y, subtitulo, 12, color=GRIS)
    y += 26

    # --- Datos de cabecera ---
    x_valor = MARGEN + 100
    ancho_valor = ANCHO_UTIL - 100

    def fila_dato(etiqueta, principal, secundario=None):
        nonlocal y
        lineas = [(t, 10, NEGRO) for t in _ajustar(principal, ancho_valor, 10)]
        if secundario:
            lineas += [(t, 8, GRIS) for t in _ajustar(secundario, ancho_valor, 8)]
        pagina.texto(MARGEN, y + 10, etiqueta, 10, True)
        for texto, tam, color in lineas:
            pagina.texto(x_valor, y + 10, texto, tam, False, color)
            y += 13 if tam == 10 else 10
        y += 5

    fila_dato("Fecha:", cabecera["fecha"])
    fila_dato("Origen:", cabecera["origen"], _valor(cabecera, "origen_direccion"))
    fila_dato("Destino:", cabecera["destino"], _valor(cabecera, "destino_direccion"))
    fila_dato("Emitido por:", cabecera["usuario"])
    fila_dato("Observaciones:", cabecera["observaciones"])
    pagina.linea(MARGEN, y, ANCHO_PAG - MARGEN, y, 0.8, GRIS_CLARO)
    y += 22

    # --- Detalle de ampollas ---
    pagina.texto(MARGEN, y, "Detalle de ampollas transferidas", 10, True)
    y += 10

    columnas = [("ID Amp.", 44), ("Vacuna", 122), ("Lote", 66), ("Vencimiento", 70),
                ("Cant.", 36), ("Dosis disp.", 70), ("Estado", 73)]
    xs = [MARGEN]
    for _, ancho in columnas:
        xs.append(xs[-1] + ancho)

    def dibujar_encabezado():
        nonlocal y
        pagina.rect(MARGEN, y, ANCHO_UTIL, 20, relleno=AZUL, borde=GRIS_CLARO)
        for (nombre, _), x in zip(columnas, xs):
            pagina.texto(x + 4, y + 13.5, nombre, 9, True, BLANCO)
        y += 20

    dibujar_encabezado()

    total_cantidad = 0
    total_dosis = 0
    for indice, d in enumerate(detalle):
        cantidad = int(_valor(d, "cantidad", 1) or 1)
        dosis = int(_valor(d, "dosis_disponibles", 0) or 0)
        total_cantidad += cantidad
        total_dosis += dosis
        estado = "Abierta" if _valor(d, "fecha_apertura") else "Cerrada"
        celdas = [d["id_ampolla"], d["vacuna_nombre"], d["numero_lote"],
                  d["fecha_vencimiento"], cantidad, dosis, estado]
        lineas_celda = [
            _ajustar(valor, ancho - 8, 9) for valor, (_, ancho) in zip(celdas, columnas)
        ]
        alto = max(len(lc) for lc in lineas_celda) * 11 + 8

        if y + alto > LIMITE_INFERIOR:
            pagina = nueva_pagina()
            y = MARGEN
            dibujar_encabezado()

        pagina.rect(MARGEN, y, ANCHO_UTIL, alto,
                    relleno=FILA_ALTERNA if indice % 2 else BLANCO, borde=GRIS_CLARO)
        for lineas, x in zip(lineas_celda, xs):
            for n, texto in enumerate(lineas):
                pagina.texto(x + 4, y + 12 + n * 11, texto, 9)
        for x in xs[1:-1]:
            pagina.linea(x, y, x, y + alto, 0.4, GRIS_CLARO)
        y += alto

    y += 16
    pagina.texto(
        MARGEN, y,
        f"Total de ampollas: {total_cantidad}      Total de dosis disponibles: {total_dosis}",
        10, True,
    )
    y += 20

    # --- Firmas ---
    if y + 110 > LIMITE_INFERIOR:
        pagina = nueva_pagina()
        y = MARGEN
    y += 80
    ancho_firma = 180
    for centro, rotulo in ((MARGEN + ANCHO_UTIL * 0.25, "Firma y aclaración (entrega)"),
                           (MARGEN + ANCHO_UTIL * 0.75, "Firma y aclaración (recibe)")):
        pagina.linea(centro - ancho_firma / 2, y, centro + ancho_firma / 2, y, 0.8, NEGRO)
        pagina.texto(centro - _ancho(rotulo, 9) / 2, y + 13, rotulo, 9, False, GRIS)

    # --- Pie de página ---
    generado = datetime.now().strftime("%d/%m/%Y %H:%M")
    total_paginas = len(paginas)
    for numero, p in enumerate(paginas, 1):
        p.texto(MARGEN, ALTO_PAG - 34, f"Sistema de Vacunación - Generado el {generado}", 8, False, GRIS_CLARO)
        etiqueta = f"Página {numero} de {total_paginas}"
        p.texto(ANCHO_PAG - MARGEN - _ancho(etiqueta, 8), ALTO_PAG - 34, etiqueta, 8, False, GRIS_CLARO)

    with open(ruta_destino, "wb") as archivo:
        archivo.write(_armar_pdf([p.contenido() for p in paginas]))
    return ruta_destino