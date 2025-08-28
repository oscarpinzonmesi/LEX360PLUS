from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QComboBox
)
from PyQt5.QtGui import QFont, QDoubleValidator
from PyQt5.QtCore import Qt
import datetime # Para la fecha del movimiento

# NO necesitamos importar ProcesosModel aquí si la instancia se pasa en el constructor.
# from SELECTA_SCAM.modulos.procesos.procesos_model import ProcesosModel

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

    def __init__(self, procesos_model, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.procesos_model = procesos_model # Almacena la instancia de ProcesosModel

        self.current_proceso_id = None # Para almacenar el ID del proceso actualmente cargado

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Etiqueta para el título de la sección
        titulo_label = QLabel("Gestión de Movimientos Contables del Proceso")
        titulo_label.setFont(QFont("Arial", 16, QFont.Bold))
        titulo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo_label)

        # Tabla de contabilidad
        self.tabla_contabilidad = QTableWidget()
        self.tabla_contabilidad.setColumnCount(5)
        # CAMBIO 1: Ajustar los encabezados para reflejar 'Descripción' en lugar de 'Concepto' si es necesario
        self.tabla_contabilidad.setHorizontalHeaderLabels(["ID", "Fecha", "Descripción", "Monto", "Tipo"]) # Se recomienda 'Descripción' para coherencia con el modelo
        self.tabla_contabilidad.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla_contabilidad.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_contabilidad.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_contabilidad.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla_contabilidad.itemSelectionChanged.connect(self.on_selection_change)
        layout.addWidget(self.tabla_contabilidad)

        # Formulario para agregar/editar movimientos
        form_layout = QHBoxLayout()

        self.input_concepto = QLineEdit()
        self.input_concepto.setPlaceholderText("Concepto del movimiento")
        self.input_concepto.setMinimumWidth(200)

        self.input_monto = QLineEdit()
        self.input_monto.setPlaceholderText("Monto")
        self.input_monto.setValidator(self.get_float_validator())
        self.input_monto.setMaximumWidth(100)

        self.combo_tipo_movimiento = QComboBox()
        self.combo_tipo_movimiento.addItems(["Gasto", "Ingreso"])
        self.combo_tipo_movimiento.setMaximumWidth(100)

        self.btn_agregar_actualizar = QPushButton("Agregar Movimiento")
        self._estilizar_boton(self.btn_agregar_actualizar)
        self.btn_agregar_actualizar.clicked.connect(self.agregar_o_actualizar_movimiento)

        self.btn_eliminar = QPushButton("Eliminar Movimiento")
        self._estilizar_boton(self.btn_eliminar)
        self.btn_eliminar.setEnabled(False)
        self.btn_eliminar.clicked.connect(self.eliminar_movimiento)
        
        self.btn_limpiar = QPushButton("Limpiar Formulario")
        self._estilizar_boton(self.btn_limpiar)
        self.btn_limpiar.clicked.connect(self._reset_formulario)

        form_layout.addWidget(QLabel("Concepto:"))
        form_layout.addWidget(self.input_concepto)
        form_layout.addWidget(QLabel("Monto:"))
        form_layout.addWidget(self.input_monto)
        form_layout.addWidget(QLabel("Tipo:"))
        form_layout.addWidget(self.combo_tipo_movimiento)
        form_layout.addWidget(self.btn_agregar_actualizar)
        form_layout.addWidget(self.btn_eliminar)
        form_layout.addWidget(self.btn_limpiar)

        layout.addLayout(form_layout)
        self.setLayout(layout)

    def _estilizar_boton(self, boton: QPushButton):
        boton.setFont(QFont("Arial", 10))
        boton.setFixedHeight(30)
        boton.setStyleSheet(self.BOTON_STYLE)
    
    def get_float_validator(self):
        validator = QDoubleValidator()
        validator.setRange(0.01, 999999999.99, 2)
        validator.setNotation(QDoubleValidator.StandardNotation)
        return validator

    def set_proceso_id(self, proceso_id: int):
        self.current_proceso_id = proceso_id
        self.load_contabilidad()

    def load_contabilidad(self):
        self.tabla_contabilidad.setRowCount(0)
        if self.current_proceso_id is None:
            return

        try:
            movimientos = self.procesos_model.obtener_movimientos_contables_por_proceso(self.current_proceso_id)
            
            for row_idx, movimiento in enumerate(movimientos):
                self.tabla_contabilidad.insertRow(row_idx)

                item_id = QTableWidgetItem(str(movimiento.get('id', '')))
                item_id.setData(Qt.UserRole, movimiento.get('id'))
                item_id.setTextAlignment(Qt.AlignCenter)

                item_fecha = QTableWidgetItem(movimiento.get('fecha', ''))
                item_fecha.setTextAlignment(Qt.AlignCenter)

                # CAMBIO 2: Usar 'descripcion' que es la clave que viene de ProcesosModel
                item_concepto = QTableWidgetItem(movimiento.get('descripcion', '')) 
                
                item_monto = QTableWidgetItem(f"{movimiento.get('valor', 0.0):.2f}")
                item_monto.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                
                # CAMBIO 3: Usar 'tipo' que es la clave que viene de ProcesosModel
                item_tipo = QTableWidgetItem(movimiento.get('tipo', '')) 
                item_tipo.setTextAlignment(Qt.AlignCenter)

                self.tabla_contabilidad.setItem(row_idx, 0, item_id)
                self.tabla_contabilidad.setItem(row_idx, 1, item_fecha)
                self.tabla_contabilidad.setItem(row_idx, 2, item_concepto)
                self.tabla_contabilidad.setItem(row_idx, 3, item_monto)
                self.tabla_contabilidad.setItem(row_idx, 4, item_tipo)

        except Exception as e:
            QMessageBox.critical(self, "Error de Carga", f"No se pudieron cargar los movimientos contables: {e}")

        self._reset_formulario()

    def on_selection_change(self):
        selected_items = self.tabla_contabilidad.selectedItems()
        if not selected_items:
            self._reset_formulario()
            return

        row = selected_items[0].row()
        movimiento_id = self.tabla_contabilidad.item(row, 0).data(Qt.UserRole)
        # Los siguientes `item.text()` ya son correctos porque recuperan lo que se mostró en la tabla
        concepto = self.tabla_contabilidad.item(row, 2).text()
        monto = self.tabla_contabilidad.item(row, 3).text()
        tipo_movimiento = self.tabla_contabilidad.item(row, 4).text()

        self.input_concepto.setText(concepto)
        self.input_monto.setText(monto)
        self.combo_tipo_movimiento.setCurrentText(tipo_movimiento)
        
        self.btn_agregar_actualizar.setText("Actualizar Movimiento")
        self.btn_eliminar.setEnabled(True)
        self.btn_agregar_actualizar.setProperty("edit_id", movimiento_id)

    def agregar_o_actualizar_movimiento(self):
        concepto = self.input_concepto.text().strip()
        monto_texto = self.input_monto.text().strip()
        tipo_movimiento = self.combo_tipo_movimiento.currentText()

        if self.current_proceso_id is None:
            QMessageBox.warning(self, "Advertencia", "Por favor, seleccione un proceso primero.")
            return

        if not concepto or not monto_texto:
            QMessageBox.warning(self, "Advertencia", "Debe completar el concepto y el monto.")
            return

        try:
            monto = float(monto_texto)
            if monto <= 0:
                raise ValueError("El monto debe ser un valor positivo.")
        except ValueError as e:
            QMessageBox.warning(self, "Advertencia", f"El monto debe ser un número positivo válido: {e}")
            return

        edit_id = self.btn_agregar_actualizar.property("edit_id")
        fecha_actual = datetime.date.today().strftime("%Y-%m-%d")

        if edit_id is None:
            # Insertar nuevo movimiento
            try:
                # CAMBIO 4: Obtener cliente_id del proceso actual para la inserción
                proceso_actual = self.procesos_model.get_proceso_by_id(self.current_proceso_id)
                if not proceso_actual:
                    QMessageBox.critical(self, "Error", "No se pudo obtener el cliente asociado al proceso.")
                    return
                cliente_id_actual = proceso_actual['cliente_id']

                self.procesos_model.insertar_movimiento_contable(
                    cliente_id=cliente_id_actual, # Se pasa el cliente_id
                    proceso_id=self.current_proceso_id,
                    tipo=tipo_movimiento, # Mapea a 'tipo' en el modelo
                    descripcion=concepto, # Mapea a 'descripcion' en el modelo
                    valor=monto,
                    fecha=fecha_actual
                )
                QMessageBox.information(self, "Éxito", "Movimiento agregado correctamente.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo agregar el movimiento: {e}")
        else:
            # Actualizar movimiento existente
            try:
                # No se necesita cliente_id para actualizar si ya está asociado al movimiento.
                # Se pasan los campos que ProcesosModel.actualizar_movimiento_contable espera.
                self.procesos_model.actualizar_movimiento_contable(
                    movimiento_id=edit_id,
                    proceso_id=self.current_proceso_id, # Se incluye proceso_id
                    tipo=tipo_movimiento, # Mapea a 'tipo' en el modelo
                    descripcion=concepto, # Mapea a 'descripcion' en el modelo
                    valor=monto,
                    fecha=fecha_actual
                )
                QMessageBox.information(self, "Éxito", "Movimiento actualizado correctamente.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo actualizar el movimiento: {e}")
            
        self.load_contabilidad()
        self._reset_formulario()

    def eliminar_movimiento(self):
        selected_items = self.tabla_contabilidad.selectedItems()
        if not selected_items:
            return

        row = selected_items[0].row()
        movimiento_id = self.tabla_contabilidad.item(row, 0).data(Qt.UserRole)
        concepto_a_eliminar = self.tabla_contabilidad.item(row, 2).text()

        if self.current_proceso_id is None:
            QMessageBox.warning(self, "Advertencia", "No hay un proceso seleccionado.")
            return

        respuesta = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Está seguro de eliminar el movimiento '{concepto_a_eliminar}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if respuesta == QMessageBox.Yes:
            try:
                self.procesos_model.eliminar_movimiento_contable(movimiento_id)
                QMessageBox.information(self, "Éxito", "Movimiento eliminado correctamente.")
                self.load_contabilidad()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar el movimiento: {e}")
        
        self._reset_formulario()

    def _reset_formulario(self):
        self.input_concepto.clear()
        self.input_monto.clear()
        self.combo_tipo_movimiento.setCurrentIndex(0)
        self.btn_agregar_actualizar.setText("Agregar Movimiento")
        self.btn_eliminar.setEnabled(False)
        self.btn_agregar_actualizar.setProperty("edit_id", None)
        self.tabla_contabilidad.clearSelection()