# modulos/contabilidad/contabilidad_widget.py

from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QComboBox,
    QDateEdit, QFileDialog
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
import os

from modulos.contabilidad.contabilidad_model import ContabilidadModel


class ContabilidadWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Contabilidad")
        self.setMinimumSize(1000, 600)

        self.model = ContabilidadModel()
        self.selected_id = None

        # Estilo unificado para botones
        self.button_style = """
            QPushButton {
                background-color: #2E86C1;
                color: white;
                font-size: 14px;
                border-radius: 5px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #1B4F72;
            }
        """

        self.init_ui()
        self.load_clientes()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # --- Formulario de entrada ---
        form_layout = QHBoxLayout()

        # Cliente
        form_layout.addWidget(QLabel("Cliente:", alignment=Qt.AlignRight))
        self.cliente_input = QComboBox()
        self.cliente_input.setPlaceholderText("Seleccione cliente")
        form_layout.addWidget(self.cliente_input)

        # Tipo
        form_layout.addWidget(QLabel("Tipo:", alignment=Qt.AlignRight))
        self.tipo_input = QLineEdit()
        self.tipo_input.setPlaceholderText("Tipo de registro")
        form_layout.addWidget(self.tipo_input)

        # Descripción
        form_layout.addWidget(QLabel("Descripción:", alignment=Qt.AlignRight))
        self.descripcion_input = QLineEdit()
        self.descripcion_input.setPlaceholderText("Descripción")
        form_layout.addWidget(self.descripcion_input)

        # Valor
        form_layout.addWidget(QLabel("Valor ($):", alignment=Qt.AlignRight))
        self.valor_input = QLineEdit()
        self.valor_input.setPlaceholderText("Valor")
        form_layout.addWidget(self.valor_input)

        # Fecha
        form_layout.addWidget(QLabel("Fecha:", alignment=Qt.AlignRight))
        self.fecha_input = QDateEdit()
        self.fecha_input.setCalendarPopup(True)
        self.fecha_input.setDisplayFormat("yyyy-MM-dd")
        self.fecha_input.setDate(QDate.currentDate())
        form_layout.addWidget(self.fecha_input)

        layout.addLayout(form_layout)

        # --- Tabla de registros ---
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Cliente", "Tipo", "Descripción", "Valor", "Fecha"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.itemSelectionChanged.connect(self.cargar_datos_seleccionados)
        layout.addWidget(self.table)

        # --- Botones de acción ---
        button_layout = QHBoxLayout()

        self.btn_agregar = QPushButton("Agregar")
        self.btn_agregar.setStyleSheet(self.button_style)
        self.btn_agregar.clicked.connect(self.agregar_contabilidad)
        button_layout.addWidget(self.btn_agregar)

        self.btn_editar = QPushButton("Editar")
        self.btn_editar.setStyleSheet(self.button_style)
        self.btn_editar.clicked.connect(self.editar_contabilidad)
        self.btn_editar.setEnabled(False)
        button_layout.addWidget(self.btn_editar)

        self.btn_eliminar = QPushButton("Eliminar")
        self.btn_eliminar.setStyleSheet(self.button_style)
        self.btn_eliminar.clicked.connect(self.eliminar_contabilidad)
        self.btn_eliminar.setEnabled(False)
        button_layout.addWidget(self.btn_eliminar)

        self.btn_pdf = QPushButton("Generar PDF")
        self.btn_pdf.setStyleSheet(self.button_style)
        self.btn_pdf.setEnabled(False)
        self.btn_pdf.clicked.connect(self.generar_pdf)
        button_layout.addWidget(self.btn_pdf)

        layout.addLayout(button_layout)

    def load_clientes(self):
        """
        Carga el ComboBox con todos los clientes (id, nombre).
        """
        self.cliente_input.clear()
        clientes = self.model.get_clientes()
        for cliente_id, nombre in clientes:
            self.cliente_input.addItem(nombre, cliente_id)

    def load_data(self):
        """
        Carga todos los registros de contabilidad en la tabla.
        Cada fila: (id, nombre_cliente, tipo, descripcion, valor, fecha)
        """
        self.table.setRowCount(0)
        filas = self.model.get_contabilidad_detallada()
        for datos in filas:
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, dato in enumerate(datos):
                item = QTableWidgetItem(str(dato))
                # Colorear montos (columna 'Valor') de azul
                if col == 4:
                    item.setForeground(QColor("blue"))
                self.table.setItem(row, col, item)

    def clear_inputs(self):
        """
        Limpia todos los campos del formulario y desactiva botones de acción.
        """
        self.cliente_input.setCurrentIndex(-1)
        self.tipo_input.clear()
        self.descripcion_input.clear()
        self.valor_input.clear()
        self.fecha_input.setDate(QDate.currentDate())
        self.selected_id = None
        self.btn_editar.setEnabled(False)
        self.btn_eliminar.setEnabled(False)
        self.btn_pdf.setEnabled(False)
        self.table.clearSelection()

    def agregar_contabilidad(self):
        """
        Toma los datos del formulario y los inserta en la base de datos.
        """
        cliente_id = self.cliente_input.currentData()
        tipo = self.tipo_input.text().strip()
        descripcion = self.descripcion_input.text().strip()
        valor_text = self.valor_input.text().strip()
        fecha = self.fecha_input.date().toString("yyyy-MM-dd")

        if cliente_id is None or not tipo or not descripcion or not valor_text:
            QMessageBox.warning(self, "Campos incompletos",
                                "Complete todos los campos obligatorios.")
            return

        try:
            valor = float(valor_text)
        except ValueError:
            QMessageBox.warning(self, "Error en los datos",
                                "El campo 'Valor' debe ser numérico.")
            return

        try:
            self.model.add_contabilidad(cliente_id, tipo, descripcion, valor, fecha)
            QMessageBox.information(self, "Éxito",
                                    "Registro agregado correctamente.")
            self.load_data()
            self.clear_inputs()
        except Exception as e:
            QMessageBox.critical(self, "Error",
                                 f"No se pudo agregar la entrada: {e}")

    def cargar_datos_seleccionados(self):
        """
        Cuando el usuario selecciona una fila en la tabla, carga los valores
        en el formulario para permitir edición/eliminación.
        """
        seleccion = self.table.selectedItems()
        if not seleccion:
            self.selected_id = None
            self.btn_editar.setEnabled(False)
            self.btn_eliminar.setEnabled(False)
            self.btn_pdf.setEnabled(False)
            return

        row = self.table.currentRow()
        self.selected_id = int(self.table.item(row, 0).text())

        # Habilitar botones
        self.btn_editar.setEnabled(True)
        self.btn_eliminar.setEnabled(True)
        self.btn_pdf.setEnabled(True)

        # Cargar datos
        cliente_nombre = self.table.item(row, 1).text()
        tipo = self.table.item(row, 2).text()
        descripcion = self.table.item(row, 3).text()
        valor = self.table.item(row, 4).text()
        fecha_texto = self.table.item(row, 5).text()

        # Seleccionar cliente en el combo
        index_cliente = self.cliente_input.findText(cliente_nombre)
        if index_cliente != -1:
            self.cliente_input.setCurrentIndex(index_cliente)

        # Tipo y descripción
        self.tipo_input.setText(tipo)
        self.descripcion_input.setText(descripcion)

        # Valor
        self.valor_input.setText(valor)

        # Fecha
        fecha = QDate.fromString(fecha_texto, "yyyy-MM-dd")
        if fecha.isValid():
            self.fecha_input.setDate(fecha)
        else:
            self.fecha_input.setDate(QDate.currentDate())

    def editar_contabilidad(self):
        """
        Actualiza el registro seleccionado con los valores del formulario.
        """
        if self.selected_id is None:
            QMessageBox.warning(self, "Sin selección",
                                "Seleccione una fila para editar.")
            return

        cliente_id = self.cliente_input.currentData()
        tipo = self.tipo_input.text().strip()
        descripcion = self.descripcion_input.text().strip()
        valor_text = self.valor_input.text().strip()
        fecha = self.fecha_input.date().toString("yyyy-MM-dd")

        if cliente_id is None or not tipo or not descripcion or not valor_text:
            QMessageBox.warning(self, "Campos incompletos",
                                "Complete todos los campos obligatorios.")
            return

        try:
            valor = float(valor_text)
        except ValueError:
            QMessageBox.warning(self, "Error en los datos",
                                "El campo 'Valor' debe ser numérico.")
            return

        try:
            self.model.update_contabilidad(
                self.selected_id,
                cliente_id,
                tipo,
                descripcion,
                valor,
                fecha
            )
            QMessageBox.information(self, "Éxito",
                                    "Registro actualizado correctamente.")
            self.load_data()
            self.clear_inputs()
        except Exception as e:
            QMessageBox.critical(self, "Error",
                                 f"No se pudo actualizar la entrada: {e}")

    def eliminar_contabilidad(self):
        """
        Elimina el registro seleccionado de la base de datos.
        """
        if self.selected_id is None:
            QMessageBox.warning(self, "Sin selección",
                                "Seleccione una fila para eliminar.")
            return

        confirm = QMessageBox.question(
            self, "Confirmar",
            "¿Está seguro de eliminar esta entrada?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            self.model.delete_contabilidad(self.selected_id)
            QMessageBox.information(self, "Éxito",
                                    "Registro eliminado correctamente.")
            self.load_data()
            self.clear_inputs()
        except Exception as e:
            QMessageBox.critical(self, "Error",
                                 f"No se pudo eliminar la entrada: {e}")

    def generar_pdf(self):
        """
        Genera un PDF con la información del registro seleccionado.
        """
        if self.selected_id is None:
            return

        row = self.table.currentRow()
        cliente = self.table.item(row, 1).text()
        tipo = self.table.item(row, 2).text()
        descripcion = self.table.item(row, 3).text()
        valor = self.table.item(row, 4).text()
        fecha = self.table.item(row, 5).text()

        # Solicitar ubicación para guardar PDF
        ruta_guardar, _ = QFileDialog.getSaveFileName(
            self, "Guardar PDF",
            "reporte_contabilidad.pdf",
            "PDF Files (*.pdf)"
        )
        if not ruta_guardar:
            return

        c = canvas.Canvas(ruta_guardar, pagesize=letter)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(200, 750, "REPORTE DE CONTABILIDAD")
        c.setFont("Helvetica", 12)

        y = 700
        c.drawString(100, y, f"Cliente: {cliente}")
        y -= 20
        c.drawString(100, y, f"Tipo: {tipo}")
        y -= 20
        c.drawString(100, y, f"Descripción: {descripcion}")
        y -= 20
        c.drawString(100, y, f"Valor: ${valor}")
        y -= 20
        c.drawString(100, y, f"Fecha: {fecha}")
        y -= 40

        # Agregar firma si existe
        firma_path = os.path.join("assets", "firma_abogado.png")
        if os.path.exists(firma_path):
            c.drawImage(ImageReader(firma_path), 400, y - 50, width=150, height=50)

        c.save()
