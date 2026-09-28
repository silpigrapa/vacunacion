"""
Vista de Vacunas: ingreso de vacuna + lote y listado del catálogo/stock.
"""

import calendar
from datetime import date, datetime

import customtkinter as ctk
from tkinter import ttk

from modelos.vacuna import listar_vacunas, registrar_ingreso_central
from modelos.lote import listar_lotes
from modelos.vacunatorio import obtener_vacunatorio_central
from vistas import tema

MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]
DIAS_SEMANA = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sa", "Do"]


class VentanaCalendario(ctk.CTkToplevel):
    """Popup modal con un calendario mensual para elegir una fecha."""

    def __init__(self, master, al_elegir, fecha_inicial=None, widget_referencia=None):
        super().__init__(master)
        self.al_elegir = al_elegir

        self.title("Elegir fecha")
        self.resizable(False, False)
        self.transient(master)
        self.overrideredirect(True)  # sin barra de título, look de "desplegable"
        self.attributes("-topmost", True)  # siempre visible por encima del resto

        base = fecha_inicial or date.today()
        self.anio = base.year
        self.mes = base.month

        self._construir_widgets()
        self._dibujar_mes()

        if widget_referencia is not None:
            self._posicionar_bajo(widget_referencia)

        self.bind("<Escape>", lambda evento: self._cerrar())
        self.lift()
        self.focus_force()

    def _posicionar_bajo(self, widget):
        """Ubica el popup justo debajo del campo de fecha que lo abrió."""
        self.update_idletasks()
        x = widget.winfo_rootx()
        y = widget.winfo_rooty() + widget.winfo_height() + 2
        self.geometry(f"+{x}+{y}")

    def _construir_widgets(self):
        cabecera = ctk.CTkFrame(self, fg_color=tema.OSCURO, corner_radius=0)
        cabecera.pack(fill="x")

        ctk.CTkButton(
            cabecera, text="◀", width=32, height=28,
            fg_color="transparent", hover_color=tema.HOVER,
            command=self._mes_anterior,
        ).pack(side="left", padx=4, pady=4)

        self.etiqueta_mes = ctk.CTkLabel(
            cabecera, text="", font=ctk.CTkFont(size=13, weight="bold"),
            text_color="white",
        )
        self.etiqueta_mes.pack(side="left", expand=True)

        ctk.CTkButton(
            cabecera, text="▶", width=32, height=28,
            fg_color="transparent", hover_color=tema.HOVER,
            command=self._mes_siguiente,
        ).pack(side="right", padx=4, pady=4)

        self.marco_dias = ctk.CTkFrame(self, fg_color="transparent")
        self.marco_dias.pack(padx=8, pady=8)

    def _mes_anterior(self):
        self.mes -= 1
        if self.mes == 0:
            self.mes = 12
            self.anio -= 1
        self._dibujar_mes()

    def _mes_siguiente(self):
        self.mes += 1
        if self.mes == 13:
            self.mes = 1
            self.anio += 1
        self._dibujar_mes()

    def _dibujar_mes(self):
        for widget in self.marco_dias.winfo_children():
            widget.destroy()

        self.etiqueta_mes.configure(text=f"{MESES[self.mes - 1]} {self.anio}")

        for columna, nombre in enumerate(DIAS_SEMANA):
            ctk.CTkLabel(
                self.marco_dias, text=nombre, width=34,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=tema.TEXTO_SUAVE,
            ).grid(row=0, column=columna, pady=(0, 4))

        semanas = calendar.Calendar(firstweekday=0).monthdayscalendar(self.anio, self.mes)
        hoy = date.today()

        for fila, semana in enumerate(semanas, start=1):
            for columna, dia in enumerate(semana):
                if dia == 0:
                    continue
                es_hoy = dia == hoy.day and self.mes == hoy.month and self.anio == hoy.year
                ctk.CTkButton(
                    self.marco_dias,
                    text=str(dia),
                    width=34,
                    height=30,
                    corner_radius=tema.RADIO,
                    fg_color=tema.PRINCIPAL if es_hoy else "transparent",
                    text_color="white" if es_hoy else tema.TEXTO,
                    hover_color=tema.SUAVE,
                    command=lambda d=dia: self._elegir(d),
                ).grid(row=fila, column=columna, padx=1, pady=1)

    def _cerrar(self):
        """
        Cierra el popup y le devuelve el foco del teclado a la ventana
        principal. Con overrideredirect(True), al destruir el popup el
        sistema no le devuelve el foco a la app y los campos no reciben teclas.
        """
        raiz = self.master.winfo_toplevel()
        self.destroy()
        raiz.after(10, raiz.focus_force)

    def _elegir(self, dia):
        fecha_elegida = date(self.anio, self.mes, dia)
        self.al_elegir(fecha_elegida)
        self._cerrar()


