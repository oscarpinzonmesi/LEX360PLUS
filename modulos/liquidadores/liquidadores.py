from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QComboBox, QMessageBox, QLabel, QDateEdit, QInputDialog
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QDate
from utils.db_manager import DBManager


class LiquidadoresWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DBManager()
        self.selected_row = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Cliente", "Concepto", "Monto", "Fecha"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.cellClicked.connect(self.select_row)
        layout.addWidget(self.table)

        form_layout = QHBoxLayout()

        font = QFont("Arial", 14)

        self.cliente_input = QComboBox()
        self.cliente_input.setFont(font)
        self.cliente_input.setEditable(True)
        clientes = [c[1] for c in self.db.get_clientes()]
        self.cliente_input.addItems(clientes)

        self.concepto_input = QLineEdit()
        self.concepto_input.setPlaceholderText("Concepto")
        self.concepto_input.setFont(font)

        self.monto_input = QLineEdit()
        self.monto_input.setPlaceholderText("Monto")
        self.monto_input.setFont(font)

        self.fecha_input = QDateEdit()
        self.fecha_input.setDisplayFormat("yyyy-MM-dd")
        self.fecha_input.setDate(QDate.currentDate())
        self.fecha_input.setFont(font)
        self.fecha_input.setCalendarPopup(True)

        self.agregar_btn = QPushButton("Agregar Liquidador")
        self.agregar_btn.setFont(font)
        self.agregar_btn.setStyleSheet("background-color: #2ecc71; color: white; border-radius: 8px;")
        self.agregar_btn.clicked.connect(self.agregar_liquidador)

        self.eliminar_btn = QPushButton("Eliminar Liquidador")
        self.eliminar_btn.setFont(font)
        self.eliminar_btn.setStyleSheet("background-color: #e74c3c; color: white; border-radius: 8px;")
        self.eliminar_btn.clicked.connect(self.eliminar_liquidador)

        self.editar_btn = QPushButton("Corregir Liquidador")
        self.editar_btn.setFont(font)
        self.editar_btn.setStyleSheet("background-color: #f39c12; color: white; border-radius: 8px;")
        self.editar_btn.clicked.connect(self.edit_liquidador)

        form_layout.addWidget(self.cliente_input)
        form_layout.addWidget(self.concepto_input)
        form_layout.addWidget(self.monto_input)
        form_layout.addWidget(self.fecha_input)
        form_layout.addWidget(self.agregar_btn)
        form_layout.addWidget(self.eliminar_btn)
        form_layout.addWidget(self.editar_btn)

        layout.addLayout(form_layout)

        # Botón volver al inicio
        self.volver_btn = QPushButton("Volver al Inicio")
        self.volver_btn.setFont(QFont("Arial", 14))
        self.volver_btn.setStyleSheet("background-color: #95a5a6; color: white; border-radius: 8px;")
        self.volver_btn.clicked.connect(self.close)
        layout.addWidget(self.volver_btn)

        self.cargar_datos()

    def cargar_datos(self):
        self.table.setRowCount(0)
        registros = self.db.get_liquidadores()
        for row_data in registros:
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, val in enumerate(row_data):
                self.table.setItem(row, col, QTableWidgetItem(str(val)))
        self.table.resizeColumnsToContents()

    def agregar_liquidador(self):
        cliente = self.cliente_input.currentText().strip()
        concepto = self.concepto_input.text().strip()
        monto_texto = self.monto_input.text().strip()
        fecha = self.fecha_input.date().toString("yyyy-MM-dd")

        if not cliente or not concepto or not monto_texto:
            QMessageBox.warning(self, "Campos incompletos", "Todos los campos son obligatorios.")
            return

        try:
            monto = float(monto_texto)
        except ValueError:
            QMessageBox.warning(self, "Error", "El monto debe ser un número válido.")
            return

        cid = self.db.get_cliente_id(cliente)
        if cid is None:
            QMessageBox.warning(self, "Error", "Cliente no encontrado.")
            return

        self.db.add_liquidador(cid, concepto, monto, fecha)
        self.cargar_datos()
        self.concepto_input.clear()
        self.monto_input.clear()
        self.fecha_input.setDate(QDate.currentDate())

    def eliminar_liquidador(self):
        if self.selected_row is None:
            return
        lid = int(self.table.item(self.selected_row, 0).text())
        confirm = QMessageBox.question(self, "Eliminar", "¿Estás seguro de eliminar este liquidador?",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.db.delete_liquidador(lid)
            self.cargar_datos()
            self.selected_row = None

    def edit_liquidador(self):
        if self.selected_row is None:
            return
        lid = int(self.table.item(self.selected_row, 0).text())
        nuevo_concepto, ok = QInputDialog.getText(self, "Editar Concepto", "Nuevo Concepto:")
        if ok and nuevo_concepto.strip():
            self.db.update_liquidador(lid, nuevo_concepto.strip())
            self.cargar_datos()

    def select_row(self, row, _):
        self.selected_row = row
