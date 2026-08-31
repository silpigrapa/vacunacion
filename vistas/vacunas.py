"""
Vista de Vacunas: ingreso de vacuna + lote y listado del catálogo/stock.
"""

from datetime import datetime

import customtkinter as ctk

from modelos.vacuna import listar_vacunas, registrar_ingreso_central
from modelos.lote import listar_lotes
from modelos.vacunatorio import obtener_vacunatorio_central
from vistas import tema


class FrameVacunas(ctk.CTkFrame):
    def __init__(self, master, usuario_logueado=None):
        super().__init__(master, fg_color="transparent")
        self.usuario_logueado = usuario_logueado
        self._construir_widgets()
        self._cargar_listados()

    def _construir_widgets(self):
        cabecera = ctk.CTkFrame(self, fg_color="transparent")
        cabecera.pack(fill="x", padx=4, pady=(0, 8))

        # Franja hospitalaria
        franja = ctk.CTkFrame(
            cabecera, height=4, corner_radius=tema.RADIO_NULO, fg_color=tema.PRINCIPAL
        )
        franja.pack(fill="x", pady=(0, 10))

        fila_titulo = ctk.CTkFrame(cabecera, fg_color="transparent")
        fila_titulo.pack(fill="x")

        ctk.CTkLabel(
            fila_titulo,
            text="Gestión de vacunas",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=tema.OSCURO,
            anchor="w",
        ).pack(side="left")

        ctk.CTkLabel(
            fila_titulo,
            text="Hospital central · ingreso y catálogo",
            font=ctk.CTkFont(size=12),
            text_color=tema.TEXTO_SUAVE,
            anchor="e",
        ).pack(side="right")

        self.pestanas = ctk.CTkTabview(
            self,
            corner_radius=tema.RADIO,
            border_width=1,
            border_color=tema.BORDE,
            segmented_button_selected_color=tema.PRINCIPAL,
            segmented_button_selected_hover_color=tema.HOVER,
            segmented_button_unselected_color=tema.CLARO,
            segmented_button_unselected_hover_color=tema.SUAVE,
            text_color=("white", "white"),
            text_color_disabled=tema.TEXTO_SUAVE,
        )
        self.pestanas.pack(fill="both", expand=True, padx=2, pady=2)

        self.tab_cargar = self.pestanas.add("Cargar Vacunas")
        self.tab_listado = self.pestanas.add("Listado")

        self._construir_formulario()
        self._construir_listado()

    def _construir_formulario(self):
        scroll = ctk.CTkScrollableFrame(self.tab_cargar, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=6, pady=6)

        intro = ctk.CTkFrame(
            scroll,
            fg_color=tema.CLARO,
            corner_radius=tema.RADIO,
            border_width=1,
            border_color=tema.BORDE,
        )
        intro.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            intro,
            text="Registrá vacuna y lote juntos, tal como llegan al hospital.",
            font=ctk.CTkFont(size=13),
            text_color=tema.OSCURO,
            anchor="w",
        ).pack(fill="x", padx=14, pady=10)

        seccion_vacuna = self._seccion(scroll, "1 · Datos de la vacuna")
        fila1 = ctk.CTkFrame(seccion_vacuna, fg_color="transparent")
        fila1.pack(fill="x", padx=12, pady=(4, 6))
        fila1.grid_columnconfigure((0, 1), weight=1)

        self.campo_nombre = self._campo_grid(fila1, 0, "Nombre de la vacuna *")
        self.campo_fabricante = self._campo_grid(fila1, 1, "Fabricante")

        fila2 = ctk.CTkFrame(seccion_vacuna, fg_color="transparent")
        fila2.pack(fill="x", padx=12, pady=(0, 10))
        fila2.grid_columnconfigure((0, 1), weight=1)

        self.campo_dosis_requeridas = self._campo_grid(
            fila2, 0, "Dosis requeridas (por paciente)", "1"
        )
        self.campo_dosis_ampolla = self._campo_grid(
            fila2, 1, "Dosis por ampolla", "1"
        )

        ctk.CTkLabel(
            seccion_vacuna,
            text="Si la vacuna ya existe, se reutiliza el catálogo y solo se agrega el lote.",
            font=ctk.CTkFont(size=11),
            text_color=tema.TEXTO_SUAVE,
            anchor="w",
        ).pack(fill="x", padx=14, pady=(0, 10))

        seccion_lote = self._seccion(scroll, "2 · Datos del lote")
        fila3 = ctk.CTkFrame(seccion_lote, fg_color="transparent")
        fila3.pack(fill="x", padx=12, pady=(4, 6))
        fila3.grid_columnconfigure((0, 1), weight=1)

        self.campo_numero_lote = self._campo_grid(fila3, 0, "Número de lote *")
        self.campo_vencimiento = self._campo_grid(
            fila3, 1, "Fecha de vencimiento *", placeholder="AAAA-MM-DD"
        )

        fila4 = ctk.CTkFrame(seccion_lote, fg_color="transparent")
        fila4.pack(fill="x", padx=12, pady=(0, 12))
        fila4.grid_columnconfigure((0, 1), weight=1)

        self.campo_cantidad = self._campo_grid(
            fila4, 0, "Cantidad de ampollas *", "1"
        )
        ctk.CTkFrame(fila4, fg_color="transparent").grid(
            row=0, column=1, sticky="nsew", padx=(8, 0)
        )

        acciones = ctk.CTkFrame(scroll, fg_color="transparent")
        acciones.pack(fill="x", pady=(2, 6))

        self.etiqueta_mensaje = ctk.CTkLabel(
            acciones, text="", anchor="w", font=ctk.CTkFont(size=12)
        )
        self.etiqueta_mensaje.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            acciones,
            text="Limpiar",
            width=110,
            height=34,
            corner_radius=tema.RADIO,
            fg_color=tema.SUAVE,
            hover_color=tema.CLARO,
            text_color=tema.OSCURO,
            command=self._limpiar_formulario,
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            acciones,
            text="Guardar llegada",
            width=160,
            height=34,
            corner_radius=tema.RADIO,
            font=ctk.CTkFont(weight="bold"),
            fg_color=tema.PRINCIPAL,
            hover_color=tema.HOVER,
            command=self._guardar_llegada,
        ).pack(side="right")

    def _seccion(self, padre, titulo):
        marco = ctk.CTkFrame(
            padre,
            fg_color=tema.FONDO_PANEL,
            corner_radius=tema.RADIO,
            border_width=1,
            border_color=tema.BORDE,
        )
        marco.pack(fill="x", pady=(0, 10))

        barra = ctk.CTkFrame(
            marco, fg_color=tema.OSCURO, corner_radius=tema.RADIO_NULO, height=34
        )
        barra.pack(fill="x")
        barra.pack_propagate(False)

        ctk.CTkLabel(
            barra,
            text=titulo,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="white",
            anchor="w",
        ).pack(side="left", padx=12)

        return marco

    def _campo_grid(self, padre, columna, etiqueta, valor_inicial="", placeholder=""):
        caja = ctk.CTkFrame(padre, fg_color="transparent")
        caja.grid(row=0, column=columna, sticky="nsew", padx=(0 if columna == 0 else 8, 0))

        ctk.CTkLabel(
            caja,
            text=etiqueta,
            font=ctk.CTkFont(size=12),
            text_color=tema.TEXTO_SUAVE,
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

        entrada = ctk.CTkEntry(
            caja,
            height=34,
            corner_radius=tema.RADIO,
            border_color=tema.BORDE,
            placeholder_text=placeholder,
        )
        if valor_inicial:
            entrada.insert(0, valor_inicial)
        entrada.pack(fill="x")
        return entrada

    def _construir_listado(self):
        barra = ctk.CTkFrame(self.tab_listado, fg_color="transparent")
        barra.pack(fill="x", padx=8, pady=(8, 4))

        self.etiqueta_resumen = ctk.CTkLabel(
            barra,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=tema.TEXTO_SUAVE,
            anchor="w",
        )
        self.etiqueta_resumen.pack(side="left")

        ctk.CTkButton(
            barra,
            text="Actualizar",
            width=110,
            height=30,
            corner_radius=tema.RADIO,
            fg_color=tema.PRINCIPAL,
            hover_color=tema.HOVER,
            command=self._cargar_listados,
        ).pack(side="right")

        self.sub = ctk.CTkTabview(
            self.tab_listado,
            height=360,
            corner_radius=tema.RADIO,
            border_width=1,
            border_color=tema.BORDE,
            segmented_button_selected_color=tema.PRINCIPAL,
            segmented_button_selected_hover_color=tema.HOVER,
            segmented_button_unselected_color=tema.CLARO,
            segmented_button_unselected_hover_color=tema.SUAVE,
        )
        self.sub.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        self.tab_catalogo = self.sub.add("Catálogo")
        self.tab_lotes = self.sub.add("Lotes ingresados")

        self.lista_vacunas = ctk.CTkScrollableFrame(
            self.tab_catalogo, fg_color="transparent"
        )
        self.lista_vacunas.pack(fill="both", expand=True, padx=4, pady=4)

        self.lista_lotes = ctk.CTkScrollableFrame(
            self.tab_lotes, fg_color="transparent"
        )
        self.lista_lotes.pack(fill="both", expand=True, padx=4, pady=4)

    def _encabezado(self, padre, columnas):
        fila = ctk.CTkFrame(
            padre,
            fg_color=tema.OSCURO,
            corner_radius=tema.RADIO,
            height=34,
        )
        fila.pack(fill="x", pady=(0, 4))
        fila.pack_propagate(False)

        for texto, peso in columnas:
            ctk.CTkLabel(
                fila,
                text=texto,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="white",
                anchor="w",
            ).pack(side="left", fill="x", expand=(peso > 0), padx=10, pady=6)

    def _fila(self, padre, valores, alterna=False):
        fila = ctk.CTkFrame(
            padre,
            fg_color=tema.FILA_ALT if alterna else tema.FONDO_PANEL,
            corner_radius=tema.RADIO,
            border_width=1,
            border_color=tema.BORDE,
            height=36,
        )
        fila.pack(fill="x", pady=1)
        fila.pack_propagate(False)

        for valor in valores:
            ctk.CTkLabel(
                fila,
                text=str(valor),
                font=ctk.CTkFont(size=12),
                text_color=tema.TEXTO,
                anchor="w",
            ).pack(side="left", fill="x", expand=True, padx=10, pady=6)

    def _vacio(self, padre, mensaje):
        ctk.CTkLabel(
            padre,
            text=mensaje,
            font=ctk.CTkFont(size=13),
            text_color=tema.TEXTO_SUAVE,
        ).pack(pady=40)

    def _limpiar_contenedor(self, contenedor):
        for widget in contenedor.winfo_children():
            widget.destroy()

    def _cargar_listados(self):
        vacunas = listar_vacunas()
        lotes = listar_lotes()

        self.etiqueta_resumen.configure(
            text=f"{len(vacunas)} vacuna(s) en catálogo  ·  {len(lotes)} lote(s) registrados"
        )

        self._limpiar_contenedor(self.lista_vacunas)
        self._limpiar_contenedor(self.lista_lotes)

        if not vacunas:
            self._vacio(self.lista_vacunas, "Todavía no hay vacunas en el catálogo.")
        else:
            self._encabezado(
                self.lista_vacunas,
                (
                    ("Nombre", 1),
                    ("Fabricante", 1),
                    ("Dosis req.", 1),
                    ("Dosis/ampolla", 1),
                ),
            )
            for i, vacuna in enumerate(vacunas):
                self._fila(
                    self.lista_vacunas,
                    (
                        vacuna["nombre"] or "-",
                        vacuna["fabricante"] or "-",
                        vacuna["dosis_requeridas"],
                        vacuna["dosis_por_ampolla"],
                    ),
                    alterna=i % 2 == 1,
                )

        if not lotes:
            self._vacio(self.lista_lotes, "Todavía no hay lotes ingresados.")
        else:
            self._encabezado(
                self.lista_lotes,
                (
                    ("Vacuna", 1),
                    ("N° lote", 1),
                    ("Vencimiento", 1),
                    ("Ampollas", 1),
                    ("Vacunatorio", 1),
                ),
            )
            for i, lote in enumerate(lotes):
                self._fila(
                    self.lista_lotes,
                    (
                        lote["nombre_vacuna"],
                        lote["numero_lote"],
                        lote["fecha_vencimiento"],
                        lote["cantidad_ampollas"],
                        lote["nombre_vacunatorio"],
                    ),
                    alterna=i % 2 == 1,
                )

    def _mostrar_mensaje(self, texto, ok=True):
        self.etiqueta_mensaje.configure(
            text=texto, text_color=tema.OK if ok else tema.ERROR
        )

    def _limpiar_formulario(self):
        for campo, default in (
            (self.campo_nombre, ""),
            (self.campo_fabricante, ""),
            (self.campo_dosis_requeridas, "1"),
            (self.campo_dosis_ampolla, "1"),
            (self.campo_numero_lote, ""),
            (self.campo_vencimiento, ""),
            (self.campo_cantidad, "1"),
        ):
            campo.delete(0, "end")
            if default:
                campo.insert(0, default)
        self.etiqueta_mensaje.configure(text="")

    def _obtener_vacunatorio_destino(self):
        central = obtener_vacunatorio_central()
        if central is not None:
            return central["id_vacunatorio"]
        if self.usuario_logueado is not None:
            return self.usuario_logueado["id_vacunatorio"]
        return None

    def _guardar_llegada(self):
        nombre = self.campo_nombre.get().strip()
        fabricante = self.campo_fabricante.get().strip() or None
        numero_lote = self.campo_numero_lote.get().strip()
        fecha_vencimiento = self.campo_vencimiento.get().strip()
        texto_req = self.campo_dosis_requeridas.get().strip()
        texto_amp = self.campo_dosis_ampolla.get().strip()
        texto_cant = self.campo_cantidad.get().strip()

        if not nombre:
            self._mostrar_mensaje("El nombre de la vacuna es obligatorio.", ok=False)
            return
        if not numero_lote:
            self._mostrar_mensaje("El número de lote es obligatorio.", ok=False)
            return
        if not fecha_vencimiento:
            self._mostrar_mensaje("La fecha de vencimiento es obligatoria.", ok=False)
            return

        try:
            datetime.strptime(fecha_vencimiento, "%Y-%m-%d")
        except ValueError:
            self._mostrar_mensaje(
                "Fecha inválida. Usá el formato AAAA-MM-DD (ej: 2027-06-30).",
                ok=False,
            )
            return

        try:
            dosis_requeridas = int(texto_req)
            dosis_por_ampolla = int(texto_amp)
            cantidad_ampollas = int(texto_cant)
        except ValueError:
            self._mostrar_mensaje(
                "Dosis y cantidad de ampollas deben ser números enteros.",
                ok=False,
            )
            return

        if dosis_requeridas < 1 or dosis_por_ampolla < 1 or cantidad_ampollas < 1:
            self._mostrar_mensaje(
                "Dosis y cantidad de ampollas deben ser mayores o iguales a 1.",
                ok=False,
            )
            return

        id_vacunatorio = self._obtener_vacunatorio_destino()
        if id_vacunatorio is None:
            self._mostrar_mensaje(
                "No hay un vacunatorio central configurado.", ok=False
            )
            return

        try:
            _, _, vacuna_nueva = registrar_ingreso_central(
                nombre=nombre,
                fabricante=fabricante,
                dosis_requeridas=dosis_requeridas,
                dosis_por_ampolla=dosis_por_ampolla,
                numero_lote=numero_lote,
                fecha_vencimiento=fecha_vencimiento,
                cantidad_ampollas=cantidad_ampollas,
                id_vacunatorio=id_vacunatorio,
            )
        except Exception as error:
            self._mostrar_mensaje(f"No se pudo guardar: {error}", ok=False)
            return

        detalle = "nueva vacuna" if vacuna_nueva else "vacuna ya existente"
        self._limpiar_formulario()
        self._mostrar_mensaje(
            f'Llegada guardada: "{nombre}" · lote {numero_lote} ({detalle}).'
        )
        self._cargar_listados()
        self.pestanas.set("Listado")
        self.sub.set("Lotes ingresados")
