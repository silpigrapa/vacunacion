"""
Vista de Stock
"""

from datetime import date

import customtkinter as ctk

from modelos.stock import (
    listar_stock_por_vacunatorio,
    listar_ampollas_detalle,
    obtener_resumen_stock,
)
from modelos.vacunatorio import listar_vacunatorios
from vistas import tema


class FrameStock(ctk.CTkFrame):
    def __init__(self, master, usuario_logueado=None):
        super().__init__(master, fg_color="transparent")
        self.usuario_logueado = usuario_logueado
        self.vacunatorios = list(listar_vacunatorios())
        self.mapa_vacunatorios = {v["nombre"]: v["id_vacunatorio"] for v in self.vacunatorios}
        self._construir_widgets()
        self._cargar_stock()

    # ------------------------------------------------------------------
    # Construcción de la interfaz
    # ------------------------------------------------------------------
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
            text="Stock de vacunas",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=tema.OSCURO,
            anchor="w",
        ).pack(side="left")

        ctk.CTkLabel(
            fila_titulo,
            text="Vacunas cargadas y ampollas disponibles",
            font=ctk.CTkFont(size=12),
            text_color=tema.TEXTO_SUAVE,
            anchor="e",
        ).pack(side="right")

        # --- Barra de filtro por vacunatorio ---
        barra_filtro = ctk.CTkFrame(
            self,
            fg_color=tema.CLARO,
            corner_radius=tema.RADIO,
            border_width=1,
            border_color=tema.BORDE,
        )
        barra_filtro.pack(fill="x", padx=2, pady=(0, 10))

        ctk.CTkLabel(
            barra_filtro,
            text="Vacunatorio:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=tema.OSCURO,
        ).pack(side="left", padx=(14, 8), pady=10)

        nombres_vacunatorios = ["Todos"] + [v["nombre"] for v in self.vacunatorios]
        self.selector_vacunatorio = ctk.CTkOptionMenu(
            barra_filtro,
            values=nombres_vacunatorios if nombres_vacunatorios else ["Sin vacunatorios"],
            fg_color=tema.PRINCIPAL,
            button_color=tema.PRINCIPAL,
            button_hover_color=tema.HOVER,
            command=lambda _seleccion: self._cargar_stock(),
        )
        self.selector_vacunatorio.set(self._vacunatorio_por_defecto(nombres_vacunatorios))
        self.selector_vacunatorio.pack(side="left", pady=8)

        ctk.CTkButton(
            barra_filtro,
            text="Actualizar",
            width=110,
            height=30,
            corner_radius=tema.RADIO,
            fg_color=tema.OSCURO,
            hover_color=tema.HOVER,
            command=self._cargar_stock,
        ).pack(side="right", padx=14, pady=8)

        # --- Tarjetas de resumen ---
        self.marco_resumen = ctk.CTkFrame(self, fg_color="transparent")
        self.marco_resumen.pack(fill="x", padx=2, pady=(0, 10))
        self.marco_resumen.grid_columnconfigure((0, 1, 2), weight=1)

        self.tarjeta_vacunas = self._tarjeta_resumen(self.marco_resumen, 0, "Vacunas con stock")
        self.tarjeta_ampollas = self._tarjeta_resumen(self.marco_resumen, 1, "Ampollas disponibles")
        self.tarjeta_dosis = self._tarjeta_resumen(self.marco_resumen, 2, "Dosis disponibles")

        # --- Pestañas: Resumen por vacuna / Detalle de ampollas ---
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

        self.tab_resumen = self.pestanas.add("Stock por vacuna")
        self.tab_detalle = self.pestanas.add("Detalle de ampollas")

        self.lista_resumen = ctk.CTkScrollableFrame(self.tab_resumen, fg_color="transparent")
        self.lista_resumen.pack(fill="both", expand=True, padx=4, pady=4)

        self.lista_detalle = ctk.CTkScrollableFrame(self.tab_detalle, fg_color="transparent")
        self.lista_detalle.pack(fill="both", expand=True, padx=4, pady=4)

    def _vacunatorio_por_defecto(self, nombres_vacunatorios):
        """
        Si el usuario logueado tiene un vacunatorio asignado, arranca
        filtrado por ese; si no, arranca mostrando 'Todos'.
        """
        if self.usuario_logueado is not None:
            for vacunatorio in self.vacunatorios:
                if vacunatorio["id_vacunatorio"] == self.usuario_logueado["id_vacunatorio"]:
                    return vacunatorio["nombre"]
        return nombres_vacunatorios[0] if nombres_vacunatorios else ""

    def _tarjeta_resumen(self, padre, columna, titulo):
        tarjeta = ctk.CTkFrame(
            padre,
            fg_color=tema.FONDO_PANEL,
            corner_radius=tema.RADIO,
            border_width=1,
            border_color=tema.BORDE,
        )
        tarjeta.grid(row=0, column=columna, sticky="nsew", padx=(0 if columna == 0 else 6, 0))

        ctk.CTkLabel(
            tarjeta,
            text=titulo,
            font=ctk.CTkFont(size=12),
            text_color=tema.TEXTO_SUAVE,
        ).pack(anchor="w", padx=14, pady=(10, 0))

        etiqueta_valor = ctk.CTkLabel(
            tarjeta,
            text="0",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=tema.OSCURO,
        )
        etiqueta_valor.pack(anchor="w", padx=14, pady=(0, 12))
        return etiqueta_valor

    def _encabezado(self, padre, columnas):
        fila = ctk.CTkFrame(padre, fg_color=tema.OSCURO, corner_radius=tema.RADIO, height=34)
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

    def _fila(self, padre, valores, alterna=False, color_texto=None):
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
                text_color=color_texto or tema.TEXTO,
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

    # ------------------------------------------------------------------
    # Carga de datos
    # ------------------------------------------------------------------
    def _id_vacunatorio_seleccionado(self):
        nombre = self.selector_vacunatorio.get()
        return self.mapa_vacunatorios.get(nombre)  # None si es "Todos" o no hay match

    def _cargar_stock(self):
        id_vacunatorio = self._id_vacunatorio_seleccionado()

        resumen_numerico = obtener_resumen_stock(id_vacunatorio)
        self.tarjeta_vacunas.configure(text=str(resumen_numerico["vacunas_con_stock"]))
        self.tarjeta_ampollas.configure(text=str(resumen_numerico["ampollas_con_stock"]))
        self.tarjeta_dosis.configure(text=str(resumen_numerico["dosis_disponibles"]))

        self._cargar_resumen_por_vacuna(id_vacunatorio)
        self._cargar_detalle_ampollas(id_vacunatorio)

    def _cargar_resumen_por_vacuna(self, id_vacunatorio):
        self._limpiar_contenedor(self.lista_resumen)

        if id_vacunatorio is not None:
            filas = listar_stock_por_vacunatorio(id_vacunatorio)
            columnas = (
                ("Vacuna", 1),
                ("Fabricante", 1),
                ("Ampollas", 1),
                ("Dosis disponibles", 1),
                ("Próximo vencimiento", 1),
            )
        else:
            # "Todos": agrupo por vacuna sumando todos los vacunatorios,
            # reutilizando listar_stock_por_vacunatorio por cada uno.
            acumulado = {}
            for vacunatorio in self.vacunatorios:
                for fila in listar_stock_por_vacunatorio(vacunatorio["id_vacunatorio"]):
                    clave = fila["id_vacuna"]
                    if clave not in acumulado:
                        acumulado[clave] = {
                            "nombre_vacuna": fila["nombre_vacuna"],
                            "fabricante": fila["fabricante"],
                            "cantidad_ampollas": 0,
                            "dosis_disponibles": 0,
                            "proximo_vencimiento": None,
                        }
                    acumulado[clave]["cantidad_ampollas"] += fila["cantidad_ampollas"]
                    acumulado[clave]["dosis_disponibles"] += fila["dosis_disponibles"]
                    if fila["proximo_vencimiento"] is not None:
                        actual = acumulado[clave]["proximo_vencimiento"]
                        if actual is None or fila["proximo_vencimiento"] < actual:
                            acumulado[clave]["proximo_vencimiento"] = fila["proximo_vencimiento"]

            filas = sorted(acumulado.values(), key=lambda f: f["nombre_vacuna"])
            columnas = (
                ("Vacuna", 1),
                ("Fabricante", 1),
                ("Ampollas", 1),
                ("Dosis disponibles", 1),
                ("Próximo vencimiento", 1),
            )

        if not filas:
            self._vacio(self.lista_resumen, "No hay stock cargado para este filtro.")
            return

        self._encabezado(self.lista_resumen, columnas)
        hoy = date.today().isoformat()
        for i, fila in enumerate(filas):
            vencimiento = fila["proximo_vencimiento"] or "-"
            color = tema.ERROR if (vencimiento != "-" and vencimiento < hoy) else None
            self._fila(
                self.lista_resumen,
                (
                    fila["nombre_vacuna"],
                    fila["fabricante"] or "-",
                    fila["cantidad_ampollas"],
                    fila["dosis_disponibles"],
                    vencimiento,
                ),
                alterna=i % 2 == 1,
                color_texto=color,
            )

    def _cargar_detalle_ampollas(self, id_vacunatorio):
        self._limpiar_contenedor(self.lista_detalle)

        ampollas = listar_ampollas_detalle(id_vacunatorio=id_vacunatorio)

        if not ampollas:
            self._vacio(self.lista_detalle, "No hay ampollas con stock para este filtro.")
            return

        columnas = [
            ("Vacuna", 1),
            ("N° lote", 1),
            ("Vencimiento", 1),
            ("Dosis restantes", 1),
            ("Estado", 1),
        ]
        if id_vacunatorio is None:
            columnas.append(("Vacunatorio", 1))

        self._encabezado(self.lista_detalle, columnas)
        hoy = date.today().isoformat()

        for i, ampolla in enumerate(ampollas):
            vencida = ampolla["fecha_vencimiento"] < hoy
            estado = "Vencida" if vencida else ("Abierta" if ampolla["fecha_apertura"] else "Cerrada")

            valores = [
                ampolla["nombre_vacuna"],
                ampolla["numero_lote"],
                ampolla["fecha_vencimiento"],
                ampolla["dosis_disponibles"],
                estado,
            ]
            if id_vacunatorio is None:
                valores.append(ampolla["nombre_vacunatorio"])

            self._fila(
                self.lista_detalle,
                valores,
                alterna=i % 2 == 1,
                color_texto=tema.ERROR if vencida else None,
            )
