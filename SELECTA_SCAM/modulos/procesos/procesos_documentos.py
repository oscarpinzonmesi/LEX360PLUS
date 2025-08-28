from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QPushButton, QFileDialog, QMessageBox,
    QComboBox, QFormLayout, QLabel, QHBoxLayout
)
from PyQt5.QtCore import Qt # Necesario para Qt.UserRole
import os
import shutil
from datetime import datetime # Para la fecha actual al subir un documento

# --- IMPORTACIÓN DEL MODELO NECESARIO ---
from SELECTA_SCAM.modulos.procesos.procesos_model import ProcesosModel

# Importar el modelo Proceso para el tipado, si lo necesitas para el cliente_id
from SELECTA_SCAM.db.models import Proceso # Añadido para obtener cliente_id


class DocumentosTab(QWidget):
    # --- CAMBIO IMPORTANTE AQUÍ: El constructor ahora espera la instancia de ProcesosModel ---
    def __init__(self, procesos_model_instance: ProcesosModel, parent=None):
        super().__init__(parent)
        self.parent_widget = parent # Almacenamos la referencia al ProcesosWidget padre
        self.procesos_model = procesos_model_instance # Almacenamos la instancia de ProcesosModel

        self.proceso_id = None # Para almacenar el ID del proceso actualmente seleccionado
        self.cliente_id_actual = None # Para almacenar el ID del cliente del proceso actual

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Lista de documentos
        self.document_list = QListWidget()
        self.document_list.itemDoubleClicked.connect(self.abrir_documento) # Doble clic para abrir
        layout.addWidget(QLabel("Documentos del proceso:"))
        layout.addWidget(self.document_list)

        # Formulario de categoría y tipo
        form_layout = QFormLayout()

        self.combo_categoria = QComboBox()
        # Ahora obtenemos los tipos de actuación del modelo
        self._tipos_actuacion_data = self.procesos_model.obtener_actuaciones_por_categoria()
        self.combo_categoria.addItems(self._tipos_actuacion_data.keys())
        self.combo_categoria.currentTextChanged.connect(self.actualizar_tipos_actuacion)

        self.combo_tipo = QComboBox()
        self.actualizar_tipos_actuacion(self.combo_categoria.currentText())

        form_layout.addRow("Categoría:", self.combo_categoria)
        form_layout.addRow("Tipo de actuación:", self.combo_tipo)

        layout.addLayout(form_layout)

        # Botones de acción (Subir, Abrir, Eliminar)
        buttons_layout = QHBoxLayout()

        self.upload_button = QPushButton("Subir documento")
        self.upload_button.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border-radius: 10px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        self.upload_button.clicked.connect(self.subir_documento)
        buttons_layout.addWidget(self.upload_button)

        self.open_button = QPushButton("Abrir documento")
        self.open_button.clicked.connect(self.abrir_documento)
        buttons_layout.addWidget(self.open_button)

        self.delete_button = QPushButton("Eliminar documento")
        self.delete_button.clicked.connect(self.eliminar_documento)
        buttons_layout.addWidget(self.delete_button)

        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    def actualizar_tipos_actuacion(self, categoria: str):
        """
        Actualiza el QComboBox de tipos de actuación basándose en la categoría seleccionada,
        obteniendo los datos del modelo.
        """
        self.combo_tipo.clear()
        if categoria in self._tipos_actuacion_data:
            self.combo_tipo.addItems(self._tipos_actuacion_data[categoria])

    def set_proceso_id(self, proceso_id: int):
        """
        Establece el ID del proceso actual y carga sus documentos.
        También obtiene el cliente_id asociado para operaciones de documentos.
        """
        self.proceso_id = proceso_id
        self.cliente_id_actual = None # Reiniciar cliente_id

        if self.proceso_id is not None:
            # Obtener el cliente_id del proceso seleccionado
            proceso_data = self.procesos_model.get_proceso_by_id(self.proceso_id)
            if proceso_data:
                self.cliente_id_actual = proceso_data.get('cliente_id')
            else:
                QMessageBox.warning(self, "Error", "No se encontró el proceso seleccionado.")
                self.proceso_id = None # Limpiar ID si no se encuentra
                self.cliente_id_actual = None

        self.load_documents_for_proceso() # Llama a la carga de documentos cuando se establece el ID

    def load_documents_for_proceso(self):
        """
        Carga y muestra los documentos para el proceso actualmente seleccionado.
        """
        self.document_list.clear()
        if self.proceso_id is not None:
            try:
                # El método ahora devuelve una lista de diccionarios
                documentos = self.procesos_model.obtener_documentos_por_proceso(self.proceso_id)
                for doc in documentos:
                    item = QListWidgetItem(doc['nombre']) # Muestra el nombre del documento
                    # Guardamos el ID del documento y la ruta completa en el item para futuras operaciones
                    item.setData(Qt.UserRole, doc['id'])
                    item.setData(Qt.UserRole + 1, doc['ruta'])
                    self.document_list.addItem(item)
            except Exception as e:
                QMessageBox.critical(self, "Error al Cargar Documentos", f"No se pudieron cargar los documentos: {e}")
        else:
            # Puedes mostrar un mensaje o dejar la lista vacía si no hay proceso seleccionado
            pass

    def subir_documento(self):
        """
        Permite al usuario seleccionar un archivo, lo copia al directorio 'documentos',
        y registra su información en la base de datos.
        """
        if self.proceso_id is None:
            QMessageBox.warning(self, "Advertencia", "No se ha seleccionado ningún proceso.")
            return
        if self.cliente_id_actual is None:
            QMessageBox.warning(self, "Advertencia", "No se pudo obtener el ID del cliente para el proceso seleccionado.")
            return

        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Seleccionar documento")
        if file_path:
            nombre_archivo = os.path.basename(file_path)
            
            # Directorio de guardado: Asegúrate de que esta ruta sea relativa a la raíz del proyecto
            # o una ruta absoluta configurada.
            documentos_dir = os.path.join(os.getcwd(), "documentos_guardados") # Una buena práctica es tener un directorio específico
            if not os.path.exists(documentos_dir):
                os.makedirs(documentos_dir)
            
            destino = os.path.join(documentos_dir, nombre_archivo)

            try:
                # Copiar el archivo al directorio de destino
                shutil.copy(file_path, destino)

                categoria_seleccionada = self.combo_categoria.currentText()
                tipo_actuacion_seleccionado = self.combo_tipo.currentText()
                # Combinamos categoria y tipo_actuacion en un solo campo 'tipo_documento'
                tipo_documento_para_db = f"{categoria_seleccionada}: {tipo_actuacion_seleccionado}" if categoria_seleccionada and tipo_actuacion_seleccionado else "Sin Categoría/Tipo"

                # Llama al método del modelo con los parámetros correctos
                documento_id = self.procesos_model.insertar_documento(
                    proceso_id=self.proceso_id,
                    cliente_id=self.cliente_id_actual, # Ahora pasamos el cliente_id
                    nombre=nombre_archivo,
                    archivo=nombre_archivo, # Asumo que 'archivo' también guarda el nombre de archivo
                    ruta=destino,
                    tipo_documento=tipo_documento_para_db
                )

                if documento_id:
                    self.load_documents_for_proceso() # Recarga la lista de documentos después de subir uno
                    QMessageBox.information(self, "Éxito", f"Documento '{nombre_archivo}' subido correctamente con ID: {documento_id}.")
                else:
                    QMessageBox.critical(self, "Error", "No se pudo registrar el documento en la base de datos.")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo subir o registrar el documento: {e}")

    def eliminar_documento(self):
        """
        Elimina el documento seleccionado de la base de datos y del sistema de archivos.
        """
        selected_item = self.document_list.currentItem()
        if selected_item:
            document_id = selected_item.data(Qt.UserRole)
            document_ruta = selected_item.data(Qt.UserRole + 1)
            document_nombre = selected_item.text()

            if not document_id:
                QMessageBox.warning(self, "Advertencia", "No se pudo obtener el ID del documento seleccionado.")
                return

            reply = QMessageBox.question(self, 'Eliminar Documento',
                                         f"¿Está seguro de que desea eliminar '{document_nombre}'?\n\n¡Esto también eliminará el archivo del disco!",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                try:
                    # Eliminar de la base de datos
                    eliminado_db = self.procesos_model.eliminar_documento(documento_id)

                    if eliminado_db:
                        # Eliminar el archivo físico si existe
                        if document_ruta and os.path.exists(document_ruta):
                            os.remove(document_ruta)
                            QMessageBox.information(self, "Éxito", f"Documento '{document_nombre}' eliminado del sistema de archivos y base de datos.")
                        else:
                            QMessageBox.warning(self, "Información", f"Documento '{document_nombre}' eliminado de la base de datos, pero el archivo físico no se encontró o la ruta estaba vacía.")
                        self.load_documents_for_proceso() # Recargar la lista
                    else:
                        QMessageBox.critical(self, "Error", f"No se pudo eliminar el documento '{document_nombre}' de la base de datos.")

                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Error al eliminar el documento: {e}")
        else:
            QMessageBox.warning(self, "Advertencia", "Seleccione un documento para eliminar.")

    def abrir_documento(self):
        """
        Abre el archivo del documento seleccionado en su aplicación predeterminada.
        """
        selected_item = self.document_list.currentItem()
        if selected_item:
            document_ruta = selected_item.data(Qt.UserRole + 1)
            if document_ruta and os.path.exists(document_ruta):
                try:
                    # Plataforma-agnóstico para abrir archivos
                    if os.name == 'nt': # Windows
                        os.startfile(document_ruta)
                    elif os.name == 'posix': # Linux, macOS
                        import subprocess
                        subprocess.call(['open', document_ruta]) # Para macOS
                        # subprocess.call(['xdg-open', document_ruta]) # Para Linux (generalmente)
                    else:
                        QMessageBox.warning(self, "Advertencia", "Sistema operativo no compatible para abrir archivos automáticamente.")

                except Exception as e:
                    QMessageBox.critical(self, "Error", f"No se pudo abrir el documento: {e}")
            else:
                QMessageBox.warning(self, "Advertencia", "El archivo no se encontró en la ruta esperada o la ruta no es válida.")
        else:
            QMessageBox.warning(self, "Advertencia", "Seleccione un documento para abrir.")