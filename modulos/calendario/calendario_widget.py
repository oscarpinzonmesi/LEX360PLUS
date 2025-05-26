from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QLineEdit, QMessageBox, QInputDialog
)
from utils.db_manager import DBManager


class CalendarioWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión de Calendario")
        self.setFixedSize(1000, 700)

        self.db = DBManager()
        layout = QVBoxLayout(self)

        # Barra de búsqueda
        search_layout = QHBoxLayout()
        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("Buscar por evento")
        self.btn_search = QPushButton("Buscar")
        search_layout.addWidget(self.input_search)
        search_layout.addWidget(self.btn_search)
        layout.addLayout(search_layout)

        # Tabla de calendario
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Evento", "Fecha", "Descripción"])
        layout.addWidget(self.table)

        # Campos para nuevo evento
        form_layout = QHBoxLayout()
        self.input_evento = QLineEdit()
        self.input_evento.setPlaceholderText("Nombre del Evento")
        self.input_fecha = QLineEdit()
        self.input_fecha.setPlaceholderText("Fecha")
        self.input_descripcion = QLineEdit()
        self.input_descripcion.setPlaceholderText("Descripción")
        self.btn_add = QPushButton("Agregar Evento")
        form_layout.addWidget(self.input_evento)
        form_layout.addWidget(self.input_fecha)
        form_layout.addWidget(self.input_descripcion)
        form_layout.addWidget(self.btn_add)
        layout.addLayout(form_layout)

        # Botones de acción
        actions_layout = QHBoxLayout()
        self.btn_edit = QPushButton("Editar Seleccionado")
        self.btn_delete = QPushButton("Eliminar Seleccionado")
        actions_layout.addWidget(self.btn_edit)
        actions_layout.addWidget(self.btn_delete)
        layout.addLayout(actions_layout)

        # Botón Volver al Inicio
        self.btn_volver = QPushButton("Volver al Inicio")
        layout.addWidget(self.btn_volver)
        self.btn_volver.clicked.connect(self.volver_inicio)

        # Conectar señales
        self.btn_add.clicked.connect(self.add_evento)
        self.btn_search.clicked.connect(self.search_evento)
        self.btn_delete.clicked.connect(self.delete_evento)
        self.btn_edit.clicked.connect(self.edit_evento)

        # Cargar datos iniciales
        self.load_data()

    def load_data(self, filter_text=None):
        self.table.setRowCount(0)
        eventos = self.db.get_calendario()
        for row_data in eventos:
            if filter_text and filter_text.lower() not in row_data[1].lower():
                continue
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, value in enumerate(row_data):
                self.table.setItem(row, col, QTableWidgetItem(str(value)))
        self.table.resizeColumnsToContents()

    def add_evento(self):
        evento = self.input_evento.text()
        fecha = self.input_fecha.text()
        descripcion = self.input_descripcion.text()
        if not evento:
            QMessageBox.warning(self, "Error", "El evento es obligatorio.")
            return
        self.db.add_evento(evento, fecha, descripcion)
        self.load_data()
        self.input_evento.clear()
        self.input_fecha.clear()
        self.input_descripcion.clear()

    def search_evento(self):
        texto = self.input_search.text()
        self.load_data(filter_text=texto)

    def delete_evento(self):
        row = self.table.currentRow()
        if row < 0:
            return
        evento_id = int(self.table.item(row, 0).text())
        self.db.delete_evento(evento_id)
        self.load_data()

    def edit_evento(self):
        row = self.table.currentRow()
        if row < 0:
            return
        evento_id = int(self.table.item(row, 0).text())
        evento = self.table.item(row, 1).text()
        fecha = self.table.item(row, 2).text()
        descripcion = self.table.item(row, 3).text()

        new_evento, ok1 = QInputDialog.getText(self, "Editar Evento", "Evento:", text=evento)
        new_fecha, ok2 = QInputDialog.getText(self, "Editar Fecha", "Fecha:", text=fecha)
        new_descripcion, ok3 = QInputDialog.getText(self, "Editar Descripción", "Descripción:", text=descripcion)

        if ok1 and ok2 and ok3:
            self.db.update_evento(evento_id, new_evento, new_fecha, new_descripcion)
            self.load_data()

    def volver_inicio(self):
        self.close()
