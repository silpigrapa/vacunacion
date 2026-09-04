"""
Panel principal del Sistema de Vacunación.

Implementado como CTkFrame (ver nota en login.py sobre por qué se
evita crear una segunda ventana ctk.CTk()).
"""

import customtkinter as ctk
from vistas.transferencias import VistaTransferencias
from vistas.vacunas import FrameVacunas
from vistas.importar_csv_vista import FrameImportarCSV
from estilos import Color, Fuente, RADIO, RADIO_CHICO


class FramePrincipal(ctk.CTkFrame):
    def __init__(self, master, usuario_logueado):
        """
        master: la ventana raíz (App) donde se monta este frame.
        usuario_logueado: sqlite3.Row con los datos del usuario que
        inició sesión.
        """
        super().__init__(master, fg_color=Color.FONDO_APP, corner_radius=0)
        self.usuario_logueado = usuario_logueado
        self.botones_menu = {}
        self._indice_seleccionado = None
        self._construir_widgets()

    def _construir_widgets(self):
        # --- Barra superior con datos del usuario logueado ---
        barra_superior = ctk.CTkFrame(
            self, height=56, corner_radius=0,
            fg_color=Color.TARJETA,
            border_width=0,
        )
        barra_superior.pack(side="top", fill="x")
        barra_superior.pack_propagate(False)

        # línea sutil debajo de la barra superior
        ctk.CTkFrame(self, height=1, fg_color=Color.BORDE, corner_radius=0).pack(
            side="top", fill="x"
        )

        ctk.CTkLabel(
            barra_superior,
            text="Sistema de Vacunación",
            font=Fuente.subtitulo(),
            text_color=Color.TEXTO,
        ).pack(side="left", padx=24)

        contenedor_usuario = ctk.CTkFrame(barra_superior, fg_color="transparent")
        contenedor_usuario.pack(side="right", padx=24)

        iniciales = (
            f"{self.usuario_logueado['nombre'][:1]}{self.usuario_logueado['apellido'][:1]}"
        ).upper()

        ctk.CTkLabel(
            contenedor_usuario,
            text=iniciales,
            width=32, height=32,
            corner_radius=16,
            fg_color=Color.PRIMARIO,
            text_color="white",
            font=Fuente.chico(),
        ).pack(side="left", padx=(0, 10))

        texto_usuario = (
            f"{self.usuario_logueado['nombre']} {self.usuario_logueado['apellido']}"
        )
        ctk.CTkLabel(
            contenedor_usuario,
            text=texto_usuario,
            font=Fuente.texto_negrita(),
            text_color=Color.TEXTO,
        ).pack(side="left")

        # --- Cuerpo: menú lateral + contenido ---
        cuerpo = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        cuerpo.pack(side="top", fill="both", expand=True)

        # --- Menú lateral ---
        menu_lateral = ctk.CTkFrame(
            cuerpo, width=230, corner_radius=0, fg_color=Color.SIDEBAR
        )
        menu_lateral.pack(side="left", fill="y")
        menu_lateral.pack_propagate(False)

        ctk.CTkLabel(
            menu_lateral,
            text="MENÚ",
            font=Fuente.chico(),
            text_color=Color.SIDEBAR_TEXTO_SECUNDARIO,
        ).pack(anchor="w", padx=20, pady=(20, 8))

        opciones = [
            ("💉", "Vacunas", self._ir_a_vacunas),
            ("📥", "Importar aplicaciones (CSV)", self._ir_a_importar_csv),
            ("📦", "Stock / Ampollas", self._ir_a_stock),
            ("🔄", "Transferencias", self._ir_a_transferencias),
            ("🏥", "Vacunatorios", self._ir_a_vacunatorios),
        ]

        for indice, (icono, texto, accion) in enumerate(opciones):
            boton = ctk.CTkButton(
                menu_lateral,
                text=f"{icono}   {texto}",
                anchor="w",
                height=40,
                corner_radius=RADIO_CHICO,
                fg_color="transparent",
                hover_color=Color.SIDEBAR_HOVER,
                text_color=Color.SIDEBAR_TEXTO,
                font=Fuente.texto(),
                command=lambda a=accion, i=indice: self._seleccionar_opcion(a, i),
            )
            boton.pack(fill="x", padx=12, pady=3)
            self.botones_menu[indice] = boton

        # --- Área central donde se van a mostrar los distintos módulos ---
        contenedor_contenido = ctk.CTkFrame(cuerpo, fg_color="transparent")
        contenedor_contenido.pack(side="left", fill="both", expand=True, padx=20, pady=20)

        self.area_contenido = ctk.CTkFrame(
            contenedor_contenido,
            fg_color=Color.TARJETA,
            corner_radius=RADIO,
            border_width=1,
            border_color=Color.BORDE,
        )
        self.area_contenido.pack(fill="both", expand=True)

        self._mostrar_bienvenida()

    def _seleccionar_opcion(self, accion, indice):
        """Resalta el botón elegido en el menú y ejecuta su acción."""
        for i, boton in self.botones_menu.items():
            boton.configure(fg_color=Color.PRIMARIO if i == indice else "transparent")
        self._indice_seleccionado = indice
        accion()

    def _limpiar_area_contenido(self):
        for widget in self.area_contenido.winfo_children():
            widget.destroy()

    def _mostrar_bienvenida(self):
        self._limpiar_area_contenido()
        contenedor = ctk.CTkFrame(self.area_contenido, fg_color="transparent")
        contenedor.place(relx=0.5, rely=0.45, anchor="center")

        ctk.CTkLabel(
            contenedor, text="👋", font=ctk.CTkFont(size=40)
        ).pack(pady=(0, 10))
        ctk.CTkLabel(
            contenedor,
            text="Seleccioná una opción del menú",
            font=Fuente.titulo(),
            text_color=Color.TEXTO,
        ).pack()
        ctk.CTkLabel(
            contenedor,
            text="Vacunas, stock, transferencias e importación de datos",
            font=Fuente.texto(),
            text_color=Color.TEXTO_SECUNDARIO,
        ).pack(pady=(4, 0))

    # --- Callbacks del menú ---
    def _ir_a_transferencias(self):
        """Módulo de Transferencias e Historial de Remitos."""
        self._limpiar_area_contenido()
        vista = VistaTransferencias(self.area_contenido, self.usuario_logueado)
        vista.pack(fill="both", expand=True)

    def _ir_a_vacunas(self):
        self._limpiar_area_contenido()
        frame_vacunas = FrameVacunas(self.area_contenido, usuario_logueado=self.usuario_logueado)
        frame_vacunas.pack(fill="both", expand=True)

    def _ir_a_importar_csv(self):
        self._limpiar_area_contenido()
        frame = FrameImportarCSV(self.area_contenido)
        frame.pack(fill="both", expand=True)

    # --- Placeholders para los módulos que faltan desarrollar ---
    def _ir_a_stock(self):
        self._limpiar_area_contenido()
        ctk.CTkLabel(
            self.area_contenido,
            text="Módulo de Stock (pendiente)",
            font=Fuente.texto(),
            text_color=Color.TEXTO_SECUNDARIO,
        ).pack(pady=40)

    def _ir_a_vacunatorios(self):
        self._limpiar_area_contenido()
        ctk.CTkLabel(
            self.area_contenido,
            text="Módulo de Vacunatorios (pendiente)",
            font=Fuente.texto(),
            text_color=Color.TEXTO_SECUNDARIO,
        ).pack(pady=40)