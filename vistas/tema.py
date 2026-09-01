"""
Tema visual compartido por las vistas del Sistema de Vacunación.

Centraliza colores y radios para que todos los módulos usen la misma
paleta que el tema por defecto de CustomTkinter, configurado en
main.py con ctk.set_default_color_theme("green").
"""

# Radios de esquina (iguales a los que usa CustomTkinter por defecto)
RADIO = 6
RADIO_NULO = 0

# Verde principal (igual al fg_color / hover_color de CTkButton en el tema "green")
PRINCIPAL = "#2CC985"
HOVER = "#0C955A"

# Variantes para cabeceras, fondos suaves y pestañas sin seleccionar
OSCURO = "#0B6E3D"   # cabeceras de sección y títulos
CLARO = "#DCF6E9"    # fondos suaves (recuadros informativos, pestañas sin seleccionar)
SUAVE = "#EFFBF5"    # hover claro para botones secundarios

# Bordes, fondos de panel y filas alternadas (iguales a CTkFrame por defecto)
BORDE = "#979DA2"
FONDO_PANEL = "gray86"
FILA_ALT = "gray81"

# Texto
TEXTO = "gray10"
TEXTO_SUAVE = "gray40"

# Estados de mensajes
OK = "#0C955A"
ERROR = "#C0392B"
