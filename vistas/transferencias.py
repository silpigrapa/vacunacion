"""
Vista del Módulo de Transferencias entre Vacunatorios.
Permite emitir remitos de envío y consultar el detalle de transferencias realizadas.
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
from database.conexion import obtener_conexion
from modelos.transferencia import (
    listar_transferencias,
    obtener_detalle_transferencia,
    registrar_transferencia,
)
from modelos.vacunatorio import listar_vacunatorios
from modelos.stock import obtener_stock_por_vacunatorio


class VistaTransferencias(ctk.CTkFrame):
    def __init__(self, parent, usuario_logueado):
        super().__init__(parent)

        self.usuario_logueado = usuario_logueado

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._construir_interfaz()
        self.cargar_transferencias()

    def _construir_interfaz(self):
        # 1. Cabecera con botón de acción
        frame_cabecera = ctk.CTkFrame(self, fg_color="transparent")
        frame_cabecera.grid(row=0, column=0, padx=15, pady=10, sticky="ew")

        ctk.CTkLabel(
            frame_cabecera,
            text="Gestión de Remitos y Transferencias",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(side="left")

        btn_nueva = ctk.CTkButton(
            frame_cabecera,
            text="+ Nueva Transferencia (Emitir Remito)",
            command=self._abrir_modal_nueva_transferencia
        )
        btn_nueva.pack(side="right")

        # 2. Tabla Principal: Cabeceras de Remito
        frame_tabla_remitos = ctk.CTkFrame(self)
        frame_tabla_remitos.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="nsew")
        frame_tabla_remitos.grid_columnconfigure(0, weight=1)
        frame_tabla_remitos.grid_rowconfigure(0, weight=1)

        cols_remito = ("id", "remito", "fecha", "origen", "destino", "usuario", "obs")
        self.tabla_remitos = ttk.Treeview(
            frame_tabla_remitos, columns=cols_remito, show="headings", selectmode="browse"
        )

        self.tabla_remitos.heading("id", text="ID")
        self.tabla_remitos.heading("remito", text="N° Remito")
        self.tabla_remitos.heading("fecha", text="Fecha")
        self.tabla_remitos.heading("origen", text="Origen")
        self.tabla_remitos.heading("destino", text="Destino")
        self.tabla_remitos.heading("usuario", text="Emisor")
        self.tabla_remitos.heading("obs", text="Observaciones")

        self.tabla_remitos.column("id", width=50, anchor="center")
        self.tabla_remitos.column("remito", width=120, anchor="center")
        self.tabla_remitos.column("fecha", width=130, anchor="center")
        self.tabla_remitos.column("origen", width=160, anchor="w")
        self.tabla_remitos.column("destino", width=160, anchor="w")
        self.tabla_remitos.column("usuario", width=140, anchor="w")
        self.tabla_remitos.column("obs", width=200, anchor="w")

        scroll_remitos = ttk.Scrollbar(frame_tabla_remitos, orient="vertical", command=self.tabla_remitos.yview)
        self.tabla_remitos.configure(yscrollcommand=scroll_remitos.set)

        self.tabla_remitos.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)
        scroll_remitos.grid(row=0, column=1, sticky="ns", padx=(0, 10), pady=10)

        # Evento de selección de un remito
        self.tabla_remitos.bind("<<TreeviewSelect>>", self._al_seleccionar_transferencia)

        # 3. Tabla Secundaria: Detalle de Ampollas de la Transferencia
        frame_tabla_detalle = ctk.CTkFrame(self)
        frame_tabla_detalle.grid(row=2, column=0, padx=15, pady=(0, 15), sticky="nsew")
        frame_tabla_detalle.grid_columnconfigure(0, weight=1)
        frame_tabla_detalle.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            frame_tabla_detalle,
            text="Detalle de Ampollas Incluidas en el Remito Seleccionado:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=10, pady=(5, 0))

        cols_det = ("id_ampolla", "vacuna", "lote", "vencimiento", "cantidad", "dosis", "estado")
        self.tabla_detalle = ttk.Treeview(
            frame_tabla_detalle, columns=cols_det, show="headings", selectmode="browse"
        )

        self.tabla_detalle.heading("id_ampolla", text="ID Ampolla")
        self.tabla_detalle.heading("vacuna", text="Vacuna")
        self.tabla_detalle.heading("lote", text="N° Lote")
        self.tabla_detalle.heading("vencimiento", text="Vencimiento")
        self.tabla_detalle.heading("cantidad", text="Cantidad")
        self.tabla_detalle.heading("dosis", text="Dosis Disp.")
        self.tabla_detalle.heading("estado", text="Estado")

        self.tabla_detalle.column("id_ampolla", width=90, anchor="center")
        self.tabla_detalle.column("vacuna", width=200, anchor="w")
        self.tabla_detalle.column("lote", width=120, anchor="center")
        self.tabla_detalle.column("vencimiento", width=120, anchor="center")
        self.tabla_detalle.column("cantidad", width=90, anchor="center")
        self.tabla_detalle.column("dosis", width=90, anchor="center")
        self.tabla_detalle.column("estado", width=100, anchor="center")

        scroll_det = ttk.Scrollbar(frame_tabla_detalle, orient="vertical", command=self.tabla_detalle.yview)
        self.tabla_detalle.configure(yscrollcommand=scroll_det.set)

        self.tabla_detalle.grid(row=1, column=0, sticky="nsew", padx=(10, 0), pady=5)
        scroll_det.grid(row=1, column=1, sticky="ns", padx=(0, 10), pady=5)

    def cargar_transferencias(self):
        for item in self.tabla_remitos.get_children():
            self.tabla_remitos.delete(item)

        id_vac = self.usuario_logueado["id_vacunatorio"]
        transferencias = listar_transferencias(id_vacunatorio=id_vac)

        for t in transferencias:
            self.tabla_remitos.insert(
                "",
                "end",
                values=(
                    t["id_transferencia"],
                    t["numero_remito"],
                    t["fecha"],
                    t["origen"],
                    t["destino"],
                    t["usuario"],
                    t["observaciones"] or "-",
                )
            )

    def _al_seleccionar_transferencia(self, event):
        for item in self.tabla_detalle.get_children():
            self.tabla_detalle.delete(item)

        seleccion = self.tabla_remitos.selection()
        if not seleccion:
            return

        item = self.tabla_remitos.item(seleccion[0])
        id_transferencia = item["values"][0]

        detalles = obtener_detalle_transferencia(id_transferencia)
        for d in detalles:
            estado_ampolla = "Abierta" if d["fecha_apertura"] else "Cerrada"
            self.tabla_detalle.insert(
                "",
                "end",
                values=(
                    d["id_ampolla"],
                    d["vacuna_nombre"],
                    d["numero_lote"],
                    d["fecha_vencimiento"],
                    d["cantidad"],
                    d["dosis_disponibles"],
                    estado_ampolla,
                )
            )

    def _abrir_modal_nueva_transferencia(self):
        modal = VentanaNuevaTransferencia(self, self.usuario_logueado)
        modal.grab_set()


class VentanaNuevaTransferencia(ctk.CTkToplevel):
    def __init__(self, parent_vista, usuario_logueado):
        super().__init__(parent_vista)

        self.parent_vista = parent_vista
        self.usuario_logueado = usuario_logueado

        self.title("Emitir Nuevo Remito de Transferencia")
        self.geometry("550x580")
        self.resizable(False, False)

        self._construir_formulario()

    def _obtener_siguiente_numero_remito(self):
        """
        Consulta en la base de datos la cantidad de transferencias
        existentes para asignar el número correlativo de 8 dígitos arrancando en 00000001.
        """
        conexion = obtener_conexion()
        cursor = conexion.cursor()

        cursor.execute("SELECT COUNT(*) AS total FROM TRANSFERENCIA")
        resultado = cursor.fetchone()
        conexion.close()

        total_remitos = resultado["total"] if resultado else 0
        siguiente_numero = total_remitos + 1

        # Formato de 8 dígitos correlativo (ej: REM-00000001)
        return f"REM-{siguiente_numero:08d}"

    def _obtener_ampollas_origen(self):
        id_vac_origen = self.usuario_logueado["id_vacunatorio"]
        return obtener_stock_por_vacunatorio(id_vacunatorio=id_vac_origen)

    def _construir_formulario(self):
        # Número de remito sugerido (8 dígitos)
        nro_remito_sugerido = self._obtener_siguiente_numero_remito()

        lbl_remito = ctk.CTkLabel(self, text="Número de Remito:")
        lbl_remito.pack(anchor="w", padx=20, pady=(15, 2))
        self.txt_remito = ctk.CTkEntry(self)
        self.txt_remito.insert(0, nro_remito_sugerido)
        self.txt_remito.pack(fill="x", padx=20)

        # Destino
        lbl_destino = ctk.CTkLabel(self, text="Vacunatorio Destino:")
        lbl_destino.pack(anchor="w", padx=20, pady=(10, 2))

        self.vacunatorios = listar_vacunatorios()
        opciones_dest = [
            v["nombre"] for v in self.vacunatorios 
            if v["id_vacunatorio"] != self.usuario_logueado["id_vacunatorio"]
        ]

        self.combo_destino = ctk.CTkComboBox(self, values=opciones_dest or ["No hay otros vacunatorios"])
        self.combo_destino.pack(fill="x", padx=20)

        # Selección de ampollas
        lbl_ampollas = ctk.CTkLabel(self, text="Ampollas a Transferir (Disponibles en el centro actual):")
        lbl_ampollas.pack(anchor="w", padx=20, pady=(10, 2))

        frame_lista = ctk.CTkFrame(self)
        frame_lista.pack(fill="both", expand=True, padx=20, pady=5)

        self.ampollas_disponibles = self._obtener_ampollas_origen()
        self.checkboxes_ampollas = []

        scroll_ampollas = ctk.CTkScrollableFrame(frame_lista, height=150)
        scroll_ampollas.pack(fill="both", expand=True, padx=5, pady=5)

        if not self.ampollas_disponibles:
            ctk.CTkLabel(scroll_ampollas, text="No hay ampollas disponibles en este vacunatorio.").pack(pady=10)
        else:
            for amp in self.ampollas_disponibles:
                var = ctk.BooleanVar()
                # Se lee 'vacuna' de forma segura según el modelo de stock
                nombre_vac = amp.get('vacuna') or amp.get('vacuna_nombre') or 'Vacuna'
                texto_amp = (
                    f"Ampolla #{amp['id_ampolla']} | {nombre_vac} "
                    f"| Lote: {amp['numero_lote']} | Dosis: {amp['dosis_disponibles']}"
                )
                chk = ctk.CTkCheckBox(scroll_ampollas, text=texto_amp, variable=var)
                chk.pack(anchor="w", pady=4, padx=5)
                self.checkboxes_ampollas.append((amp['id_ampolla'], var))

        # Observaciones
        lbl_obs = ctk.CTkLabel(self, text="Observaciones:")
        lbl_obs.pack(anchor="w", padx=20, pady=(10, 2))
        self.txt_obs = ctk.CTkEntry(self, placeholder_text="Opcional: Motivo del traslado, transporte, etc.")
        self.txt_obs.pack(fill="x", padx=20)

        # Botón Guardar
        btn_guardar = ctk.CTkButton(
            self, text="Emitir Remito y Transferir", command=self._guardar
        )
        btn_guardar.pack(pady=15, padx=20, fill="x")

    def _guardar(self):
        from datetime import datetime

        num_remito = self.txt_remito.get().strip()
        nombre_destino = self.combo_destino.get()
        obs = self.txt_obs.get().strip()

        if not num_remito:
            messagebox.showwarning("Atención", "Ingresá un número de remito.")
            return

        vac_destino = next((v for v in self.vacunatorios if v["nombre"] == nombre_destino), None)
        if not vac_destino:
            messagebox.showwarning("Atención", "Seleccioná un vacunatorio de destino válido.")
            return

        # Seleccionar ampollas marcadas con cantidad por defecto = 1
        ampollas_a_enviar = [
            (id_amp, 1) for id_amp, var in self.checkboxes_ampollas if var.get()
        ]

        if not ampollas_a_enviar:
            messagebox.showwarning("Atención", "Marcá al menos una ampolla para transferir.")
            return

        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            registrar_transferencia(
                numero_remito=num_remito,
                fecha=fecha_actual,
                id_vacunatorio_origen=self.usuario_logueado["id_vacunatorio"],
                id_vacunatorio_destino=vac_destino["id_vacunatorio"],
                id_usuario=self.usuario_logueado["id_usuario"],
                lista_ampollas_con_cantidad=ampollas_a_enviar,
                observaciones=obs,
            )

            messagebox.showinfo("Éxito", f"Remito {num_remito} emitido correctamente.")
            self.parent_vista.cargar_transferencias()
            self.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo registrar la transferencia:\n{str(e)}")