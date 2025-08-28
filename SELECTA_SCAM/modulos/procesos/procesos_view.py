# SELECTA_SCAM/modulos/procesos/procesos_view.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QTableView, QMessageBox, QHeaderView, QSizePolicy, QToolButton,
    QComboBox, QLabel, QSpacerItem, QDateEdit, QCheckBox, QDialog,
    QTextEdit, QCalendarWidget, QScrollArea, QTabWidget, QGridLayout,
    QFileDialog, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, QDate, QSize, QTimer
from PyQt5.QtGui import QIcon, QFont, QPixmap # Para iconos y fuentes

# Importar los modelos y DBs necesarios
from SELECTA_SCAM.modulos.procesos.procesos_model import ProcesosModel
from SELECTA_SCAM.modulos.procesos.procesos_db import ProcesosDB
from SELECTA_SCAM.modulos.clientes.clientes_db import ClientesDB # Necesario para cargar clientes en el combo
# Asumo que estas clases DB existirán cuando las implementemos
from SELECTA_SCAM.modulos.documentos.documentos_db import DocumentosDB
from SELECTA_SCAM.modulos.contabilidad.contabilidad_db import ContabilidadDB

from datetime import datetime, date

class ProcesosView(QWidget):
    def __init__(self, db_session, parent=None):
        super().__init__(parent)
        self.db_session = db_session # Sesión de base de datos de SQLAlchemy

        # Instanciar las clases DB, pasándoles la sesión
        self.procesos_db = ProcesosDB(self.db_session)
        self.clientes_db = ClientesDB(self.db_session)
        self.documentos_db = DocumentosDB(self.db_session) # Instanciar
        self.contabilidad_db = ContabilidadDB(self.db_session) # Instanciar

        # Instanciar el modelo, pasándole todas las dependencias
        self.model = ProcesosModel(
            procesos_db_instance=self.procesos_db,
            clientes_db_instance=self.clientes_db,
            documentos_db_instance=self.documentos_db,
            contabilidad_db_instance=self.contabilidad_db,
            parent=self # Pasar self como parent para acceder a widgets de la vista si es necesario (ej. para load_data en setData)
        )
        self.model.error_occurred.connect(self.show_error_message) # Conectar la señal de error

        self.current_proceso_id = None # Para almacenar el ID del proceso seleccionado

        self.init_ui()
        self.load_clientes_into_combo() # Cargar clientes al iniciar la vista

        # Conectar la selección de fila para cargar detalles del proceso
        self.tabla_procesos.selectionModel().selectionChanged.connect(self.on_proceso_selection_changed)

    def init_ui(self):
        self.setWindowTitle("Gestión de Procesos")
        self.setGeometry(100, 100, 1600, 900) # Tamaño inicial de la ventana

        # Establecer un estilo de fuente para toda la aplicación si es necesario
        font = QFont("Arial", 14)
        self.setFont(font)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # --- Sección Superior: Búsqueda y Filtros ---
        top_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por radicado, tipo, estado, juzgado...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self.filter_procesos)
        top_layout.addWidget(self.search_input)

        self.check_eliminados = QCheckBox("Mostrar eliminados")
        self.check_eliminados.stateChanged.connect(self.filter_procesos)
        top_layout.addWidget(self.check_eliminados)

        add_button = QPushButton("Agregar Proceso")
        add_button.clicked.connect(self.open_add_proceso_dialog)
        top_layout.addWidget(add_button)

        main_layout.addLayout(top_layout)

        # --- Sección Central: Tabla de Procesos ---
        self.tabla_procesos = QTableView()
        self.tabla_procesos.setModel(self.model)
        self.tabla_procesos.setSelectionBehavior(QTableView.SelectRows)
        self.tabla_procesos.setSelectionMode(QTableView.SingleSelection) # Permitir solo una selección
        self.tabla_procesos.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) # Ajustar columnas al ancho
        self.tabla_procesos.setSortingEnabled(True) # Habilitar ordenación por columnas

        # Ocultar la columna ID si no es necesaria para la visualización directa
        self.tabla_procesos.hideColumn(0) # Columna ID
        # Ocultar la columna de Fecha Creación si no es de interés principal en la tabla
        # self.tabla_procesos.hideColumn(9) # Fecha Creación

        main_layout.addWidget(self.tabla_procesos)

        # --- Sección Inferior: Botones de Acción (Editar, Eliminar, Restaurar) ---
        action_buttons_layout = QHBoxLayout()
        edit_button = QPushButton("Editar Proceso")
        edit_button.clicked.connect(self.open_edit_proceso_dialog)
        action_buttons_layout.addWidget(edit_button)

        delete_button = QPushButton("Eliminar (lógico)")
        delete_button.clicked.connect(self.delete_selected_proceso)
        action_buttons_layout.addWidget(delete_button)

        restore_button = QPushButton("Restaurar Proceso")
        restore_button.clicked.connect(self.restore_selected_procesos)
        action_buttons_layout.addWidget(restore_button)

        permanent_delete_button = QPushButton("Eliminar (permanente)")
        permanent_delete_button.clicked.connect(self.delete_selected_proceso_permanently)
        action_buttons_layout.addWidget(permanent_delete_button)

        main_layout.addLayout(action_buttons_layout)

        # --- Panel de Detalles del Proceso (QTabWidget) ---
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Pestaña "General" - ya no es necesaria aquí si se edita en diálogo
        # Podemos usarla para mostrar un resumen no editable o quitarla
        # self.tab_general = QWidget()
        # self.tabs.addTab(self.tab_general, "General")
        # self.init_general_tab() # Si decides tener una pestaña general con solo visualización

        self.tab_documentos = QWidget()
        self.tabs.addTab(self.tab_documentos, "Documentos")
        self.init_documentos_tab()

        self.tab_contabilidad = QWidget()
        self.tabs.addTab(self.tab_contabilidad, "Contabilidad")
        self.init_contabilidad_tab()

        # Pestañas placeholder (a desarrollar)
        self.tab_actuaciones = QWidget()
        self.tabs.addTab(self.tab_actuaciones, "Actuaciones/Robot")
        # self.init_actuaciones_tab() # si es necesario

        self.tab_calendario = QWidget()
        self.tabs.addTab(self.tab_calendario, "Calendario")
        # self.init_calendario_tab() # si es necesario

        self.tab_notas = QWidget()
        self.tabs.addTab(self.tab_notas, "Notas")
        # self.init_notas_tab() # si es necesario

        self.tab_alertas = QWidget()
        self.tabs.addTab(self.tab_alertas, "Alertas")
        # self.init_alertas_tab() # si es necesario

        # Inicialmente deshabilitar las pestañas hasta que se seleccione un proceso
        self.tabs.setTabEnabled(self.tabs.indexOf(self.tab_documentos), False)
        self.tabs.setTabEnabled(self.tabs.indexOf(self.tab_contabilidad), False)
        self.tabs.setTabEnabled(self.tabs.indexOf(self.tab_actuaciones), False)
        self.tabs.setTabEnabled(self.tabs.indexOf(self.tab_calendario), False)
        self.tabs.setTabEnabled(self.tabs.indexOf(self.tab_notas), False)
        self.tabs.setTabEnabled(self.tabs.indexOf(self.tab_alertas), False)

    def load_clientes_into_combo(self):
        """Carga los clientes disponibles en el QComboBox."""
        clientes = self.clientes_db.get_all_clientes()
        self.cliente_combo.clear()
        self.cliente_combo.addItem("Seleccione un cliente", None) # Opción por defecto
        for cliente in clientes:
            self.cliente_combo.addItem(cliente.nombre, cliente.id)

    def filter_procesos(self):
        """Filtra los procesos mostrados en la tabla."""
        search_text = self.search_input.text().strip()
        include_deleted = self.check_eliminados.isChecked()
        self.model.load_data(incluir_eliminados=include_deleted, query=search_text)

    def on_proceso_selection_changed(self):
        """
        Cuando la selección de la tabla cambia, carga los detalles del proceso
        y habilita las pestañas de detalles.
        """
        selected_indexes = self.tabla_procesos.selectionModel().selectedRows()
        if selected_indexes:
            index = selected_indexes[0]
            proceso_id = self.model.data(self.model.index(index.row(), 0), Qt.DisplayRole)
            self.current_proceso_id = proceso_id
            self.load_proceso_details_into_tabs(proceso_id)
            self.enable_detail_tabs(True)
        else:
            self.current_proceso_id = None
            self.enable_detail_tabs(False)
            self.clear_detail_tabs() # Limpiar contenido al deseleccionar

    def enable_detail_tabs(self, enable: bool):
        """Habilita o deshabilita las pestañas de detalles."""
        # self.tabs.setTabEnabled(self.tabs.indexOf(self.tab_general), enable) # Si hay pestaña general
        self.tabs.setTabEnabled(self.tabs.indexOf(self.tab_documentos), enable)
        self.tabs.setTabEnabled(self.tabs.indexOf(self.tab_contabilidad), enable)
        self.tabs.setTabEnabled(self.tabs.indexOf(self.tab_actuaciones), enable)
        self.tabs.setTabEnabled(self.tabs.indexOf(self.tab_calendario), enable)
        self.tabs.setTabEnabled(self.tabs.indexOf(self.tab_notas), enable)
        self.tabs.setTabEnabled(self.tabs.indexOf(self.tab_alertas), enable)

    def clear_detail_tabs(self):
        """Limpia el contenido de las pestañas de detalles."""
        # self.clear_general_tab() # Si existe
        self.clear_documentos_tab()
        self.clear_contabilidad_tab()
        # self.clear_actuaciones_tab()
        # self.clear_calendario_tab()
        # self.clear_notas_tab()
        # self.clear_alertas_tab()

    def load_proceso_details_into_tabs(self, proceso_id: int):
        """Carga los datos específicos del proceso en las pestañas de detalles."""
        self.load_documentos_for_proceso(proceso_id)
        self.load_contabilidad_for_proceso(proceso_id)
        # Otros métodos de carga para otras pestañas

    def open_add_proceso_dialog(self):
        dialog = ProcesoDialog(self.model, self.clientes_db, parent=self)
        if dialog.exec_():
            # El modelo ya recarga los datos si la inserción fue exitosa
            QMessageBox.information(self, "Éxito", "Proceso agregado correctamente.")

    def open_edit_proceso_dialog(self):
        selected_indexes = self.tabla_procesos.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self, "Selección Requerida", "Por favor, seleccione un proceso para editar.")
            return

        index = selected_indexes[0]
        proceso_id = self.model.data(self.model.index(index.row(), 0), Qt.DisplayRole)

        proceso_data = self.model.get_proceso_by_id(proceso_id)
        if not proceso_data:
            QMessageBox.critical(self, "Error", "No se pudo cargar los datos del proceso seleccionado.")
            return

        # Pasar solo los datos que el diálogo espera
        dialog = ProcesoDialog(self.model, self.clientes_db, proceso_data=proceso_data, parent=self)
        if dialog.exec_():
            # El modelo ya recarga los datos si la actualización fue exitosa
            QMessageBox.information(self, "Éxito", "Proceso actualizado correctamente.")

    def delete_selected_proceso(self):
        selected_indexes = self.tabla_procesos.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self, "Selección Requerida", "Por favor, seleccione un proceso para eliminar.")
            return

        index = selected_indexes[0]
        proceso_id = self.model.data(self.model.index(index.row(), 0), Qt.DisplayRole)
        radicado = self.model.data(self.model.index(index.row(), 1), Qt.DisplayRole)

        reply = QMessageBox.question(self, "Confirmar Eliminación",
                                    f"¿Está seguro de que desea marcar el proceso '{radicado}' (ID: {proceso_id}) como eliminado (lógico)?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.model.marcar_como_eliminado(proceso_id):
                QMessageBox.information(self, "Éxito", f"Proceso '{radicado}' marcado como eliminado.")
            else:
                QMessageBox.critical(self, "Error", f"No se pudo marcar el proceso '{radicado}' como eliminado.")

    def restore_selected_procesos(self):
        selected_indexes = self.tabla_procesos.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self, "Selección Requerida", "Por favor, seleccione uno o más procesos para restaurar.")
            return

        proceso_ids = [self.model.data(self.model.index(idx.row(), 0), Qt.DisplayRole) for idx in selected_indexes]
        radicados = [self.model.data(self.model.index(idx.row(), 1), Qt.DisplayRole) for idx in selected_indexes]

        if not all(self.model.data(self.model.index(idx.row(), 10), Qt.DisplayRole) == "Sí" for idx in selected_indexes):
             QMessageBox.warning(self, "Error", "Solo puede restaurar procesos que estén marcados como eliminados.")
             return

        reply = QMessageBox.question(self, "Confirmar Restauración",
                                    f"¿Está seguro de que desea restaurar los siguientes procesos:\n{', '.join(radicados)}?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.model.restaurar_procesos(proceso_ids):
                QMessageBox.information(self, "Éxito", f"Procesos restaurados correctamente.")
            else:
                QMessageBox.critical(self, "Error", "No se pudieron restaurar todos los procesos seleccionados.")

    def delete_selected_proceso_permanently(self):
        selected_indexes = self.tabla_procesos.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self, "Selección Requerida", "Por favor, seleccione un proceso para eliminar permanentemente.")
            return

        index = selected_indexes[0]
        proceso_id = self.model.data(self.model.index(index.row(), 0), Qt.DisplayRole)
        radicado = self.model.data(self.model.index(index.row(), 1), Qt.DisplayRole)

        reply = QMessageBox.question(self, "Confirmar Eliminación PERMANENTE",
                                    f"¡ADVERTENCIA! Esta acción eliminará permanentemente el proceso '{radicado}' (ID: {proceso_id}) y TODOS sus datos asociados (documentos, contabilidad). Esta acción es IRREVERSIBLE.\n\n¿Está ABSOLUTAMENTE seguro?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.model.eliminar_proceso_definitivo(proceso_id):
                QMessageBox.information(self, "Éxito", f"Proceso '{radicado}' y todos sus datos eliminados permanentemente.")
            else:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar permanentemente el proceso '{radicado}'.")

    def show_error_message(self, message: str):
        """Muestra un cuadro de diálogo de error."""
        QMessageBox.critical(self, "Error", message)

    # --- Pestaña de Documentos ---
    def init_documentos_tab(self):
        layout = QVBoxLayout(self.tab_documentos)

        # Subir documento
        upload_layout = QHBoxLayout()
        self.document_name_input = QLineEdit()
        self.document_name_input.setPlaceholderText("Nombre del Documento")
        upload_layout.addWidget(self.document_name_input)

        self.document_type_combo = QComboBox()
        # Cargar categorías de documentos del modelo
        self.document_type_combo.addItem("Seleccione tipo de documento", None)
        for category, types in self.model.get_tipos_actuacion().items():
            self.document_type_combo.addItem(f"--- {category} ---", None)
            for doc_type in types:
                self.document_type_combo.addItem(doc_type, doc_type)
        upload_layout.addWidget(self.document_type_combo)


        self.document_path_input = QLineEdit()
        self.document_path_input.setPlaceholderText("Ruta del archivo...")
        self.document_path_input.setReadOnly(True)
        upload_layout.addWidget(self.document_path_input)

        browse_button = QPushButton("Examinar...")
        browse_button.clicked.connect(self.browse_document_file)
        upload_layout.addWidget(browse_button)

        upload_button = QPushButton("Subir Documento")
        upload_button.clicked.connect(self.upload_document)
        upload_layout.addWidget(upload_button)
        layout.addLayout(upload_layout)

        # Lista de documentos
        self.document_list_widget = QListWidget()
        self.document_list_widget.itemDoubleClicked.connect(self.open_document_file)
        layout.addWidget(self.document_list_widget)

        # Botones de acción para documentos
        doc_action_layout = QHBoxLayout()
        download_doc_button = QPushButton("Descargar Seleccionado")
        download_doc_button.clicked.connect(self.download_selected_document)
        doc_action_layout.addWidget(download_doc_button)

        delete_doc_button = QPushButton("Eliminar Documento")
        delete_doc_button.clicked.connect(self.delete_selected_document)
        doc_action_layout.addWidget(delete_doc_button)
        layout.addLayout(doc_action_layout)

    def browse_document_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Documento", "", "Todos los Archivos (*.*)")
        if file_path:
            self.document_path_input.setText(file_path)

    def upload_document(self):
        if not self.current_proceso_id:
            QMessageBox.warning(self, "Error", "Por favor, seleccione un proceso primero.")
            return

        doc_name = self.document_name_input.text().strip()
        doc_path = self.document_path_input.text().strip()
        doc_type = self.document_type_combo.currentData() # Obtener el dato asociado al item

        if not doc_name or not doc_path:
            QMessageBox.warning(self, "Entrada Incompleta", "Por favor, ingrese el nombre y la ruta del documento.")
            return
        if not doc_type:
            QMessageBox.warning(self, "Tipo de Documento", "Por favor, seleccione un tipo de documento.")
            return

        try:
            # Obtener el cliente_id del proceso actual
            proceso_obj = self.model.get_proceso_by_id(self.current_proceso_id)
            cliente_id = proceso_obj.cliente_id if proceso_obj else None

            if not cliente_id:
                QMessageBox.critical(self, "Error de Cliente", "No se pudo determinar el cliente asociado al proceso.")
                return

            # `archivo` sería el nombre del archivo (con extensión)
            file_name = doc_path.split('/')[-1]

            success = self.model.insertar_documento(
                proceso_id=self.current_proceso_id,
                cliente_id=cliente_id,
                nombre=doc_name,
                archivo=file_name, # Solo el nombre del archivo
                ruta=doc_path, # La ruta completa donde se guardó o se encuentra el archivo
                tipo_documento=doc_type
            )
            if success:
                QMessageBox.information(self, "Éxito", "Documento subido correctamente.")
                self.document_name_input.clear()
                self.document_path_input.clear()
                self.document_type_combo.setCurrentIndex(0) # Resetear a la primera opción
                self.load_documentos_for_proceso(self.current_proceso_id) # Recargar la lista
            else:
                QMessageBox.critical(self, "Error", "No se pudo subir el documento.")
        except Exception as e:
            QMessageBox.critical(self, "Error de Subida", f"Ocurrió un error al subir el documento: {e}")

    def load_documentos_for_proceso(self, proceso_id: int):
        self.document_list_widget.clear()
        documentos = self.model.obtener_documentos_por_proceso(proceso_id)
        for doc in documentos:
            item_text = f"{doc['nombre']} ({doc['tipo_documento']}) - {doc['fecha_subida']}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, doc['id']) # Guardar ID del documento
            item.setData(Qt.UserRole + 1, doc['ruta']) # Guardar ruta del archivo
            self.document_list_widget.addItem(item)

    def open_document_file(self):
        selected_item = self.document_list_widget.currentItem()
        if selected_item:
            file_path = selected_item.data(Qt.UserRole + 1)
            if file_path:
                try:
                    # Abre el archivo usando la aplicación predeterminada del sistema
                    import os
                    os.startfile(file_path) # Para Windows
                    # os.system(f'xdg-open "{file_path}"') # Para Linux
                    # os.system(f'open "{file_path}"') # Para macOS
                except Exception as e:
                    QMessageBox.critical(self, "Error al Abrir", f"No se pudo abrir el archivo: {e}")
            else:
                QMessageBox.warning(self, "Advertencia", "La ruta del archivo no está disponible.")

    def download_selected_document(self):
        selected_item = self.document_list_widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Selección Requerida", "Por favor, seleccione un documento para descargar.")
            return

        source_path = selected_item.data(Qt.UserRole + 1)
        doc_name = selected_item.text().split('(')[0].strip() # Nombre del documento de la lista

        if not source_path:
            QMessageBox.warning(self, "Error", "La ruta del documento no está disponible.")
            return

        save_path, _ = QFileDialog.getSaveFileName(self, "Guardar Documento Como", doc_name, "Todos los Archivos (*.*)")
        if save_path:
            try:
                import shutil
                shutil.copy(source_path, save_path)
                QMessageBox.information(self, "Éxito", f"Documento guardado en:\n{save_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error de Descarga", f"No se pudo guardar el documento: {e}")

    def delete_selected_document(self):
        selected_item = self.document_list_widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Selección Requerida", "Por favor, seleccione un documento para eliminar.")
            return

        document_id = selected_item.data(Qt.UserRole)
        doc_name = selected_item.text().split('(')[0].strip()

        reply = QMessageBox.question(self, "Confirmar Eliminación",
                                    f"¿Está seguro de que desea eliminar el documento '{doc_name}'?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.model.eliminar_documento(document_id):
                QMessageBox.information(self, "Éxito", f"Documento '{doc_name}' eliminado.")
                self.load_documentos_for_proceso(self.current_proceso_id) # Recargar la lista
            else:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar el documento '{doc_name}'.")

    def clear_documentos_tab(self):
        self.document_name_input.clear()
        self.document_path_input.clear()
        self.document_type_combo.setCurrentIndex(0)
        self.document_list_widget.clear()

    # --- Pestaña de Contabilidad ---
    def init_contabilidad_tab(self):
        layout = QVBoxLayout(self.tab_contabilidad)

        # Formulario para agregar/editar movimiento contable
        form_layout = QGridLayout()

        form_layout.addWidget(QLabel("Tipo:"), 0, 0)
        self.cont_type_combo = QComboBox()
        self.cont_type_combo.addItems(["Ingreso", "Egreso"])
        form_layout.addWidget(self.cont_type_combo, 0, 1)

        form_layout.addWidget(QLabel("Descripción:"), 1, 0)
        self.cont_description_input = QLineEdit()
        form_layout.addWidget(self.cont_description_input, 1, 1)

        form_layout.addWidget(QLabel("Valor:"), 2, 0)
        self.cont_value_input = QLineEdit()
        # Configurar para aceptar solo números (flotantes)
        # self.cont_value_input.setValidator(QDoubleValidator(0.0, 999999999.0, 2)) # Opcional: restringir entrada
        form_layout.addWidget(self.cont_value_input, 2, 1)

        form_layout.addWidget(QLabel("Fecha:"), 3, 0)
        self.cont_date_edit = QDateEdit(QDate.currentDate())
        self.cont_date_edit.setCalendarPopup(True)
        self.cont_date_edit.setDisplayFormat("yyyy-MM-dd")
        form_layout.addWidget(self.cont_date_edit, 3, 1)

        add_mov_button = QPushButton("Agregar Movimiento")
        add_mov_button.clicked.connect(self.add_contabilidad_movimiento)
        form_layout.addWidget(add_mov_button, 4, 0, 1, 2)

        layout.addLayout(form_layout)

        # Lista de movimientos contables
        self.cont_list_widget = QListWidget()
        # Puedes usar una QTableView aquí si los datos son más complejos y necesitas un modelo
        layout.addWidget(self.cont_list_widget)

        # Botones de acción para contabilidad
        cont_action_layout = QHBoxLayout()
        edit_mov_button = QPushButton("Editar Movimiento")
        edit_mov_button.clicked.connect(self.edit_selected_contabilidad_movimiento)
        cont_action_layout.addWidget(edit_mov_button)

        delete_mov_button = QPushButton("Eliminar Movimiento")
        delete_mov_button.clicked.connect(self.delete_selected_contabilidad_movimiento)
        cont_action_layout.addWidget(delete_mov_button)
        layout.addLayout(cont_action_layout)

    def add_contabilidad_movimiento(self):
        if not self.current_proceso_id:
            QMessageBox.warning(self, "Error", "Por favor, seleccione un proceso primero.")
            return

        tipo = self.cont_type_combo.currentText()
        descripcion = self.cont_description_input.text().strip()
        valor_str = self.cont_value_input.text().strip()
        fecha = self.cont_date_edit.date().toPyDate()

        if not descripcion or not valor_str:
            QMessageBox.warning(self, "Entrada Incompleta", "Por favor, ingrese descripción y valor.")
            return

        try:
            valor = float(valor_str)
        except ValueError:
            QMessageBox.warning(self, "Valor Inválido", "Por favor, ingrese un valor numérico válido.")
            return

        try:
            # Obtener el cliente_id del proceso actual
            proceso_obj = self.model.get_proceso_by_id(self.current_proceso_id)
            cliente_id = proceso_obj.cliente_id if proceso_obj else None

            if not cliente_id:
                QMessageBox.critical(self, "Error de Cliente", "No se pudo determinar el cliente asociado al proceso.")
                return

            success = self.model.insertar_movimiento_contable(
                cliente_id=cliente_id,
                proceso_id=self.current_proceso_id,
                tipo=tipo,
                descripcion=descripcion,
                valor=valor,
                fecha=fecha
            )
            if success:
                QMessageBox.information(self, "Éxito", "Movimiento contable agregado correctamente.")
                self.clear_contabilidad_form()
                self.load_contabilidad_for_proceso(self.current_proceso_id)
            else:
                QMessageBox.critical(self, "Error", "No se pudo agregar el movimiento contable.")
        except Exception as e:
            QMessageBox.critical(self, "Error al Agregar", f"Ocurrió un error al agregar el movimiento: {e}")

    def edit_selected_contabilidad_movimiento(self):
        selected_item = self.cont_list_widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Selección Requerida", "Por favor, seleccione un movimiento para editar.")
            return

        movimiento_id = selected_item.data(Qt.UserRole)
        # En una aplicación real, cargarías los datos del movimiento por ID desde el modelo
        # Por simplicidad aquí, asumimos que los datos están en el item si se añadieron correctamente
        movimientos = self.model.obtener_movimientos_contables_por_proceso(self.current_proceso_id)
        movimiento_data = next((m for m in movimientos if m['id'] == movimiento_id), None)

        if not movimiento_data:
            QMessageBox.critical(self, "Error", "No se pudieron cargar los datos del movimiento seleccionado.")
            return

        # Crear un diálogo para editar
        dialog = ContabilidadMovimientoDialog(self.model, movimiento_data, self.current_proceso_id, parent=self)
        if dialog.exec_():
            QMessageBox.information(self, "Éxito", "Movimiento contable actualizado correctamente.")
            self.load_contabilidad_for_proceso(self.current_proceso_id)

    def delete_selected_contabilidad_movimiento(self):
        selected_item = self.cont_list_widget.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Selección Requerida", "Por favor, seleccione un movimiento para eliminar.")
            return

        movimiento_id = selected_item.data(Qt.UserRole)
        mov_desc = selected_item.text()

        reply = QMessageBox.question(self, "Confirmar Eliminación",
                                    f"¿Está seguro de que desea eliminar el movimiento:\n'{mov_desc}'?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.model.eliminar_movimiento_contable(movimiento_id):
                QMessageBox.information(self, "Éxito", f"Movimiento eliminado.")
                self.load_contabilidad_for_proceso(self.current_proceso_id)
            else:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar el movimiento.")

    def load_contabilidad_for_proceso(self, proceso_id: int):
        self.cont_list_widget.clear()
        movimientos = self.model.obtener_movimientos_contables_por_proceso(proceso_id)
        total_ingresos = 0
        total_egresos = 0

        for mov in movimientos:
            item_text = f"{mov['fecha']} - {mov['tipo']}: {mov['descripcion']} - ${mov['valor']:,.2f}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, mov['id']) # Guardar ID del movimiento

            if mov['tipo'] == "Ingreso":
                total_ingresos += mov['valor']
            elif mov['tipo'] == "Egreso":
                total_egresos += mov['valor']
            self.cont_list_widget.addItem(item)

        # Mostrar resumen de totales
        self.cont_list_widget.addItem(f"\n--- Resumen Contable ---")
        self.cont_list_widget.addItem(f"Total Ingresos: ${total_ingresos:,.2f}")
        self.cont_list_widget.addItem(f"Total Egresos: ${total_egresos:,.2f}")
        self.cont_list_widget.addItem(f"Balance Neto: ${total_ingresos - total_egresos:,.2f}")


    def clear_contabilidad_form(self):
        self.cont_type_combo.setCurrentIndex(0)
        self.cont_description_input.clear()
        self.cont_value_input.clear()
        self.cont_date_edit.setDate(QDate.currentDate())

    def clear_contabilidad_tab(self):
        self.clear_contabilidad_form()
        self.cont_list_widget.clear()


# --- Diálogo para Agregar/Editar Proceso ---
class ProcesoDialog(QDialog):
    def __init__(self, model: ProcesosModel, clientes_db: ClientesDB, proceso_data: dict = None, parent=None):
        super().__init__(parent)
        self.model = model
        self.clientes_db = clientes_db
        self.proceso_data = proceso_data # Si se pasa, es modo edición
        self.is_edit_mode = proceso_data is not None

        self.setWindowTitle("Editar Proceso" if self.is_edit_mode else "Agregar Nuevo Proceso")
        self.setGeometry(200, 200, 600, 700) # Tamaño del diálogo

        self.init_ui()
        self.load_clientes()
        if self.is_edit_mode:
            self.populate_form()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QGridLayout()

        form_layout.addWidget(QLabel("Cliente:"), 0, 0)
        self.cliente_combo = QComboBox()
        self.cliente_combo.setMinimumWidth(300)
        form_layout.addWidget(self.cliente_combo, 0, 1)

        form_layout.addWidget(QLabel("Radicado:"), 1, 0)
        self.radicado_input = QLineEdit()
        form_layout.addWidget(self.radicado_input, 1, 1)

        form_layout.addWidget(QLabel("Tipo de Proceso:"), 2, 0)
        self.tipo_input = QLineEdit()
        form_layout.addWidget(self.tipo_input, 2, 1)

        form_layout.addWidget(QLabel("Fecha Inicio:"), 3, 0)
        self.fecha_inicio_edit = QDateEdit(QDate.currentDate())
        self.fecha_inicio_edit.setCalendarPopup(True)
        self.fecha_inicio_edit.setDisplayFormat("yyyy-MM-dd")
        form_layout.addWidget(self.fecha_inicio_edit, 3, 1)

        form_layout.addWidget(QLabel("Fecha Fin:"), 4, 0)
        self.fecha_fin_edit = QDateEdit()
        self.fecha_fin_edit.setCalendarPopup(True)
        self.fecha_fin_edit.setDisplayFormat("yyyy-MM-dd")
        self.fecha_fin_edit.setSpecialValueText("N/A") # Para indicar que no hay fecha fin
        self.fecha_fin_edit.setDate(QDate()) # Valor nulo inicial
        form_layout.addWidget(self.fecha_fin_edit, 4, 1)

        form_layout.addWidget(QLabel("Estado:"), 5, 0)
        self.estado_input = QLineEdit()
        form_layout.addWidget(self.estado_input, 5, 1)

        form_layout.addWidget(QLabel("Juzgado:"), 6, 0)
        self.juzgado_input = QLineEdit()
        form_layout.addWidget(self.juzgado_input, 6, 1)

        form_layout.addWidget(QLabel("Observaciones:"), 7, 0)
        self.observaciones_input = QTextEdit()
        self.observaciones_input.setMinimumHeight(100)
        form_layout.addWidget(self.observaciones_input, 7, 1)

        layout.addLayout(form_layout)

        button_box = QHBoxLayout()
        self.save_button = QPushButton("Guardar")
        self.save_button.clicked.connect(self.save_proceso)
        button_box.addWidget(self.save_button)

        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.reject)
        button_box.addWidget(cancel_button)

        layout.addLayout(button_box)

    def load_clientes(self):
        clientes = self.clientes_db.get_all_clientes()
        self.cliente_combo.clear()
        self.cliente_combo.addItem("Seleccione un cliente", None)
        for cliente in clientes:
            self.cliente_combo.addItem(cliente.nombre, cliente.id)

    def populate_form(self):
        # Asegúrate de que los nombres de las claves en proceso_data coinciden con tu modelo
        if self.proceso_data:
            # Encuentra el índice del cliente
            cliente_id = self.proceso_data.get('cliente_id')
            if cliente_id:
                index = self.cliente_combo.findData(cliente_id)
                if index != -1:
                    self.cliente_combo.setCurrentIndex(index)
                else:
                    QMessageBox.warning(self, "Advertencia", f"Cliente ID {cliente_id} no encontrado en la lista.")

            self.radicado_input.setText(self.proceso_data.get('radicado', ''))
            self.tipo_input.setText(self.proceso_data.get('tipo', '')) # Usa 'tipo' no 'clase_proceso'

            fecha_inicio_str = self.proceso_data.get('fecha_inicio')
            if fecha_inicio_str:
                self.fecha_inicio_edit.setDate(QDate.fromString(fecha_inicio_str, "yyyy-MM-dd"))
            else:
                self.fecha_inicio_edit.setDate(QDate.currentDate())

            fecha_fin_str = self.proceso_data.get('fecha_fin')
            if fecha_fin_str:
                self.fecha_fin_edit.setDate(QDate.fromString(fecha_fin_str, "yyyy-MM-dd"))
            else:
                self.fecha_fin_edit.setDate(QDate()) # Nulo

            self.estado_input.setText(self.proceso_data.get('estado', ''))
            self.juzgado_input.setText(self.proceso_data.get('juzgado', ''))
            self.observaciones_input.setText(self.proceso_data.get('observaciones', ''))

    def save_proceso(self):
        cliente_id = self.cliente_combo.currentData()
        radicado = self.radicado_input.text().strip()
        tipo = self.tipo_input.text().strip()
        fecha_inicio = self.fecha_inicio_edit.date().toPyDate()
        fecha_fin = self.fecha_fin_edit.date().toPyDate() if self.fecha_fin_edit.date().isValid() else None
        estado = self.estado_input.text().strip()
        juzgado = self.juzgado_input.text().strip()
        observaciones = self.observaciones_input.toPlainText().strip()

        if not cliente_id or not radicado or not tipo or not estado or not juzgado:
            QMessageBox.warning(self, "Entrada Incompleta", "Por favor, complete todos los campos obligatorios (Cliente, Radicado, Tipo, Estado, Juzgado).")
            return

        if self.is_edit_mode:
            proceso_id = self.proceso_data['id']
            success = self.model.actualizar_proceso_por_id(
                proceso_id=proceso_id,
                cliente_id=cliente_id,
                radicado=radicado,
                tipo=tipo,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                estado=estado,
                juzgado=juzgado,
                observaciones=observaciones
            )
        else:
            success = self.model.agregar_proceso(
                cliente_id=cliente_id,
                radicado=radicado,
                tipo=tipo,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                estado=estado,
                juzgado=juzgado,
                observaciones=observaciones
            )

        if success:
            self.accept() # Cierra el diálogo y retorna QDialog.Accepted
        else:
            # El modelo ya emite la señal de error, solo necesitamos manejarla si hay un caso no cubierto.
            QMessageBox.critical(self, "Error de Operación", "No se pudo completar la operación. Verifique los datos e intente de nuevo.")


# --- Diálogo para Editar Movimiento Contable (si usas QListWidget para Contabilidad) ---
class ContabilidadMovimientoDialog(QDialog):
    def __init__(self, model: ProcesosModel, movimiento_data: dict, proceso_id: int, parent=None):
        super().__init__(parent)
        self.model = model
        self.movimiento_data = movimiento_data
        self.proceso_id = proceso_id

        self.setWindowTitle("Editar Movimiento Contable")
        self.setGeometry(300, 300, 400, 300)

        self.init_ui()
        self.populate_form()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QGridLayout()

        form_layout.addWidget(QLabel("Tipo:"), 0, 0)
        self.cont_type_combo = QComboBox()
        self.cont_type_combo.addItems(["Ingreso", "Egreso"])
        form_layout.addWidget(self.cont_type_combo, 0, 1)

        form_layout.addWidget(QLabel("Descripción:"), 1, 0)
        self.cont_description_input = QLineEdit()
        form_layout.addWidget(self.cont_description_input, 1, 1)

        form_layout.addWidget(QLabel("Valor:"), 2, 0)
        self.cont_value_input = QLineEdit()
        form_layout.addWidget(self.cont_value_input, 2, 1)

        form_layout.addWidget(QLabel("Fecha:"), 3, 0)
        self.cont_date_edit = QDateEdit()
        self.cont_date_edit.setCalendarPopup(True)
        self.cont_date_edit.setDisplayFormat("yyyy-MM-dd")
        form_layout.addWidget(self.cont_date_edit, 3, 1)

        layout.addLayout(form_layout)

        button_box = QHBoxLayout()
        save_button = QPushButton("Guardar Cambios")
        save_button.clicked.connect(self.save_changes)
        button_box.addWidget(save_button)

        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.reject)
        button_box.addWidget(cancel_button)

        layout.addLayout(button_box)

    def populate_form(self):
        self.cont_type_combo.setCurrentText(self.movimiento_data.get('tipo', ''))
        self.cont_description_input.setText(self.movimiento_data.get('descripcion', ''))
        self.cont_value_input.setText(str(self.movimiento_data.get('valor', '')))

        fecha_str = self.movimiento_data.get('fecha')
        if fecha_str:
            self.cont_date_edit.setDate(QDate.fromString(fecha_str, "yyyy-MM-dd"))

    def save_changes(self):
        tipo = self.cont_type_combo.currentText()
        descripcion = self.cont_description_input.text().strip()
        valor_str = self.cont_value_input.text().strip()
        fecha = self.cont_date_edit.date().toPyDate()

        if not descripcion or not valor_str:
            QMessageBox.warning(self, "Entrada Incompleta", "Por favor, ingrese descripción y valor.")
            return

        try:
            valor = float(valor_str)
        except ValueError:
            QMessageBox.warning(self, "Valor Inválido", "Por favor, ingrese un valor numérico válido.")
            return

        try:
            # El cliente_id se puede obtener del proceso padre o se pasa al diálogo si se conoce
            proceso_obj = self.model.get_proceso_by_id(self.proceso_id)
            cliente_id = proceso_obj.cliente_id if proceso_obj else None

            success = self.model.actualizar_movimiento_contable(
                movimiento_id=self.movimiento_data['id'],
                cliente_id=cliente_id,
                proceso_id=self.proceso_id, # Asegúrate de pasar el proceso_id
                tipo=tipo,
                descripcion=descripcion,
                valor=valor,
                fecha=fecha
            )
            if success:
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "No se pudo actualizar el movimiento contable.")
        except Exception as e:
            QMessageBox.critical(self, "Error al Actualizar", f"Ocurrió un error al actualizar el movimiento: {e}")