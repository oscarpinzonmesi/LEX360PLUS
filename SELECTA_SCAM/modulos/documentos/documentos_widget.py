import os
import logging
import datetime
from datetime import datetime, date
from .visor_documento_dialog import VisorDocumentoDialog
from .editar_documento_dialog import EditarDocumentoDialog
import traceback
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QCheckBox, QListWidget, QListWidgetItem,
    QTableView,
    QSizePolicy,
    QFileDialog,
    QAbstractItemView,
    QDialog
)
from PyQt5.QtCore import (
    Qt, QModelIndex, QTimer,
    QAbstractTableModel,
    pyqtSignal,
    QEvent, QVariant
)
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtCore import Qt

from PyQt5.QtGui import QFont, QColor, QFontMetrics
from SELECTA_SCAM.modulos.documentos.documentos_controller import DocumentosController
from SELECTA_SCAM.modulos.clientes.clientes_logic import ClientesLogic
from SELECTA_SCAM.modulos.documentos.documentos_utils import color_por_extension
from SELECTA_SCAM.modulos.documentos.documentos_logic import DocumentosLogic
logger = logging.getLogger(__name__)


# En la parte superior de documentos_widget.py

# Paleta de colores para tipos de archivo
FILE_TYPE_COLORS = {
    'PDF': '#D92D28',  # Rojo Adobe
    'DOC': '#2B579A',  # Azul Word
    'DOCX': '#2B579A',
    'XLS': '#1D6F42',  # Verde Excel
    'XLSX': '#1D6F42',
    'PPT': '#D24726',  # Naranja PowerPoint
    'PPTX': '#D24726',
    'TXT': '#555555',  # Gris oscuro
    'PNG': '#007BFF',  # Azul genérico para imágenes
    'JPG': '#007BFF',
    'JPEG': '#007BFF',
}


class DocumentosTableModel(QAbstractTableModel):
    HEADERS = ["ID Cliente", 'ID', 'Cliente', 'Nombre Documento', 'Tipo Archivo', 'Tipo Documento', 'Fecha Carga', 'Ubicación Archivo', 'Eliminado']

    error_occurred = pyqtSignal(str)

    def __init__(self, documentos_logic_instance, parent=None):
        super().__init__(parent)
        self.documentos_logic = documentos_logic_instance
        self._data = [] # _data ahora será una lista de tuplas

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self.HEADERS)





    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._data)):
            return None

        doc_tuple = self._data[index.row()]
        col_name = self.HEADERS[index.column()]

        # Lógica para mostrar el TEXTO de cada celda
        if role == Qt.DisplayRole:
            try:
                # El orden de la tupla ahora es:
                # 0:cliente_id, 1:id, 2:cliente_nombre, 3:nombre_doc, 4:ubicacion, 5:tipo_doc, 6:fecha, 7:ruta_completa, 8:eliminado

                if col_name == 'ID Cliente': return str(doc_tuple[0])
                elif col_name == 'ID': return str(doc_tuple[1])
                elif col_name == 'Cliente': return str(doc_tuple[2])
                elif col_name == 'Nombre Documento': return str(doc_tuple[3])
                elif col_name == 'Tipo Archivo':
                    ubicacion = doc_tuple[4]
                    return os.path.splitext(ubicacion)[1].upper().replace('.', '') if ubicacion else "N/A"
                elif col_name == 'Tipo Documento': return str(doc_tuple[5])
                elif col_name == 'Fecha Carga':
                    value = doc_tuple[6]
                    # Usamos el formato completo con hora y segundos
                    return value.strftime("%Y-%m-%d %H:%M:%S") if isinstance(value, datetime) else str(value or "")
                elif col_name == 'Ubicación Archivo': return str(doc_tuple[7])
                elif col_name == 'Eliminado': return "Sí" if doc_tuple[8] else "No"

            except IndexError:
                return ""

        # Lógica para pintar el COLOR del texto
        elif role == Qt.ForegroundRole:
            if col_name == 'Tipo Archivo':
                try:
                    ubicacion = doc_tuple[4] # La ubicación está en el índice 4
                    if ubicacion and isinstance(ubicacion, str):
                        extension = os.path.splitext(ubicacion)[1].upper().replace('.', '')
                        color_hex = FILE_TYPE_COLORS.get(extension, "#000000")
                        return QColor(color_hex)
                except IndexError:
                    pass

        return None
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.HEADERS[section]
        return None

    def get_id_from_row(self, row):
        """Devuelve el ID del documento en una fila específica."""
        if 0 <= row < len(self._data):
            return self._data[row][0] # El ID siempre está en la primera posición
        return None
        
    def set_data(self, data):
        """Método clave para recibir los datos y refrescar la tabla."""
        self.beginResetModel()
        self._data = data
        self.endResetModel()

    def load_data(self, **filters):
        """Refresca la tabla pidiendo los datos a la capa de lógica."""
        self.beginResetModel()
        self._data = self.documentos_logic.get_documentos_para_tabla(**filters)
        self.endResetModel()

    # En la clase DocumentosTableModel

    def get_documento_id(self, row):
        """Devuelve el ID del documento leyendo desde la tupla de datos."""
        if 0 <= row < len(self._data):
            # El ID del documento está en el índice 1 de la tupla
            return self._data[row][1] 
        return None

    def get_documento_path(self, row):
        """Devuelve la ruta del archivo leyendo desde la tupla de datos."""
        if 0 <= row < len(self._data):
            # La ubicación del archivo está en el índice 6 de la tupla
            return self._data[row][6]
        return None
    def get_document_id(self, row: int) -> int | None:
        """
        Devuelve el ID del documento en la fila dada.
        """
        if 0 <= row < len(self._data):   # Asumiendo que self._data guarda las tuplas
            return self._data[row][1]    # Columna 1 = Documento.id
        return None


