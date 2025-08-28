# SELECTA_SCAM/modulos/clientes/cliente_editor_dialog.py

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QHBoxLayout, QComboBox, QMessageBox, QFormLayout)
from PyQt5.QtCore import Qt

class ClienteEditorDialog(QDialog):
    def __init__(self, data_to_edit=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Cliente" if data_to_edit else "Nuevo Cliente")
        self.data_to_edit = data_to_edit or {}
        self.inputs = {}
        self.setMinimumWidth(800)

        # Aplicar el estilo visual de tu versión original
        self.setStyleSheet("""
            QDialog {
                background-color: #F8F9FA;
            }
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #495057;
                margin-bottom: 5px;
            }
            QLineEdit, QComboBox {
                padding: 10px;
                border: 1px solid #CED4DA;
                border-radius: 5px;
                font-size: 26px;
                color: #495057;
                background-color: white;
            }
            QPushButton {
                background-color: #007BFF;
                color: white;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover { background-color: #0069D9; }
            QPushButton#cancelButton { background-color: #6C757D; }
            QPushButton#cancelButton:hover { background-color: #5A6268; }
        """)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        # Definimos los campos y sus tipos
        self.campos = {
            "nombre": {"label": "Nombre:", "widget": QLineEdit},
            "tipo_identificacion": {"label": "Tipo ID:", "widget": QComboBox, "items": ["Cédula de Ciudadanía", "Tarjeta de Identidad", "Cédula de Extranjería", "Pasaporte", "NIT"]},
            "numero_identificacion": {"label": "Identificación:", "widget": QLineEdit},
            "email": {"label": "Correo:", "widget": QLineEdit},
            "telefono": {"label": "Teléfono:", "widget": QLineEdit},
            "direccion": {"label": "Dirección:", "widget": QLineEdit},
            "tipo_cliente": {"label": "Tipo de Cliente:", "widget": QComboBox, "items": ["Natural", "Jurídico"]}
        }

        # Creamos los widgets dinámicamente
        for key, config in self.campos.items():
            input_widget = config["widget"]()
            
            if isinstance(input_widget, QComboBox):
                input_widget.addItems(config["items"])
                # Seleccionar el valor correcto si estamos editando
                if self.data_to_edit.get(key):
                    input_widget.setCurrentText(self.data_to_edit.get(key))
            else:
                input_widget.setText(str(self.data_to_edit.get(key, "")))
            
            self.inputs[key] = input_widget
            form_layout.addRow(config["label"], input_widget)

        layout.addLayout(form_layout)

        # Botones
        botones_layout = QHBoxLayout()
        self.btn_aceptar = QPushButton("Aceptar")
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setObjectName("cancelButton")
        
        botones_layout.addStretch()
        botones_layout.addWidget(self.btn_aceptar)
        botones_layout.addWidget(self.btn_cancelar)
        layout.addLayout(botones_layout)

        self.btn_aceptar.clicked.connect(self.validate_and_accept)
        self.btn_cancelar.clicked.connect(self.reject)

    def get_data(self):
        """Recoge los datos de los campos de entrada y los devuelve como un diccionario."""
        values = {}
        for key, widget in self.inputs.items():
            if isinstance(widget, QLineEdit):
                values[key] = widget.text().strip()
            elif isinstance(widget, QComboBox):
                values[key] = widget.currentText()
        return values
        
    def validate_and_accept(self):
        """Valida que los campos obligatorios no estén vacíos antes de aceptar."""
        data = self.get_data()
        if not data.get('nombre') or not data.get('numero_identificacion'):
            QMessageBox.warning(self, "Datos Incompletos", "El Nombre y el Número de Identificación son campos obligatorios.")
            return
        self.accept()