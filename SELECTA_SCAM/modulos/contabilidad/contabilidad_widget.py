from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QMessageBox, QHeaderView, QComboBox, QDateEdit, QFileDialog, QTableView,
    QAbstractItemView, QFormLayout, QDialog,
    QListWidget, QListWidgetItem, QGridLayout, QTableWidgetItem
)
from PyQt5.QtCore import Qt, QDate, QAbstractTableModel, QVariant, pyqtSignal, QModelIndex
from PyQt5.QtGui import QColor, QFont
from datetime import date, datetime
import os

from SELECTA_SCAM.modulos.contabilidad.contabilidad_controller import ContabilidadController
from SELECTA_SCAM.modulos.contabilidad.contabilidad_model import ContabilidadModel
from SELECTA_SCAM.modulos.contabilidad.contabilidad_editor_dialog import ContabilidadEditorDialog
from SELECTA_SCAM.modulos.clientes.clientes_logic import ClientesLogic
from SELECTA_SCAM.modulos.procesos.procesos_logic import ProcesosLogic
from .contabilidad_pdf import generar_pdf_resumen_contabilidad
from SELECTA_SCAM.modulos.contabilidad.contabilidad_logic import ContabilidadLogic


class FormatoReporteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar Formato")
        self.formato_seleccionado = None
        
        layout = QVBoxLayout(self)
        label = QLabel("¿En qué formato deseas generar el reporte?")
        layout.addWidget(label)
        
        btn_layout = QHBoxLayout()
        
        self.btn_pdf = QPushButton("PDF")
        self.btn_excel = QPushButton("Excel")
        self.btn_csv = QPushButton("CSV")
        
        self.btn_pdf.clicked.connect(lambda: self.seleccionar_formato("pdf"))
        self.btn_excel.clicked.connect(lambda: self.seleccionar_formato("excel"))
        self.btn_csv.clicked.connect(lambda: self.seleccionar_formato("csv"))
        
        btn_layout.addWidget(self.btn_pdf)
        btn_layout.addWidget(self.btn_excel)
        btn_layout.addWidget(self.btn_csv)
        
        layout.addLayout(btn_layout)

    def seleccionar_formato(self, formato):
        self.formato_seleccionado = formato
        self.accept()


