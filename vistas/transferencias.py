"""
Vista del Módulo de Transferencias entre Vacunatorios.
Permite emitir remitos de envío seleccionando vacunatorio de origen y destino,
y consultar el detalle de transferencias realizadas.
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

        id_vac = None
        if self.usuario_logueado:
            try:
                id_vac = self.usuario_logueado["id_vacunatorio"]
            except (KeyError, IndexError, TypeError):
                id_vac = None

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
        self.geometry("620x650")
        self.resizable(False, False)

        self.vacunatorios = listar_vacunatorios()
        self.checkboxes_ampollas = []

        self._construir_formulario()

    def _obtener_siguiente_numero_remito(self):
        conexion = obtener_conexion()
        cursor = conexion.cursor()

        cursor.execute("SELECT COUNT(*) AS total FROM TRANSFERENCIA")
        resultado = cursor.fetchone()
        conexion.close()

        total_remitos = resultado["total"] if resultado else 0
        siguiente_numero = total_remitos + 1

        return f"REM-{siguiente_numero:08d}"

    def _construir_formulario(self):
        nro_remito_sugerido = self._obtener_siguiente_numero_remito()

        frame_top = ctk.CTkFrame(self, fg_color="transparent")
        frame_top.pack(fill="x", padx=20, pady=(15, 5))

        # Número de remito
        lbl_remito = ctk.CTkLabel(frame_top, text="N° Remito:")
        lbl_remito.grid(row=0, column=0, sticky="w", pady=2)
        self.txt_remito = ctk.CTkEntry(frame_top, width=150)
        self.txt_remito.insert(0, nro_remito_sugerido)
        self.txt_remito.grid(row=0, column=1, sticky="w", padx=(5, 20), pady=2)

        # Vacunatorio Origen
        lbl_origen = ctk.CTkLabel(frame_top, text="Origen:")
        lbl_origen.grid(row=1, column=0, sticky="w", pady=5)

        nombres_vac = [v["nombre"] for v in self.vacunatorios]
        
        id_usr_vac = None
        if self.usuario_logueado:
            try:
                id_usr_vac = self.usuario_logueado["id_vacunatorio"]
            except (KeyError, IndexError, TypeError):
                id_usr_vac = None

        vac_usr = next((v["nombre"] for v in self.vacunatorios if v["id_vacunatorio"] == id_usr_vac), None)
        origen_defecto = vac_usr if vac_usr else (nombres_vac[0] if nombres_vac else "")

        self.combo_origen = ctk.CTkComboBox(
            frame_top, 
            values=nombres_vac or ["Sin vacunatorios"],
            width=230,
            command=self._al_cambiar_origen
        )
        if origen_defecto:
            self.combo_origen.set(origen_defecto)
        self.combo_origen.grid(row=1, column=1, sticky="w", padx=(5, 20), pady=5)

        # Vacunatorio Destino
        lbl_destino = ctk.CTkLabel(frame_top, text="Destino:")
        lbl_destino.grid(row=1, column=2, sticky="w", pady=5)

        self.combo_destino = ctk.CTkComboBox(frame_top, values=[], width=230)
        self.combo_destino.grid(row=1, column=3, sticky="w", pady=5)

        # Sección de ampollas / stock
        lbl_ampollas = ctk.CTkLabel(
            self, 
            text="Ampollas y Dosis Disponibles en Origen:",
            font=ctk.CTkFont(weight="bold")
        )
        lbl_ampollas.pack(anchor="w", padx=20, pady=(10, 2))

        self.frame_lista = ctk.CTkFrame(self)
        self.frame_lista.pack(fill="both", expand=True, padx=20, pady=5)

        self._actualizar_opciones_destino()
        self._actualizar_lista_ampollas()

        # Observaciones
        lbl_obs = ctk.CTkLabel(self, text="Observaciones:")
        lbl_obs.pack(anchor="w", padx=20, pady=(10, 2))
        self.txt_obs = ctk.CTkEntry(self, placeholder_text="Opcional: Motivo del traslado, responsable de transporte, etc.")
        self.txt_obs.pack(fill="x", padx=20)

        # Botón Guardar
        btn_guardar = ctk.CTkButton(
            self, text="Emitir Remito y Transferir Stock", command=self._guardar
        )
        btn_guardar.pack(pady=15, padx=20, fill="x")

    def _al_cambiar_origen(self, choice):
        self._actualizar_opciones_destino()
        self._actualizar_lista_ampollas()

    def _actualizar_opciones_destino(self):
        origen_sel = self.combo_origen.get()
        opciones_dest = [v["nombre"] for v in self.vacunatorios if v["nombre"] != origen_sel]
        self.combo_destino.configure(values=opciones_dest or ["Sin otros vacunatorios"])
        if opciones_dest:
            self.combo_destino.set(opciones_dest[0])

    def _actualizar_lista_ampollas(self):
        for widget in self.frame_lista.winfo_children():
            widget.destroy()

        origen_sel = self.combo_origen.get()
        vac_origen = next((v for v in self.vacunatorios if v["nombre"] == origen_sel), None)

        if not vac_origen:
            return

        ampollas = obtener_stock_por_vacunatorio(id_vacunatorio=vac_origen["id_vacunatorio"])
        self.checkboxes_ampollas = []

        scroll_ampollas = ctk.CTkScrollableFrame(self.frame_lista, height=200)
        scroll_ampollas.pack(fill="both", expand=True, padx=5, pady=5)

        if not ampollas:
            ctk.CTkLabel(
                scroll_ampollas, 
                text=f"No hay ampollas disponibles en '{origen_sel}'."
            ).pack(pady=15)
        else:
            for amp in ampollas:
                var = ctk.BooleanVar()
                
                # Manejo seguro de llaves para evitar KeyError
                nombre_vac = "Vacuna"
                try:
                    nombre_vac = amp["vacuna"]
                except (KeyError, IndexError, TypeError):
                    try:
                        nombre_vac = amp["vacuna_nombre"]
                    except (KeyError, IndexError, TypeError):
                        pass

                texto_amp = (
                    f"Ampolla #{amp['id_ampolla']} | Vacuna: {nombre_vac} "
                    f"| Lote: {amp['numero_lote']} | Dosis disponibles: {amp['dosis_disponibles']}"
                )
                chk = ctk.CTkCheckBox(scroll_ampollas, text=texto_amp, variable=var)
                chk.pack(anchor="w", pady=5, padx=5)
                self.checkboxes_ampollas.append((amp['id_ampolla'], var))

    def _guardar(self):
        from datetime import datetime

        num_remito = self.txt_remito.get().strip()
        origen_nombre = self.combo_origen.get()
        destino_nombre = self.combo_destino.get()
        obs = self.txt_obs.get().strip()

        if not num_remito:
            messagebox.showwarning("Atención", "Ingresá un número de remito.")
            return

        vac_origen = next((v for v in self.vacunatorios if v["nombre"] == origen_nombre), None)
        vac_destino = next((v for v in self.vacunatorios if v["nombre"] == destino_nombre), None)

        if not vac_origen or not vac_destino:
            messagebox.showwarning("Atención", "Seleccioná vacunatorios de origen y destino válidos.")
            return

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
                id_vacunatorio_origen=vac_origen["id_vacunatorio"],
                id_vacunatorio_destino=vac_destino["id_vacunatorio"],
                id_usuario=self.usuario_logueado["id_usuario"],
                lista_ampollas_con_cantidad=ampollas_a_enviar,
                observaciones=obs,
            )

            messagebox.showinfo(
                "Éxito", 
                f"Remito {num_remito} emitido correctamente.\n"
                f"Origen: {origen_nombre} -> Destino: {destino_nombre}"
            )
            self.parent_vista.cargar_transferencias()
            self.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo registrar la transferencia:\n{str(e)}")


# --- ALIAS DE COMPATIBILIDAD ---
FrameTransferencias = VistaTransferencias
FrameTransferencia = VistaTransferencias