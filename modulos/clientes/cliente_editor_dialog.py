from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox, QFormLayout, QMessageBox, QComboBox
)
from PyQt5.QtGui import QFont
import re

class ClienteEditorDialog(QDialog):
    def __init__(self, campos, valores, parent=None):
        super().__init__(parent)
        # Asignación de los valores pasados como parámetros
        self.campos = campos
        self.valores = valores
        self.parent = parent

        # Asegúrate de que los valores coincidan con los campos
        self.nombre = valores[0]
        self.tipo_id = valores[1]
        self.identificacion = valores[2]
        self.correo = valores[3]
        self.telefono = valores[4]
        self.direccion = valores[5]
        
        # Definir atributos para cada campo
        self.entrada_nombre = QLineEdit(self.nombre)
        self.combo_tipo_id = QComboBox()
        self.entrada_identificacion = QLineEdit(self.identificacion)
        self.entrada_correo = QLineEdit(self.correo)
        self.entrada_telefono = QLineEdit(self.telefono)
        self.entrada_direccion = QLineEdit(self.direccion)

        # Lista solo de QLineEdit para validación genérica
        self.inputs = [
            self.entrada_nombre,
            self.combo_tipo_id,  # Se agrega el combo box aquí
            self.entrada_identificacion,
            self.entrada_correo,
            self.entrada_telefono,
            self.entrada_direccion
        ]

        self.init_ui()

    def init_ui(self):
        fuente = QFont("Arial", 14)
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Nombre
        label = QLabel("Nombre:")
        label.setFont(fuente)
        self.entrada_nombre.setFont(fuente)
        self.entrada_nombre.setFixedSize(300, 40)
        form_layout.addRow(label, self.entrada_nombre)

        # Tipo ID
        label = QLabel("Tipo ID:")
        label.setFont(fuente)
        self.combo_tipo_id.setFont(fuente)
        self.combo_tipo_id.setFixedSize(300, 40)
        self.combo_tipo_id.addItems([
            "Cédula de Ciudadanía",
            "Cédula de Extranjería",
            "Pasaporte",
            "NIT",
            "Tarjeta de Identidad",
            "Registro Civil"
        ])
        # Pre-seleccionar el tipo de ID si se pasó algún valor
        if self.tipo_id:
            index = self.combo_tipo_id.findText(self.tipo_id)
            if index >= 0:
                self.combo_tipo_id.setCurrentIndex(index)
        form_layout.addRow(label, self.combo_tipo_id)

        # Identificación
        label = QLabel("Identificación:")
        label.setFont(fuente)
        self.entrada_identificacion.setFont(fuente)
        self.entrada_identificacion.setFixedSize(300, 40)
        form_layout.addRow(label, self.entrada_identificacion)

        # Correo
        label = QLabel("Correo:")
        label.setFont(fuente)
        self.entrada_correo.setFont(fuente)
        self.entrada_correo.setFixedSize(300, 40)
        form_layout.addRow(label, self.entrada_correo)

        # Teléfono
        label = QLabel("Teléfono:")
        label.setFont(fuente)
        self.entrada_telefono.setFont(fuente)
        self.entrada_telefono.setFixedSize(300, 40)
        form_layout.addRow(label, self.entrada_telefono)

        # Dirección
        label = QLabel("Dirección:")
        label.setFont(fuente)
        self.entrada_direccion.setFont(fuente)
        self.entrada_direccion.setFixedSize(300, 40)
        form_layout.addRow(label, self.entrada_direccion)

        layout.addLayout(form_layout)

        botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botones.setFont(fuente)
        botones.accepted.connect(self.on_accept)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def on_accept(self):
        # Validar campos de texto
        for edit in self.inputs:
            if isinstance(edit, QLineEdit) and edit.text().strip() == '':
                QMessageBox.warning(self, "Campos incompletos", "Por favor, completa todos los campos.")
                return

        # Verificar que el `combo_tipo_id` tenga una selección válida
        if self.combo_tipo_id.currentText().strip() == '':
            QMessageBox.warning(self, "Selección incompleta", "Por favor, selecciona un tipo de identificación.")
            return

        # Validar Identificación (solo dígitos)
        id_text = self.entrada_identificacion.text().strip()
        if not id_text.isdigit():
            QMessageBox.warning(self, "Identificación incorrecta", "La identificación debe contener solo números.")
            return

        # Validar correo
        correo_text = self.entrada_correo.text().strip()
        if not re.match(r"[^@]+@[^@]+\.[^@]+", correo_text):
            QMessageBox.warning(self, "Correo incorrecto", "Por favor, ingresa un correo electrónico válido.")
            return

        super().accept()

    def get_values(self):
        # Este método devuelve un diccionario con los valores de los campos
        return {
            "Nombre": self.entrada_nombre.text().strip(),
            "Tipo ID": self.combo_tipo_id.currentText().strip(),
            "Identificación": self.entrada_identificacion.text().strip(),
            "Correo": self.entrada_correo.text().strip(),
            "Teléfono": self.entrada_telefono.text().strip(),
            "Dirección": self.entrada_direccion.text().strip()
        }
