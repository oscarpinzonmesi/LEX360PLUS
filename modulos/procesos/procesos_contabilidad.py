from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt


class ContabilidadTab(QWidget):
    BOTON_STYLE = """
        QPushButton {
            background-color: #4a4a4a;
            color: white;
            border-radius: 8px;
            padding: 8px 16px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #6b6b6b;
        }
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.db = parent.db
        self.model = parent.model

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Tabla de contabilidad
        self.tabla_contabilidad = QTableWidget()
        self.tabla_contabilidad.setColumnCount(3)
        self.tabla_contabilidad.setHorizontalHeaderLabels(["ID", "Concepto", "Monto"])
        self.tabla_contabilidad.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla_contabilidad.horizontalHeader().setStretchLastSection(True)
        self.tabla_contabilidad.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_contabilidad.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla_contabilidad.itemSelectionChanged.connect(self.on_selection_change)
        layout.addWidget(self.tabla_contabilidad)

        # Formulario para agregar/editar gastos
        form_layout = QHBoxLayout()
        self.input_concepto = QLineEdit()
        self.input_concepto.setPlaceholderText("Concepto")
        self.input_monto = QLineEdit()
        self.input_monto.setPlaceholderText("Monto")

        self.btn_agregar = QPushButton("Agregar")
        self._estilizar_boton(self.btn_agregar)
        self.btn_agregar.clicked.connect(self.agregar_o_actualizar_gasto)

        self.btn_eliminar = QPushButton("Eliminar")
        self._estilizar_boton(self.btn_eliminar)
        self.btn_eliminar.setEnabled(False)
        self.btn_eliminar.clicked.connect(self.eliminar_gasto)

        form_layout.addWidget(QLabel("Concepto:"))
        form_layout.addWidget(self.input_concepto)
        form_layout.addWidget(QLabel("Monto:"))
        form_layout.addWidget(self.input_monto)
        form_layout.addWidget(self.btn_agregar)
        form_layout.addWidget(self.btn_eliminar)

        layout.addLayout(form_layout)
        self.setLayout(layout)

    def _estilizar_boton(self, boton: QPushButton):
        boton.setFont(QFont("Arial", 14))
        boton.setFixedHeight(40)
        boton.setStyleSheet(self.BOTON_STYLE)

    def load_contabilidad(self, proceso_id: int):
        """
        Carga los registros contables asociados a `proceso_id`.
        Se asume que `self.model.obtener_contabilidad_por_proceso(proceso_id)`
        retorna tuplas: (id, concepto, monto).
        """
        self.tabla_contabilidad.setRowCount(0)
        registros = self.model.obtener_contabilidad_por_proceso(proceso_id)
        for registro in registros:
            reg_id, concepto, monto = registro
            row = self.tabla_contabilidad.rowCount()
            self.tabla_contabilidad.insertRow(row)

            item_id = QTableWidgetItem(str(reg_id))
            item_id.setData(Qt.UserRole, reg_id)
            item_id.setTextAlignment(Qt.AlignCenter)

            item_concepto = QTableWidgetItem(concepto)
            item_monto = QTableWidgetItem(f"{monto:.2f}")
            item_monto.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            self.tabla_contabilidad.setItem(row, 0, item_id)
            self.tabla_contabilidad.setItem(row, 1, item_concepto)
            self.tabla_contabilidad.setItem(row, 2, item_monto)

        # Reiniciar formulario y botones
        self._reset_formulario()

    def on_selection_change(self):
        selected_items = self.tabla_contabilidad.selectedItems()
        if not selected_items:
            self._reset_formulario()
            return

        # Tomar los datos de la fila seleccionada
        row = selected_items[0].row()
        reg_id = int(self.tabla_contabilidad.item(row, 0).text())
        concepto = self.tabla_contabilidad.item(row, 1).text()
        monto = self.tabla_contabilidad.item(row, 2).text()

        # Llenar campos para edición
        self.input_concepto.setText(concepto)
        self.input_monto.setText(monto)
        self.btn_agregar.setText("Actualizar")
        self.btn_eliminar.setEnabled(True)
        self.btn_agregar.setProperty("edit_id", reg_id)

    def agregar_o_actualizar_gasto(self):
        concepto = self.input_concepto.text().strip()
        monto_texto = self.input_monto.text().strip()
        proceso_id = self.parent.selected_proceso_id

        if not concepto or not monto_texto:
            QMessageBox.warning(self, "Advertencia", "Debe completar todos los campos.")
            return

        try:
            monto = float(monto_texto)
        except ValueError:
            QMessageBox.warning(self, "Advertencia", "El monto debe ser un número.")
            return

        edit_id = self.btn_agregar.property("edit_id")
        if edit_id is None:
            # Insertar nuevo registro
            try:
                self.model.insertar_gasto(proceso_id, concepto, monto)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo agregar el gasto: {e}")
        else:
            # Actualizar registro existente
            try:
                self.model.actualizar_gasto(edit_id, concepto, monto)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo actualizar el gasto: {e}")
            self.btn_agregar.setProperty("edit_id", None)
            self.btn_agregar.setText("Agregar")

        self.input_concepto.clear()
        self.input_monto.clear()
        self.btn_eliminar.setEnabled(False)
        self.load_contabilidad(proceso_id)

    def eliminar_gasto(self):
        selected_items = self.tabla_contabilidad.selectedItems()
        if not selected_items:
            return

        row = selected_items[0].row()
        reg_id = int(self.tabla_contabilidad.item(row, 0).text())
        proceso_id = self.parent.selected_proceso_id

        respuesta = QMessageBox.question(
            self,
            "Confirmar eliminación",
            "¿Estás seguro de eliminar este registro?",
            QMessageBox.Yes | QMessageBox.No
        )
        if respuesta == QMessageBox.Yes:
            try:
                self.model.eliminar_gasto(reg_id)
                self.load_contabilidad(proceso_id)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar el gasto: {e}")

    def _reset_formulario(self):
        self.input_concepto.clear()
        self.input_monto.clear()
        self.btn_agregar.setText("Agregar")
        self.btn_eliminar.setEnabled(False)
        self.btn_agregar.setProperty("edit_id", None)