class DocumentosModule(QWidget):
    def __init__(self, documentos_db_instance, clientes_logic_instance, user_data: dict, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.documentos_db = documentos_db_instance
        self.clientes_logic = clientes_logic_instance
        self.user_data = user_data

        # Estado UI
        self.ruta_archivo_seleccionado = None
        self.mostrando_papelera = False
        self.is_editing = False
        self.modo_busqueda_en_carga = False
        self.selected_cliente_id_para_carga = None

        # Lógica y controlador
        self.documentos_logic = DocumentosLogic(self.documentos_db)
        self.controller = DocumentosController(
            self.documentos_db,
            self.clientes_logic,
            user_data=self.user_data
        )

        # Modelo + tabla
        self.documentos_model = DocumentosTableModel(self.documentos_logic)
        self.tabla_documentos = QTableView(self)
        self.tabla_documentos.setObjectName("tabla_documentos")
        self.logger.info("DocumentosModule inicializado y datos iniciales cargados.")
        self.tabla_documentos.setModel(self.documentos_model)
        self.tabla_documentos.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tabla_documentos.horizontalHeader().setStretchLastSection(False)
        self.tabla_documentos.setSelectionBehavior(QTableView.SelectRows)
        self.tabla_documentos.setSelectionMode(QTableView.SingleSelection)
        self.tabla_documentos.selectionModel().selectionChanged.connect(self.on_table_selection_changed)
        self.tabla_documentos.setAlternatingRowColors(False)

        # Señales del controlador/modelo
        self.controller.documentos_cargados.connect(self.update_document_table)
        self.controller.clientes_cargados.connect(lambda lista: self.cargar_clientes_en_combo(lista, include_search_option=True))
        self.documentos_model.error_occurred.connect(self.mostrar_error)
        self.controller.operation_successful.connect(self.mostrar_informacion)
        # Si el controller emite un solo string en error_occurred, lo adaptamos a (título, mensaje)
        self.controller.error_occurred.connect(lambda msg: self.mostrar_error("Error", msg))

        # Label de tabla vacía
        self.empty_table_label = QLabel("No hay documentos para mostrar.")
        self.empty_table_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(14)
        font.setItalic(True)
        self.empty_table_label.setFont(font)
        self.empty_table_label.setStyleSheet("color: #888;")
        self.empty_table_label.setVisible(False)

        # Estilos
        self.setStyleSheet("""
            QWidget {
                background-color: #F8F0F5;
                color: #333333;
                font-family: 'Segoe UI', 'Arial', sans-serif;
            }
            QLabel {
                color: #333333;
                font-size: 16px;
                font-weight: bold;
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
            QPushButton:hover { background-color: #7B718D; }
            QPushButton:pressed { background-color: #4A445C; }
            QPushButton:disabled { background-color: #B0B0B0; color: #DDDDDD; }
            QPushButton#btn_toggle_form { background-color: #D36B92; }
            QPushButton#btn_toggle_form:hover { background-color: #E279A1; }
            QPushButton#btn_toggle_form:pressed { background-color: #B85F7F; }
            QPushButton#btn_editar { background-color: #5AA1B9; }
            QPushButton#btn_editar:hover { background-color: #7BC2DA; }
            QPushButton#btn_editar:pressed { background-color: #4E8BA3; }
            QPushButton#btn_eliminar { background-color: #CC5555; }
            QPushButton#btn_eliminar:hover { background-color: #D96666; }
            QPushButton#btn_eliminar:pressed { background-color: #B34444; }
            QPushButton#btn_papelera { background-color: #8C8C8C; }
            QPushButton#btn_papelera:hover { background-color: #A0A0A0; }
            QPushButton#btn_papelera:pressed { background-color: #707070; }
            QPushButton#btn_recuperar { background-color: #6EB24B; }
            QPushButton#btn_recuperar:hover { background-color: #7EC25C; }
            QPushButton#btn_recuperar:pressed { background-color: #5D993A; }
            QPushButton#btn_eliminar_def { background-color: #A93226; }
            QPushButton#btn_eliminar_def:hover { background-color: #C0392B; }
            QPushButton#btn_eliminar_def:pressed { background-color: #8D281F; }
            QPushButton#btn_limpiar_filtros {
                background-color: #5AA1B9;
                color: white;
                border-radius: 6px;
                padding: 12px 25px;
            }
            QPushButton#btn_limpiar_filtros:hover { background-color: #7BC2DA; }
            QPushButton#btn_limpiar_filtros:pressed { background-color: #4E8BA3; }
            QLineEdit {
                padding: 10px 15px;
                border: 1px solid #CED4DA;
                border-radius: 6px;
                font-size: 20px;
                color: #495057;
                background-color: white;
            }
            QLineEdit::placeholder { color: #ADB5BD; }
            QComboBox {
                padding: 10px 15px;
                border: 1px solid #CED4DA;
                border-radius: 6px;
                font-size: 20px;
                color: #495057;
                background-color: white;
            }
            QComboBox::drop-down { border-left: 1px solid #CED4DA; background-color: #E9ECEF; width: 30px; }
            QComboBox::down-arrow { width: 16px; height: 16px; }
            QComboBox QAbstractItemView {
                border: 1px solid #CED4DA;
                border-radius: 6px;
                background-color: white;
                selection-background-color: #D36B92;
                selection-color: white;
                padding: 5px;
            }
            QComboBox QAbstractItemView::item { min-height: 30px; padding: 5px 10px; font-size: 16px; font-weight: bold; }
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
            QDialog QPushButton:hover { background-color: #7B718D; }
            QDialog QPushButton:pressed { background-color: #4A445C; }
            QDialog QLabel { color: #333333; font-size: 16px; }
            QDialog QLineEdit {
                border: 1px solid #CED4DA;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 14px;
            }
            QLabel#CustomTooltip {
                background-color: #333333;
                color: white;
                border: 1px solid #5D566F;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 20px;
                font-weight: bold;
            }
            QTableView {
                background-color: white;
                border: 1px solid #E0E0E0;
                gridline-color: #F0F0F0;
                border-radius: 8px;
                selection-background-color: #D36B92;
                selection-color: white;
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 26px;
            }
            QTableView::item { padding: 8px 10px; font-size: 24px; }
            QTableView::item:alternate { background-color: #FDF7FA; }
            QHeaderView::section {
                background-color: #F8F0F5;
                color: #5D566F;
                font-size: 18px;
                font-weight: bold;
                border-bottom: 2px solid #D36B92;
                padding: 10px 10px;
            }
            QHeaderView::section:horizontal { border-right: 1px solid #F0F0F0; }
            QHeaderView::section:last { border-right: none; }
        """)
        self.setWindowTitle("Gestión de Documentos")

        # Tooltip custom
        self.custom_tooltip_label = QLabel(self)
        self.custom_tooltip_label.setObjectName("CustomTooltip")
        self.custom_tooltip_label.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.custom_tooltip_label.hide()
        self.hide_tooltip_timer = QTimer(self)
        self.hide_tooltip_timer.setSingleShot(True)
        self.hide_tooltip_timer.timeout.connect(self.custom_tooltip_label.hide)
        self._last_hovered_index = QModelIndex()

        # Construcción de UI (crea los widgets como search_* y cliente_combo)
        self.setup_ui()

        # 🔗 Conexiones SOLO de BÚSQUEDA (no tocar Cargar Docus)
        self.search_cliente_input.returnPressed.connect(self.ejecutar_busqueda)
        self.search_cliente_input.textChanged.connect(self.ejecutar_busqueda)
        self.search_cliente_combo.currentIndexChanged.connect(self.ejecutar_busqueda)
        self.search_doc_input.returnPressed.connect(self.ejecutar_busqueda)
        self.search_doc_input.textChanged.connect(self.ejecutar_busqueda)
        self.search_tipo_doc_combo.currentIndexChanged.connect(self.ejecutar_busqueda)

        # 🔗 Conexión de “Cargar Docus” (combo independiente del filtro)
        self.cliente_combo.currentIndexChanged.connect(self._on_cliente_combo_changed)

        self.logger.info("DocumentosModule inicializado y datos iniciales cargados.")

        # 🚀 Carga inicial de clientes y documentos usando el controlador
        # (Se hace al final para que la tabla/combos ya estén construidos y conectados)
        self.controller.cargar_datos_iniciales()


    def setup_ui(self):
        self.label_archivo_seleccionado = QLabel("Ningún archivo seleccionado")
        self.tabla_documentos.setMouseTracking(True)
        self.tabla_documentos.viewport().installEventFilter(self)
        self.tabla_documentos.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla_documentos.setSelectionMode(QAbstractItemView.ExtendedSelection)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 5, 20, 20)
        main_layout.setSpacing(10)
        self.label = QLabel("Gestión de Documentos")
        self.label.setObjectName("mainTitle")
        self.label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.label)
        upper_section_grid_layout = QGridLayout()
        upper_section_grid_layout.setSpacing(10)
        upper_section_grid_layout.setContentsMargins(0, 0, 0, 0)
        upper_section_grid_layout.setColumnStretch(0, 3)
        upper_section_grid_layout.setColumnStretch(1, 5)
        upper_section_grid_layout.setColumnStretch(2, 3)
        upper_section_grid_layout.setColumnStretch(3, 7)
        upper_section_grid_layout.setColumnStretch(4, 0)
        upper_section_grid_layout.setColumnStretch(5, 3)
        upper_section_grid_layout.setColumnStretch(6, 5)
        upper_section_grid_layout.setColumnStretch(7, 0)
        upper_section_grid_layout.setColumnStretch(8, 0)
        upper_section_grid_layout.setColumnStretch(9, 0)
        upper_section_grid_layout.setColumnStretch(10, 1)
        self.doc_id_label = QLabel("ID Documento:")
        self.doc_id_label.setVisible(False)
        self.doc_id_label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        self.doc_id_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.doc_id_display = QLineEdit()
        self.doc_id_display.setReadOnly(True)
        self.doc_id_display.setVisible(False)
        upper_section_grid_layout.addWidget(self.doc_id_label, 0, 0)
        upper_section_grid_layout.addWidget(self.doc_id_display, 0, 1)
        row_main_form = 1
        row_edit_buttons = 2
        self.main_load_docs_label = QLabel("Cargar Docus:")
        self.main_load_docs_label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        self.main_load_docs_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        upper_section_grid_layout.addWidget(self.main_load_docs_label, row_main_form, 0)
        self.cliente_combo = QComboBox()
        self.cliente_combo.setPlaceholderText("Seleccione Cliente")
        self.cliente_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.cliente_combo.addItem("Buscar Cliente por Nombre o ID", "SEARCH_MODE")
        upper_section_grid_layout.addWidget(self.cliente_combo, row_main_form, 1)
        self.cliente_search_label = QLabel("Buscar Cliente:")
        self.cliente_search_label.setVisible(False)
        self.cliente_search_label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        self.cliente_search_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.cliente_search_input = QLineEdit()
        self.cliente_search_input.setPlaceholderText("Ingrese nombre o ID del cliente...")
        self.cliente_search_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.cliente_search_input.setVisible(False)
        upper_section_grid_layout.addWidget(self.cliente_search_label, row_main_form, 0)
        upper_section_grid_layout.addWidget(self.cliente_search_input, row_main_form, 1)
        self.cliente_search_results_list = QListWidget()
        self.cliente_search_results_list.setVisible(False)
        self.cliente_search_results_list.setFixedHeight(150)
        upper_section_grid_layout.addWidget(self.cliente_search_results_list, row_main_form + 1, 1, 1, 5)
        self.nom_doc_label = QLabel("Nom Docu:")
        self.nom_doc_label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        self.nom_doc_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        upper_section_grid_layout.addWidget(self.nom_doc_label, row_main_form, 2)
        self.nombre_doc_input = QLineEdit()
        self.nombre_doc_input.setPlaceholderText("Nombre del documento")
        self.nombre_doc_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        upper_section_grid_layout.addWidget(self.nombre_doc_input, row_main_form, 3, 1, 2)
        self.tipo_doc_label = QLabel("Tipo de Docu:")
        self.tipo_doc_label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        self.tipo_doc_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        upper_section_grid_layout.addWidget(self.tipo_doc_label, row_main_form, 5)
        self.tipo_documento_combo = QComboBox()
        self.tipo_documento_combo.addItems(["General", "Contrato", "Demanda", "Sentencia", "Poder", "Acuerdo", "Factura", "Otro"])
        self.tipo_documento_combo.setCurrentText("General")
        self.tipo_documento_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        upper_section_grid_layout.addWidget(self.tipo_documento_combo, row_main_form, 6)
        self.btn_seleccionar_archivo = QPushButton("Seleccionar Archivo")
        self.btn_seleccionar_archivo.setEnabled(False)
        self.btn_seleccionar_archivo.setObjectName("btn_seleccionar_archivo")
        upper_section_grid_layout.addWidget(self.btn_seleccionar_archivo, row_main_form, 8)
        self.btn_agregar = QPushButton("Agregar Documento")
        self.btn_agregar.setObjectName("btn_nuevo_documento")
        upper_section_grid_layout.addWidget(self.btn_agregar, row_main_form, 9)
        self.label_ruta_archivo = QLabel("Ruta del Archivo:")
        self.label_ruta_archivo.setVisible(False)
        self.label_ruta_archivo.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        self.label_ruta_archivo.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.archivo_path_display = QLineEdit()
        self.archivo_path_display.setReadOnly(True)
        self.archivo_path_display.setPlaceholderText("Ruta del archivo local...")
        self.archivo_path_display.setVisible(False)
        upper_section_grid_layout.addWidget(self.label_ruta_archivo, row_edit_buttons, 0, Qt.AlignLeft | Qt.AlignVCenter)
        upper_section_grid_layout.addWidget(self.archivo_path_display, row_edit_buttons, 1, 1, 5)
        self.btn_editar = QPushButton("Guardar Cambios")
        self.btn_editar.setObjectName("btn_guardar_documento")
        self.btn_editar.setVisible(False)
        upper_section_grid_layout.addWidget(self.btn_editar, row_edit_buttons, 7)
        self.btn_cancelar_edicion = QPushButton("Cancelar Edición")
        self.btn_cancelar_edicion.setVisible(False)
        upper_section_grid_layout.addWidget(self.btn_cancelar_edicion, row_edit_buttons, 8)
        main_layout.addLayout(upper_section_grid_layout)
        filters_and_table_container_layout = QVBoxLayout()
        filters_and_table_container_layout.setContentsMargins(0, 0, 0, 0)
        filters_and_table_container_layout.setSpacing(0)
        search_layout = QHBoxLayout()
        search_layout.setSpacing(5)
        search_layout.setContentsMargins(0, 0, 0, 0)
        self.search_client_label_main = QLabel("Buscar Cliente:")
        search_layout.addWidget(self.search_client_label_main)
        self.search_cliente_combo = QComboBox()
        self.search_cliente_combo.setPlaceholderText("Filtrar por Cliente")
        self.search_cliente_combo.addItem("Todos los clientes", None)
        self.search_cliente_combo.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        search_layout.addWidget(self.search_cliente_combo)
        self.search_cliente_label = QLabel("O por nombre o ID:")
        search_layout.addWidget(self.search_cliente_label)
        self.search_cliente_input = QLineEdit()
        self.search_cliente_input.setPlaceholderText("Buscar por nombre de cliente (texto)")
        self.search_cliente_input.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        search_layout.addWidget(self.search_cliente_input)
        self.search_doc_name_or_id_label = QLabel("Por Dto O por ID:")
        search_layout.addWidget(self.search_doc_name_or_id_label)
        self.search_doc_input = QLineEdit()
        self.search_doc_input.setPlaceholderText("Buscar por nombre de documento")
        self.search_doc_input.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        search_layout.addWidget(self.search_doc_input)
        search_layout.addWidget(QLabel("Tipo:"))
        self.search_tipo_doc_combo = QComboBox()
        self.search_tipo_doc_combo.addItem("Todos", "Todos")
        self.search_tipo_doc_combo.addItems(["General", "Contrato", "Demanda", "Sentencia", "Poder", "Acuerdo", "Factura", "Otro"])
        self.search_tipo_doc_combo.setCurrentText("Todos")
        self.search_tipo_doc_combo.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        search_layout.addWidget(self.search_tipo_doc_combo)
        self.search_doc_id_label = QLabel("ID:")
        self.search_doc_id_label.setVisible(False)
        search_layout.addWidget(self.search_doc_id_label)
        self.search_doc_id_input = QLineEdit()
        self.search_doc_id_input.setPlaceholderText("Buscar por ID de documento")
        self.search_doc_id_input.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        self.search_doc_id_input.setVisible(False)
        search_layout.addWidget(self.search_doc_id_input)
        self.btn_limpiar_busqueda = QPushButton("Limpiar Filtros")
        self.btn_limpiar_busqueda.setObjectName("btn_limpiar_filtros")
        search_layout.addWidget(self.btn_limpiar_busqueda)
        filters_and_table_container_layout.addLayout(search_layout)
        filters_and_table_container_layout.addWidget(self.empty_table_label, 1)
        filters_and_table_container_layout.addWidget(self.tabla_documentos, 1)
        main_layout.addLayout(filters_and_table_container_layout, 1)
        table_actions_layout = QHBoxLayout()
        table_actions_layout.setSpacing(10)
        table_actions_layout.setContentsMargins(0, 10, 0, 0)
        self.btn_ver_documento = QPushButton("Ver Documento Seleccionado")
        self.btn_ver_documento.setObjectName("btn_ver_documento")
        self.btn_ver_documento.setVisible(False)
        self.btn_ver_documento.setToolTip("Abre el documento seleccionado en un visor.")
        self.btn_ver_documento.setEnabled(False)
        table_actions_layout.addWidget(self.btn_ver_documento)
        self.btn_editar_seleccion = QPushButton("Editar Selección")
        table_actions_layout.addWidget(self.btn_editar_seleccion)
        self.btn_editar_seleccion.clicked.connect(self.on_btn_editar_seleccion_clicked)
        self.btn_eliminar_seleccion = QPushButton("Enviar a Papelera")
        table_actions_layout.addWidget(self.btn_eliminar_seleccion)
        table_actions_layout.addStretch()
        self.btn_papelera = QPushButton("Ver Papelera")
        self.btn_papelera.setObjectName("papeleraBtn")
        table_actions_layout.addWidget(self.btn_papelera)
        self.btn_restaurar = QPushButton("Restaurar")
        self.btn_restaurar.setObjectName("restaurarBtn")
        self.btn_restaurar.setVisible(False)
        table_actions_layout.addWidget(self.btn_restaurar)
        self.btn_eliminar_definitivo = QPushButton("Eliminar Definitivamente")
        self.btn_eliminar_definitivo.setObjectName("eliminarDefinitivoBtn")
        self.btn_eliminar_definitivo.setVisible(False)
        table_actions_layout.addWidget(self.btn_eliminar_definitivo)

        self.btn_eliminar_seleccion.clicked.connect(self.enviar_a_papelera)
        self.btn_restaurar.clicked.connect(self.restaurar_documento_seleccionado)

        self.btn_eliminar_definitivo.clicked.connect(self.on_btn_eliminar_definitivo_clicked)
        main_layout.addLayout(table_actions_layout)
        self.tabla_documentos.setModel(self.documentos_model)
        self.connect_signals()
        logger.info("DocumentosModule inicializado y datos iniciales cargados.")
    
    def _handle_cliente_combo_selection_mode(self):
        """
        Maneja la visibilidad de los campos de selección/búsqueda de cliente
        basándose en la opción seleccionada en self.cliente_combo.
        """
        selected_data = self.cliente_combo.currentData()

        if selected_data == "SEARCH_MODE":
            # Modo búsqueda activado
            self.cliente_combo.setVisible(False)
            self.main_load_docs_label.setText("Buscar Cliente:") # Mantener este texto general para la sección
            
            self.cliente_search_label.setVisible(True)
            self.cliente_search_label.setText("Por Nom o ID:") # <-- Etiqueta para el campo de búsqueda
            
            self.cliente_search_input.setVisible(True)
            self.cliente_search_input.setMinimumWidth(250) # <-- Ajuste de tamaño
            self.cliente_search_input.setFocus() # Poner el foco en el campo de búsqueda
            self.cliente_search_input.clear() # Limpiar el campo al activarse

            self.cliente_search_results_list.setVisible(True) # Hacer visible la lista de resultados
            self.cliente_search_results_list.clear() # Limpiar resultados anteriores
        else:
            # Se ha seleccionado un cliente real o la opción por defecto
            self.cliente_combo.setVisible(True)
            self.main_load_docs_label.setText("Cargar Docus:") # Restaurar texto de la etiqueta principal
            
            self.cliente_search_label.setVisible(False)
            self.cliente_search_input.setVisible(False)
            self.cliente_search_input.clear() # Limpiar campo al salir del modo búsqueda

            self.cliente_search_results_list.setVisible(False) # Ocultar la lista de resultados
            self.cliente_search_results_list.clear() # Limpiar la lista al salir del modo búsqueda
    

    def on_btn_editar_seleccion_clicked(self):
        selected_indexes = self.tabla_documentos.selectionModel().selectedRows()
        self.logger.info(f"Botón 'Editar Selección' clicado.")
        self.logger.info(f"DEBUG: Contenido de selected_indexes (desde selectedRows): {selected_indexes}")

        if not selected_indexes:
            # Esta parte se queda porque es una validación inicial
            QMessageBox.warning(self, "Advertencia", "Por favor, selecciona un documento para editar.")
            self.logger.warning("No se seleccionó ningún documento para editar.")
            return

        selected_row = selected_indexes[0].row()
        self.logger.info(f"DEBUG: Fila seleccionada (desde selectedRows): {selected_row}")
        documento_id = self.documentos_model.get_documento_id(selected_row)
        logger.debug(f"DEBUG: Documento ID enviado al controlador: {documento_id} (Tipo: {type(documento_id)})")
        documento_data_original = self.documentos_logic.get_documento_por_id(documento_id)
        if not documento_data_original:
            self.mostrar_error("No encontrado", f"No pude cargar el documento ID {documento_id}.")
            return


        if not documento_data_original:
            self.logger.error(f"Error: No se pudo recuperar los datos originales del documento ID {documento_id} para edición.")
            QMessageBox.critical(self, "Error de Edición", "No se pudo recuperar los datos originales del documento para actualizar.")
            return
        self.logger.info(f"DEBUG: documento_data antes de abrir diálogo: {documento_data_original}")
        self.abrir_dialogo_editar_documento(documento_data_original)

    def on_document_edited_successfully(self, edited_data: dict):
        self.logger.info("Diálogo de edición de documento aceptado. Recargando tabla...")
        self.logger.info(f"DEBUG: Datos recibidos de la señal para actualizar DB: {edited_data}")

        doc_id = edited_data.get("id_documento")
        if not doc_id:
            self.mostrar_error("Error de Edición", "No se recibió un ID válido para actualizar el documento.")
            return

        # Extraer datos normalizados
        nombre = edited_data.get("nombre")
        nuevo_tipo = edited_data.get("tipo_documento")
        nueva_fecha_subida_dt = edited_data.get("fecha_subida")
        fecha_expiracion_dt = edited_data.get("fecha_expiracion")
        ubicacion_archivo = edited_data.get("ubicacion_archivo")
        archivo = edited_data.get("archivo")

        # Convertir fechas
        fecha_subida_str = None
        if isinstance(nueva_fecha_subida_dt, datetime):
            fecha_subida_str = nueva_fecha_subida_dt.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(nueva_fecha_subida_dt, date):
            fecha_subida_str = nueva_fecha_subida_dt.strftime('%Y-%m-%d 00:00:00')

        fecha_expiracion_str = None
        if isinstance(fecha_expiracion_dt, datetime):
            fecha_expiracion_str = fecha_expiracion_dt.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(fecha_expiracion_dt, date):
            fecha_expiracion_str = fecha_expiracion_dt.strftime('%Y-%m-%d 00:00:00')

        # Obtener datos originales para cliente/proceso
        documento_original_data = self.controller.get_document_by_id(doc_id)
        if not documento_original_data:
            self.mostrar_error("Error de Edición", "No se pudo recuperar los datos originales del documento.")
            self.logger.error(f"Error: No se encontró el documento original con ID {doc_id}.")
            return

        cliente_id_para_actualizar = documento_original_data.get('cliente_id')
        proceso_id_para_actualizar = documento_original_data.get('proceso_id')

        # --- Llamada al controlador ---
        success = self.controller.editar_documento(
            doc_id=doc_id,
            nombre=nombre,
            cliente_id=cliente_id_para_actualizar,
            proceso_id=proceso_id_para_actualizar,
            fecha_subida=fecha_subida_str,
            ubicacion_archivo=ubicacion_archivo,
            archivo=archivo,
            tipo_documento=nuevo_tipo,
            fecha_expiracion=fecha_expiracion_str,
            eliminado=False
        )

        if success:
            self.mostrar_informacion("Éxito", "Documento actualizado correctamente.")
            self.logger.info(f"Documento con ID {doc_id} actualizado exitosamente via controller.")
            self.ejecutar_busqueda()
        else:
            self.mostrar_error("Error", "No se pudo actualizar el documento.")
            self.logger.error(f"Falló la actualización del documento {doc_id} en el controller.")


    def verificar_cliente_seleccionado(self):
        cliente_valido = False

        # Caso 1: cliente seleccionado directamente del combo
        index_combo = self.cliente_combo.currentIndex()
        data_combo = self.cliente_combo.itemData(index_combo)
        if data_combo != "SEARCH_MODE" and data_combo is not None:
            cliente_valido = True

        # Caso 2: cliente seleccionado desde la lista de búsqueda
        if self.cliente_search_results_list.isVisible() and self.cliente_search_results_list.currentItem():
            cliente_valido = True

        self.btn_seleccionar_archivo.setEnabled(cliente_valido)
    
   
    def _perform_cliente_search(self):
        """
        Realiza la búsqueda de clientes por nombre o ID
        basándose en el texto del campo cliente_search_input
        y actualiza self.cliente_search_results_list con los resultados.
        """
        search_text = self.cliente_search_input.text().strip()
        filtered_clients = []

        if not search_text:
            self.cliente_search_results_list.clear()
            self.cliente_search_results_list.setVisible(False)
        else:
            # Utiliza el método de ClientesLogic que ya adaptamos.
            # Este devolverá tuplas (ID, Nombre)
            filtered_clients = self.clientes_logic.search_clientes(search_text)
            
        self._update_cliente_search_results_list(filtered_clients)
        self.logger.info(f"Búsqueda de cliente por input: '{search_text}', encontrados {len(filtered_clients)} resultados.")
    
    def eventFilter(self, source, event):
        if source == self.tabla_documentos.viewport():
            if event.type() == QEvent.ToolTip:
                index = self.tabla_documentos.indexAt(event.pos())
                if index.isValid():
                    self.show_custom_tooltip(index, event.pos()) 
                else:
                    self.hide_custom_tooltip()
                return True 
            
            elif event.type() == QEvent.MouseMove:
                index = self.tabla_documentos.indexAt(event.pos())
                if index.isValid() and index != self._last_hovered_index:
                    self._last_hovered_index = index
                    # Ya no es necesario llamar show_custom_tooltip aquí, QEvent.ToolTip lo hará.
                    # Si lo dejas aquí, podría causar parpadeos al usar QEvent.ToolTip.
                    # Si aun así no ves tooltips con QEvent.ToolTip, puedes reactivar esta línea
                    # como un fallback, pero no es la forma ideal.
                    # self.show_custom_tooltip(index, event.pos()) 
                elif not index.isValid() and self._last_hovered_index.isValid():
                    self.hide_custom_tooltip()
                    self._last_hovered_index = QModelIndex()
            
            elif event.type() == QEvent.Leave:
                self.hide_custom_tooltip()
                self._last_hovered_index = QModelIndex()

        return super().eventFilter(source, event)

        
    def show_custom_tooltip(self, index, mouse_pos):
        tooltip_text_from_model = self.documentos_model.data(index, Qt.ToolTipRole)
        cell_display_data = self.documentos_model.data(index, Qt.DisplayRole)
        cell_display_text = str(cell_display_data) if cell_display_data is not None else ""

        final_tooltip_content = tooltip_text_from_model if tooltip_text_from_model is not None else cell_display_text

        if final_tooltip_content:
            font_metrics = QFontMetrics(self.custom_tooltip_label.font()) # Usar la fuente del QLabel del tooltip
            text_width = font_metrics.width(final_tooltip_content)

            column_name = self.documentos_model.headerData(index.column(), Qt.Horizontal, Qt.DisplayRole)

            always_show_tooltip_columns = [
                'ID Cliente', 
                'ID', 
                'Cliente', 
                'Nombre Documento', 
                'Tipo Archivo', 
                'Tipo Documento', 
                'Fecha Carga'
            ]
            
            if (text_width > (self.tabla_documentos.columnWidth(index.column()) - 15) or
                column_name in always_show_tooltip_columns or
                column_name == 'Ubicación Archivo'): 
                
                self.custom_tooltip_label.setText(final_tooltip_content)
                self.custom_tooltip_label.adjustSize()
                global_pos = self.tabla_documentos.viewport().mapToGlobal(mouse_pos)
                self.custom_tooltip_label.move(global_pos.x() + 10, global_pos.y() + 10) 
                self.custom_tooltip_label.show()
                self.hide_tooltip_timer.start(2000)
            else:
                self.hide_custom_tooltip()
        else:
            self.hide_custom_tooltip()

    def on_table_selection_changed(self, selected=None, deselected=None):
        self.logger.debug("DEBUG: on_table_selection_changed triggered.")
        self.update_action_buttons_state()



    def hide_custom_tooltip(self):
        self.custom_tooltip_label.hide()
        if self.hide_tooltip_timer.isActive():
            self.hide_tooltip_timer.stop()

    def load_initial_data_into_view(self):
        clientes_data = self.controller.get_clientes()
        if clientes_data:
            self.cargar_clientes_en_combo(clientes_data)
        else:
            self.mostrar_advertencia("Sin clientes", "No se encontraron clientes activos en la base de datos.")
            self.cargar_clientes_en_combo([])

        documentos = self.controller.get_documentos_activos()
        if documentos:
            self.update_document_table(documentos)
        else:
            self.mostrar_mensaje("Sin documentos", "No hay documentos activos en la base de datos.")
        if not documentos:
            self.mostrar_mensaje("Sin documentos", "No hay documentos activos en la base de datos.")
    
    
    def abrir_dialogo_editar_documento(self, documento_data: dict | None):
        if not isinstance(documento_data, (dict, type(None))):
            self.mostrar_error(
                "Error de Datos",
                f"Se recibió un tipo de dato inesperado para la edición del documento: {type(documento_data)}"
            )
            logger.error(f"Tipo de dato inesperado en abrir_dialogo_editar_documento: {type(documento_data)} - {documento_data}")
            return

        # Crear el diálogo con los datos del documento
        dialog = EditarDocumentoDialog(documento_data, self)

        # Conectar la señal solo una vez
        try:
            dialog.document_edited.connect(self.on_document_edited_successfully, Qt.UniqueConnection)
        except TypeError:
            # Ya estaba conectada, no pasa nada
            pass

        # Ejecutar el diálogo
        result = dialog.exec_()

        if result == QDialog.Accepted:
            self.logger.info("Diálogo de edición aceptado. La actualización se gestiona en la señal document_edited.")
        else:
            self.logger.info("Diálogo de edición cancelado o cerrado.")

        # Desconectar y limpiar
        try:
            dialog.document_edited.disconnect(self.on_document_edited_successfully)
        except TypeError:
            pass  # ya estaba desconectada

        dialog.deleteLater()
        self.logger.debug("abrir_dialogo_editar_documento finalizado correctamente.")

    def get_selected_document_rows(self):
        """
        Retorna una lista con los IDs de los documentos seleccionados en la tabla.
        Si no hay selección, retorna [] sin forzar error.
        """
        if not self.tabla_documentos.selectionModel():
            return []

        selected_rows = []
        selected_indexes = self.tabla_documentos.selectionModel().selectedRows()

        for index in selected_indexes:
            row = index.row()
            try:
                doc_id = self.documentos_model.get_documento_id(row)
            except AttributeError:
                # Protección en caso de refresco de modelo
                doc_id = None
            if doc_id is not None:
                selected_rows.append(doc_id)

        return selected_rows


    def enviar_a_papelera(self):
        try:
            doc_ids = self.get_selected_document_rows()
            if not doc_ids:
                self.mostrar_error("Selección inválida", "Debes seleccionar al menos un documento.")
                return

            success = self.controller.mover_a_papelera(doc_ids)

            if success:
                # ✅ Primero muestra el mensaje
                self.mostrar_informacion("Éxito", f"Se enviaron {len(doc_ids)} documento(s) a la papelera.")
                # ✅ Luego refresca la tabla SOLO una vez
                self.ejecutar_busqueda()
            else:
                self.mostrar_error("Error", "No se pudieron enviar los documentos a la papelera.")

        except Exception as e:
            logger.error(f"Error al enviar a papelera: {e}", exc_info=True)
            self.mostrar_error("Error en vista", f"Ocurrió un error: {e}")


    def ver_documento_seleccionado(self):
        selected_indexes = self.tabla_documentos.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self, "Ver Documento", "Por favor, seleccione un documento para ver.")
            return

        row = selected_indexes[0].row()

        # Obtenemos los datos de la forma nueva y segura
        documento_id = self.documentos_model.get_documento_id(row)
        documento_nombre = self.documentos_model._data[row][3] # El nombre está en el índice 3

        if documento_id is None:
            self.mostrar_error("Error", "No se pudo obtener el ID del documento seleccionado.")
            return

        try:
            # Pedimos al controlador la ruta completa del archivo
            document_path = self.controller.get_full_document_path(documento_id)

            if document_path and os.path.exists(document_path):
                # Abrimos el visor, que ya sabe qué hacer con la ruta
                visor_dialog = VisorDocumentoDialog(document_path, documento_nombre, parent=self)
                visor_dialog.exec_()
            else:
                QMessageBox.warning(self, "Archivo no Encontrado", 
                                    "No se pudo encontrar el archivo físico del documento. "
                                    "Verifique que no haya sido movido o eliminado.")
        except Exception as e:
            self.mostrar_error("Error al Abrir", f"Ocurrió un error al intentar abrir el documento: {e}")
        
    def connect_signals(self):
        self.btn_seleccionar_archivo.clicked.connect(self.seleccionar_archivo)
        self.btn_agregar.clicked.connect(self.agregar_documento)
        self.btn_editar.clicked.connect(self.guardar_cambios_documento)
        self.btn_cancelar_edicion.clicked.connect(self.cancelar_edicion)
        self.btn_papelera.clicked.connect(self.toggle_papelera_view)
        self.btn_eliminar_definitivo.clicked.connect(self.eliminar_documento_definitivamente_seleccionado)
        self.tabla_documentos.doubleClicked.connect(self.on_tabla_documentos_double_clicked)
        self.btn_limpiar_busqueda.clicked.connect(self.limpiar_filtros_busqueda)
        self.search_cliente_combo.currentIndexChanged.connect(self.on_search_cliente_changed)
        self.search_tipo_doc_combo.currentIndexChanged.connect(self.on_search_tipo_doc_changed)
        self.search_cliente_input.textChanged.connect(self.on_search_input_changed)
        self.search_doc_input.textChanged.connect(self.on_search_input_changed)
        self.search_doc_id_input.textChanged.connect(self.on_search_input_changed)
        self.cliente_combo.currentIndexChanged.connect(self._handle_cliente_combo_selection_mode)
        self.cliente_search_input.textChanged.connect(self._perform_cliente_search)
        self.cliente_search_results_list.itemClicked.connect(self._select_client_from_search_list)
        self.cliente_combo.currentIndexChanged.connect(self.verificar_cliente_seleccionado)
        self.cliente_search_results_list.itemSelectionChanged.connect(self.verificar_cliente_seleccionado)
        self.cliente_search_results_list.itemClicked.connect(self.verificar_cliente_seleccionado)
        self.documentos_model.error_occurred.connect(self.mostrar_error)
        self.tabla_documentos.selectionModel().selectionChanged.connect(self.update_action_buttons_state)
        self.btn_ver_documento.clicked.connect(self.ver_documento_seleccionado) # Conecta el botón "Ver Documento Seleccionado"
        self.on_search_cliente_changed()
        self._handle_cliente_combo_selection_mode()

        
    def cambiar_color_boton_archivo_si_cliente_valido(self):
        cliente_id = self.cliente_combo.currentData()
        if cliente_id:  # Si hay un cliente seleccionado válido (no None)
            self.btn_seleccionar_archivo.setStyleSheet(
                "background-color: #4CAF50; color: white; font-weight: bold;"
            )

    def _activar_boton_agregar_documento(self):
        self.btn_agregar.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border-radius: 6px;
                padding: 15px 25px;
                font-size: 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)

    def _restaurar_boton_agregar_documento(self):
        self.btn_agregar.setStyleSheet("")  # Restaura estilo original (rosa del theme general)

    def seleccionar_archivo(self):
        self.custom_tooltip_label.hide()
        if self.hide_tooltip_timer.isActive():
            self.hide_tooltip_timer.stop()
        self._last_hovered_index = QModelIndex()
        if self.btn_seleccionar_archivo.text() == "Abortar Carga":
            self.ruta_archivo_seleccionado = None
            self.label_archivo_seleccionado.setText("Ningún archivo seleccionado")
            self._restaurar_boton_seleccion()
            self._restaurar_boton_agregar_documento()
            logger.info("Carga de archivo abortada por el usuario.")
            return
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Archivo", "", 
            "Todos los Archivos (*);;PDF Files (*.pdf);;Word Documents (*.doc *.docx)", 
            options=options
        )
        if file_path:
            self.ruta_archivo_seleccionado = file_path
            self.label_archivo_seleccionado.setText(os.path.basename(file_path))
            self._cambiar_boton_a_abortar()
            self._activar_boton_agregar_documento()
            logger.info(f"Archivo seleccionado: {file_path}")
        else:
            self.ruta_archivo_seleccionado = None
            self.label_archivo_seleccionado.setText("Ningún archivo seleccionado")
            logger.info("Selección de archivo cancelada.")

    def _cambiar_boton_a_abortar(self):
        self.btn_seleccionar_archivo.setText("Abortar Carga")
        self.btn_seleccionar_archivo.setStyleSheet("""
            QPushButton {
                background-color: #DC3545;  /* rojo Bootstrap */
                color: white;
                border-radius: 6px;
                padding: 15px 25px;
                font-size: 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #C82333;
            }
            QPushButton:pressed {
                background-color: #A71D2A;
            }
        """)

    def mostrar_informacion(self, titulo: str, mensaje: str):
        """Muestra un mensaje de información y limpia los campos si es un éxito de guardado."""
        QMessageBox.information(self, titulo, mensaje)
        self.logger.info(f"Información en vista: {titulo} - {mensaje}")
        if "agregado correctamente" in mensaje.lower():
            self.limpiar_campos_entrada()
            self._restaurar_boton_seleccion()

    def _restaurar_boton_seleccion(self):
        self.btn_seleccionar_archivo.setText("Seleccionar Archivo")
        self.btn_seleccionar_archivo.setStyleSheet("")  # Volver al estilo por defecto (heredado del theme general)

    def agregar_documento(self):
        self.custom_tooltip_label.hide()
        if self.hide_tooltip_timer.isActive():
            self.hide_tooltip_timer.stop()
        self._last_hovered_index = QModelIndex()
        logger.info("Intentando agregar documento...")
        nombre_documento = self.nombre_doc_input.text().strip()
        tipo_documento_seleccionado = self.tipo_documento_combo.currentText()
        cliente_id = self.cliente_combo.currentData()
        if not self.ruta_archivo_seleccionado:
            QMessageBox.warning(self, "Archivo no seleccionado", "Por favor, seleccione un archivo para el documento.")
            return
        if not nombre_documento:
            if self.ruta_archivo_seleccionado:
                nombre_documento = os.path.basename(self.ruta_archivo_seleccionado)
                self.nombre_doc_input.setText(nombre_documento)
            else:
                QMessageBox.warning(self, "Datos incompletos", "Por favor, ingrese el nombre del documento o seleccione un archivo.")
                return
        if cliente_id is None or not isinstance(cliente_id, int):
            QMessageBox.warning(self, "Cliente inválido", "Por favor, seleccione un cliente válido de la lista.")
            return
        if self.controller.agregar_documento(
            nombre=nombre_documento, # <-- CAMBIO CLAVE AQUÍ
            ruta_archivo_origen=self.ruta_archivo_seleccionado,
            cliente_id=cliente_id,
            tipo_documento=tipo_documento_seleccionado
        ):
            QMessageBox.information(self, "Éxito", "Documento agregado correctamente.")
            self.limpiar_campos_entrada()
            self.load_initial_data_into_view()
            self._restaurar_boton_seleccion()
            self._restaurar_boton_agregar_documento()
        else:
            QMessageBox.critical(self, "Error", "No se pudo agregar el documento. Verifique el log para más detalles.")

    def limpiar_campos_entrada(self):
        self.nombre_doc_input.clear()
        self.tipo_documento_combo.setCurrentIndex(0)
        self.cliente_combo.setCurrentIndex(0)
        self.ruta_archivo_seleccionado = None
        self.label_archivo_seleccionado.setText("Ningún archivo seleccionado")
        logger.info("Campos del formulario de documentos limpiados.")

    def cargar_clientes_en_combo(self, clientes_data: list[tuple], include_search_option: bool = True):
        # Combo de CARGA
        self.cliente_combo.clear()
        self.cliente_combo.addItem("Seleccione Cliente", None)

        if include_search_option:
            # 🔑 Deja el sentinel que usabas antes para que tu lógica lo detecte
            self.cliente_combo.addItem("Buscar Cliente por Nombre o ID", "SEARCH_MODE")

        # Combo de BÚSQUEDA
        self.search_cliente_combo.clear()
        self.search_cliente_combo.addItem("Todos los clientes", None)

        if clientes_data:
            for c_id, c_nombre in clientes_data:
                self.cliente_combo.addItem(c_nombre, c_id)
                self.search_cliente_combo.addItem(c_nombre, c_id)

            self.logger.info(f"Cargados {len(clientes_data)} clientes en combos.")


    def _on_cliente_combo_changed(self, index: int):
        """
        Maneja el combo de Cargar Docus (cliente_combo).
        - Si el usuario elige 'Buscar Cliente por Nombre o ID' (SEARCH_MODE),
        activamos el modo de carga por búsqueda (tu flujo especial).
        - Si elige un cliente concreto (ID), guardamos ese ID para el formulario de carga.
        """
        valor = self.cliente_combo.currentData()

        # Sentinel: activa tu modo especial de búsqueda para la CARGA
        if valor == "SEARCH_MODE":
            self.modo_busqueda_en_carga = True
            self.logger.info("Cargar Docus: modo búsqueda de cliente activado.")
            # Aquí NO llamamos ejecutar_busqueda(); este combo es para el formulario de carga.
            # Si tienes UI específica (mostrar campos/ocultar otros), hazlo aquí:
            # self.search_cliente_input.setVisible(True)
            # self.btn_agregar.setEnabled(False)  # etc. si aplica

        elif valor is None:
            # Nada seleccionado
            self.modo_busqueda_en_carga = False
            self.selected_cliente_id_para_carga = None
            self.logger.info("Cargar Docus: sin cliente seleccionado.")
            # self.btn_agregar.setEnabled(False)  # si aplica

        else:
            # Cliente concreto seleccionado para CARGA
            self.modo_busqueda_en_carga = False
            self.selected_cliente_id_para_carga = valor
            self.logger.info(f"Cargar Docus: cliente seleccionado para carga = {valor}")
            # self.btn_agregar.setEnabled(True)  # si aplica



    def _filter_clientes_by_input(self):
        """
        Realiza la búsqueda de clientes por nombre o ID
        basándose en el texto del campo cliente_search_input
        y actualiza self.cliente_search_results_list con los resultados.
        """
        search_text = self.cliente_search_input.text().strip()
        filtered_clients = []

        if not search_text:
            # Si el campo está vacío, no mostrar resultados en la lista de búsqueda
            self.cliente_search_results_list.clear()
            # Opcional: podrías cargar todos los clientes aquí si el campo vacío debe mostrar todos
            # all_clients = self.clientes_logic.obtener_todos_los_clientes()
            # for c in all_clients:
            #     filtered_clients.append((c.id, c.nombre))
        else:
            try:
                # Intenta buscar por ID
                cliente_id = int(search_text)
                cliente = self.clientes_logic.buscar_cliente_por_id(cliente_id)
                if cliente:
                    filtered_clients.append((cliente.id, cliente.nombre))
            except ValueError:
                # Si no es un ID, busca por nombre
                clientes_encontrados = self.clientes_logic.buscar_clientes_por_nombre(search_text)
                for cliente in clientes_encontrados:
                    filtered_clients.append((cliente.id, cliente.nombre))
        
        self._update_cliente_search_results_list(filtered_clients)
        logger.info(f"Búsqueda de cliente por input: '{search_text}', encontrados {len(filtered_clients)} resultados.")




        # Dentro de tu clase DocumentosModule(QWidget) en documentos_widget.py

 

    def _update_cliente_search_results_list(self, clients: list[tuple]):
        """
        Actualiza la QListWidget con los resultados de la búsqueda de clientes.
        """
        self.cliente_search_results_list.clear()
        if clients:
            # Define una nueva fuente con un tamaño de punto específico
            # Puedes ajustar '12' a un tamaño que te parezca adecuado.
            new_font = QFont()
            new_font.setPointSize(14) # <--- CAMBIA ESTA LÍNEA PARA FIJAR EL TAMAÑO
            # Si la fuente por defecto tiene un tipo específico que quieres mantener:
            # new_font = QFont(self.cliente_search_results_list.font().family())
            # new_font.setPointSize(12)

            for client_id, client_name in clients:
                item_text = f"{client_name} (ID: {client_id})"
                item = QListWidgetItem(item_text)
                
                # Establece el color de fondo del elemento a blanco
                item.setBackground(QColor("white")) 
                
                # Establece la nueva fuente del elemento
                item.setFont(new_font)
                item.setData(Qt.UserRole, client_id)
                self.cliente_search_results_list.addItem(item)
            self.cliente_search_results_list.setVisible(True)
        else:
            self.cliente_search_results_list.setVisible(False)
            self.logger.info("No se encontraron clientes que coincidan con la búsqueda.")

    # ... (resto de tus métodos) ...

    # ... (resto de tus métodos) ...
   
   
    def _update_cliente_combo_with_filtered_results(self, clientes_data: list[tuple]):
        """
        Actualiza self.cliente_combo con los clientes filtrados,
        preservando las opciones "Seleccione Cliente" y "Buscar Cliente por Nombre o ID".
        """
        self.cliente_combo.blockSignals(True) # Bloquear señales para evitar recursión
        self.cliente_combo.clear()
        self.cliente_combo.addItem("Seleccione Cliente", None)
        self.cliente_combo.addItem("Buscar Cliente por Nombre o ID", "SEARCH_MODE")

        if clientes_data:
            for c_id, c_nombre in clientes_data:
                self.cliente_combo.addItem(c_nombre, c_id)
        
        self.cliente_combo.blockSignals(False) # Desbloquear señales
        logger.info(f"Combo de clientes actualizado con {len(clientes_data)} clientes filtrados.")

    def update_document_table(self, documentos_a_mostrar):
        """
        Actualiza los datos mostrados en la QTableView de documentos
        con la lista de documentos proporcionada, aplicando los estilos
        de columnas deseados.
        """
        try:
            documentos_a_mostrar = documentos_a_mostrar or []  # ← pequeño guard
            self.documentos_model.set_data(documentos_a_mostrar)
            self.logger.info(f"Tabla de documentos actualizada con {len(documentos_a_mostrar)} documentos.")


            # Bloque 1: Ocultar 'Ubicación Archivo'
            try:
                col_index_ubicacion = self.documentos_model.HEADERS.index('Ubicación Archivo')
                self.tabla_documentos.setColumnHidden(col_index_ubicacion, True)
                self.logger.info(f"Columna 'Ubicación Archivo' (índice {col_index_ubicacion}) oculta.")
            except ValueError:
                self.logger.warning("La columna 'Ubicación Archivo' no se encontró en los encabezados.")

            # Bloque 2: Ocultar 'Eliminado' (corregido al mismo nivel)
            try:
                col_index_eliminado = self.documentos_model.HEADERS.index('Eliminado')
                self.tabla_documentos.setColumnHidden(col_index_eliminado, True)
                self.logger.info(f"Columna 'Eliminado' (índice {col_index_eliminado}) oculta.")
            except ValueError:
                self.logger.warning("La columna 'Eliminado' no se encontró en los encabezados.")

            # El resto del método continúa igual
            self.tabla_documentos.setColumnWidth(0, 100) # ID Cliente
            self.tabla_documentos.setColumnWidth(1, 150) # ID Documento
            self.tabla_documentos.setColumnWidth(2, 400) # Cliente
            self.tabla_documentos.setColumnWidth(3, 250) # Nombre Documento
            self.tabla_documentos.setColumnWidth(4, 150) # Tipo Archivo
            self.tabla_documentos.setColumnWidth(5, 200) # Tipo Documento
            self.tabla_documentos.setColumnWidth(6, 300) # Fecha Carga
            
            self.tabla_documentos.clearSelection()

        except Exception as e:
            self.logger.error(f"Error al actualizar la tabla de documentos: {e}")
            self.mostrar_error("Error de Actualización de Tabla",
                               f"No se pudo actualizar la tabla de documentos: {e}")

    def _select_client_from_search_list(self, item: QListWidgetItem):
        """
        Maneja la selección de un cliente desde la lista de resultados de búsqueda.
        """
        cliente_id = item.data(Qt.UserRole) # Recupera el ID del cliente guardado en el ítem

        # Encontrar el índice del cliente en self.cliente_combo y seleccionarlo
        # Es importante que los clientes ya estén cargados en cliente_combo
        index = self.cliente_combo.findData(cliente_id)
        if index != -1:
            self.cliente_combo.setCurrentIndex(index)
            self.logger.info(f"Cliente seleccionado de la búsqueda: ID {cliente_id}")
            
            # Al cambiar el currentIndex de cliente_combo, se disparará
            # _handle_cliente_combo_selection_mode(), que se encargará de
            # ocultar los campos de búsqueda y mostrar el combo principal.
            # No necesitas limpiar los campos de búsqueda aquí, ya que
            # _handle_cliente_combo_selection_mode() lo hará al restaurar la UI.
        else:
            self.logger.warning(f"Cliente con ID {cliente_id} no encontrado en cliente_combo para selección.")
    
    def on_tabla_documentos_double_clicked(self, index: QModelIndex):
        """
        Maneja el evento de doble clic en la tabla. Si el clic es en la columna
        'Tipo Archivo', abre el visor de documentos.
        """
        if not index.isValid():
            return

        # 1. Obtenemos el nombre de la columna en la que se hizo clic
        col_name = self.documentos_model.headerData(index.column(), Qt.Horizontal)

        # 2. Verificamos si la columna es la que nos interesa
        if col_name == 'Tipo Archivo':
            # 3. Si es la correcta, llamamos a la función que abre el visor
            self.ver_documento_seleccionado()
    def editar_documento_seleccionado(self):
        # Ocultar tooltip al interactuar
        self.custom_tooltip_label.hide()
        if self.hide_tooltip_timer.isActive():
            self.hide_tooltip_timer.stop()
        self._last_hovered_index = QModelIndex()

        selected_indexes = self.tabla_documentos.selectionModel().selectedRows()
        if not selected_indexes:
            self.mostrar_advertencia("Ninguna selección", "Por favor, seleccione un documento de la tabla para editar.")
            return

        # Solo editamos el primer documento seleccionado
        row = selected_indexes[0].row()
        doc_data = self.tabla_documentos_model.get_documento_data_for_edit(row)

        if doc_data:
            self.doc_id_display.setText(str(doc_data['id']))
            self.nombre_doc_input.setText(doc_data['nombre_documento'])
            self.tipo_documento_combo.setCurrentText(doc_data['tipo'])
            
            # Seleccionar cliente en el combo
            cliente_index = self.cliente_combo.findData(doc_data['cliente_id'])
            if cliente_index != -1:
                self.cliente_combo.setCurrentIndex(cliente_index)
            else:
                self.cliente_combo.setCurrentIndex(0) # Si no encuentra el cliente, selecciona "Seleccione Cliente"

            self.ruta_archivo_seleccionado = doc_data['ubicacion_archivo']
            self.label_archivo_seleccionado.setText(os.path.basename(self.ruta_archivo_seleccionado) if self.ruta_archivo_seleccionado else "Ningún archivo seleccionado")
            self.archivo_path_display.setText(self.ruta_archivo_seleccionado if self.ruta_archivo_seleccionado else "")

            # Mostrar campos de edición y ocultar botón de agregar
            self.doc_id_label.setVisible(True)
            self.doc_id_display.setVisible(True)
            self.label_ruta_archivo.setVisible(True)
            self.archivo_path_display.setVisible(True)
            self.btn_agregar.setVisible(False)
            self.btn_editar.setVisible(True)
            self.btn_cancelar_edicion.setVisible(True)
            logger.info(f"Preparando edición para documento ID: {doc_data['id']}")
        else:
            self.mostrar_error("Error de Edición", "No se pudieron cargar los datos del documento seleccionado para edición.")

    def guardar_cambios_documento(self):
        # Ocultar tooltip al interactuar
        self.custom_tooltip_label.hide()
        if self.hide_tooltip_timer.isActive():
            self.hide_tooltip_timer.stop()
        self._last_hovered_index = QModelIndex()

        doc_id = self.doc_id_display.text()
        nombre_documento = self.nombre_doc_input.text().strip()
        tipo_documento = self.tipo_documento_combo.currentText()
        cliente_id = self.cliente_combo.currentData()
        ubicacion_archivo = self.ruta_archivo_seleccionado # Usar la ruta almacenada

        if not doc_id:
            self.mostrar_advertencia("Error", "ID del documento no encontrado. No se puede guardar.")
            return
        
        if not nombre_documento:
            self.mostrar_advertencia("Datos incompletos", "El nombre del documento no puede estar vacío.")
            return
        
        if cliente_id is None or not isinstance(cliente_id, int):
            QMessageBox.warning(self, "Cliente inválido", "Por favor, seleccione un cliente válido de la lista.")
            return

        if self.controller.actualizar_documento(
            doc_id=int(doc_id),
            nuevo_nombre_documento=nombre_documento,
            nuevo_tipo_documento=tipo_documento,
            nueva_ubicacion_archivo=ubicacion_archivo,
            nuevo_cliente_id=cliente_id
        ):
            QMessageBox.information(self, "Éxito", "Documento actualizado correctamente.")
            self.cancelar_edicion() # Limpiar campos y volver a modo agregar
            self.load_initial_data_into_view()
        else:
            QMessageBox.critical(self, "Error", "No se pudo actualizar el documento. Verifique el log para más detalles.")

    def cancelar_edicion(self):
        # Ocultar tooltip al interactuar
        self.custom_tooltip_label.hide()
        if self.hide_tooltip_timer.isActive():
            self.hide_tooltip_timer.stop()
        self._last_hovered_index = QModelIndex()

        self.limpiar_campos_entrada()
        # Ocultar campos de edición y mostrar botón de agregar
        self.doc_id_label.setVisible(False)
        self.doc_id_display.setVisible(False)
        self.label_ruta_archivo.setVisible(False)
        self.archivo_path_display.setVisible(False)
        self.btn_agregar.setVisible(True)
        self.btn_editar.setVisible(False)
        self.btn_cancelar_edicion.setVisible(False)
        logger.info("Edición de documento cancelada.")

    def eliminar_documento_seleccionado(self):
        # Ocultar tooltip al interactuar
        self.custom_tooltip_label.hide()
        if self.hide_tooltip_timer.isActive():
            self.hide_tooltip_timer.stop()
        self._last_hovered_index = QModelIndex()

        selected_indexes = self.tabla_documentos.selectionModel().selectedRows()
        if not selected_indexes:
            self.mostrar_advertencia("Ninguna selección", "Por favor, seleccione uno o más documentos para enviar a la papelera.")
            return
        
        resp = QMessageBox.question(self, "Confirmar Envío a Papelera",
                                    "¿Está seguro de que desea enviar el/los documento(s) seleccionado(s) a la papelera?",
                                    QMessageBox.Yes | QMessageBox.No)
        if resp == QMessageBox.Yes:
            document_ids_to_delete = [self.tabla_documentos_model.get_documento_id(index.row()) for index in selected_indexes]
            success = True
            for doc_id in document_ids_to_delete:
                if not self.controller.enviar_documento_a_papelera(doc_id):
                    success = False
                    break
            
            if success:
                QMessageBox.information(self, "Éxito", "Documento(s) enviado(s) a la papelera correctamente.")
                self.load_initial_data_into_view()
            else:
                QMessageBox.critical(self, "Error", "Hubo un error al enviar uno o más documentos a la papelera.")

    def toggle_papelera_view(self):
        # Ocultar tooltip al interactuar
        if hasattr(self, 'custom_tooltip_label') and self.custom_tooltip_label is not None:
            self.custom_tooltip_label.hide()
        if hasattr(self, 'hide_tooltip_timer') and self.hide_tooltip_timer.isActive():
            self.hide_tooltip_timer.stop()
        self._last_hovered_index = QModelIndex()

        self.mostrando_papelera = not self.mostrando_papelera
        #self.documentos_model.set_mostrando_papelera(self.mostrando_papelera) # ASEGÚRATE que tu modelo tiene este método y se llama 'documentos_model'

        if self.mostrando_papelera:
            self.btn_papelera.setText("Volver a Documentos Activos")
            self.label.setText("Gestión de Documentos - Papelera") # Título principal de la ventana
            
            # Oculta los botones de acción normales y campos de entrada de carga
            self.btn_eliminar_seleccion.setVisible(False) # "Enviar a Papelera"
            self.btn_editar_seleccion.setVisible(False) # "Editar Selección"
            self.btn_ver_documento.setVisible(False) # "Ver Documento Seleccionado"
            
            self.main_load_docs_label.setVisible(False)
            self.cliente_combo.setVisible(False)
            self.nom_doc_label.setVisible(False)
            self.nombre_doc_input.setVisible(False)
            self.tipo_doc_label.setVisible(False)
            self.tipo_documento_combo.setVisible(False)
            self.btn_seleccionar_archivo.setVisible(False)
            self.btn_agregar.setVisible(False)
            
            # Oculta campos de edición si están visibles
            self.cancelar_edicion() # Llama a cancelar edición para asegurar que los campos de edición se oculten
            
            # Muestra los botones de papelera
            self.btn_restaurar.setVisible(True)
            self.btn_eliminar_definitivo.setVisible(True)

        else:
            self.btn_papelera.setText("Ver Papelera")
            self.label.setText("Gestión de Documentos") # Título principal de la ventana
            
            # Muestra los botones de acción normales y campos de entrada de carga
            self.btn_eliminar_seleccion.setVisible(True)
            self.btn_editar_seleccion.setVisible(True)
            self.btn_ver_documento.setVisible(True)

            self.main_load_docs_label.setVisible(True)
            self.cliente_combo.setVisible(True)
            self.nom_doc_label.setVisible(True)
            self.nombre_doc_input.setVisible(True)
            self.tipo_doc_label.setVisible(True)
            self.tipo_documento_combo.setVisible(True)
            self.btn_seleccionar_archivo.setVisible(True)
            self.btn_agregar.setVisible(True)

            # Oculta los botones de papelera
            self.btn_restaurar.setVisible(False)
            self.btn_eliminar_definitivo.setVisible(False)

        self.limpiar_filtros_busqueda() # Limpiar filtros al cambiar de vista
        self.ejecutar_busqueda() # Centralizamos la carga de datos aquí
        self.update_action_buttons_state() # Asegura que los botones se activen/desactiven correctamente
        logger.info(f"Modo papelera: {self.mostrando_papelera}")

        if self.tabla_documentos.selectionModel():
            self.tabla_documentos.selectionModel().clearSelection()
        self.update_action_buttons_state()


    def update_action_buttons_state(self):
        sel = False
        if self.tabla_documentos.selectionModel():
            sel = self.tabla_documentos.selectionModel().hasSelection()

        if not self.mostrando_papelera:
            self.btn_eliminar_seleccion.setEnabled(sel)
            self.btn_editar_seleccion.setEnabled(sel)
            self.btn_ver_documento.setEnabled(sel)
            self.btn_restaurar.setEnabled(False)
            self.btn_eliminar_definitivo.setEnabled(False)
        else:
            self.btn_eliminar_seleccion.setEnabled(False)
            self.btn_editar_seleccion.setEnabled(False)
            self.btn_ver_documento.setEnabled(False)
            self.btn_restaurar.setEnabled(sel)
            self.btn_eliminar_definitivo.setEnabled(sel)




    def load_papelera_data(self):
        documentos_en_papelera = self.controller.get_documentos_en_papelera()
        self.actualizar_tabla_documentos(documentos_en_papelera)
        if not documentos_en_papelera:
            self.mostrar_mensaje("Papelera Vacía", "No hay documentos en la papelera.")

    def restaurar_documento_seleccionado(self):
        """
        Restaura los documentos seleccionados desde la papelera.
        Si después de restaurar no queda ningún documento en la papelera,
        cambia automáticamente a la vista de documentos activos.
        """
        try:
            selected_indexes = self.tabla_documentos.selectionModel().selectedRows()
            if not selected_indexes:
                self.mostrar_advertencia("Ninguna selección", "Por favor, seleccione uno o más documentos para restaurar.")
                return

            # Recolectar IDs de documentos
            doc_ids = []
            for index in selected_indexes:
                doc_id = self.documentos_model.get_documento_id(index.row())
                if doc_id is not None:
                    doc_ids.append(doc_id)

            if not doc_ids:
                self.mostrar_advertencia("Error", "No se encontraron IDs de documentos válidos para restaurar.")
                return

            # Restaurar en el controlador
            self.controller.recuperar_de_papelera(doc_ids)
            success = True


            if success:
                QMessageBox.information(self, "Éxito", f"Se restauraron {len(doc_ids)} documento(s).")
                self.ejecutar_busqueda()
                # Forzar selección del primer documento y actualizar botones
                if self.documentos_model.rowCount() > 0:
                    index = self.documentos_model.index(0, 0)
                    self.tabla_documentos.selectRow(0)
                    self.on_table_selection_changed()  # fuerza la actualización de botones


                # ✅ Si la papelera quedó vacía
                if self.mostrando_papelera and self.documentos_model.rowCount() == 0:
                    self.logger.info("Papelera vacía tras restaurar. Volviendo a documentos activos...")
                    self.toggle_papelera_view()
                    self._cambiando_vista_auto = True
                    self.toggle_papelera_view()
                    self._cambiando_vista_auto = False

            else:
                self.mostrar_error("Error", "No se pudieron restaurar todos los documentos seleccionados.")

        except Exception as e:
            self.mostrar_error("Error en vista", f"Ocurrió un error al restaurar: {e}")
            self.logger.error(f"Error en vista - Ocurrió un error al restaurar: {e}", exc_info=True)

    def eliminar_documento_definitivamente_seleccionado(self):
        # Ocultar tooltip al interactuar (estas líneas son buenas y las mantenemos)
        if hasattr(self, 'custom_tooltip_label') and self.custom_tooltip_label is not None:
            self.custom_tooltip_label.hide()
        if hasattr(self, 'hide_tooltip_timer') and self.hide_tooltip_timer.isActive():
            self.hide_tooltip_timer.stop()
        self._last_hovered_index = QModelIndex()

        selected_indexes = self.tabla_documentos.selectionModel().selectedRows()
        if not selected_indexes:
            self.mostrar_advertencia("Eliminar Definitivamente", "Por favor, seleccione uno o más documentos para eliminar definitivamente.")
            return
        
        # Recolectar información de los documentos seleccionados
        documentos_a_eliminar_info = []
        nombres_documentos = []
        for index in selected_indexes:
            row = index.row()
            doc_id = self.documentos_model.get_documento_id(row) # Usar self.documentos_model
            # Asegúrate de que doc_id sea un entero antes de agregarlo
            if isinstance(doc_id, int):
                doc_nombre = self.documentos_model.data(index.sibling(row, 2), Qt.DisplayRole) # Asumiendo columna 2 es el nombre
                # doc_ruta_relativa no es necesaria para la llamada al controlador aquí, pero la mantendremos si la usas para otra cosa
                # doc_ruta_relativa = self.documentos_model.get_documento_path(row) # Usar self.documentos_model
                
                if doc_id is not None: # doble chequeo aunque ya validamos el tipo
                    documentos_a_eliminar_info.append({'id': doc_id, 'nombre': doc_nombre}) # No necesitamos ruta_relativa en esta info
                    nombres_documentos.append(doc_nombre)
                else:
                    logger.warning(f"No se pudo obtener el ID del documento en la fila {row} para eliminar definitivamente.")
            else:
                logger.error(f"El ID del documento en la fila {row} no es un entero válido: {doc_id}. No se puede eliminar.")
                self.mostrar_error("Error de Datos", f"El ID del documento seleccionado en la fila {row} es inválido.")
                return # Detener la operación si hay un ID no válido.
        
        if not documentos_a_eliminar_info:
            self.mostrar_advertencia("Error", "No se encontraron IDs de documentos válidos para eliminar.")
            return

        nombres_str = ", ".join(nombres_documentos[:3]) # Mostrar los primeros 3, si hay más
        if len(nombres_documentos) > 3:
            nombres_str += ", ..."

        resp = QMessageBox.question(self, "Confirmar Eliminación Definitiva",
                                    f"¡ADVERTENCIA! Esta acción eliminará el/los documento(s) PERMANENTEMENTE de la base de datos y, si existe, del sistema de archivos.\n({nombres_str})\n¿Está seguro de que desea continuar?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if resp == QMessageBox.Yes:
            all_success = True
            failed_docs_list = []

            for doc_info in documentos_a_eliminar_info:
                doc_id = doc_info['id']
                doc_nombre = doc_info['nombre']
                try:
                    success, message = self.controller.eliminar_documento_definitivamente(doc_id)
                    if success:
                        logger.info(f"Documento '{doc_nombre}' (ID: {doc_id}) eliminado permanentemente. Mensaje: {message}")
                    else:
                        all_success = False
                        failed_docs_list.append(f"'{doc_nombre}' (ID: {doc_id}) - Falló: {message}")
                except Exception as e:
                    all_success = False
                    failed_docs_list.append(f"'{doc_nombre}' (ID: {doc_id}) - Error inesperado: {e}")
                    logger.error(f"Error inesperado al eliminar definitivamente documento ID {doc_id}: {e}", exc_info=True)

            if all_success:
                QMessageBox.information(self, "Éxito", "Documento(s) eliminado(s) permanentemente.")
            else:
                if len(failed_docs_list) == len(documentos_a_eliminar_info):
                    self.mostrar_error("Error Grave", "No se pudo eliminar ninguno de los documentos seleccionados permanentemente.")
                else:
                    self.mostrar_advertencia("Eliminación Parcial", 
                                            f"Se eliminaron algunos documentos, pero hubo problemas con:\n- " + "\n- ".join(failed_docs_list))

            # 🔥 Ajuste clave:
            # En lugar de volver a llamar búsqueda y provocar que el mensaje aparezca sin selección
            self.tabla_documentos.clearSelection()   # Limpia la selección
            self.ejecutar_busqueda()                 # Refresca la tabla sin provocar advertencias


    def ejecutar_busqueda(self):
        """
        Ejecuta la búsqueda de documentos basándose en los filtros actuales de la UI
        y la vista seleccionada (activos o papelera), y gestiona la visibilidad de la UI.
        """
        if hasattr(self, 'custom_tooltip_label') and self.custom_tooltip_label is not None:
            self.custom_tooltip_label.hide()
        if hasattr(self, 'hide_tooltip_timer') and self.hide_tooltip_timer.isActive():
            self.hide_tooltip_timer.stop()
        self._last_hovered_index = QModelIndex()

        # --- Filtros de cliente ---
        cliente_id_from_combo = self.search_cliente_combo.currentData()
        cliente_input_text = self.search_cliente_input.text().strip()

        final_cliente_id_filter = cliente_id_from_combo
        final_cliente_nombre_filter = ""

        # Si no hay selección en combo, intentamos con el campo de texto
        if cliente_id_from_combo is None and cliente_input_text:
            try:
                # Si es un número → cliente_id
                potential_cliente_id = int(cliente_input_text)
                final_cliente_id_filter = potential_cliente_id
            except ValueError:
                # Si es texto → nombre del cliente
                final_cliente_nombre_filter = cliente_input_text

        # --- Filtros de documento (nombre, tipo, etc.) ---
        combined_doc_search_text = self.search_doc_input.text().strip()

        final_documento_id_filter = None
        final_nombre_doc_filter = None

        if combined_doc_search_text:
            try:
                # Si es número → lo tratamos como ID del documento
                potential_doc_id = int(combined_doc_search_text)
                final_documento_id_filter = potential_doc_id
            except ValueError:
                # Si no es número → se busca por nombre del documento
                final_nombre_doc_filter = combined_doc_search_text
                logger.info(f"Texto de búsqueda de documento '{combined_doc_search_text}' no es un ID numérico. Se buscará por nombre.")


        tipo_documento_filtro = self.search_tipo_doc_combo.currentText()
        if tipo_documento_filtro == "Todos":
            tipo_documento_filtro = None

        mostrando_papelera_actual = self.mostrando_papelera
        print(f"DEBUG: Valor de self.mostrando_papelera (interno) para la búsqueda: {mostrando_papelera_actual}")

        logger.info(
            f"FILTROS FINALES enviados al controlador (unificado): "
            f"cliente_id_exacto={final_cliente_id_filter}, "
            f"cliente_nombre_filtro_texto='{final_cliente_nombre_filter}', "
            f"documento_id_filtro={final_documento_id_filter}, "
            f"tipo_documento_filtro='{tipo_documento_filtro}', "
            f"mostrando_papelera={mostrando_papelera_actual}"
        )

        try:
            documentos_obtenidos = self.controller.buscar_documentos(
                cliente_id_exacto=final_cliente_id_filter,
                cliente_nombre_filtro_texto=final_cliente_nombre_filter,
                documento_nombre_filtro=final_nombre_doc_filter,
                documento_id_filtro=final_documento_id_filter,
                tipo_documento_filtro=tipo_documento_filtro,
                mostrando_papelera=mostrando_papelera_actual
            ) or []   # ⚠️ siempre aseguramos que sea lista

            logger.info(f"Controlador devolvió {len(documentos_obtenidos)} documentos.")
            print(f"DEBUG: Controlador devolvió {len(documentos_obtenidos)} documentos.")

            self.update_document_table(documentos_obtenidos)

            if not documentos_obtenidos:
                # ⚠️ Nuevo comportamiento
                self.tabla_documentos.setVisible(False)
                self.empty_table_label.setText("No se encontraron documentos para ese cliente.")
                self.empty_table_label.setVisible(True)
            else:
                self.tabla_documentos.setVisible(True)
                self.empty_table_label.setVisible(False)

            if mostrando_papelera_actual:
                self.btn_restaurar.setVisible(True)
                self.btn_eliminar_definitivo.setVisible(True)
                self.btn_papelera.setText("Ver Documentos Activos")
                self.btn_papelera.setToolTip("Haz clic para ver los documentos activos.")
                self.btn_seleccionar_archivo.setVisible(False)
                self.btn_agregar.setVisible(False)
                self.main_load_docs_label.setVisible(False)
                self.cliente_combo.setVisible(False)
                self.nom_doc_label.setVisible(False)
                self.nombre_doc_input.setVisible(False)
                self.tipo_doc_label.setVisible(False)
                self.tipo_documento_combo.setVisible(False)
                self.label_ruta_archivo.setVisible(False)
                self.archivo_path_display.setVisible(False)
                self.btn_editar.setVisible(False)
                self.btn_cancelar_edicion.setVisible(False)
                self.doc_id_label.setVisible(False)
                self.doc_id_display.setVisible(False)

                if not documentos_obtenidos:
                    self.tabla_documentos.setVisible(False)
                    self.empty_table_label.setText("La papelera está vacía.")
                    self.empty_table_label.setVisible(True)
                else:
                    self.tabla_documentos.setVisible(True)
                    self.empty_table_label.setVisible(False)

            else:  # Documentos activos
                self.btn_restaurar.setVisible(False)
                self.btn_eliminar_definitivo.setVisible(False)
                self.btn_papelera.setText("Ver Papelera")
                self.btn_papelera.setToolTip("Haz clic para ver los documentos enviados a la papelera.")
                if hasattr(self, "btn_eliminar_seleccion"): self.btn_eliminar_seleccion.setVisible(True)   # "Enviar a Papelera"
                if hasattr(self, "btn_editar_seleccion"):   self.btn_editar_seleccion.setVisible(True)
                if hasattr(self, "btn_ver_documento"):      self.btn_ver_documento.setVisible(True)

                self.btn_seleccionar_archivo.setVisible(True)
                self.btn_agregar.setVisible(True)
                self.main_load_docs_label.setVisible(True)
                self.cliente_combo.setVisible(True)
                self.nom_doc_label.setVisible(True)
                self.nombre_doc_input.setVisible(True)
                self.tipo_doc_label.setVisible(True)
                self.tipo_documento_combo.setVisible(True)

                if not self.is_editing:
                    self.label_ruta_archivo.setVisible(False)
                    self.archivo_path_display.setVisible(False)
                    self.btn_editar.setVisible(False)
                    self.btn_cancelar_edicion.setVisible(False)
                    self.doc_id_label.setVisible(False)
                    self.doc_id_display.setVisible(False)

                if not documentos_obtenidos:
                    self.tabla_documentos.setVisible(False)
                    self.empty_table_label.setText("No hay documentos disponibles. ¡Agrega uno nuevo!")
                    self.empty_table_label.setVisible(True)
                else:
                    self.tabla_documentos.setVisible(True)
                    self.empty_table_label.setVisible(False)

            self.update_action_buttons_state()

        except Exception as e:
            logger.error(f"Error al ejecutar búsqueda en el controlador: {e}")
            self.mostrar_error("Error de Búsqueda", f"No se pudieron cargar los documentos: {e}")

    
    def limpiar_filtros_busqueda(self):
        self.logger.info("Limpiando todos los filtros de búsqueda...") # Añadí este log para trazar

        # Limpiar los campos de entrada de texto (parte de los filtros de la tabla)
        self.cliente_search_input.clear() # Esto limpia el input de búsqueda de cliente para los filtros
        self.search_doc_input.clear() # Asegura que el campo unificado se limpia
        self.search_doc_id_input.clear() 

        # Restablecer los ComboBox a su primera opción ("Todos los clientes", "Todos") (parte de los filtros de la tabla)
        self.search_cliente_combo.setCurrentIndex(0)
        self.search_tipo_doc_combo.setCurrentIndex(0)

        # Restablecer la etiqueta "Buscar Cliente:" a su texto original (parte de los filtros de la tabla)
        self.search_client_label_main.setText("Buscar Cliente:") 

        # Ocultar tooltip al limpiar filtros (esto ya estaba y es correcto)
        self.custom_tooltip_label.hide()
        if self.hide_tooltip_timer.isActive():
            self.hide_tooltip_timer.stop()
        self._last_hovered_index = QModelIndex()
        
        # Llama a on_search_cliente_changed para reconfigurar la UI y los placeholders para los FILTROS DE LA TABLA
        # Esto también ejecutará la búsqueda inicial de la tabla.
        self.on_search_cliente_changed()

        # --- AÑADIMOS LAS LÍNEAS PARA LIMPIAR LA SECCIÓN DE CARGA DE DOCUMENTOS ---
        # Esto asegura que el cliente seleccionado para CARGAR un documento también se reinicie.
        self.cliente_combo.setCurrentIndex(0) # Reinicia el ComboBox de selección de cliente para la carga
        self.cliente_search_input.clear() # Limpia el campo de texto de búsqueda de cliente para la carga
        self.cliente_search_results_list.clear() # Limpia la lista de resultados de búsqueda (donde salen los nombres de clientes)
        self.cliente_search_results_list.setVisible(False) # Oculta la lista de resultados de búsqueda
        
        # Llama a _handle_cliente_combo_selection_mode para asegurar que la UI de carga de documentos
        # se reinicie correctamente (mostrar el combo, ocultar la barra de búsqueda si estaba activa).
        self._handle_cliente_combo_selection_mode()
        # --------------------------------------------------------------------------

        self.logger.info("Filtros de búsqueda limpiados y campos de carga de documentos reiniciados.")

    def on_search_cliente_changed(self):
        # Ocultar tooltip al interactuar
        self.custom_tooltip_label.hide()
        if self.hide_tooltip_timer.isActive():
            self.hide_tooltip_timer.stop()
        self._last_hovered_index = QModelIndex()

        cliente_id_selected = self.search_cliente_combo.currentData()

        # --- CAMBIO PRINCIPAL AQUÍ: Ocultar el campo de ID del documento y su etiqueta ---
        # Aseguramos que el campo de ID separado y su etiqueta estén siempre ocultos
        self.search_doc_id_input.setVisible(False)
        # Si tienes una etiqueta específica para el ID del documento (self.search_doc_id_label), hazla invisible.
        # Si no la tienes o si search_doc_name_or_id_label es la única etiqueta, puedes omitir la siguiente línea.
        self.search_doc_id_label.setVisible(False) 


        if cliente_id_selected is None: # Si "Todos los clientes" está seleccionado
            self.search_client_label_main.setText("Buscar Cliente:")
            self.search_cliente_label.setVisible(True)
            self.search_cliente_input.setVisible(True)
            self.search_cliente_input.setPlaceholderText("Buscar por nombre, ID o identificación de cliente")
            
            # El campo self.search_doc_input ahora manejará tanto nombre como ID
            self.search_doc_input.setPlaceholderText("Buscar por nombre o ID de documento") 
            self.search_doc_id_input.clear() # Limpia este campo, aunque estará oculto
            
            self.search_doc_name_or_id_label.setText("Buscar Docu:") # Etiqueta más genérica para el campo unificado

        else: # Si un cliente específico está seleccionado
            self.search_client_label_main.setText("Docus de:")
            self.search_cliente_label.setVisible(False)
            self.search_cliente_input.setVisible(False)
            self.search_cliente_input.clear()
            
            # El campo self.search_doc_input ahora manejará tanto nombre como ID para este cliente
            self.search_doc_input.setPlaceholderText("Ingrese nombre o ID del documento")
            
            self.search_doc_name_or_id_label.setText("Por Docu O por ID:")
            
        self.ejecutar_busqueda()
            

    def on_search_tipo_doc_changed(self):
        self.ejecutar_busqueda()

    def on_search_input_changed(self):
        self.ejecutar_busqueda()

    def mostrar_error(self, titulo: str, mensaje: str):
        QMessageBox.critical(self, titulo, mensaje)
        logger.error(f"Error en vista: {titulo} - {mensaje}")

    def mostrar_advertencia(self, titulo: str, mensaje: str):
        QMessageBox.warning(self, titulo, mensaje)
        logger.warning(f"Advertencia en vista: {titulo} - {mensaje}")

    def mostrar_mensaje(self, titulo: str, mensaje: str):
        QMessageBox.information(self, titulo, mensaje)
    def show_info_message(self, title: str, message: str):
        """Muestra un mensaje de información al usuario."""
        QMessageBox.information(self, title, message)

    def on_btn_restaurar_clicked(self):
        try:
            doc_ids = self.get_selected_document_rows()
            if not doc_ids:
                # ⚡ Si no hay selección y estamos en papelera y ya está vacía → volver a activos
                if self.mostrando_papelera and self.documentos_model.rowCount() == 0:
                    self.logger.info("Papelera vacía, volviendo automáticamente a documentos activos.")
                    self.mostrando_papelera = False
                    self.ejecutar_busqueda()
                    return
                else:
                    self.mostrar_error("Selección inválida", "Debes seleccionar al menos un documento.")
                    return

            if self.controller.recuperar_de_papelera(doc_ids):
                self.mostrar_informacion("Éxito", f"Se restauraron {len(doc_ids)} documento(s).")

                self.ejecutar_busqueda()

                # ⚡ Después de restaurar, si la papelera está vacía → volver a activos
                if self.mostrando_papelera and self.documentos_model.rowCount() == 0:
                    self.logger.info("Papelera vacía tras restaurar, volviendo automáticamente a documentos activos.")
                    self.mostrando_papelera = False
                    self.ejecutar_busqueda()
            else:
                self.mostrar_error("Error", "No se pudieron restaurar los documentos seleccionados.")
        except Exception as e:
            self.logger.error(f"Error al restaurar documentos: {e}", exc_info=True)
            self.mostrar_error("Error en vista", f"Ocurrió un error al restaurar: {e}")



    def on_btn_eliminar_definitivo_clicked(self):
        try:
            selected_indexes = self.tabla_documentos.selectionModel().selectedRows()
            if not selected_indexes:
                # Salir en silencio: no mostrar ningún mensaje
                return

            doc_ids = [self.documentos_model.get_document_id(index.row()) for index in selected_indexes]

            if not doc_ids:
                self.mostrar_advertencia("Ninguna selección", "No se pudieron obtener los IDs de los documentos seleccionados.")
                return

            confirm = QMessageBox.question(
                self,
                "Confirmar Eliminación",
                f"¿Está seguro de que desea eliminar definitivamente el/los documento(s) seleccionado(s)? Esta acción no se puede deshacer.",
                QMessageBox.Yes | QMessageBox.No
            )

            if confirm == QMessageBox.Yes:
                success = self.controller.eliminar_documentos_definitivamente(doc_ids)
                if success:
                    self.mostrar_informacion("Éxito", f"Se eliminaron {len(doc_ids)} documento(s) de forma definitiva.")

                    # ✅ Aquí permanecemos en papelera para seguir gestionando los eliminados
                    self.mostrando_papelera = True
                    self.ejecutar_busqueda()
                    self.tabla_documentos.clearSelection()
                    self.update_action_buttons_state()
                else:
                    self.mostrar_error("Error", "Hubo un error al eliminar los documentos definitivamente.")
        except Exception as e:
            self.mostrar_error("Error en vista", f"Ocurrió un error al eliminar: {e}")
            logger.error(f"Error al eliminar definitivamente: {e}", exc_info=True)
<<<<<<< HEAD
# prueba de commit automático
=======
        
    def on_restaurar_clicked(self):
        """
        Acción al restaurar un documento desde la papelera:
        - Restaura usando el controller (ya está configurado en tu app).
        - Luego vuelve automáticamente a documentos activos.
        """
        try:
            # Aquí llamas al método de restaurar (tú ya lo tienes hecho en el controller).
            # Ejemplo: self.controller.restaurar_documento(self.get_selected_document_id())

            # 👇 Después de restaurar, forzamos la vista de documentos activos:
            self.mostrando_papelera = False
            self.btn_restaurar.setVisible(False)
            self.btn_eliminar_definitivo.setVisible(False)
            self.btn_papelera.setVisible(True)

            # Volvemos a cargar documentos activos
            self.ejecutar_busqueda()

        except Exception as e:
            print(f"Error al restaurar documento: {e}")

>>>>>>> develop
