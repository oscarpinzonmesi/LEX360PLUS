import re
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QMessageBox, QHeaderView, QComboBox, QFileDialog, QDateEdit,
    QListWidgetItem, QListWidget, QTabWidget, QStyledItemDelegate,
    QCalendarWidget, QDialog, QFormLayout, QDialogButtonBox, QTableView
)
from PyQt5.QtCore import Qt, QDate, QAbstractTableModel, QVariant, pyqtSignal, QModelIndex
from PyQt5.QtGui import QColor, QFont, QIcon
import os
import webbrowser
from SELECTA_SCAM.modulos.procesos.procesos_contabilidad import ContabilidadTab
from SELECTA_SCAM.modulos.procesos.procesos_documentos import DocumentosTab
from SELECTA_SCAM.modulos.procesos.procesos_model import ProcesosModel
from SELECTA_SCAM.modulos.clientes.clientes_db import ClientesDB

class ProcesosTableModel(QAbstractTableModel):
    error_occurred = pyqtSignal(str)
    def __init__(self, procesos_model_instance, parent=None):
        super().__init__(parent)
        self.procesos_model = procesos_model_instance
        self.headers = [
            'ID', 'Clase Proceso', 'Descripción', 'Estado',
            'Fecha Inicio', 'Fecha Fin', 'Radicado', 'Cliente',
            'ID Cliente', 'Tipo', 'Juzgado', 'Observaciones', 'Activo'
        ]
        self._data = []
        self.load_data()
    def load_data(self, query=None, filtro_estado=None, filtro_cliente_id=None):
        raw_data = self.procesos_model.get_all_procesos()
        filtered_data = []
        for item in raw_data:
            match = True
            if filtro_estado and filtro_estado != "Todos":
                if item.get('estado') != filtro_estado:
                    match = False
            if filtro_cliente_id is not None:
                if item.get('cliente_id') != filtro_cliente_id:
                    match = False
            if query:
                radicado_item = item.get('radicado', '').lower()
                if query.lower() not in radicado_item:
                    match = False
            if match:
                row = [
                    item.get('id'),
                    item.get('nombre'),
                    item.get('descripcion'),
                    item.get('estado'),
                    item.get('fecha_inicio'),
                    item.get('fecha_fin'),
                    item.get('radicado'),
                    item.get('nombre_cliente'),
                    item.get('cliente_id'),
                    item.get('tipo'),
                    item.get('juzgado'),
                    item.get('observaciones'),
                    item.get('activo')
                ]
                filtered_data.append(row)
        self._data = filtered_data
        self.layoutChanged.emit()
    def rowCount(self, parent=None):
        return len(self._data)
    def columnCount(self, parent=None):
        return len(self.headers)
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            if 0 <= index.row() < len(self._data) and \
               0 <= index.column() < len(self.headers):
                return str(self._data[index.row()][index.column()])
        return None
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if 0 <= section < len(self.headers):
                return self.headers[section]
        return None
    def get_proceso_id(self, row):
        if 0 <= row < len(self._data):
            return self._data[row][0]
        return None
    def get_proceso_radicado(self, row):
        if 0 <= row < len(self._data):
            return self._data[row][6]
        return None

