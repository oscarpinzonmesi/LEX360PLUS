# SELECTA_SCAM/modulos/liquidadores/liquidadores_controller.py
import sys
import subprocess
import os

from PyQt5.QtWidgets import QMessageBox

# Assuming LiquidadoresDB already exists and is functional
# from SELECTA_SCAM.modulos.liquidadores.liquidadores_db import LiquidadoresDB

class LiquidadoresController:
    def __init__(self, db_connector, view):
        self.db = db_connector  # Instance of LiquidadoresDB
        self.view = view        # Instance of LiquidadoresWidget

    def load_tools(self):
        """Carga las herramientas de liquidación desde la DB y las pasa a la vista."""
        try:
            herramientas = self.db.obtener_herramientas_liquidacion()
            self.view.update_table(herramientas)
        except Exception as e:
            self.view.show_error("Error de Carga", f"No se pudieron cargar las herramientas: {e}")

    def add_tool(self, nombre, descripcion, ruta, area):
        """Agrega una nueva herramienta de liquidación a la DB."""
        try:
            self.db.agregar_herramienta_liquidacion(nombre, descripcion, ruta, area)
            self.view.show_info("Éxito", "Herramienta agregada correctamente.")
            self.view.clear_fields()
            self.load_tools() # Recargar la tabla
        except Exception as e:
            self.view.show_error("Error al Agregar", f"No se pudo agregar la herramienta: {e}")

    def edit_tool(self, tool_id, nombre, descripcion, ruta, area):
        """Actualiza una herramienta de liquidación existente en la DB."""
        try:
            self.db.actualizar_herramienta_liquidacion(tool_id, nombre, descripcion, ruta, area)
            self.view.show_info("Éxito", "Herramienta actualizada correctamente.")
            self.view.clear_fields()
            self.load_tools() # Recargar la tabla
        except Exception as e:
            self.view.show_error("Error al Editar", f"No se pudo actualizar la herramienta: {e}")

    def delete_tool(self, tool_id):
        """Elimina una herramienta de liquidación de la DB."""
        reply = self.view.show_question("Confirmar Eliminación",
                                        "¿Está seguro de que desea eliminar esta herramienta de liquidación?",
                                        QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                self.db.eliminar_herramienta_liquidacion(tool_id)
                self.view.show_info("Éxito", "Herramienta eliminada correctamente.")
                self.view.clear_fields()
                self.load_tools() # Recargar la tabla
            except Exception as e:
                self.view.show_error("Error al Eliminar", f"No se pudo eliminar la herramienta: {e}")

    def execute_tool(self, ruta_ejecutable):
        """Ejecuta la herramienta externa especificada por su ruta."""
        if not ruta_ejecutable:
            self.view.show_warning("Ruta no válida", "La ruta ejecutable para esta herramienta está vacía.")
            return

        script_path = ruta_ejecutable

        try:
            if script_path.lower().endswith('.py'):
                # Asegúrate de que 'sys.executable' apunte al intérprete de Python de tu entorno virtual
                subprocess.Popen([sys.executable, script_path])
                self.view.show_info("Ejecución", f"Intentando ejecutar script Python: {script_path}")
            else:
                # Para ejecutar un ejecutable directamente (ej. .exe o un comando de consola)
                # Usar shell=True con precaución. Es necesario si el comando no es un ejecutable directo
                # sino un comando de shell (ej. 'start my_app.exe' en Windows) o si hay espacios en la ruta
                # y no se manejan con comillas adecuadamente en la lista de comandos.
                # Para la mayoría de ejecutables directos, subprocess.Popen([script_path]) debería funcionar sin shell=True.
                subprocess.Popen([script_path], shell=True)
                self.view.show_info("Ejecución", f"Intentando ejecutar: {script_path}")

        except FileNotFoundError:
            self.view.show_error("Error de Ejecución", f"Archivo o programa no encontrado en la ruta: {script_path}")
        except Exception as e:
            self.view.show_error("Error de Ejecución", f"Ocurrió un error al intentar ejecutar la herramienta: {e}")