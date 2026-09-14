"""
Pantalla de Stock / Ampollas.

Tres funciones en una pantalla:
  1. Comparativa de stock de una vacuna en TODOS los vacunatorios
     (para saber quién puede cubrir un faltante).
  2. Detalle de ampollas de un vacunatorio puntual (con su estado:
     Utilizable, Vencida o Agotada).
  3. Alta de nuevo stock: carga un lote nuevo y genera sus ampollas.
"""

from datetime import datetime

import customtkinter as ctk

from modelos.vacuna import listar_vacunas
from modelos.vacunatorio import listar_vacunatorios
from modelos.lote import crear_lote
from modelos.ampolla import (
    crear_ampolla,
    listar_ampollas_por_vacunatorio,
    obtener_stock_por_vacunatorio,
)


class FrameStock(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.vacunas = listar_vacunas()
        self.vacunatorios = listar_vacunatorios()
        self._construir_widgets()

    # ------------------------------------------------------------------
    # Construcción de la interfaz
    # ------------------------------------------------------------------
    def _construir_widgets(self):
        ctk.CTkLabel(
            self, text="Stock de vacunas",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(10, 15), anchor="w", padx=10)

        if not self.vacunas or not self.vacunatorios:
            ctk.CTkLabel(
                self,
                text="Necesitás tener al menos una vacuna y un vacunatorio cargados para usar esta pantalla.",
            ).pack(pady=40)
            return

        pestañas = ctk.CTkTabview(self)
        pestañas.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        tab_comparativa = pestañas.add("Stock por vacunatorio")
        tab_detalle = pestañas.add("Detalle de ampollas")
        tab_alta = pestañas.add("Cargar nuevo stock")

        self._construir_tab_comparativa(tab_comparativa)
        self._construir_tab_detalle(tab_detalle)
        self._construir_tab_alta(tab_alta)

    # ------------------------------------------------------------------
    # Tab 1: comparativa de stock por vacunatorio
    # ------------------------------------------------------------------
    def _construir_tab_comparativa(self, tab):
        fila = ctk.CTkFrame(tab, fg_color="transparent")
        fila.pack(fill="x", pady=(10, 15), padx=10)

        ctk.CTkLabel(fila, text="Vacuna:").pack(side="left", padx=(0, 10))
        self.combo_vacuna_comparativa = ctk.CTkComboBox(
            fila, values=[v["nombre"] for v in self.vacunas],
            command=lambda _: self._refrescar_comparativa(),
            state="readonly", width=280,
        )
        self.combo_vacuna_comparativa.pack(side="left")
        self.combo_vacuna_comparativa.set(self.vacunas[0]["nombre"])

        self.marco_comparativa = ctk.CTkScrollableFrame(tab)
        self.marco_comparativa.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self._refrescar_comparativa()

    def _id_vacuna_por_nombre(self, nombre):
        for v in self.vacunas:
            if v["nombre"] == nombre:
                return v["id_vacuna"]
        return None

    def _refrescar_comparativa(self):
        for widget in self.marco_comparativa.winfo_children():
            widget.destroy()

        id_vacuna = self._id_vacuna_por_nombre(self.combo_vacuna_comparativa.get())
        if id_vacuna is None:
            return

        filas = obtener_stock_por_vacunatorio(id_vacuna)

        encabezado = ctk.CTkFrame(self.marco_comparativa, fg_color="transparent")
        encabezado.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(encabezado, text="Vacunatorio", font=ctk.CTkFont(weight="bold")).pack(
            side="left", padx=10
        )
        ctk.CTkLabel(encabezado, text="Stock disponible", font=ctk.CTkFont(weight="bold")).pack(
            side="right", padx=10
        )

        for f in filas:
            fila_widget = ctk.CTkFrame(self.marco_comparativa)
            fila_widget.pack(fill="x", pady=2)
            ctk.CTkLabel(fila_widget, text=f["nombre"]).pack(side="left", padx=10, pady=6)

            color = None
            if f["stock"] == 0:
                color = "#b3261e"  # sin stock: destacar en rojo
            ctk.CTkLabel(
                fila_widget, text=str(f["stock"]), text_color=color
            ).pack(side="right", padx=10, pady=6)

    # ------------------------------------------------------------------
    # Tab 2: detalle de ampollas de un vacunatorio
    # ------------------------------------------------------------------
    def _construir_tab_detalle(self, tab):
        fila = ctk.CTkFrame(tab, fg_color="transparent")
        fila.pack(fill="x", pady=(10, 15), padx=10)

        ctk.CTkLabel(fila, text="Vacunatorio:").pack(side="left", padx=(0, 10))
        self.combo_vacunatorio_detalle = ctk.CTkComboBox(
            fila, values=[v["nombre"] for v in self.vacunatorios],
            command=lambda _: self._refrescar_detalle(),
            state="readonly", width=280,
        )
        self.combo_vacunatorio_detalle.pack(side="left")
        self.combo_vacunatorio_detalle.set(self.vacunatorios[0]["nombre"])

        self.marco_detalle = ctk.CTkScrollableFrame(tab)
        self.marco_detalle.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self._refrescar_detalle()

    def _id_vacunatorio_por_nombre(self, nombre):
        for v in self.vacunatorios:
            if v["nombre"] == nombre:
                return v["id_vacunatorio"]
        return None

    def _refrescar_detalle(self):
        for widget in self.marco_detalle.winfo_children():
            widget.destroy()

        id_vacunatorio = self._id_vacunatorio_por_nombre(self.combo_vacunatorio_detalle.get())
        if id_vacunatorio is None:
            return

        ampollas = listar_ampollas_por_vacunatorio(id_vacunatorio)

        if not ampollas:
            ctk.CTkLabel(self.marco_detalle, text="No hay ampollas cargadas para este vacunatorio.").pack(pady=20)
            return

        colores_estado = {
            "Utilizable": "#0f6e56",
            "Vencida": "#993c1d",
            "Agotada": "gray50",
        }

        for a in ampollas:
            fila_widget = ctk.CTkFrame(self.marco_detalle)
            fila_widget.pack(fill="x", pady=3)

            texto = (
                f"{a['vacuna_nombre']}  ·  Lote {a['numero_lote']}  ·  "
                f"Vence {a['fecha_vencimiento']}  ·  {a['dosis_disponibles']} dosis"
            )
            ctk.CTkLabel(fila_widget, text=texto, anchor="w").pack(
                side="left", padx=10, pady=8, fill="x", expand=True
            )
            ctk.CTkLabel(
                fila_widget, text=a["estado"],
                text_color=colores_estado.get(a["estado"], None),
                font=ctk.CTkFont(weight="bold"),
            ).pack(side="right", padx=10)

    # ------------------------------------------------------------------
    # Tab 3: alta de nuevo stock (lote + ampollas)
    # ------------------------------------------------------------------
    def _construir_tab_alta(self, tab):
        ctk.CTkLabel(tab, text="Vacunatorio").pack(anchor="w", padx=15, pady=(15, 0))
        self.combo_vacunatorio_alta = ctk.CTkComboBox(
            tab, values=[v["nombre"] for v in self.vacunatorios], state="readonly"
        )
        self.combo_vacunatorio_alta.pack(fill="x", padx=15, pady=(0, 10))
        self.combo_vacunatorio_alta.set(self.vacunatorios[0]["nombre"])

        ctk.CTkLabel(tab, text="Vacuna").pack(anchor="w", padx=15)
        self.combo_vacuna_alta = ctk.CTkComboBox(
            tab, values=[v["nombre"] for v in self.vacunas], state="readonly"
        )
        self.combo_vacuna_alta.pack(fill="x", padx=15, pady=(0, 10))
        self.combo_vacuna_alta.set(self.vacunas[0]["nombre"])

        ctk.CTkLabel(tab, text="Número de lote").pack(anchor="w", padx=15)
        self.campo_numero_lote = ctk.CTkEntry(tab)
        self.campo_numero_lote.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(tab, text="Fecha de vencimiento (AAAA-MM-DD)").pack(anchor="w", padx=15)
        self.campo_fecha_vencimiento = ctk.CTkEntry(tab, placeholder_text="2027-01-31")
        self.campo_fecha_vencimiento.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(tab, text="Cantidad de ampollas recibidas").pack(anchor="w", padx=15)
        self.campo_cantidad_ampollas = ctk.CTkEntry(tab, placeholder_text="10")
        self.campo_cantidad_ampollas.pack(fill="x", padx=15, pady=(0, 10))

        self.etiqueta_error_alta = ctk.CTkLabel(tab, text="", text_color="red")
        self.etiqueta_error_alta.pack(anchor="w", padx=15)

        ctk.CTkButton(
            tab, text="Cargar stock", command=self._cargar_stock
        ).pack(anchor="w", padx=15, pady=15)

    def _cargar_stock(self):
        nombre_vacunatorio = self.combo_vacunatorio_alta.get()
        nombre_vacuna = self.combo_vacuna_alta.get()
        numero_lote = self.campo_numero_lote.get().strip()
        fecha_vencimiento = self.campo_fecha_vencimiento.get().strip()
        cantidad_texto = self.campo_cantidad_ampollas.get().strip()

        if not numero_lote or not fecha_vencimiento or not cantidad_texto:
            self.etiqueta_error_alta.configure(text="Completá todos los campos.")
            return

        try:
            datetime.strptime(fecha_vencimiento, "%Y-%m-%d")
        except ValueError:
            self.etiqueta_error_alta.configure(text="La fecha debe tener el formato AAAA-MM-DD.")
            return

        if not cantidad_texto.isdigit() or int(cantidad_texto) <= 0:
            self.etiqueta_error_alta.configure(text="La cantidad de ampollas debe ser un número mayor a 0.")
            return

        cantidad_ampollas = int(cantidad_texto)
        id_vacunatorio = self._id_vacunatorio_por_nombre(nombre_vacunatorio)
        vacuna = next(v for v in self.vacunas if v["nombre"] == nombre_vacuna)
        id_vacuna = vacuna["id_vacuna"]
        dosis_por_ampolla = vacuna["dosis_por_ampolla"]

        try:
            id_lote = crear_lote(
                numero_lote=numero_lote,
                fecha_vencimiento=fecha_vencimiento,
                cantidad_ampollas=cantidad_ampollas,
                id_vacuna=id_vacuna,
                id_vacunatorio=id_vacunatorio,
            )
            for _ in range(cantidad_ampollas):
                crear_ampolla(
                    id_lote=id_lote,
                    id_vacunatorio_actual=id_vacunatorio,
                    dosis_disponibles=dosis_por_ampolla,
                )
        except Exception as error:
            self.etiqueta_error_alta.configure(text=f"No se pudo cargar el stock: {error}")
            return

        self.etiqueta_error_alta.configure(
            text_color=("black", "white"),
            text=(
                f"Se cargaron {cantidad_ampollas} ampollas del lote {numero_lote} "
                f"({dosis_por_ampolla} dosis cada una)."
            ),
        )
        self.campo_numero_lote.delete(0, "end")
        self.campo_fecha_vencimiento.delete(0, "end")
        self.campo_cantidad_ampollas.delete(0, "end")

        # Refrescar las otras pestañas para que se vea el stock recién cargado
        self._refrescar_comparativa()
        self._refrescar_detalle()