class ProcesosWidget(QWidget):
    def __init__(self, procesos_model_instance: ProcesosModel, clientes_db_instance: ClientesDB, user_data: dict = None, parent=None):
        super().__init__(parent)
        self.procesos_model_db = procesos_model_instance
        self.clientes_db = clientes_db_instance
        self.user_data = user_data
        self.procesos_table_model = self.procesos_model_db
        self.procesos_table_model.error_occurred.connect(self.handle_model_error)
        self.procesos_table_model.HEADERS = [
            'ID', 'Radicado', 'Tipo', 'Cliente', 'Fecha Inicio', 'Fecha Fin',
            'Estado', 'Juzgado', 'Observaciones', 'Fecha Creación', 'Eliminado'
        ]
        self.selected_proceso_id = None
        self.init_ui()
        self.load_data()
    def init_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #F8F0F5;
                color: #333333;
                font-family: 'Segoe UI', 'Arial', sans-serif;
            }
            QLabel#mainTitle {
                color: #D36B92;
                font-size: 28px;
                font-weight: bold;
                padding-bottom: 15px;
                border-bottom: 1px solid #E0E0E0;
                margin-bottom: 20px;
                padding-top: 10px;
            }
            QTableView {
                background-color: white;
                border: 1px solid #E0E0E0;
                gridline-color: #F0F0F0;
                border-radius: 8px;
                selection-background-color: #D36B92;
                selection-color: white;
            }
            QTableView::item {
                padding: 8px 10px;
                font-size: 15px;
            }
            QTableView::item:alternate {
                background-color: #FDF7FA;
            }
            QHeaderView::section {
                background-color: #F8F0F5;
                color: #5D566F;
                font-size: 16px;
                font-weight: bold;
                border-bottom: 2px solid #D36B92;
                padding: 10px 10px;
            }
            QHeaderView::section:horizontal {
                border-right: 1px solid #F0F0F0;
            }
            QHeaderView::section:last {
                border-right: none;
            }
            QPushButton {
                background-color: #5D566F;
                color: white;
                border-radius: 6px;
                padding: 12px 25px;
                font-size: 15px;
                font-weight: 600;
                border: none;
                outline: none;
            }
            QPushButton:hover {
                background-color: #7B718D;
            }
            QPushButton:pressed {
                background-color: #4A445C;
            }
            QPushButton:disabled {
                background-color: #B0B0B0;
                color: #DDDDDD;
            }
            QPushButton#btn_nuevo_proceso, QPushButton#btn_toggle_form {
                background-color: #D36B92;
            }
            QPushButton#btn_nuevo_proceso:hover, QPushButton#btn_toggle_form:hover {
                background-color: #E279A1;
            }
            QPushButton#btn_nuevo_proceso:pressed, QPushButton#btn_toggle_form:pressed {
                background-color: #B85F7F;
            }
            QPushButton#btn_editar_proceso, QPushButton#btn_editar {
                background-color: #5AA1B9;
            }
            QPushButton#btn_editar_proceso:hover, QPushButton#btn_editar:hover {
                background-color: #7BC2DA;
            }
            QPushButton#btn_editar_proceso:pressed, QPushButton#btn_editar:pressed {
                background-color: #4E8BA3;
            }
            QPushButton#btn_micrositios {
                background-color: #5D566F;
            }
            QPushButton#btn_micrositios:hover {
                background-color: #7B718D;
            }
            QPushButton#btn_micrositios:pressed {
                background-color: #4A445C;
            }
            QLineEdit {
                padding: 10px 15px;
                border: 1px solid #CED4DA;
                border-radius: 6px;
                font-size: 16px;
                color: #495057;
                background-color: white;
            }
            QLineEdit::placeholder {
                color: #ADB5BD;
            }
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #CED4DA;
                border-radius: 6px;
                font-size: 16px;
                background-color: white;
                selection-background-color: #D36B92;
                selection-color: white;
            }
            QComboBox::drop-down {
                border-left: 1px solid #CED4DA;
                width: 25px;
            }
            QDialog {
                background-color: #F8F0F5;
                color: #333333;
                font-family: 'Segoe UI', 'Arial', sans-serif;
            }
            QDialog QPushButton {
                background-color: #5D566F;
                color: white;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 14px;
            }
            QDialog QPushButton:hover {
                background-color: #7B718D;
            }
            QDialog QPushButton:pressed {
                background-color: #4A445C;
            }
            QDialog QLabel {
                color: #333333;
                font-size: 16px;
            }
            QDialog QLineEdit, QDialog QDateEdit {
                border: 1px solid #CED4DA;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 14px;
            }
            QDialog QDateEdit::drop-down {
                border-left: 1px solid #CED4DA;
                width: 25px;
            }
        """)
        self.setWindowTitle("Gestión de Procesos")
        self.setFont(QFont("Segoe UI", 12))
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        self.label = QLabel("Lista de Procesos")
        self.label.setObjectName("mainTitle")
        self.label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.label)
        filtro_layout = QHBoxLayout()
        filtro_layout.setSpacing(10)
        filtro_layout.addWidget(QLabel("Estado:"))
        self.filtro_estado = QComboBox()
        self.filtro_estado.addItems(["Todos", "Activo", "Finalizado", "Archivado"])
        self.filtro_estado.currentTextChanged.connect(self.filtrar_tabla)
        filtro_layout.addWidget(self.filtro_estado)
        filtro_layout.addWidget(QLabel("Cliente:"))
        self.filtro_cliente = QComboBox()
        self.filtro_cliente.addItem("Todos", None)
        try:
            clientes = self.clientes_db.get_all_clientes()
            for cliente in clientes:
                if isinstance(cliente, dict) and 'nombre_cliente' in cliente:
                    self.filtro_cliente.addItem(cliente['nombre_cliente'], cliente.get('id_cliente'))
                elif isinstance(cliente, (list, tuple)) and len(cliente) > 1:
                    self.filtro_cliente.addItem(str(cliente[1]), cliente[0])
                else:
                    print(f"Advertencia: Formato de cliente inesperado en filtro: {cliente}")
                    if hasattr(cliente, 'nombre_cliente') and hasattr(cliente, 'id_cliente'):
                        self.filtro_cliente.addItem(cliente.nombre_cliente, cliente.id_cliente)
                    else:
                        self.filtro_cliente.addItem(str(cliente), None)
        except Exception as e:
            QMessageBox.warning(self, "Error de Carga", f"No se pudieron cargar los clientes para el filtro: {e}")
        self.filtro_cliente.currentTextChanged.connect(self.filtrar_tabla)
        filtro_layout.addWidget(self.filtro_cliente)
        filtro_layout.addWidget(QLabel("Radicado:"))
        self.filtro_radicado = QLineEdit()
        self.filtro_radicado.setPlaceholderText("Buscar por radicado...")
        self.filtro_radicado.textChanged.connect(self.filtrar_tabla)
        filtro_layout.addWidget(self.filtro_radicado)
        main_layout.addLayout(filtro_layout)
        self.table_view = QTableView()
        self.table_view.setModel(self.procesos_table_model)
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setEditTriggers(QTableView.NoEditTriggers)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.selectionModel().selectionChanged.connect(self._actualizar_seleccion_proceso_desde_tabla)
        main_layout.addWidget(self.table_view)
        actuacion_form_layout = QFormLayout()
        actuacion_form_layout.setContentsMargins(0, 0, 0, 0)
        actuacion_form_layout.setHorizontalSpacing(5)
        actuacion_form_layout.setVerticalSpacing(10)
        self.combo_categoria = QComboBox()
        self.combo_categoria.addItem("Seleccione una categoría")
        try:
            self.combo_categoria.addItems(list(self.procesos_model_db.obtener_actuaciones_por_categoria().keys()))
        except Exception as e:
            print(f"Advertencia: No se pudo cargar categorías de actuación: {e}")
            self.combo_categoria.addItem("Error al cargar categorías")
        self.combo_categoria.currentTextChanged.connect(self.actualizar_tipos_de_actuacion)
        actuacion_form_layout.addRow("Categoría de Actuación:", self.combo_categoria)
        self.combo_tipo_actuacion = QComboBox()
        actuacion_form_layout.addRow("Tipo de Actuación:", self.combo_tipo_actuacion)
        wrapper_actuacion_layout = QHBoxLayout()
        wrapper_actuacion_layout.addLayout(actuacion_form_layout)
        wrapper_actuacion_layout.addStretch()
        main_layout.addLayout(wrapper_actuacion_layout)
        buttons_layout_top = QHBoxLayout()
        buttons_layout_top.addStretch()
        self.btn_nuevo_proceso = QPushButton("Nuevo Proceso")
        self.btn_nuevo_proceso.setObjectName("btn_nuevo_proceso")
        self.btn_nuevo_proceso.clicked.connect(self.crear_nuevo_proceso)
        buttons_layout_top.addWidget(self.btn_nuevo_proceso)
        self.btn_editar_proceso = QPushButton("Editar Proceso")
        self.btn_editar_proceso.setObjectName("btn_editar_proceso")
        self.btn_editar_proceso.clicked.connect(self.editar_proceso)
        self.btn_editar_proceso.setEnabled(False)
        buttons_layout_top.addWidget(self.btn_editar_proceso)
        buttons_layout_top.addStretch()
        main_layout.addLayout(buttons_layout_top)
        micrositios_layout = QHBoxLayout()
        micrositios_layout.setSpacing(10)
        micrositios_layout.addStretch()
        micrositios_layout.addWidget(QLabel("Radicado:"))
        self.radicado_mostrar = QLineEdit()
        self.radicado_mostrar.setReadOnly(True)
        micrositios_layout.addWidget(self.radicado_mostrar)
        self.selector_micrositio = QComboBox()
        self.selector_micrositio.addItems(["Selecciona Micrositio", "Tyba", "Samai", "Fiscalía", "CPNU", "Estados"])
        micrositios_layout.addWidget(self.selector_micrositio)
        self.btn_micrositios = QPushButton("Abrir Micrositio")
        self.btn_micrositios.setObjectName("btn_micrositios")
        self.btn_micrositios.setEnabled(False)
        self.btn_micrositios.clicked.connect(self.abrir_micrositio)
        micrositios_layout.addWidget(self.btn_micrositios)
        micrositios_layout.addStretch()
        main_layout.addLayout(micrositios_layout)
        self.tabs = QTabWidget()
        self.tab_documentos = DocumentosTab(self.procesos_model_db, parent=self)
        self.tab_contabilidad = ContabilidadTab(self.procesos_model_db, parent=self)
        self.tabs.addTab(self.tab_documentos, "Documentos")
        self.tabs.addTab(self.tab_contabilidad, "Contabilidad")
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)
        self._actualizar_seleccion_proceso_desde_tabla()
    def handle_model_error(self, message: str):
        QMessageBox.critical(self, "Error de Operación", message)
    def actualizar_tipos_de_actuacion(self, categoria):
        self.combo_tipo_actuacion.clear()
        if categoria and categoria != "Seleccione una categoría":
            tipos = self.procesos_model_db.obtener_actuaciones_por_categoria().get(categoria, [])
            self.combo_tipo_actuacion.addItems(tipos)
    def filtrar_tabla(self):
        filtro_estado = self.filtro_estado.currentText()
        filtro_cliente_id = self.filtro_cliente.currentData()
        query_radicado = self.filtro_radicado.text()
        self.procesos_table_model.load_data(
            query=query_radicado,
            filtro_estado=filtro_estado,
            filtro_cliente_id=filtro_cliente_id
        )
    def load_data(self):
        self.procesos_table_model.load_data()
    def _actualizar_seleccion_proceso_desde_tabla(self):
        selected_indexes = self.table_view.selectionModel().selectedRows()
        if not selected_indexes:
            self.selected_proceso_id = None
            self.radicado_mostrar.clear()
            self.btn_micrositios.setEnabled(False)
            self.tab_documentos.set_proceso_id(None)
            self.tab_contabilidad.set_proceso_id(None)
            self.btn_editar_proceso.setEnabled(False)
            return
        row = selected_indexes[0].row()
        self.selected_proceso_id = self.procesos_table_model.get_proceso_id(row)
        radicado_seleccionado = self.procesos_table_model.get_proceso_radicado(row)
        if self.selected_proceso_id:
            self.radicado_mostrar.setText(radicado_seleccionado)
            self.btn_micrositios.setEnabled(True)
            self.btn_editar_proceso.setEnabled(True)
            if hasattr(self.tab_documentos, 'set_proceso_id'):
                self.tab_documentos.set_proceso_id(self.selected_proceso_id)
            if hasattr(self.tab_contabilidad, 'set_proceso_id'):
                self.tab_contabilidad.set_proceso_id(self.selected_proceso_id)
        else:
            self.selected_proceso_id = None
            self.radicado_mostrar.clear()
            self.btn_micrositios.setEnabled(False)
            self.tab_documentos.set_proceso_id(None)
            self.tab_contabilidad.set_proceso_id(None)
            self.btn_editar_proceso.setEnabled(False)
    def crear_nuevo_proceso(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Nuevo Proceso")
        layout = QFormLayout(dialog)
        radicado_input = QLineEdit()
        cliente_cb = QComboBox()
        try:
            clientes = self.clientes_db.get_all_clientes()
            for cliente in clientes:
                if isinstance(cliente, dict) and 'nombre_cliente' in cliente:
                    cliente_cb.addItem(cliente['nombre_cliente'], cliente.get('id_cliente'))
                elif isinstance(cliente, (list, tuple)) and len(cliente) > 1:
                    cliente_cb.addItem(str(cliente[1]), cliente[0])
                else:
                    print(f"Advertencia: Formato de cliente inesperado al crear proceso: {cliente}")
                    if hasattr(cliente, 'nombre_cliente') and hasattr(cliente, 'id_cliente'):
                        cliente_cb.addItem(cliente.nombre_cliente, cliente.id_cliente)
                    else:
                        cliente_cb.addItem(str(cliente), None)
        except Exception as e:
            QMessageBox.critical(self, "Error de Clientes", f"No se pudieron cargar los clientes: {e}")
        tipo_input = QLineEdit()
        descripcion_input = QLineEdit()
        juzgado_input = QLineEdit()
        estado_cb = QComboBox()
        estado_cb.addItems(["Activo", "Finalizado", "Archivado"])
        fecha_inicio_input = QDateEdit()
        fecha_inicio_input.setCalendarPopup(True)
        fecha_inicio_input.setDate(QDate.currentDate())
        fecha_fin_input = QDateEdit()
        fecha_fin_input.setCalendarPopup(True)
        fecha_fin_input.setDate(QDate(1900, 1, 1))
        layout.addRow("Cliente:", cliente_cb)
        layout.addRow("Radicado:", radicado_input)
        layout.addRow("Clase de Proceso:", tipo_input)
        layout.addRow("Descripción:", descripcion_input)
        layout.addRow("Juzgado:", juzgado_input)
        layout.addRow("Estado:", estado_cb)
        layout.addRow("Fecha Inicio:", fecha_inicio_input)
        layout.addRow("Fecha Fin:", fecha_fin_input)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addRow(buttons)
        def aceptar():
            cliente_id = cliente_cb.currentData()
            radicado = radicado_input.text().strip()
            clase_proceso = tipo_input.text().strip()
            descripcion = descripcion_input.text().strip()
            juzgado = juzgado_input.text().strip()
            estado = estado_cb.currentText()
            fecha_inicio = fecha_inicio_input.date().toString("yyyy-MM-dd")
            fecha_fin_qdate = fecha_fin_input.date()
            fecha_fin = None
            if fecha_fin_qdate != QDate(1900, 1, 1):
                fecha_fin = fecha_fin_qdate.toString("yyyy-MM-dd")
            if not all([cliente_id, radicado, clase_proceso, descripcion, juzgado, estado, fecha_inicio]):
                QMessageBox.warning(self, "Campos incompletos", "Complete todos los campos obligatorios (excepto Fecha Fin, que es opcional).")
                return
            try:
                self.procesos_model_db.insertar_proceso(cliente_id, radicado, clase_proceso, descripcion, juzgado, estado, fecha_inicio, fecha_fin)
                dialog.accept()
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo agregar el proceso: {e}")
        buttons.accepted.connect(aceptar)
        buttons.rejected.connect(dialog.reject)
        dialog.exec_()
    def editar_proceso(self):
        selected_indexes = self.table_view.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self, 'Atención', 'No se ha seleccionado ningún proceso para editar.')
            return
        row = selected_indexes[0].row()
        proceso_id = self.procesos_table_model.get_proceso_id(row)
        proceso_data = self.procesos_model_db.get_proceso_by_id(proceso_id)
        if not proceso_data:
            QMessageBox.critical(self, "Error", "No se pudo cargar el proceso seleccionado para edición.")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Editar Proceso")
        layout = QFormLayout(dialog)
        cliente_cb = QComboBox()
        try:
            clientes = self.clientes_db.get_all_clientes()
            cliente_actual_index = -1
            for i, cliente in enumerate(clientes):
                current_id = None
                current_name = ""
                if isinstance(cliente, dict) and 'nombre_cliente' in cliente:
                    current_id = cliente.get('id_cliente')
                    current_name = cliente['nombre_cliente']
                elif isinstance(cliente, (list, tuple)) and len(cliente) > 1:
                    current_id = cliente[0]
                    current_name = str(cliente[1])
                cliente_cb.addItem(current_name, current_id)
                if current_id == proceso_data.get('cliente_id'):
                    cliente_actual_index = i
            if cliente_actual_index != -1:
                cliente_cb.setCurrentIndex(cliente_actual_index)
        except Exception as e:
            QMessageBox.critical(self, "Error de Clientes", f"No se pudieron cargar los clientes para edición: {e}")
        radicado_input = QLineEdit(proceso_data.get('radicado', ''))
        tipo_input = QLineEdit(proceso_data.get('nombre', ''))
        descripcion_input = QLineEdit(proceso_data.get('descripcion', ''))
        juzgado_input = QLineEdit(proceso_data.get('juzgado', ''))
        estado_cb = QComboBox()
        estado_cb.addItems(["Activo", "Finalizado", "Archivado"])
        estado_cb.setCurrentText(proceso_data.get('estado', ''))
        fecha_inicio_input = QDateEdit()
        fecha_inicio_input.setCalendarPopup(True)
        fecha_inicio_str = proceso_data.get('fecha_inicio', '')
        if fecha_inicio_str:
            fecha_inicio_qdate = QDate.fromString(fecha_inicio_str, "yyyy-MM-dd")
            if fecha_inicio_qdate.isValid():
                fecha_inicio_input.setDate(fecha_inicio_qdate)
            else:
                fecha_inicio_input.setDate(QDate.currentDate())
        else:
            fecha_inicio_input.setDate(QDate.currentDate())
        fecha_fin_input = QDateEdit()
        fecha_fin_input.setCalendarPopup(True)
        fecha_fin_str = proceso_data.get('fecha_fin', '')
        if fecha_fin_str:
            fecha_fin_qdate = QDate.fromString(fecha_fin_str, "yyyy-MM-dd")
            if fecha_fin_qdate.isValid():
                fecha_fin_input.setDate(fecha_fin_qdate)
            else:
                fecha_fin_input.setDate(QDate(1900, 1, 1))
        else:
            fecha_fin_input.setDate(QDate(1900, 1, 1))
        layout.addRow("Cliente:", cliente_cb)
        layout.addRow("Radicado:", radicado_input)
        layout.addRow("Clase de Proceso:", tipo_input)
        layout.addRow("Descripción:", descripcion_input)
        layout.addRow("Juzgado:", juzgado_input)
        layout.addRow("Estado:", estado_cb)
        layout.addRow("Fecha Inicio:", fecha_inicio_input)
        layout.addRow("Fecha Fin:", fecha_fin_input)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addRow(buttons)
        def aceptar_edicion():
            updated_cliente_id = cliente_cb.currentData()
            updated_radicado = radicado_input.text().strip()
            updated_clase_proceso = tipo_input.text().strip()
            updated_descripcion = descripcion_input.text().strip()
            updated_juzgado = juzgado_input.text().strip()
            updated_estado = estado_cb.currentText()
            updated_fecha_inicio = fecha_inicio_input.date().toString("yyyy-MM-dd")
            updated_fecha_fin_qdate = fecha_fin_input.date()
            updated_fecha_fin = None
            if updated_fecha_fin_qdate != QDate(1900, 1, 1):
                updated_fecha_fin = updated_fecha_fin_qdate.toString("yyyy-MM-dd")
            if not all([updated_cliente_id, updated_radicado, updated_clase_proceso, updated_descripcion, updated_juzgado, updated_estado, updated_fecha_inicio]):
                QMessageBox.warning(self, "Campos incompletos", "Complete todos los campos obligatorios (excepto Fecha Fin, que es opcional).")
                return
            try:
                self.procesos_model_db.actualizar_proceso(
                    proceso_id,
                    updated_cliente_id,
                    updated_radicado,
                    updated_clase_proceso,
                    updated_descripcion,
                    updated_juzgado,
                    updated_estado,
                    updated_fecha_inicio,
                    updated_fecha_fin
                )
                dialog.accept()
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo actualizar el proceso: {e}")
        buttons.accepted.connect(aceptar_edicion)
        buttons.rejected.connect(dialog.reject)
        dialog.exec_()
    def abrir_micrositio(self):
        micrositio = self.selector_micrositio.currentText()
        radicado = self.radicado_mostrar.text().strip()
        if not radicado:
            QMessageBox.warning(self, "Información Faltante", "Por favor, seleccione un proceso con un número de radicado para abrir un micrositio.")
            return
        base_urls = {
            "Tyba": "https://www.ejemplo.com/tyba?radicado=",
            "Samai": "https://www.ejemplo.com/samai?radicado=",
            "Fiscalía": "https://www.ejemplo.com/fiscalia?radicado=",
            "CPNU": "https://www.ejemplo.com/cpnu?radicado=",
            "Estados": "https://www.ejemplo.com/estados?radicado="
        }
        if micrositio == "Selecciona Micrositio":
            QMessageBox.warning(self, "Selección Inválida", "Por favor, seleccione un micrositio de la lista.")
            return
        url = base_urls.get(micrositio)
        if url:
            full_url = f"{url}{radicado}"
            try:
                webbrowser.open_new_tab(full_url)
                print(f"Abriendo: {full_url}")
            except Exception as e:
                QMessageBox.critical(self, "Error al Abrir", f"No se pudo abrir el enlace: {e}\nURL: {full_url}")
        else:
            QMessageBox.error(self, "URL No Encontrada", f"No se ha configurado una URL para el micrositio: {micrositio}")