def _mostrar_selector_fecha(master, entrada, fecha_inicial=None):
    """
    Abre el popup de calendario debajo del campo `entrada`. Al elegir una
    fecha, la escribe en la entrada con formato DD/MM/AAAA.

    `entrada` puede estar en estado "readonly": esta función la habilita
    temporalmente para poder escribir la fecha elegida.
    """

    def al_elegir(fecha):
        estado_previo = entrada.cget("state")
        entrada.configure(state="normal")
        entrada.delete(0, "end")
        entrada.insert(0, fecha.strftime("%d/%m/%Y"))
        entrada.configure(state=estado_previo)

    VentanaCalendario(
        master, al_elegir, fecha_inicial=fecha_inicial, widget_referencia=entrada
    )


class FrameVacunas(ctk.CTkFrame):
    def __init__(self, master, usuario_logueado=None):
        super().__init__(master, fg_color="transparent")
        self.usuario_logueado = usuario_logueado
        self._construir_widgets()
        self._cargar_listados()
        # Foco automático en el primer campo vacío para poder escribir de una
        self.after(100, self.campo_nombre.focus_set)

    def _actualizar_color_texto_pestanas(self, tabview):
        botones = tabview._segmented_button._buttons_dict
        seleccionada = tabview.get()
        for nombre, boton in botones.items():
            boton.configure(text_color="white" if nombre == seleccionada else tema.TEXTO_PESTANA_INACTIVA)

    def _al_cambiar_pestana_principal(self):
        self._actualizar_color_texto_pestanas(self.pestanas)
        if self.pestanas.get() == "Cargar Vacunas":
            self.after(100, self.campo_nombre.focus_set)

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
            text_color=tema.TEXTO,
            text_color_disabled=tema.TEXTO_SUAVE,
            command=self._al_cambiar_pestana_principal,
        )
        self.pestanas.pack(fill="both", expand=True, padx=2, pady=2)

        self.tab_cargar = self.pestanas.add("Cargar Vacunas")
        self.tab_listado = self.pestanas.add("Listado")
        self._actualizar_color_texto_pestanas(self.pestanas)

        self._construir_formulario()
        self._construir_listado()

    def _construir_formulario(self):
        scroll = ctk.CTkScrollableFrame(self.tab_cargar, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=6, pady=6)

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
        self.campo_vencimiento = self._campo_fecha_grid(fila3, 1, "Fecha de vencimiento *")

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

    def _campo_fecha_grid(self, padre, columna, etiqueta):
        """Igual que _campo_grid, pero de solo lectura: al hacer clic abre
        un calendario y la fecha elegida se completa como DD/MM/AAAA."""
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
            placeholder_text="DD/MM/AAAA",
            state="readonly",
        )
        entrada.pack(fill="x")
        entrada.bind("<Button-1>", lambda evento, e=entrada: self._abrir_calendario(e))
        return entrada

    def _abrir_calendario(self, entrada):
        fecha_inicial = None
        texto_actual = entrada.get().strip()
        if texto_actual:
            try:
                fecha_inicial = datetime.strptime(texto_actual, "%d/%m/%Y").date()
            except ValueError:
                fecha_inicial = None
        _mostrar_selector_fecha(self, entrada, fecha_inicial=fecha_inicial)

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
            text_color=tema.TEXTO,
            text_color_disabled=tema.TEXTO_SUAVE,
            command=lambda: self._actualizar_color_texto_pestanas(self.sub),
        )
        self.sub.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        self.tab_catalogo = self.sub.add("Catálogo")
        self.tab_lotes = self.sub.add("Lotes ingresados")
        self._actualizar_color_texto_pestanas(self.sub)
        self.tab_catalogo.grid_columnconfigure(0, weight=1)
        self.tab_catalogo.grid_rowconfigure(0, weight=1)
        self.tab_lotes.grid_columnconfigure(0, weight=1)
        self.tab_lotes.grid_rowconfigure(0, weight=1)

        # Mismo estilo de tabla que usa el módulo de Transferencias
        estilo = ttk.Style()
        estilo.theme_use("default")
        estilo.configure("Treeview", rowheight=25, font=("Arial", 10))
        estilo.configure("Treeview.Heading", font=("Arial", 10, "bold"))

        columnas_vacunas = ("nombre", "fabricante", "dosis_req", "dosis_amp", "lote", "vencimiento", "ampollas")
        self.tabla_vacunas = ttk.Treeview(
            self.tab_catalogo, columns=columnas_vacunas, show="headings", selectmode="browse"
        )
        self.tabla_vacunas.heading("nombre", text="Nombre")
        self.tabla_vacunas.heading("fabricante", text="Fabricante")
        self.tabla_vacunas.heading("dosis_req", text="Dosis req.")
        self.tabla_vacunas.heading("dosis_amp", text="Dosis/ampolla")
        self.tabla_vacunas.heading("lote", text="N° lote")
        self.tabla_vacunas.heading("vencimiento", text="Vencimiento")
        self.tabla_vacunas.heading("ampollas", text="Ampollas")
        self.tabla_vacunas.column("nombre", width=170, anchor="w")
        self.tabla_vacunas.column("fabricante", width=130, anchor="w")
        self.tabla_vacunas.column("dosis_req", width=90, anchor="center")
        self.tabla_vacunas.column("dosis_amp", width=100, anchor="center")
        self.tabla_vacunas.column("lote", width=100, anchor="center")
        self.tabla_vacunas.column("vencimiento", width=100, anchor="center")
        self.tabla_vacunas.column("ampollas", width=90, anchor="center")

        scroll_vacunas = ttk.Scrollbar(
            self.tab_catalogo, orient="vertical", command=self.tabla_vacunas.yview
        )
        self.tabla_vacunas.configure(yscrollcommand=scroll_vacunas.set)
        self.tabla_vacunas.grid(row=0, column=0, sticky="nsew", padx=(4, 0), pady=4)
        scroll_vacunas.grid(row=0, column=1, sticky="ns", padx=(0, 4), pady=4)

        columnas_lotes = ("vacuna", "lote", "vencimiento", "ampollas", "vacunatorio")
        self.tabla_lotes = ttk.Treeview(
            self.tab_lotes, columns=columnas_lotes, show="headings", selectmode="browse"
        )
        self.tabla_lotes.heading("vacuna", text="Vacuna")
        self.tabla_lotes.heading("lote", text="N° lote")
        self.tabla_lotes.heading("vencimiento", text="Vencimiento")
        self.tabla_lotes.heading("ampollas", text="Ampollas")
        self.tabla_lotes.heading("vacunatorio", text="Vacunatorio")
        self.tabla_lotes.column("vacuna", width=170, anchor="w")
        self.tabla_lotes.column("lote", width=110, anchor="center")
        self.tabla_lotes.column("vencimiento", width=110, anchor="center")
        self.tabla_lotes.column("ampollas", width=90, anchor="center")
        self.tabla_lotes.column("vacunatorio", width=160, anchor="w")

        scroll_lotes = ttk.Scrollbar(
            self.tab_lotes, orient="vertical", command=self.tabla_lotes.yview
        )
        self.tabla_lotes.configure(yscrollcommand=scroll_lotes.set)
        self.tabla_lotes.grid(row=0, column=0, sticky="nsew", padx=(4, 0), pady=4)
        scroll_lotes.grid(row=0, column=1, sticky="ns", padx=(0, 4), pady=4)

    @staticmethod
    def _formatear_fecha(fecha_iso):
        """Convierte AAAA-MM-DD (como se guarda en la base) a DD/MM/AAAA para mostrar."""
        try:
            return datetime.strptime(fecha_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
        except (ValueError, TypeError):
            return fecha_iso or "-"

    def _cargar_listados(self):
        vacunas = listar_vacunas()
        lotes = listar_lotes()

        self.etiqueta_resumen.configure(
            text=f"{len(vacunas)} vacuna(s) en catálogo  ·  {len(lotes)} lote(s) registrados"
        )

        for item in self.tabla_vacunas.get_children():
            self.tabla_vacunas.delete(item)
        for item in self.tabla_lotes.get_children():
            self.tabla_lotes.delete(item)

        for lote in lotes:
            self.tabla_vacunas.insert(
                "",
                "end",
                values=(
                    lote["nombre_vacuna"] or "-",
                    lote["fabricante"] or "-",
                    lote["dosis_requeridas"],
                    lote["dosis_por_ampolla"],
                    lote["numero_lote"],
                    self._formatear_fecha(lote["fecha_vencimiento"]),
                    lote["cantidad_ampollas"],
                ),
            )

        for lote in lotes:
            self.tabla_lotes.insert(
                "",
                "end",
                values=(
                    lote["nombre_vacuna"],
                    lote["numero_lote"],
                    self._formatear_fecha(lote["fecha_vencimiento"]),
                    lote["cantidad_ampollas"],
                    lote["nombre_vacunatorio"],
                ),
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
            (self.campo_cantidad, "1"),
        ):
            campo.delete(0, "end")
            if default:
                campo.insert(0, default)

        self.campo_vencimiento.configure(state="normal")
        self.campo_vencimiento.delete(0, "end")
        self.campo_vencimiento.configure(state="readonly")

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
        fecha_vencimiento_ddmmaaaa = self.campo_vencimiento.get().strip()
        texto_req = self.campo_dosis_requeridas.get().strip()
        texto_amp = self.campo_dosis_ampolla.get().strip()
        texto_cant = self.campo_cantidad.get().strip()

        if not nombre:
            self._mostrar_mensaje("El nombre de la vacuna es obligatorio.", ok=False)
            return
        if not numero_lote:
            self._mostrar_mensaje("El número de lote es obligatorio.", ok=False)
            return
        if not fecha_vencimiento_ddmmaaaa:
            self._mostrar_mensaje("La fecha de vencimiento es obligatoria.", ok=False)
            return

        try:
            fecha_vencimiento = datetime.strptime(
                fecha_vencimiento_ddmmaaaa, "%d/%m/%Y"
            ).strftime("%Y-%m-%d")
        except ValueError:
            self._mostrar_mensaje(
                "Fecha inválida. Elegila con el calendario.",
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