"""
Vista de NOTIFICACIONES (pantalla de inicio del Sistema de Vacunación).

Muestra, para el vacunatorio del usuario logueado:
  - Lotes que vencen en un mes o menos (o que ya vencieron).
  - Vacunas con stock bajo, con el umbral de alerta editable por vacuna.
  - Una sección desplegable para ajustar el umbral de cualquier vacuna,
    incluso de las que hoy no están en alerta.
"""

from datetime import datetime

import customtkinter as ctk

from modelos.notificaciones import (
    listar_lotes_por_vencer,
    listar_stock_bajo,
    listar_stock_con_umbral,
    guardar_umbral,
)
from vistas import tema

COLOR_AVISO = "#B9770E"  # Color de próximo a vencer / stock bajo (Agregar este color en TEMA...)
COLOR_CRITICO = tema.ERROR  # rojo: vencido / sin stock


def _plural(cantidad, singular, plural):
    return f"{cantidad} {singular if cantidad == 1 else plural}"


def _formatear_fecha(texto):
    try:
        return datetime.strptime(texto, "%Y-%m-%d").strftime("%d/%m/%Y")
    except (TypeError, ValueError):
        return str(texto)


class FrameNotificaciones(ctk.CTkFrame):
    def __init__(self, master, usuario_logueado):
        super().__init__(master, fg_color="transparent")
        self.id_vacunatorio = usuario_logueado["id_vacunatorio"]
        self.config_visible = False
        self._construir_widgets()
        self._cargar()

    # ------------------------------------------------------------------
    # Estructura fija (cabecera + cuerpo desplazable)
    # ------------------------------------------------------------------
    def _construir_widgets(self):
        cabecera = ctk.CTkFrame(self, fg_color="transparent")
        cabecera.pack(fill="x", padx=4, pady=(0, 8))

        franja = ctk.CTkFrame(
            cabecera, height=4, corner_radius=tema.RADIO_NULO, fg_color=tema.PRINCIPAL
        )
        franja.pack(fill="x", pady=(0, 10))

        fila_titulo = ctk.CTkFrame(cabecera, fg_color="transparent")
        fila_titulo.pack(fill="x")

        ctk.CTkLabel(
            fila_titulo,
            text="Notificaciones",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=tema.OSCURO,
            anchor="w",
        ).pack(side="left")

        ctk.CTkButton(
            fila_titulo,
            text="Actualizar",
            width=110,
            height=30,
            corner_radius=tema.RADIO,
            fg_color=tema.OSCURO,
            hover_color=tema.HOVER,
            command=self._cargar,
        ).pack(side="right")

        self.etiqueta_estado = ctk.CTkLabel(
            self, text="", anchor="w", font=ctk.CTkFont(size=12)
        )
        self.etiqueta_estado.pack(fill="x", padx=6)

        self.cuerpo = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.cuerpo.pack(fill="both", expand=True, padx=2, pady=(4, 2))

    # ------------------------------------------------------------------
    # Carga / redibujado del contenido
    # ------------------------------------------------------------------
    def _cargar(self):
        for widget in self.cuerpo.winfo_children():
            widget.destroy()

        try:
            lotes = listar_lotes_por_vencer(self.id_vacunatorio)
            stock_bajo = listar_stock_bajo(self.id_vacunatorio)
            todas = listar_stock_con_umbral(self.id_vacunatorio)
        except Exception as error:
            self._mensaje(f"No se pudieron cargar las notificaciones: {error}", COLOR_CRITICO)
            return

        self._seccion_vencimientos(lotes)
        self._seccion_stock_bajo(stock_bajo)
        self._seccion_configuracion(todas)

    def _mensaje(self, texto, color):
        self.etiqueta_estado.configure(text=texto, text_color=color)

    def _titulo_seccion(self, texto, cantidad):
        fila = ctk.CTkFrame(self.cuerpo, fg_color="transparent")
        fila.pack(fill="x", pady=(12, 4))
        ctk.CTkLabel(
            fila,
            text=texto,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=tema.OSCURO,
        ).pack(side="left", padx=4)
        if cantidad:
            ctk.CTkLabel(
                fila,
                text=str(cantidad),
                width=26,
                corner_radius=13,
                fg_color=COLOR_AVISO,
                text_color="white",
                font=ctk.CTkFont(size=12, weight="bold"),
            ).pack(side="left", padx=6)

    def _sin_novedades(self, texto):
        ctk.CTkLabel(
            self.cuerpo, text="✔ " + texto, text_color=tema.OK, anchor="w"
        ).pack(fill="x", padx=10, pady=4)

    # ------------------------------------------------------------------
    # Sección 1: lotes por vencer
    # ------------------------------------------------------------------
    def _seccion_vencimientos(self, lotes):
        self._titulo_seccion("Lotes por vencer o vencidos", len(lotes))
        if not lotes:
            self._sin_novedades("No hay lotes con stock próximos a vencer.")
            return

        for lote in lotes:
            dias = lote["dias_restantes"]
            if dias < 0:
                estado = f"VENCIDO hace {_plural(-dias, 'día', 'días')}"
                color = COLOR_CRITICO
            elif dias == 0:
                estado = "vence HOY"
                color = COLOR_CRITICO
            else:
                estado = f"vence en {_plural(dias, 'día', 'días')}"
                color = COLOR_AVISO

            fila = ctk.CTkFrame(self.cuerpo)
            fila.pack(fill="x", pady=2)
            ctk.CTkLabel(
                fila,
                text=f"{lote['vacuna']}  ·  Lote {lote['numero_lote']}",
                font=ctk.CTkFont(weight="bold"),
                text_color=tema.TEXTO,
            ).pack(side="left", padx=10, pady=6)
            ctk.CTkLabel(
                fila,
                text=(
                    f"{_plural(lote['ampollas'], 'ampolla', 'ampollas')}  ·  "
                    f"{_formatear_fecha(lote['fecha_vencimiento'])}  ·  {estado}"
                ),
                text_color=color,
            ).pack(side="right", padx=10, pady=6)

    # ------------------------------------------------------------------
    # Sección 2: stock bajo (con umbral editable)
    # ------------------------------------------------------------------
    def _seccion_stock_bajo(self, filas):
        self._titulo_seccion("Stock bajo", len(filas))
        if not filas:
            self._sin_novedades("Ninguna vacuna llegó a su umbral de alerta.")
            return
        for fila in filas:
            self._fila_umbral(fila)

    def _fila_umbral(self, fila):
        marco = ctk.CTkFrame(self.cuerpo)
        marco.pack(fill="x", pady=2)

        stock = fila["stock"]
        en_alerta = stock <= fila["umbral"]

        ctk.CTkLabel(
            marco,
            text=fila["vacuna"],
            font=ctk.CTkFont(weight="bold"),
            text_color=tema.TEXTO,
        ).pack(side="left", padx=10, pady=6)

        # Controles de edición del umbral (a la derecha)
        boton = ctk.CTkButton(
            marco, text="Guardar", width=70, height=28, corner_radius=tema.RADIO,
            fg_color=tema.PRINCIPAL, hover_color=tema.HOVER,
        )
        boton.pack(side="right", padx=(4, 10), pady=6)

        entrada = ctk.CTkEntry(marco, width=56, height=28, justify="center")
        entrada.insert(0, str(fila["umbral"]))
        entrada.pack(side="right", pady=6)

        ctk.CTkLabel(
            marco, text="Avisar con", text_color=tema.TEXTO_SUAVE,
            font=ctk.CTkFont(size=12),
        ).pack(side="right", padx=(10, 4), pady=6)

        texto_stock = "Sin stock" if stock == 0 else f"Quedan {_plural(stock, 'ampolla', 'ampollas')}"
        ctk.CTkLabel(
            marco,
            text=texto_stock,
            text_color=(
                COLOR_CRITICO if stock == 0 else COLOR_AVISO if en_alerta else tema.TEXTO_SUAVE
            ),
        ).pack(side="right", padx=10, pady=6)

        boton.configure(
            command=lambda f=fila, e=entrada: self._guardar_umbral(f, e)
        )
        entrada.bind("<Return>", lambda _evento, f=fila, e=entrada: self._guardar_umbral(f, e))

    def _guardar_umbral(self, fila, entrada):
        texto = entrada.get().strip()
        if not texto.isdigit():
            self._mensaje(
                f"El umbral de «{fila['vacuna']}» debe ser un número entero (0 o más).",
                COLOR_CRITICO,
            )
            return
        try:
            guardar_umbral(fila["id_vacuna"], int(texto))
        except Exception as error:
            self._mensaje(f"No se pudo guardar el umbral: {error}", COLOR_CRITICO)
            return
        self._cargar()
        self._mensaje(
            f"Umbral de «{fila['vacuna']}» actualizado: avisar con {texto} ampolla(s) o menos.",
            tema.OK,
        )

    # ------------------------------------------------------------------
    # Sección 3: configurar el umbral de todas las vacunas
    # ------------------------------------------------------------------
    def _seccion_configuracion(self, todas):
        fila_boton = ctk.CTkFrame(self.cuerpo, fg_color="transparent")
        fila_boton.pack(fill="x", pady=(14, 4))
        ctk.CTkButton(
            fila_boton,
            text=(
                "▾ Ocultar umbrales de todas las vacunas"
                if self.config_visible
                else "▸ Configurar umbral de todas las vacunas"
            ),
            height=30,
            corner_radius=tema.RADIO,
            fg_color=tema.CLARO,
            hover_color=tema.SUAVE,
            text_color=tema.OSCURO,
            border_width=1,
            border_color=tema.BORDE,
            command=self._alternar_configuracion,
        ).pack(side="left", padx=4)

        if not self.config_visible:
            return
        if not todas:
            self._sin_novedades("Todavía no hay vacunas con stock en este vacunatorio.")
            return
        for fila in todas:
            self._fila_umbral(fila)

    def _alternar_configuracion(self):
        self.config_visible = not self.config_visible
        self._cargar()