class ContabilidadTableModel(QAbstractTableModel):
    HEADERS = ["ID", "Cliente", "Proceso", "Tipo", "Descripción", "Valor", "Fecha"]
    COLUMN_MAP = {
        "ID": 0, "Cliente": 1, "Proceso": 2, "Tipo": 3, "Descripción": 4, "Valor": 5, "Fecha": 6
    }
    error_occurred = pyqtSignal(str)

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self._headers = ["ID", "Fecha", "Cliente", "Proceso", "Tipo", "Descripción", "Valor"]
        self._data = []

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self.HEADERS)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._data)):
            return QVariant()

        record = self._data[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            try:
                if col == self.COLUMN_MAP["ID"]:
                    return str(record[0])
                elif col == self.COLUMN_MAP["Cliente"]:
                    return str(record[1])
                elif col == self.COLUMN_MAP["Proceso"]:
                    return str(record[2])
                elif col == self.COLUMN_MAP["Tipo"]:
                    return str(record[3])
                elif col == self.COLUMN_MAP["Descripción"]:
                    return str(record[4])
                elif col == self.COLUMN_MAP["Valor"]:
                    return f"${float(record[5]):,.2f}"
                elif col == self.COLUMN_MAP["Fecha"]:
                    return str(record[6])
            except IndexError:
                return "Error de Datos"
        
        elif role == Qt.ForegroundRole:
            try:
                tipo_value = str(record[3]).lower()
                if col == self.COLUMN_MAP["Tipo"]:
                    if "ingreso" in tipo_value:
                        return QColor("#006400")
                    elif "gasto" in tipo_value:
                        return QColor("#8B0000")
                if col == self.COLUMN_MAP["Valor"]:
                    return QColor("#5AA1B9")
            except IndexError:
                pass
        return QVariant()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if 0 <= section < len(self.HEADERS):
                return self.HEADERS[section]
        return QVariant()

    def set_data(self, data):
        self.beginResetModel()
        self._data = data
        self.endResetModel()

    def get_record_id(self, row):
        if 0 <= row < len(self._data):
            return self._data[row][self.COLUMN_MAP["ID"]]
        return None

    def get_record_data(self, row):
        if 0 <= row < len(self._data):
            return self._data[row]
        return None

    def get_all_records(self):
        return self._data

    def load_data(self, cliente_id: int = None, proceso_id: int = None):
        try:
            self._data = self.controller.get_contabilidad_data_for_table(cliente_id, proceso_id)
            self.layoutChanged.emit()
        except Exception as e:
            self.controller.operation_failed.emit(f"Error al cargar datos de tabla: {e}")
            self._data = []
            self.layoutChanged.emit()

class ContabilidadWidget(QWidget):
    def __init__(self, controller: ContabilidadController, clientes_logic: ClientesLogic, procesos_logic: ProcesosLogic, user_data: dict = None, parent=None):
        super().__init__(parent)

        self.controller = controller
        self.user_data = user_data if user_data is not None else {}
        self.clientes_logic = clientes_logic
        self.procesos_logic = procesos_logic
        self.cliente_filter_combo = QComboBox()
        self.setWindowTitle("Contabilidad")
        self.setMinimumSize(1000, 600)

        self.contabilidad_table_model = ContabilidadTableModel(self.controller)
        self.controller.data_updated.connect(self.contabilidad_table_model.set_data)

        self.selected_cliente_id = None
        self.is_search_mode_active = False
        self.cliente_input = QComboBox()
        self.proceso_input = QComboBox()
        self.proceso_input.addItem("Todos los Procesos", None)
        self.proceso_input.currentIndexChanged.connect(self.on_proceso_filter_changed)
        self.proceso_input.setEnabled(False)

        self.tipo_input = QComboBox()

        self.controller.clientes_loaded.connect(self.update_cliente_combo)
        self.controller.procesos_loaded_for_client.connect(self.update_proceso_combo)
        self.controller.tipos_contables_loaded.connect(self.update_tipo_combo)
        self.controller.operation_successful.connect(self.on_operation_successful)
        self.controller.operation_failed.connect(lambda msg: QMessageBox.critical(None, "Error de Operación", msg))
        self.controller.summary_data_loaded.connect(self.update_summary_display)
        self.controller.record_updated.connect(self.reselect_row_by_id)
        self.controller.procesos_loaded_for_dialog.connect(self.handle_procesos_for_dialog)

        self.init_ui()
        self.controller.get_all_clientes_sync()
        self.controller.get_tipos_contables_sync()
        self.update_contabilidad_display()
        self.check_user_permissions()

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)

        self.connect_signals()
    def init_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #F8F0F5; color: #333333; font-family: 'Segoe UI', 'Arial', sans-serif; }
            QLabel#mainTitle { color: #D36B92; font-size: 28px; font-weight: bold; padding-bottom: 15px; border-bottom: 1px solid #E0E0E0; margin-bottom: 20px; padding-top: 10px; }
            QTableView#tablaContabilidad { font-family: 'Segoe UI'; font-size: 24px; background-color: white; border: 1px solid #E0E0E0; gridline-color: #F0F0F0; border-radius: 8px; selection-background-color: #D36B92; selection-color: white; }
            QTableView#tablaContabilidad::item { padding: 8px 10px; }
            QTableView::item:alternate { background-color: #FDF7FA; }
            QHeaderView::section { background-color: #F8F0F5; color: #5D566F; font-size: 18px; font-weight: bold; border-bottom: 2px solid #D36B92; padding: 10px 10px; }
            QHeaderView::section:horizontal { border-right: 1px solid #F0F0F0; }
            QHeaderView::section:last { border-right: none; }
            QLabel#CustomTooltip { background-color: #333333; color: white; border: 1px solid #5D566F; border-radius: 5px; padding: 5px 10px; font-size: 20px; font-weight: bold; }
            QPushButton { background-color: #5D566F; color: white; border-radius: 6px; padding: 12px 25px; font-size: 20px; font-weight: 600; border: none; outline: none; }
            QPushButton:hover { background-color: #7B718D; }
            QPushButton:pressed { background-color: #4A445C; }
            QPushButton:disabled { background-color: #B0B0B0; color: #DDDDDD; }
            QPushButton#btn_agregar { background-color: #D36B92; }
            QPushButton#btn_agregar:hover { background-color: #E279A1; }
            QPushButton#btn_agregar:pressed { background-color: #B85F7F; }
            QPushButton#btn_editar { background-color: #5AA1B9; }
            QPushButton#btn_editar:hover { background-color: #7BC2DA; }
            QPushButton#btn_editar:pressed { background-color: #4E8BA3; }
            QPushButton#btn_eliminar { background-color: #CC5555; }
            QPushButton#btn_eliminar:hover { background-color: #D96666; }
            QPushButton#btn_eliminar:pressed { background-color: #B34444; }
            QPushButton#btn_pdf, QPushButton#btn_generar_resumen_pdf { background-color: #6C757D; }
            QPushButton#btn_pdf:hover, QPushButton#btn_generar_resumen_pdf:hover { background-color: #8D9BA6; }
            QPushButton#btn_pdf:pressed, QPushButton#btn_generar_resumen_pdf:pressed { background-color: #5A6268; }
            QLineEdit, QDateEdit, QComboBox { padding: 10px 15px; border: 1px solid #CED4DA; border-radius: 6px; font-size: 20px; color: #495057; background-color: white; }
            QLineEdit::placeholder { color: #ADB5BD; }
            QComboBox QAbstractItemView { border: 1px solid #D36B92; background-color: white; selection-background-color: #FDF7FA; selection-color: #333333; }
            QLabel { color: #5D566F; font-size: 16px; font-weight: bold; padding-right: 5px; }
        """)

        self.btn_agregar = QPushButton("Agregar")
        self.btn_agregar.setObjectName("btn_agregar")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        self.title_label = QLabel("Gestión de Contabilidad")
        self.title_label.setObjectName("mainTitle")
        self.title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.title_label)

        top_filter_and_action_layout = QHBoxLayout()
        top_filter_and_action_layout.setSpacing(10)
        top_filter_and_action_layout.setAlignment(Qt.AlignLeft)

        top_filter_and_action_layout.addWidget(QLabel("Cliente:"))
        top_filter_and_action_layout.addWidget(self.cliente_filter_combo)

        self.cliente_search_label = QLabel("Buscar Cliente:")
        self.cliente_search_label.hide()
        top_filter_and_action_layout.addWidget(self.cliente_search_label)

        self.cliente_search_input = QLineEdit(self)
        self.cliente_search_input.setPlaceholderText("Buscar cliente por nombre o ID...")
        self.cliente_search_input.hide()
        top_filter_and_action_layout.addWidget(self.cliente_search_input)

        top_filter_and_action_layout.addWidget(QLabel("Tipo:"))
        top_filter_and_action_layout.addWidget(self.tipo_input)

        top_filter_and_action_layout.addWidget(QLabel("Proceso:"))
        top_filter_and_action_layout.addWidget(self.proceso_input)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por descripción...")
        self.search_input.textChanged.connect(self.update_contabilidad_display)
        top_filter_and_action_layout.addWidget(self.search_input)

        self.btn_limpiar_filtros = QPushButton("Limpiar Filtros")
        self.btn_limpiar_filtros.setObjectName("btn_limpiar_filtros")
        top_filter_and_action_layout.addWidget(self.btn_limpiar_filtros)

        top_filter_and_action_layout.addStretch()
        top_filter_and_action_layout.addWidget(self.btn_agregar)
        main_layout.addLayout(top_filter_and_action_layout)

        self.table_view = QTableView()
        self.table_view.setObjectName("tablaContabilidad")
        self.table_view.setMouseTracking(True)
        self.table_view.entered.connect(self.show_custom_tooltip)

        self._last_hovered_index = QModelIndex()
        self.table_view.viewport().installEventFilter(self)

        self.custom_tooltip_label = QLabel(self)
        self.custom_tooltip_label.setObjectName("CustomTooltip")
        self.custom_tooltip_label.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.custom_tooltip_label.hide()

        self.hide_tooltip_timer = QTimer(self)
        self.hide_tooltip_timer.setSingleShot(True)
        self.hide_tooltip_timer.timeout.connect(self.custom_tooltip_label.hide)

        self.table_view.setModel(self.contabilidad_table_model)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.selectionModel().selectionChanged.connect(self.update_action_button_states)
        main_layout.addWidget(self.table_view)

        summary_group_box = QWidget()
        summary_group_box.setStyleSheet("""
            QWidget { background-color: #FDF7FA; border: 1px solid #E0E0E0; border-radius: 8px; padding: 15px; margin-top: 10px; }
            QLabel { font-size: 15px; font-weight: 600; color: #5D566F; }
            QLineEdit { background-color: #FFFFFF; border: 1px solid #CED4DA; border-radius: 4px; padding: 5px; font-size: 15px; color: #333333; }
        """)
        summary_layout = QFormLayout(summary_group_box)
        summary_layout.setContentsMargins(10, 10, 10, 10)
        summary_layout.setSpacing(10)

        self.total_ingresos_label = QLabel("Ingresos Totales:")
        self.total_ingresos_display = QLineEdit("0.00")
        self.total_ingresos_display.setReadOnly(True)
        summary_layout.addRow(self.total_ingresos_label, self.total_ingresos_display)

        self.total_gastos_label = QLabel("Gastos Totales:")
        self.total_gastos_display = QLineEdit("0.00")
        self.total_gastos_display.setReadOnly(True)
        summary_layout.addRow(self.total_gastos_label, self.total_gastos_display)

        self.saldo_label = QLabel("Saldo (Neto):")
        self.saldo_display = QLineEdit("0.00")
        self.saldo_display.setReadOnly(True)
        summary_layout.addRow(self.saldo_label, self.saldo_display)

        main_layout.addWidget(summary_group_box)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.addStretch()

        self.btn_editar = QPushButton("Editar")
        self.btn_editar.setObjectName("btn_editar")
        self.btn_editar.setEnabled(False)
        button_layout.addWidget(self.btn_editar)

        self.btn_eliminar = QPushButton("Eliminar")
        self.btn_eliminar.setObjectName("btn_eliminar")
        self.btn_eliminar.clicked.connect(self.eliminar_contabilidad)
        self.btn_eliminar.setEnabled(False)
        button_layout.addWidget(self.btn_eliminar)

        self.btn_pdf = QPushButton("Generar Reporte")
        self.btn_pdf.setObjectName("btn_pdf")
        button_layout.addWidget(self.btn_pdf)

        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        self.update_action_button_states()
    def handle_controller_error(self, message: str):
        QMessageBox.critical(self, "Error de Operación", message)

    def update_cliente_combo(self, clientes_data: list):
        self.cliente_filter_combo.clear()
        self.cliente_filter_combo.addItem("Seleccione o busque cliente...", None)
        self.cliente_filter_combo.addItem("🔍 Buscar Cliente...", "SEARCH_MODE")
        for cliente in clientes_data:
            self.cliente_filter_combo.addItem(cliente[1], cliente[0])
        self.selected_cliente_id = None
        self.cliente_filter_combo.setCurrentIndex(0)
        self.toggle_cliente_search_mode(False)

    def on_cliente_filter_changed(self, index):
        cliente_id = self.cliente_filter_combo.currentData()
        if cliente_id == "SEARCH_MODE":
            self.toggle_cliente_search_mode(True)
            self.proceso_input.setEnabled(False)
        else:
            self.toggle_cliente_search_mode(False)
            if cliente_id is None:
                self.proceso_input.setEnabled(False)
            else:
                self.proceso_input.setEnabled(True)
                self.controller.get_procesos_for_client_sync(cliente_id)
        self.update_contabilidad_display()

    def show_custom_tooltip(self, index: QModelIndex):
        if not index.isValid():
            self.custom_tooltip_label.hide()
            if self.hide_tooltip_timer.isActive():
                self.hide_tooltip_timer.stop()
            self._last_hovered_index = QModelIndex()
            return
        if self._last_hovered_index == index and self.custom_tooltip_label.isVisible():
            return
        self._last_hovered_index = index
        value = self.contabilidad_table_model.data(index, Qt.DisplayRole)
        tooltip_text = str(value)
        if not tooltip_text:
            self.custom_tooltip_label.hide()
            if self.hide_tooltip_timer.isActive():
                self.hide_tooltip_timer.stop()
            return
        self.custom_tooltip_label.setText(tooltip_text)
        self.custom_tooltip_label.adjustSize()
        rect = self.table_view.visualRect(index)
        global_pos = self.table_view.mapToGlobal(rect.center())
        self.custom_tooltip_label.move(global_pos.x() + 10, global_pos.y() - self.custom_tooltip_label.height() - 5)
        self.custom_tooltip_label.show()
        self.hide_tooltip_timer.stop()
        self.hide_tooltip_timer.start(5000)

    def eventFilter(self, source, event):
        if source == self.table_view.viewport():
            if event.type() == event.MouseMove:
                index = self.table_view.indexAt(event.pos())
                if not index.isValid():
                    self.custom_tooltip_label.hide()
                    if self.hide_tooltip_timer.isActive():
                        self.hide_tooltip_timer.stop()
                    self._last_hovered_index = QModelIndex()
                elif index != self._last_hovered_index:
                    self.show_custom_tooltip(index)
            elif event.type() == event.Leave:
                self.custom_tooltip_label.hide()
                if self.hide_tooltip_timer.isActive():
                    self.hide_tooltip_timer.stop()
                self._last_hovered_index = QModelIndex()
        return super().eventFilter(source, event)

    def on_operation_successful(self, message: str):
        self.update_contabilidad_display()
        QTimer.singleShot(100, lambda: self.contabilidad_table_model.print_internal_data("DESPUÉS de refrescar"))

    def connect_signals(self):
        self.proceso_input.currentIndexChanged.connect(self.on_proceso_filter_changed)
        self.tipo_input.currentIndexChanged.connect(self.on_tipo_filter_changed)
        self.table_view.selectionModel().selectionChanged.connect(self.update_action_button_states)
        self.btn_editar.clicked.connect(self.editar_contabilidad)
        self.btn_eliminar.clicked.connect(self.eliminar_contabilidad)
        self.btn_limpiar_filtros.clicked.connect(self.limpiar_filtros)
        self.btn_pdf.clicked.connect(self.on_generar_reporte_clicked)
        self.btn_agregar.clicked.connect(self.agregar_contabilidad)
        self.cliente_filter_combo.currentIndexChanged.connect(self.on_cliente_filter_changed)
        self.cliente_search_input.textChanged.connect(self.search_timer.start)
        self.search_timer.setInterval(300)

    def limpiar_filtros(self):
        self.cliente_filter_combo.blockSignals(True)
        self.proceso_input.blockSignals(True)
        self.tipo_input.blockSignals(True)
        self.search_input.blockSignals(True)
        self.cliente_search_input.blockSignals(True)
        if self.is_search_mode_active:
            self.toggle_cliente_search_mode(False)
        self.cliente_filter_combo.setCurrentIndex(0)
        self.proceso_input.clear()
        self.proceso_input.addItem("Todos los Procesos", None)
        self.proceso_input.setEnabled(False)
        self.tipo_input.setCurrentIndex(0)
        self.search_input.clear()
        self.cliente_search_input.clear()
        self.cliente_filter_combo.blockSignals(False)
        self.proceso_input.blockSignals(False)
        self.tipo_input.blockSignals(False)
        self.search_input.blockSignals(False)
        self.cliente_search_input.blockSignals(False)
        self.update_contabilidad_display()

    def perform_search(self):
        self.update_contabilidad_display()

    def agregar_contabilidad(self):
        from .contabilidad_editor_dialog import ContabilidadEditorDialog
        clientes_data = self.controller.get_all_clientes_sync()
        procesos_data = self.controller.get_all_procesos_sync()
        tipos_data = self.controller.get_tipos_contables_sync()
        dialog = ContabilidadEditorDialog(
            contabilidad_data=None,
            clientes_data=clientes_data,
            procesos_data=procesos_data,
            tipos_data=tipos_data,
            clientes_logic=self.controller.clientes_logic,
            parent=self
        )
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_values()
            if data:
                current_cliente_filter = self.cliente_filter_combo.currentData()
                current_proceso_filter = self.proceso_input.currentData()
                self.controller.add_record(
                    cliente_id=data.get('cliente_id'),
                    proceso_id=data.get('proceso_id'),
                    tipo_id=data.get('tipo_id'),
                    descripcion=data.get('descripcion'),
                    valor=data.get('valor'),
                    fecha=data.get('fecha'),
                    current_filter_cliente_id=current_cliente_filter,
                    current_filter_proceso_id=current_proceso_filter
                )

    def reselect_row_by_id(self, record_id: int):
        for row in range(self.contabilidad_table_model.rowCount()):
            if self.contabilidad_table_model.get_record_id(row) == record_id:
                self.table_view.clearSelection()
                self.table_view.selectRow(row)
                self.table_view.scrollTo(self.contabilidad_table_model.index(row, 0))
                break

    def toggle_cliente_search_mode(self, enable: bool):
        self.is_search_mode_active = enable
        self.cliente_search_label.setVisible(enable)
        self.cliente_search_input.setVisible(enable)
        if not enable:
            self.cliente_search_input.clear()
        self.cliente_filter_combo.setVisible(not enable)

    def on_tipo_filter_changed(self):
        self.update_contabilidad_display()

    def add_record_button_clicked(self):
        new_cliente_id = self.dialog.cliente_combo.currentData()
        new_proceso_id = self.dialog.proceso_combo.currentData()
        new_tipo_id = self.dialog.tipo_combo.currentData()
        new_descripcion = self.dialog.descripcion_input.text()
        new_valor = float(self.dialog.valor_input.text())
        new_fecha = self.dialog.fecha_edit.date().toPyDate()
        current_filter_cliente_id, current_filter_proceso_id = self._get_current_filter_ids()
        self.controller.add_record(
            new_cliente_id, new_proceso_id, new_tipo_id, new_descripcion, new_valor, new_fecha,
            current_filter_cliente_id=current_filter_cliente_id,
            current_filter_proceso_id=current_filter_proceso_id
        )

    def update_record_button_clicked(self):
        record_id = self.table_model.data(self.table_model.index(selected_row, 0), Qt.UserRole)
        updated_cliente_id = self.dialog.cliente_combo.currentData()
        updated_proceso_id = self.dialog.proceso_combo.currentData()
        updated_tipo_id = self.dialog.tipo_combo.currentData()
        updated_descripcion = self.dialog.descripcion_input.text()
        updated_valor = float(self.dialog.valor_input.text())
        updated_fecha = self.dialog.fecha_edit.date().toPyDate()
        current_filter_cliente_id, current_filter_proceso_id = self._get_current_filter_ids()
        self.controller.update_record(
            record_id, updated_cliente_id, updated_proceso_id, updated_tipo_id,
            updated_descripcion, updated_valor, updated_fecha,
            current_filter_cliente_id=current_filter_cliente_id,
            current_filter_proceso_id=current_filter_proceso_id
        )

    def delete_record_button_clicked(self):
        selected_row = self.table_view.currentIndex().row()
        if selected_row < 0:
            QMessageBox.warning(self, "Advertencia", "Seleccione un registro para eliminar.")
            return
        record_id = self.table_model.data(self.table_model.index(selected_row, 0), Qt.UserRole)
        reply = QMessageBox.question(self, "Confirmar Eliminación",
                                    f"¿Está seguro de que desea eliminar el registro ID {record_id}?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            current_filter_cliente_id, current_filter_proceso_id = self._get_current_filter_ids()
            self.controller.delete_record(
                record_id,
                current_filter_cliente_id=current_filter_cliente_id,
                current_filter_proceso_id=current_filter_proceso_id
            )
    def _get_current_filter_ids(self):
        cliente_id = self.cliente_filter_combo.currentData()
        if cliente_id == -1:
            cliente_id = None
        proceso_id = self.proceso_input.currentData()
        if proceso_id == -1:
            proceso_id = None
        return cliente_id, proceso_id

    def on_proceso_filter_changed(self, index):
        self.update_contabilidad_display()

    def update_proceso_combo(self, procesos_data: list):
        self.proceso_input.blockSignals(True)
        self.proceso_input.clear()
        self.proceso_input.addItem("Sin proceso asociado (opcional)", None)
        for proceso_id, radicado in procesos_data:
            self.proceso_input.addItem(radicado, proceso_id)
        self.proceso_input.setCurrentIndex(0)
        self.proceso_input.blockSignals(False)

    def update_tipo_combo(self, tipos_data: list):
        self.tipo_input.blockSignals(True)
        self.tipo_input.clear()
        self.tipo_input.addItem("Todos los tipos", None)
        for tipo in tipos_data:
            self.tipo_input.addItem(tipo.nombre, tipo.id)
        self.tipo_input.setCurrentIndex(0)
        self.tipo_input.blockSignals(False)

    def on_cliente_selected(self, index):
        cliente_id = self.cliente_filter_combo.itemData(index)
        if cliente_id is None or cliente_id == -1:
            self.update_proceso_combo([])
            self.proceso_input.setEnabled(False)
        else:
            self.proceso_input.setEnabled(True)
        self.update_contabilidad_display()

    def on_proceso_selected(self, index):
        self.update_contabilidad_display()

    def update_summary_display(self, summary_data: dict):
        self.total_ingresos_display.setText(f"${summary_data.get('total_ingresos', 0.0):,.2f}")
        self.total_gastos_display.setText(f"${summary_data.get('total_gastos', 0.0):,.2f}")
        self.saldo_display.setText(f"${summary_data.get('saldo', 0.0):,.2f}")
        saldo_value = summary_data.get('saldo', 0.0)
        if saldo_value < 0:
            self.saldo_display.setStyleSheet("color: red; font-weight: bold;")
        elif saldo_value > 0:
            self.saldo_display.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.saldo_display.setStyleSheet("color: black;")

    def update_contabilidad_display(self):
        try:
            cliente_id = self.cliente_filter_combo.currentData()
            proceso_id = self.proceso_input.currentData()
            tipo_id = self.tipo_input.currentData()
            search_term = self.cliente_search_input.text() if self.is_search_mode_active else self.search_input.text()
            if self.is_search_mode_active:
                cliente_id = None
            self.controller.get_contabilidad_records_sync(
                cliente_id=cliente_id,
                proceso_id=proceso_id,
                search_term=search_term,
                tipo_id=tipo_id
            )
        except Exception as e:
            QMessageBox.critical(self, "Error Crítico", f"No se pudo actualizar la vista: {e}")

    def on_filter_changed(self):
        self.update_contabilidad_display()

    def generar_resumen_pdf(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Guardar Resumen PDF", "", "PDF Files (*.pdf)", options=options)
        if file_name:
            cliente_id = self.cliente_filter_combo.currentData()
            proceso_id = self.proceso_input.currentData()
            search_term = self.cliente_search_input.text()
            tipo_id = self.tipo_input.currentData()
            success = self.controller.generate_summary_pdf(file_name, cliente_id, proceso_id, search_term, tipo_id)
            if success:
                QMessageBox.information(self, "Éxito", "Resumen PDF generado exitosamente.")
            else:
                QMessageBox.warning(self, "Error", "Ocurrió un error al generar el resumen PDF.")

    def load_data(self):
        cliente_id = self.cliente_input.currentData()
        proceso_id = self.proceso_input.currentData()
        self.contabilidad_table_model.load_data(cliente_id, proceso_id)
        self.update_action_button_states()

    def clear_inputs(self):
        self.cliente_input.setCurrentIndex(0)
        self.proceso_input.setCurrentIndex(0)

    def editar_contabilidad(self):
        selection_model = self.table_view.selectionModel()
        if not selection_model.hasSelection():
            QMessageBox.warning(self, "Editar Registro", "Por favor, seleccione un registro para editar.")
            return
        selected_rows = selection_model.selectedRows()
        if len(selected_rows) != 1:
            QMessageBox.warning(self, "Editar Registro", "Por favor, seleccione una sola fila para editar.")
            return
        row = selected_rows[0].row()
        record_id = self.contabilidad_table_model.get_record_id(row)
        if record_id is None:
            return
        datos_para_editar = self.controller.contabilidad_logic.get_contabilidad_record_raw(record_id)
        if not datos_para_editar:
            return
        clientes_data = self.controller.get_all_clientes_sync()
        procesos_data = self.controller.get_all_procesos_sync()
        tipos_data = self.controller.get_tipos_contables_sync()
        dialog = ContabilidadEditorDialog(
            contabilidad_data=datos_para_editar,
            clientes_data=clientes_data,
            procesos_data=procesos_data,
            tipos_data=tipos_data,
            clientes_logic=self.clientes_logic,
            parent=self
        )
        if dialog.exec() == QDialog.Accepted:
            nuevos_valores = dialog.get_values()
            if nuevos_valores:
                try:
                    self.controller.model.update_contabilidad_record(
                        record_id=record_id,
                        cliente_id=nuevos_valores.get('cliente_id'),
                        proceso_id=nuevos_valores.get('proceso_id'),
                        tipo_id=nuevos_valores.get('tipo_id'),
                        descripcion=nuevos_valores.get('descripcion'),
                        valor=nuevos_valores.get('valor'),
                        fecha=nuevos_valores.get('fecha')
                    )
                    self.update_contabilidad_display()
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"No se pudo actualizar el registro: {e}")

    def eliminar_contabilidad(self):
        selection_model = self.table_view.selectionModel()
        if not selection_model.hasSelection():
            QMessageBox.warning(self, "Eliminar Registro", "Por favor, seleccione un registro para eliminar.")
            return
        selected_rows = selection_model.selectedRows()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        record_id = self.contabilidad_table_model.get_record_id(row)
        if record_id is None:
            QMessageBox.critical(self, "Error", "No se pudo obtener el ID del registro seleccionado.")
            return
        cliente_nombre = self.contabilidad_table_model.data(self.contabilidad_table_model.index(row, 1))
        descripcion = self.contabilidad_table_model.data(self.contabilidad_table_model.index(row, 4))
        confirm = QMessageBox.question(
            self, "Confirmar Eliminación",
            f"¿Está seguro de que desea eliminar el registro?\n\nID: {record_id}\nCliente: {cliente_nombre}\nDescripción: {descripcion}",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            self.controller.delete_record(record_id)


    def update_action_button_states(self):
        """
        Habilita/deshabilita los botones de acción basados en la selección
        y los permisos del usuario.
        """
        selected_rows = self.table_view.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0
        user_role = self.user_data.get('role', 'user')
        is_admin = (user_role == 'admin')
        
        # Lógica para Editar (solo 1 fila seleccionada y es admin)
            # Lógica para Editar (solo depende de si hay 1 fila seleccionada)
        self.btn_editar.setEnabled(len(selected_rows) == 1)
        
        # Lógica para Eliminar (solo depende de si hay al menos 1 fila seleccionada)
        self.btn_eliminar.setEnabled(has_selection)
        
        # --- LÍNEA CLAVE CORREGIDA ---
        # Lógica para Agregar (siempre activo si es admin, sin importar la selección)
        self.btn_agregar.setEnabled(True)
        
        # --- El resto del método para calcular los totales se mantiene igual ---
        total_ingresos_seleccion = 0.0
        total_gastos_seleccion = 0.0

        if has_selection:
            for index in selected_rows:
                row = index.row()
                record_data = self.contabilidad_table_model.get_record_data(row)
                if record_data:
                    valor = record_data[self.contabilidad_table_model.COLUMN_MAP["Valor"]]
                    tipo_str = record_data[self.contabilidad_table_model.COLUMN_MAP["Tipo"]]
                    try:
                        if isinstance(valor, str):
                            valor = float(valor.replace('$', '').replace(',', ''))
                        
                        tipo_str_lower = tipo_str.lower()
                        
                        if "ingreso" in tipo_str_lower:
                            total_ingresos_seleccion += valor
                        else:
                            total_gastos_seleccion += valor
                    except (ValueError, IndexError, TypeError) as e:
                        self.logger.warning(f"Error al procesar los datos de la fila seleccionada en la fila {row}. Error: {e}. Datos: {record_data}")
            
            saldo_neto_seleccion = total_ingresos_seleccion - total_gastos_seleccion
            self.total_ingresos_display.setText(f"${total_ingresos_seleccion:,.2f}")
            self.total_gastos_display.setText(f"${total_gastos_seleccion:,.2f}")
            self.saldo_display.setText(f"${saldo_neto_seleccion:,.2f}")
        else:
            # Si no hay nada seleccionado, volvemos a mostrar los totales generales
            self.update_contabilidad_display()
    
    def clear_inputs(self):
        self.cliente_input.blockSignals(True)
        self.proceso_input.blockSignals(True)
        self.cliente_input.setCurrentIndex(0)
        self.proceso_input.setCurrentIndex(0)
        self.cliente_input.blockSignals(False)
        self.proceso_input.blockSignals(False)
        
    def check_user_permissions(self): 
        """
        Ajusta la visibilidad y el estado de los botones de acción basados en el rol del usuario.
        """
        user_role = self.user_data.get('role', 'user')
        is_admin = (user_role == 'admin') # Esta línea sigue para que el log de debug pueda usarla, pero su efecto directo se anula.
        self.btn_agregar.setEnabled(True)
        self.btn_editar.setEnabled(True) 
        self.btn_eliminar.setEnabled(True)
        self.btn_pdf.setEnabled(self.btn_pdf.isEnabled()) 
    
    def handle_procesos_for_dialog(self, procesos_data: list):
        """
        Este método es un slot que recibe los procesos que el controlador
        obtuvo específicamente para el diálogo de edición/adición.
        Si el diálogo está activo, se los pasa.
        """
        if hasattr(self, '_current_dialog_instance') and self._current_dialog_instance:
            self._current_dialog_instance.update_proceso_combo_dialog(procesos_data)
        else:
            logger.warning("ContabilidadWidget: Procesos para diálogo recibidos, pero no hay diálogo activo.")


            # En: SELECTA_SCAM/modulos/contabilidad/contabilidad_widget.py
    # En: SELECTA_SCAM/modulos/contabilidad/contabilidad_widget.py
        # Reemplaza el método completo con este:

    # En: SELECTA_SCAM/modulos/contabilidad/contabilidad_widget.py
# Reemplaza tu método on_btn_pdf_clicked con este:

    def on_generar_reporte_clicked(self):
        """
        Orquesta la generación de reportes. Primero pide al usuario que elija
        un formato (PDF, Excel, CSV) y luego procede a generar el archivo.
        """
        try:
            # 1. Obtener datos y preparar nombre de archivo (lógica que ya funciona)
            cliente_id = self.cliente_filter_combo.currentData()
            tipo_id = self.tipo_input.currentData()
            selected_ids = self.get_selected_record_ids()
            
            nombre_base = ""
            report_data = None

            if selected_ids:
                report_data = self.controller.contabilidad_logic.get_contabilidad_report_data(record_ids=selected_ids)
                if report_data.records:
                    ids_de_clientes = {rec.cliente_id for rec in report_data.records}
                    if len(ids_de_clientes) == 1:
                        cliente_nombre = report_data.records[0].cliente.nombre.replace(" ", "_")
                        nombre_base = f"reporte_consolidado_de_{cliente_nombre}" if len(selected_ids) > 1 else f"reporte_especifico_de_{cliente_nombre}"
                    else:
                        nombre_base = "reporte_general_seleccion_multiple"
                else:
                    nombre_base = "reporte_general"
            else:
                report_data = self.controller.contabilidad_logic.get_contabilidad_report_data(
                    cliente_id=cliente_id, proceso_id=self.proceso_input.currentData(),
                    tipo_id=tipo_id, search_term=self.search_input.text()
                )
                if cliente_id and not tipo_id:
                    nombre_base = f"reporte_consolidado_de_{self.cliente_filter_combo.currentText().replace(' ', '_')}"
                elif cliente_id and tipo_id:
                    nombre_base = f"reporte_de_{self.cliente_filter_combo.currentText().replace(' ', '_')}_por_{self.tipo_input.currentText().replace(' ', '_')}"
                else:
                    nombre_base = "reporte_general"
            
            if not (report_data and report_data.records):
                QMessageBox.information(self, "Sin Datos", "No hay registros para generar el reporte.")
                return

            # 2. Abrir el diálogo para seleccionar el formato
            dialogo_formato = FormatoReporteDialog(self)
            if not dialogo_formato.exec() == QDialog.Accepted:
                return # El usuario cerró el diálogo

            formato = dialogo_formato.formato_seleccionado
            
            # 3. Preparar la ruta de guardado según el formato
            extension, filtro_archivo, funcion_generadora = "", "", None

            if formato == "pdf":
                # Importación local para evitar dependencias circulares si se mueve el archivo
                from .contabilidad_pdf import generar_pdf_resumen_contabilidad
                extension, filtro_archivo, funcion_generadora = "pdf", "Archivos PDF (*.pdf)", generar_pdf_resumen_contabilidad
            
            elif formato == "excel":
                # Asegúrate de haber creado el archivo contabilidad_excel.py
                from .contabilidad_excel import generar_excel_resumen_contabilidad
                extension, filtro_archivo, funcion_generadora = "xlsx", "Archivos Excel (*.xlsx)", generar_excel_resumen_contabilidad
            
            elif formato == "csv":
                # Asegúrate de haber creado el archivo contabilidad_csv.py
                from .contabilidad_csv import generar_csv_resumen_contabilidad
                extension, filtro_archivo, funcion_generadora = "csv", "Archivos CSV (*.csv)", generar_csv_resumen_contabilidad

            nombre_archivo_sugerido = f"{nombre_base}_{datetime.now().strftime('%Y-%m-%d')}.{extension}"
            
            home_dir = os.path.expanduser("~")
            save_dir_es = os.path.join(home_dir, "Descargas")
            save_dir_en = os.path.join(home_dir, "Downloads")
            save_dir = save_dir_es if os.path.isdir(save_dir_es) else (save_dir_en if os.path.isdir(save_dir_en) else home_dir)
            default_path = os.path.join(save_dir, nombre_archivo_sugerido)

            # 4. Mostrar diálogo "Guardar Como" y generar el archivo
            ruta_guardar, _ = QFileDialog.getSaveFileName(self, f"Guardar Reporte {formato.upper()}", default_path, filtro_archivo)

            if ruta_guardar:
                success = funcion_generadora(ruta_guardar, report_data)
                if success:
                    QMessageBox.information(self, "Éxito", f"El reporte se ha guardado exitosamente en:\n{ruta_guardar}")
                else:
                    QMessageBox.critical(self, "Error", f"Ocurrió un error al guardar el reporte en formato {formato.upper()}.")

        except Exception as e:
            self.logger.error(f"Error en el proceso de generación de reporte: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Ocurrió un error inesperado: {e}")


    def get_selected_record_ids(self) -> list:
        """
        Obtiene los IDs de los registros seleccionados en la QTableView.
        """
        selected_ids = []
        selection_model = self.table_view.selectionModel()

        if selection_model:
            selected_rows = set()
            for index in selection_model.selectedRows():
                selected_rows.add(index.row())
            
            # En: contabilidad_widget.py
# Dentro de: def get_selected_record_ids(self):

        # Reemplaza tu bucle 'for' con este:
        for row in selected_rows:
            # CORRECCIÓN: Usamos 'self.table_view' con 'v' minúscula
            id_index = self.table_view.model().index(row, 0)
            record_id = self.table_view.model().data(id_index, Qt.DisplayRole)
            if record_id is not None:
                try:
                    selected_ids.append(int(record_id))
                except (ValueError, TypeError):
                    self.logger.warning(f"No se pudo convertir el ID '{record_id}' a entero en la fila {row}.")
        return selected_ids