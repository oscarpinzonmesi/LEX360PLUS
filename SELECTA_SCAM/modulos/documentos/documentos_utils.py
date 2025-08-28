# C:\Users\oscar\OneDrive\Desktop\LEX360PLUS\SELECTA_SCAM\modulos\documentos\documentos_utils.py

import os
import sys
import shutil
import subprocess
import sqlite3
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMessageBox
# Modifica esta línea para importar RUTA_CLARO_DRIVE y DATABASE_PATH
from SELECTA_SCAM.config.settings import RUTA_CLARO_DRIVE, DATABASE_PATH

# ELIMINA la siguiente línea, ya no es necesaria aquí:
# DATABASE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "base_datos.db")

# ... el resto de tu código
def abrir_archivo(path, parent=None):
    """Abre un archivo con la aplicación predeterminada del sistema."""
    if not isinstance(path, (str, bytes, os.PathLike)):
        if parent:
            QMessageBox.warning(parent, "Ruta inválida", "La ruta del archivo no es válida.")
        return

    if os.path.exists(path):
        try:
            if os.name == 'nt':
                os.startfile(path)
            elif sys.platform == 'darwin':
                subprocess.call(('open', path))
            else:
                subprocess.call(('xdg-open', path))
        except Exception as e:
            if parent:
                QMessageBox.warning(parent, "Error", f"No se pudo abrir el archivo:\n{e}")
    else:
        if parent:
            QMessageBox.warning(parent, "Error", "El archivo no existe o fue movido.")

def color_por_extension(ext):
    """Devuelve un QColor según la extensión de archivo."""
    colores = {
        '.pdf': QColor("red"),
        '.docx': QColor("blue"),
        '.doc': QColor("blue"),
        '.xlsx': QColor("green"),
        '.xls': QColor("green"),
        '.png': QColor("darkMagenta"),
        '.jpg': QColor("darkMagenta"),
        '.jpeg': QColor("darkMagenta"),
        '.txt': QColor("gray"),
        '.zip': QColor("darkCyan"),
        '.rar': QColor("darkCyan")
    }
    return colores.get(ext.lower(), QColor("black"))

def cargar_datos_iniciales():
    """
    Carga los datos iniciales: clientes y procesos.
    Retorna:
        tuple: (clientes, procesos)
            clientes: list of (id, nombre)
            procesos:  list of (id, radicado, tipo, cliente_id)
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Cargar clientes activos
    cursor.execute("SELECT id, nombre FROM clientes")
    clientes = cursor.fetchall()

    # Cargar todos los procesos (sin filtro 'eliminado')
    cursor.execute("SELECT id, radicado, tipo, cliente_id FROM procesos")
    procesos = cursor.fetchall()

    conn.close()
    return clientes, procesos


def filtrar_procesos_por_cliente(procesos, cliente_id):
    """
    Filtra una lista de procesos para devolver solo aquellos
    que pertenecen al cliente indicado.
    Args:
        procesos (list): Lista de tuplas (id, radicado, cliente_id)
        cliente_id (int): ID del cliente
    Retorna:
        list: Procesos filtrados para ese cliente
    """
    return [p for p in procesos if p[3] == cliente_id]




def copiar_archivo_a_destino(ruta_origen, nombre_destino):
    """
    Copia el archivo desde la ruta de origen a la carpeta fija,
    evitando duplicar la extensión si ya la incluye.
    """
    carpeta_destino = r"C:/Users/oscar/Claro drive2/LEX360"
    # Obtener extensión real del origen (incluye el punto), p.ej. ".docx"
    ext = os.path.splitext(ruta_origen)[1].lower()

    # Si el nombre_destino ya termina con esa extensión, no la volvemos a agregar
    if nombre_destino.lower().endswith(ext):
        archivo_final = nombre_destino
    else:
        archivo_final = f"{nombre_destino}{ext}"

    ruta_destino = os.path.join(carpeta_destino, archivo_final)

    # Verificar si ya existe
    if os.path.exists(ruta_destino):
        raise FileExistsError(f"El archivo {ruta_destino} ya existe.")

    # Copiar
    shutil.copy2(ruta_origen, ruta_destino)
    return ruta_destino

