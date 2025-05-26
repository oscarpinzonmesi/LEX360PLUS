from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QPushButton, QFileDialog, QMessageBox,
    QComboBox, QFormLayout, QLabel
)
import os
import shutil

# Diccionario de tipos de actuación por categoría
TIPOS_ACTUACION = {
    "Actuaciones Judiciales": [
        "Demanda", "Auto admisorio", "Traslado de demanda",
        "Contestación", "Audiencia inicial", "Pruebas",
        "Alegatos", "Sentencia", "Recurso"
    ],
    "Actuaciones Administrativas": [
        "Radicación", "Notificación", "Revisión", "Resolución"
    ],
    "Comunicaciones": [
        "Correo", "Oficio", "Citación", "Acta"
    ],
    "Otros": [
        "Informe", "Solicitud", "Documento soporte"
    ]
}


class DocumentosTab(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.db = parent.db
        self.model = parent.model

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Lista de documentos
        self.document_list = QListWidget()
        layout.addWidget(QLabel("Documentos del proceso:"))
        layout.addWidget(self.document_list)

        # Formulario de categoría y tipo
        form_layout = QFormLayout()

        self.combo_categoria = QComboBox()
        self.combo_categoria.addItems(TIPOS_ACTUACION.keys())
        self.combo_categoria.currentTextChanged.connect(self.actualizar_tipos_actuacion)

        self.combo_tipo = QComboBox()
        self.actualizar_tipos_actuacion(self.combo_categoria.currentText())

        form_layout.addRow("Categoría:", self.combo_categoria)
        form_layout.addRow("Tipo de actuación:", self.combo_tipo)

        layout.addLayout(form_layout)

        # Botón para subir documento
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
        layout.addWidget(self.upload_button)

        self.setLayout(layout)

    def actualizar_tipos_actuacion(self, categoria):
        self.combo_tipo.clear()
        if categoria in TIPOS_ACTUACION:
            self.combo_tipo.addItems(TIPOS_ACTUACION[categoria])

    def load_documents(self, proceso_id):
        self.document_list.clear()
        documentos = self.model.obtener_documentos_por_proceso(proceso_id)
        for doc in documentos:
            self.document_list.addItem(doc[1])  # doc[1] = nombre del archivo

    def subir_documento(self):
        proceso_id = self.parent.selected_proceso_id
        if proceso_id is None:
            QMessageBox.warning(self, "Advertencia", "No se ha seleccionado ningún proceso.")
            return

        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Seleccionar documento")
        if file_path:
            nombre_archivo = os.path.basename(file_path)
            destino = os.path.join("documentos", nombre_archivo)

            try:
                shutil.copy(file_path, destino)

                categoria = self.combo_categoria.currentText()
                tipo_actuacion = self.combo_tipo.currentText()

                # En el siguiente paso, guardaremos también `categoria` y `tipo_actuacion` en la base de datos
                self.model.insertar_documento(proceso_id, nombre_archivo, destino, categoria, tipo_actuacion)

                self.load_documents(proceso_id)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo subir el documento: {e}")
