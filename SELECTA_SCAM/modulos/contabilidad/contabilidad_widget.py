from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QMessageBox, QHeaderView, QComboBox, QFileDialog, QTableView,
    QAbstractItemView, QFormLayout, QDialog
)
from PyQt5.QtCore import Qt, QAbstractTableModel, QVariant, pyqtSignal, QModelIndex, QTimer
from PyQt5.QtGui import QColor
from datetime import datetime
import os

from SELECTA_SCAM.modulos.contabilidad.contabilidad_controller import ContabilidadController
from SELECTA_SCAM.modulos.contabilidad.contabilidad_editor_dialog import ContabilidadEditorDialog
from SELECTA_SCAM.modulos.clientes.clientes_logic import ClientesLogic
from SELECTA_SCAM.modulos.procesos.procesos_logic import ProcesosLogic


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
    COLUMN_MAP = {"ID": 0, "Cliente": 1, "Proceso": 2, "Tipo": 3, "Descripción": 4, "Valor": 5, "Fecha": 6}

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self._data = []

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
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
            except Exception:
                return "Error"
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
            except Exception:
                pass
        return QVariant()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
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


class ContabilidadWidget(QWidget):
    def __init__(self, controller: ContabilidadController, clientes_logic: ClientesLogic,
                 procesos_logic: ProcesosLogic, user_data: dict = None, parent=None):
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
        self.controller.operation_failed.connect(lambda msg: QMessageBox.critical(self, "Error", msg))
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
        self.btn_agregar.setStyleSheet("QPushButton { background-color: #6CBF84; color: white; border-radius: 6px; padding: 8px 18px; font-size: 15px; font-weight: 600; border: none; } QPushButton:hover { background-color: #5AA870; } QPushButton:pressed { background-color: #4C8C5D; }")
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

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # 📌 Título
        self.title_label = QLabel("Gestión de Contabilidad")
        self.title_label.setObjectName("mainTitle")
        self.title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.title_label)

        # 📌 Filtros y acciones superiores
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)
        top_layout.setAlignment(Qt.AlignLeft)

        top_layout.addWidget(QLabel("Cliente:"))
        top_layout.addWidget(self.cliente_filter_combo)

        self.cliente_search_label = QLabel("Buscar Cliente:")
        self.cliente_search_label.hide()
        top_layout.addWidget(self.cliente_search_label)

        self.cliente_search_input = QLineEdit(self)
        self.cliente_search_input.setPlaceholderText("Buscar cliente por nombre o ID...")
        self.cliente_search_input.hide()
        top_layout.addWidget(self.cliente_search_input)

        top_layout.addWidget(QLabel("Tipo:"))
        top_layout.addWidget(self.tipo_input)

        top_layout.addWidget(QLabel("Proceso:"))
        top_layout.addWidget(self.proceso_input)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por descripción...")
        self.search_input.textChanged.connect(self.update_contabilidad_display)
        top_layout.addWidget(self.search_input)

        self.btn_limpiar_filtros = QPushButton("Limpiar Filtros")
        self.btn_limpiar_filtros.setObjectName("btn_limpiar_filtros")
        top_layout.addWidget(self.btn_limpiar_filtros)

        top_layout.addStretch()
        self.btn_agregar = QPushButton("Agregar")
        self.btn_agregar.setObjectName("btn_agregar")
        top_layout.addWidget(self.btn_agregar)
        main_layout.addLayout(top_layout)

        # 📌 Tabla
        self.table_view = QTableView()
        self.table_view.setObjectName("tablaContabilidad")
        self.table_view.setMouseTracking(True)
        self.table_view.setModel(self.contabilidad_table_model)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_view.verticalHeader().setVisible(False)
        main_layout.addWidget(self.table_view)

        # 📌 Resumen
        summary_group_box = QWidget()
        summary_group_box.setStyleSheet("""
            QWidget { background-color: #FDF7FA; border: 1px solid #E0E0E0; border-radius: 8px; padding: 15px; margin-top: 10px; }
            QLabel { font-size: 15px; font-weight: 600; color: #5D566F; }
            QLineEdit { background-color: #FFFFFF; border: 1px solid #CED4DA; border-radius: 4px; padding: 5px; font-size: 15px; color: #333333; }
        """)
        summary_layout = QFormLayout(summary_group_box)
        summary_layout.setContentsMargins(10, 10, 10, 10)
        summary_layout.setSpacing(10)

        self.total_ingresos_display = QLineEdit("0.00")
        self.total_ingresos_display.setReadOnly(True)
        summary_layout.addRow("Ingresos Totales:", self.total_ingresos_display)

        self.total_gastos_display = QLineEdit("0.00")
        self.total_gastos_display.setReadOnly(True)
        summary_layout.addRow("Gastos Totales:", self.total_gastos_display)

        self.saldo_display = QLineEdit("0.00")
        self.saldo_display.setReadOnly(True)
        summary_layout.addRow("Saldo (Neto):", self.saldo_display)

        main_layout.addWidget(summary_group_box)

        # 📌 Botones inferiores
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        btn_layout.addStretch()

        self.btn_editar = QPushButton("Editar")
        self.btn_editar.setObjectName("btn_editar")
        self.btn_editar.setEnabled(False)
        btn_layout.addWidget(self.btn_editar)

        self.btn_eliminar = QPushButton("Eliminar")
        self.btn_eliminar.setObjectName("btn_eliminar")
        self.btn_eliminar.setEnabled(False)
        btn_layout.addWidget(self.btn_eliminar)

        self.btn_pdf = QPushButton("Generar Reporte")
        self.btn_pdf.setObjectName("btn_pdf")
        btn_layout.addWidget(self.btn_pdf)

        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        # 📌 Tooltip personalizado
        self._last_hovered_index = QModelIndex()
        self.table_view.viewport().installEventFilter(self)

        self.custom_tooltip_label = QLabel(self)
        self.custom_tooltip_label.setObjectName("CustomTooltip")
        self.custom_tooltip_label.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.custom_tooltip_label.hide()

        self.hide_tooltip_timer = QTimer(self)
        self.hide_tooltip_timer.setSingleShot(True)
        self.hide_tooltip_timer.timeout.connect(self.custom_tooltip_label.hide)


    def on_proceso_filter_changed(self, index):
        """
        Maneja el cambio en el filtro de procesos.
        """
        cliente_id = self.cliente_filter_combo.currentData()
        proceso_id = self.proceso_input.currentData()
        self.update_contabilidad_display()



    def update_cliente_combo(self, clientes_data: list):
        self.cliente_filter_combo.clear()
        self.cliente_filter_combo.addItem("Seleccione...", None)
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
            self.proceso_input.setEnabled(cliente_id is not None)
            if cliente_id: self.controller.get_procesos_for_client_sync(cliente_id)
        self.update_contabilidad_display()

    def update_proceso_combo(self, procesos_data: list):
        self.proceso_input.clear()
        self.proceso_input.addItem("Sin proceso asociado", None)
        for proceso_id, radicado in procesos_data:
            self.proceso_input.addItem(radicado, proceso_id)

    def update_tipo_combo(self, tipos_data: list):
        self.tipo_input.clear()
        self.tipo_input.addItem("Todos", None)
        for tipo in tipos_data:
            self.tipo_input.addItem(tipo.nombre, tipo.id)

    def toggle_cliente_search_mode(self, enable: bool):
        self.is_search_mode_active = enable
        self.cliente_search_label.setVisible(enable)
        self.cliente_search_input.setVisible(enable)
        if not enable: self.cliente_search_input.clear()
        self.cliente_filter_combo.setVisible(not enable)

    def update_contabilidad_display(self):
        try:
            cliente_id = self.cliente_filter_combo.currentData()
            proceso_id = self.proceso_input.currentData()
            tipo_id = self.tipo_input.currentData()
            search_term = self.cliente_search_input.text() if self.is_search_mode_active else self.search_input.text()
            if self.is_search_mode_active: cliente_id = None
            self.controller.get_contabilidad_records_sync(
                cliente_id=cliente_id, proceso_id=proceso_id,
                search_term=search_term, tipo_id=tipo_id
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo actualizar la vista: {e}")

    def perform_search(self): self.update_contabilidad_display()

    def on_operation_successful(self, message: str): self.update_contabilidad_display()

    def connect_signals(self):
        self.btn_agregar.clicked.connect(self.agregar_contabilidad)
        self.btn_editar.clicked.connect(self.editar_contabilidad)
        self.btn_eliminar.clicked.connect(self.eliminar_contabilidad)
        self.btn_pdf.clicked.connect(self.on_generar_reporte_clicked)
        self.btn_limpiar_filtros.clicked.connect(self.limpiar_filtros)
        self.cliente_filter_combo.currentIndexChanged.connect(self.on_cliente_filter_changed)
        self.cliente_search_input.textChanged.connect(self.search_timer.start)

    def limpiar_filtros(self):
        self.toggle_cliente_search_mode(False)
        self.cliente_filter_combo.setCurrentIndex(0)
        self.proceso_input.clear(); self.proceso_input.addItem("Todos", None); self.proceso_input.setEnabled(False)
        self.tipo_input.setCurrentIndex(0)
        self.search_input.clear(); self.cliente_search_input.clear()
        self.update_contabilidad_display()

    def agregar_contabilidad(self):
        clientes_data = self.controller.get_all_clientes_sync()
        procesos_data = self.controller.get_all_procesos_sync()
        tipos_data = self.controller.get_tipos_contables_sync()
        dialog = ContabilidadEditorDialog(None, clientes_data, procesos_data, tipos_data, self.controller.clientes_logic, self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_values()
            if data:
                self.controller.add_record(**data)

    def editar_contabilidad(self):
        sel = self.table_view.selectionModel().selectedRows()
        if len(sel) != 1:
            QMessageBox.warning(self, "Editar", "Seleccione un único registro.")
            return
        row = sel[0].row()
        record_id = self.contabilidad_table_model.get_record_id(row)
        if not record_id: return
        datos_para_editar = self.controller.contabilidad_logic.get_contabilidad_record_raw(record_id)
        clientes_data = self.controller.get_all_clientes_sync()
        procesos_data = self.controller.get_all_procesos_sync()
        tipos_data = self.controller.get_tipos_contables_sync()
        dialog = ContabilidadEditorDialog(datos_para_editar, clientes_data, procesos_data, tipos_data, self.clientes_logic, self)
        if dialog.exec() == QDialog.Accepted:
            nuevos = dialog.get_values()
            self.controller.model.update_contabilidad_record(record_id=record_id, **nuevos)
            self.update_contabilidad_display()

    def eliminar_contabilidad(self):
        sel = self.table_view.selectionModel().selectedRows()
        if not sel: return
        row = sel[0].row()
        record_id = self.contabilidad_table_model.get_record_id(row)
        confirm = QMessageBox.question(self, "Eliminar", f"¿Eliminar registro ID {record_id}?",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if confirm == QMessageBox.Yes: self.controller.delete_record(record_id)

    def update_summary_display(self, summary_data: dict):
        self.total_ingresos_display.setText(f"${summary_data.get('total_ingresos', 0.0):,.2f}")
        self.total_gastos_display.setText(f"${summary_data.get('total_gastos', 0.0):,.2f}")
        saldo = summary_data.get('saldo', 0.0)
        self.saldo_display.setText(f"${saldo:,.2f}")
        if saldo < 0: self.saldo_display.setStyleSheet("color:red; font-weight:bold;")
        elif saldo > 0: self.saldo_display.setStyleSheet("color:green; font-weight:bold;")
        else: self.saldo_display.setStyleSheet("color:black;")

    def check_user_permissions(self):
        self.btn_agregar.setEnabled(True)
        self.btn_editar.setEnabled(True)
        self.btn_eliminar.setEnabled(True)

    def handle_procesos_for_dialog(self, procesos_data: list):
        if hasattr(self, '_current_dialog_instance') and self._current_dialog_instance:
            self._current_dialog_instance.update_proceso_combo_dialog(procesos_data)

    def on_generar_reporte_clicked(self):
        try:
            cliente_id = self.cliente_filter_combo.currentData()
            tipo_id = self.tipo_input.currentData()
            report_data = self.controller.contabilidad_logic.get_contabilidad_report_data(
                cliente_id=cliente_id, proceso_id=self.proceso_input.currentData(),
                tipo_id=tipo_id, search_term=self.search_input.text()
            )
            if not (report_data and report_data.records):
                QMessageBox.information(self, "Sin Datos", "No hay registros para generar el reporte.")
                return
            dialogo = FormatoReporteDialog(self)
            if not dialogo.exec() == QDialog.Accepted: return
            formato = dialogo.formato_seleccionado
            if formato == "pdf":
                from .contabilidad_pdf import generar_pdf_resumen_contabilidad
                extension, funcion = "pdf", generar_pdf_resumen_contabilidad
            elif formato == "excel":
                from .contabilidad_excel import generar_excel_resumen_contabilidad
                extension, funcion = "xlsx", generar_excel_resumen_contabilidad
            else:
                from .contabilidad_csv import generar_csv_resumen_contabilidad
                extension, funcion = "csv", generar_csv_resumen_contabilidad
            nombre_sugerido = f"reporte_{datetime.now().strftime('%Y-%m-%d')}.{extension}"
            ruta, _ = QFileDialog.getSaveFileName(self, f"Guardar Reporte {formato.upper()}",
                                                  os.path.join(os.path.expanduser("~"), nombre_sugerido),
                                                  f"Archivos {formato.upper()} (*.{extension})")
            if ruta:
                if funcion(ruta, report_data):
                    QMessageBox.information(self, "Éxito", f"Reporte guardado en:\n{ruta}")
                else:
                    QMessageBox.critical(self, "Error", "Error al guardar reporte.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def get_selected_record_ids(self) -> list:
        ids = []
        sel = self.table_view.selectionModel().selectedRows()
        for idx in sel:
            row = idx.row()
            record_id = self.contabilidad_table_model.get_record_id(row)
            if record_id: ids.append(int(record_id))
        return ids

    def reselect_row_by_id(self, record_id: int):
        for row in range(self.contabilidad_table_model.rowCount()):
            if self.contabilidad_table_model.get_record_id(row) == record_id:
                self.table_view.clearSelection()
                self.table_view.selectRow(row)
                self.table_view.scrollTo(self.contabilidad_table_model.index(row, 0))
                break
