from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QDateEdit, QMessageBox, QComboBox, QFormLayout
)
from PyQt5.QtCore import QDate, Qt, pyqtSignal
from datetime import datetime

class EditarDocumentoDialog(QDialog):
    document_edited = pyqtSignal(dict)
    
    def __init__(self, documento_data: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Documento")
        self.setMinimumWidth(500)
        self.documento_data = documento_data or {}
        self.setStyleSheet("""
            QDialog { background-color: #F8F9FA; }
            QLabel { font-size: 16px; font-weight: bold; color: #495057; }
            QLineEdit, QComboBox, QDateEdit {
                padding: 10px; border: 1px solid #CED4DA; border-radius: 5px;
                font-size: 16px; background-color: white;
            }
            QPushButton {
                background-color: #007BFF; color: white; border-radius: 8px;
                padding: 10px 20px; font-weight: bold; border: none;
            }
            QPushButton:hover { background-color: #0069D9; }
            QPushButton#cancelButton { background-color: #6C757D; }
            QPushButton#cancelButton:hover { background-color: #5A6268; }
        """)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        # --- Campos del Formulario ---
        self.nombre_input = QLineEdit(self.documento_data.get('nombre', ''))
        form_layout.addRow("Nombre del Documento:", self.nombre_input)

        self.tipo_doc_combo = QComboBox()
        self.tipo_doc_combo.addItems(
            ["General", "Contrato", "Demanda", "Sentencia", "Poder", "Acuerdo", "Factura", "Otro"]
        )
        self.tipo_doc_combo.setCurrentText(self.documento_data.get('tipo_documento', 'General'))
        form_layout.addRow("Tipo de Documento:", self.tipo_doc_combo)

        self.fecha_input = QDateEdit()
        self.fecha_input.setCalendarPopup(True)
        self.fecha_input.setDisplayFormat("yyyy-MM-dd")
        fecha_actual = self.documento_data.get('fecha_subida') or datetime.now()
        if isinstance(fecha_actual, datetime):
            year, month, day = fecha_actual.year, fecha_actual.month, fecha_actual.day
        else:
            try:
                dt = datetime.fromisoformat(str(fecha_actual))
                year, month, day = dt.year, dt.month, dt.day
            except Exception:
                now = datetime.now()
                year, month, day = now.year, now.month, now.day
        self.fecha_input.setDate(QDate(year, month, day))
        form_layout.addRow("Fecha de Subida:", self.fecha_input)

        layout.addLayout(form_layout)

        # --- Botones de Acción ---
        button_box = QHBoxLayout()
        self.save_button = QPushButton("Guardar")
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setObjectName("cancelButton")

        button_box.addStretch()
        button_box.addWidget(self.save_button)
        button_box.addWidget(self.cancel_button)
        layout.addLayout(button_box)

        self.save_button.clicked.connect(self.validate_and_accept)
        self.cancel_button.clicked.connect(self.reject)

    def get_edited_data(self) -> dict:
        """Recoge los datos editados y los devuelve en un diccionario válido para DB."""
        fecha_qdate = self.fecha_input.date()
        fecha_obj = datetime(fecha_qdate.year(), fecha_qdate.month(), fecha_qdate.day())
        
        return {
            "id_documento": self.documento_data.get("id"),
            "nombre": self.nombre_input.text().strip(),              # 👈 coincide con modelo
            "tipo_documento": self.tipo_doc_combo.currentText(),
            "fecha_subida": fecha_obj,                               # 👈 coincide con modelo
            "ubicacion_archivo": self.documento_data.get("ubicacion_archivo"),
            "archivo": self.documento_data.get("archivo"),           # 👈 obligatorio en modelo
            "fecha_expiracion": None,                                # reservado para futuro
        }

    def validate_and_accept(self):
        """Valida, arma el dict de datos editados y lo emite."""
        if not self.nombre_input.text().strip():
            QMessageBox.warning(self, "Dato Faltante", "El nombre del documento no puede estar vacío.")
            return

        edited = self.get_edited_data()
        if not edited.get("id_documento"):
            QMessageBox.critical(self, "Error", "No se encontró el ID del documento para editar.")
            return

        # ✅ Emitir dict y cerrar
        self.document_edited.emit(edited)
        self.accept()
