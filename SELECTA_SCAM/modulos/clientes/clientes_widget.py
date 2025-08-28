# SELECTA_SCAM/modulos/clientes/clientes_widget.py
import logging
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QHBoxLayout, QMessageBox, QDialog, 
                             QTableView, QHeaderView, QAbstractItemView, QApplication)
from PyQt5.QtCore import Qt, pyqtSignal
from .clientes_model import ClientesModel
from .cliente_editor_dialog import ClienteEditorDialog
from PyQt5.QtCore import (Qt, pyqtSignal, QModelIndex, QTimer, QEvent, 
                          QItemSelectionModel, QItemSelection)
logger = logging.getLogger(__name__)

class ClientesWidget(QWidget):
    def __init__(self, clientes_model_instance, user_data, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            /* --- Estilo para el Tooltip Personalizado --- */
            QLabel#CustomTooltip {
                background-color: #333333;
                color: white;
                border: 1px solid #5D566F;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 24px;
                font-weight: bold;
            }
            /* --- Estilos Unificados para Módulos --- */
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
            }
            QTableView {
                background-color: white;
                border: 1px solid #E0E0E0;
                gridline-color: #F0F0F0;
                border-radius: 8px;
                selection-background-color: #D36B92;
                selection-color: white;
                font-size: 26px;
            }
            QTableView::item {
                padding: 8px 10px;
            }
            QTableView::item:alternate {
                background-color: #FDF7FA;
            }
            QHeaderView::section {
                background-color: #F8F0F5;
                color: #5D566F;
                font-size: 18px;
                font-weight: bold;
                border-bottom: 2px solid #D36B92;
                padding: 10px;
            }
            QLineEdit, QComboBox, QDateEdit {
                padding: 10px 15px;
                border: 1px solid #CED4DA;
                border-radius: 6px;
                font-size: 24px;
                background-color: white;
            }
            QPushButton {
                background-color: #5D566F;
                color: white;
                border-radius: 6px;
                padding: 12px 25px; 
                font-size: 20px;
                font-weight: 600;
                border: none;
            }
            QPushButton:hover { background-color: #7B718D; }
            QPushButton:pressed { background-color: #4A445C; }
            QPushButton#btn_agregar, QPushButton#btn_toggle_form { background-color: #D36B92; }
            QPushButton#btn_editar { background-color: #5AA1B9; }
            QPushButton#btn_eliminar { background-color: #CC5555; }
        """)
        self.clientes_model = clientes_model_instance
        self.user_data = user_data
        self.init_ui()
        self.update_button_states()
        self.mostrando_papelera = False 

        self.connect_signals()
        self.clientes_model.error_occurred.connect(lambda msg: QMessageBox.critical(self, "Error", msg))
        self.clientes_model.return_to_active_view.connect(self.handle_return_to_active_view)
        self.clientes_model.load_data()
    def init_ui(self):
        # Este UI es básico. Puedes adaptarlo a tu diseño original.
        layout = QVBoxLayout(self)
        self.title_label = QLabel("Gestor de Clientes")
        self.title_label.setObjectName("mainTitle") # Conecta con el estilo
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)
        top_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por Nombre o ID...")
        self.btn_agregar = QPushButton("Nuevo Cliente")
        top_layout.addWidget(self.search_input)
        top_layout.addWidget(self.btn_agregar)
        
        self.table_view = QTableView()

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
        
        self.table_view.setModel(self.clientes_model)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.table_view.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table_view.verticalHeader().setSectionsClickable(True)

        # --- Botones Inferiores ---
        bottom_layout = QHBoxLayout()
        self.btn_editar = QPushButton("Editar")
        self.btn_eliminar = QPushButton("Enviar a Papelera") # Texto cambiado
        self.btn_papelera = QPushButton("Ver Papelera")
        
        # Botones que solo aparecen en la vista de papelera
        self.btn_recuperar = QPushButton("Recuperar")
        self.btn_eliminar_def = QPushButton("Eliminar Definitivamente")
        self.btn_recuperar.hide() # Oculto por defecto
        self.btn_eliminar_def.hide() # Oculto por defecto

        bottom_layout.addWidget(self.btn_papelera)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.btn_recuperar)
        bottom_layout.addWidget(self.btn_eliminar_def)
        bottom_layout.addWidget(self.btn_editar)
        bottom_layout.addWidget(self.btn_eliminar)

        layout.addLayout(top_layout)
        layout.addWidget(self.table_view)
        layout.addLayout(bottom_layout)

    def filtrar_datos(self):
        """Llama a load_data respetando si la vista de papelera está activa."""
        texto_busqueda = self.search_input.text()
        self.clientes_model.load_data(query=texto_busqueda, solo_eliminados=self.mostrando_papelera)

    def toggle_papelera_view(self):
        """El interruptor principal entre la vista de activos y la papelera."""
        self.mostrando_papelera = not self.mostrando_papelera
        
        is_papelera = self.mostrando_papelera
        
        self.title_label.setText("Papelera de Clientes" if is_papelera else "Lista de Clientes")
        self.btn_papelera.setText("Ver Clientes Activos" if is_papelera else "Ver Papelera")
        
        # Ocultar o mostrar botones según la vista
        self.btn_agregar.setVisible(not is_papelera)
        self.btn_editar.setVisible(not is_papelera)
        self.btn_eliminar.setVisible(not is_papelera)
        
        self.btn_recuperar.setVisible(is_papelera)
        self.btn_eliminar_def.setVisible(is_papelera)
        
        # Cargar los datos correspondientes
        self.clientes_model.load_data(solo_eliminados=is_papelera)

    # En: SELECTA_SCAM/modulos/clientes/clientes_widget.py

    def eliminar_cliente_logico(self):
        """
        Envía uno o varios clientes seleccionados a la papelera.
        """
        # 1. Obtenemos las filas seleccionadas (esto ya lo tenías)
        indices = self.table_view.selectionModel().selectedRows()
        if not indices:
            QMessageBox.warning(self, "Atención", "Por favor, seleccione una o más filas para eliminar.")
            return

        # --- INICIO DE LA CORRECCIÓN ---
        # 2. Creamos una LISTA para guardar todos los IDs
        ids_para_eliminar = []
        nombres_para_mostrar = []
        for index in indices:
            # Obtenemos el ID (índice 0) y el nombre (índice 1) de los datos
            record_id = self.clientes_model._data[index.row()][0]
            nombre = self.clientes_model._data[index.row()][1]
            if record_id is not None:
                ids_para_eliminar.append(record_id)
                nombres_para_mostrar.append(nombre)
        
        if not ids_para_eliminar:
            QMessageBox.critical(self, "Error", "No se pudieron obtener los IDs de los registros seleccionados.")
            return

        # 3. Pedimos confirmación para el lote
        mensaje = f"¿Está seguro de que desea enviar {len(ids_para_eliminar)} cliente(s) a la papelera?\n\n- {', '.join(nombres_para_mostrar[:5])}"
        if len(nombres_para_mostrar) > 5:
            mensaje += ", ..."

        confirm = QMessageBox.question(self, "Confirmar Eliminación", mensaje,
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if confirm == QMessageBox.Yes:
            # 4. Pasamos la LISTA completa de IDs al modelo
            self.clientes_model.marcar_como_eliminado(ids_para_eliminar)
        # --- FIN DE LA CORRECCIÓN ---

    def recuperar_cliente(self):
        """Restaura uno o varios clientes seleccionados desde la papelera."""
        indices = self.table_view.selectionModel().selectedRows()
        if not indices:
            QMessageBox.warning(self, "Atención", "Por favor, seleccione una o más filas para recuperar.")
            return

        ids_para_recuperar = [self.clientes_model._data[index.row()][0] for index in indices]
        
        if not ids_para_recuperar:
            QMessageBox.critical(self, "Error", "No se pudieron obtener los IDs de los registros seleccionados.")
            return

        # Pasamos la lista completa de IDs al modelo
        self.clientes_model.restaurar_clientes(ids_para_recuperar)
        
    def eliminar_cliente_definitivo(self):
        """Elimina permanentemente el/los cliente(s) seleccionado(s)."""
        indices = self.table_view.selectionModel().selectedRows()
        if not indices:
            QMessageBox.warning(self, "Atención", "Por favor, seleccione una o más filas para eliminar.")
            return

        ids_para_eliminar = [self.clientes_model._data[index.row()][0] for index in indices]
        
        confirm = QMessageBox.question(self, "Confirmación Final", 
            f"¿Está seguro de que desea ELIMINAR PERMANENTEMENTE {len(ids_para_eliminar)} cliente(s)?\n\n¡Esta acción no se puede deshacer!",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
        if confirm == QMessageBox.Yes:
            self.clientes_model.eliminar_definitivo(ids_para_eliminar)

    def show_custom_tooltip(self, index: QModelIndex):
        if not index.isValid():
            self.custom_tooltip_label.hide()
            return

        # Usamos el modelo de la tabla de clientes
        value = self.clientes_model.data(index, Qt.DisplayRole)
        tooltip_text = str(value)
        
        if not tooltip_text:
            self.custom_tooltip_label.hide()
            return

        self.custom_tooltip_label.setText(tooltip_text)
        self.custom_tooltip_label.adjustSize()

        rect = self.table_view.visualRect(index)
        global_pos = self.table_view.mapToGlobal(rect.center())
        
        # Posicionamos el tooltip arriba del centro de la celda
        tooltip_x = global_pos.x() - self.custom_tooltip_label.width() // 2
        tooltip_y = global_pos.y() - self.custom_tooltip_label.height() - 5

        self.custom_tooltip_label.move(tooltip_x, tooltip_y)
        self.custom_tooltip_label.show()
        
        self.hide_tooltip_timer.start(5000) # El tooltip dura 5 segundos

    def eventFilter(self, source, event):
        if source == self.table_view.viewport():
            if event.type() == event.MouseMove:
                pos = event.pos()
                index = self.table_view.indexAt(pos)
                if not index.isValid():
                    self.custom_tooltip_label.hide()
                elif index != self._last_hovered_index:
                    self.show_custom_tooltip(index)
                self._last_hovered_index = index
            
            elif event.type() == event.Leave:
                self.custom_tooltip_label.hide()
        
        return super().eventFilter(source, event)



    # En: SELECTA_SCAM/modulos/clientes/clientes_widget.py

    def connect_signals(self):
        self.btn_agregar.clicked.connect(self.agregar_cliente)
        self.btn_editar.clicked.connect(self.editar_cliente)
        self.search_input.textChanged.connect(self.filtrar_datos)
        
        # Conexiones de la nueva funcionalidad de papelera
        self.btn_eliminar.clicked.connect(self.eliminar_cliente_logico)
        self.btn_papelera.clicked.connect(self.toggle_papelera_view)
        self.btn_recuperar.clicked.connect(self.recuperar_cliente)
        self.btn_eliminar_def.clicked.connect(self.eliminar_cliente_definitivo)

        # Conexiones de la tabla que ya tenías
        self.table_view.selectionModel().selectionChanged.connect(self.update_button_states)
        self.table_view.verticalHeader().sectionClicked.connect(self.seleccionar_fila_completa)
        self.original_keyPressEvent = self.table_view.keyPressEvent
        self.table_view.keyPressEvent = self.custom_keyPressEvent

    def custom_keyPressEvent(self, event):
        """Intercepta Ctrl+C para llamar a nuestra función de copiado."""
        if event.key() == Qt.Key_C and (event.modifiers() & Qt.ControlModifier):
            self.copy_selection_to_clipboard()
        else:
            self.original_keyPressEvent(event)
    

    # En: SELECTA_SCAM/modulos/clientes/clientes_widget.py

    def seleccionar_fila_completa(self, logicalIndex):
        """
        Selecciona filas de forma inteligente al hacer clic en el encabezado vertical.
        - Clic: Selecciona solo esta fila.
        - Ctrl+Clic: Añade/quita esta fila de la selección.
        - Shift+Clic: Selecciona un rango de filas.
        """
        selection_model = self.table_view.selectionModel()
        modifiers = QApplication.keyboardModifiers()

        # Define el rango de la fila que se ha clickeado
        top_left_index = self.clientes_model.index(logicalIndex, 0)
        bottom_right_index = self.clientes_model.index(logicalIndex, self.clientes_model.columnCount() - 1)
        selection = QItemSelection(top_left_index, bottom_right_index)

        if modifiers == Qt.ControlModifier:
            # Con Ctrl, alterna la selección de la fila (la añade o la quita si ya está)
            selection_model.select(selection, QItemSelectionModel.Toggle)
        elif modifiers == Qt.ShiftModifier:
            # Con Shift, extiende la selección hasta la fila actual
            # (El comportamiento por defecto de ExtendedSelection ya maneja esto bien,
            # pero lo forzamos para mayor claridad)
            current_index = self.table_view.currentIndex()
            selection_model.select(QItemSelection(current_index, top_left_index), QItemSelectionModel.Select)
        else:
            # Sin modificadores, limpia todo y selecciona solo la fila actual
            selection_model.clear()
            selection_model.select(selection, QItemSelectionModel.Select)

    def copy_selection_to_clipboard(self):
        """Copia las celdas seleccionadas al portapapeles."""
        selection = self.table_view.selectionModel().selectedIndexes()
        if not selection:
            return

        rows = sorted(list(set(index.row() for index in selection)))
        cols = sorted(list(set(index.column() for index in selection)))
        
        table_data = [['' for _ in cols] for _ in rows]
        for index in selection:
            row_idx = rows.index(index.row())
            col_idx = cols.index(index.column())
            table_data[row_idx][col_idx] = index.data()

        clipboard_string = "\n".join(["\t".join(map(str, row)) for row in table_data])
        QApplication.clipboard().setText(clipboard_string)


    def agregar_cliente(self):
        dialogo = ClienteEditorDialog(parent=self)
        if dialogo.exec_() == QDialog.Accepted:
            datos_nuevos = dialogo.get_data()
            self.clientes_model.agregar_cliente(**datos_nuevos)

    # En: SELECTA_SCAM/modulos/clientes/clientes_widget.py

    def update_button_states(self):
        """
        Habilita o deshabilita los botones de acción basados en la selección.
        """
        # Verificamos si hay CUALQUIER celda seleccionada
        has_any_selection = self.table_view.selectionModel().hasSelection()
        
        # Obtenemos las filas completas seleccionadas
        selected_rows = self.table_view.selectionModel().selectedRows()
        
        # El botón "Editar" se activa si hay cualquier tipo de selección
        self.btn_editar.setEnabled(has_any_selection)
        
        # El botón "Eliminar" se activa si hay una o más filas completas seleccionadas
        self.btn_eliminar.setEnabled(len(selected_rows) > 0)

    def editar_cliente(self):
        """
        Abre el diálogo para editar un cliente, validando de forma inteligente
        el tipo de selección del usuario.
        """
        selection_model = self.table_view.selectionModel()

        # Obtenemos tanto las filas completas como las celdas individuales
        selected_rows = selection_model.selectedRows()
        
        # --- LÓGICA DE VALIDACIÓN ---
        # Caso 1: Hay MÁS DE UNA fila completa seleccionada.
        if len(selected_rows) > 1:
            QMessageBox.warning(self, "Selección Múltiple", "Solo puede editar un cliente a la vez. Por favor, seleccione una sola fila.")
            return
        
        # Caso 2: Hay CELDAS seleccionadas, pero no una fila completa.
        if not selected_rows and selection_model.hasSelection():
            QMessageBox.information(self, "Instrucción", "Para editar, por favor seleccione la fila completa haciendo clic en el número de la izquierda.")
            return
            
        # Caso 3: No hay NINGUNA fila seleccionada.
        if not selected_rows:
            QMessageBox.warning(self, "Sin Selección", "Por favor, seleccione la fila del cliente que desea editar.")
            return
        # --- FIN DE LA LÓGICA ---

        # Si se pasa la validación, significa que hay exactamente UNA fila seleccionada.
        fila_seleccionada = selected_rows[0].row()
        cliente_para_editar = self.clientes_model.get_cliente_para_editar(fila_seleccionada)
        
        if not cliente_para_editar:
            QMessageBox.critical(self, "Error", "No se pudieron obtener los datos del cliente seleccionado.")
            return

        dialogo = ClienteEditorDialog(cliente_para_editar, self)
        if dialogo.exec_() == QDialog.Accepted:
            datos_actualizados = dialogo.get_data()
            self.clientes_model.actualizar_cliente(cliente_para_editar['id'], **datos_actualizados)


    def handle_return_to_active_view(self):
        """
        Se activa cuando la papelera se queda vacía.
        Muestra un mensaje y cambia a la vista de clientes activos.
        """
        QMessageBox.information(self, "Papelera Vacía", "No hay más clientes en la papelera. Volviendo a la vista de clientes activos.")
        # Llamamos a la función que ya sabe cómo cambiar de vista
        self.toggle_papelera_view()

    def eliminar_cliente(self):
        """
        Marca uno o varios clientes seleccionados como eliminados (eliminación lógica).
        """
        # 1. Obtenemos las filas seleccionadas (esto ya lo tenías)
        indices = self.table_view.selectionModel().selectedRows()
        if not indices:
            QMessageBox.warning(self, "Atención", "Por favor, seleccione una o más filas para eliminar.")
            return

        # --- INICIO DEL CÓDIGO FALTANTE ---
        # 2. Creamos una lista para guardar todos los IDs de las filas seleccionadas
        ids_para_eliminar = []
        nombres_para_mostrar = []
        for index in indices:
            # Obtenemos el ID (índice 0) y el nombre (índice 1) de los datos de la tabla
            record_id = self.clientes_model._data[index.row()][0]
            nombre = self.clientes_model._data[index.row()][1]
            if record_id is not None:
                ids_para_eliminar.append(record_id)
                nombres_para_mostrar.append(nombre)
        
        if not ids_para_eliminar:
            QMessageBox.critical(self, "Error", "No se pudieron obtener los IDs de los registros seleccionados.")
            return

        # 3. Pedimos una única confirmación para el lote, mostrando los nombres
        mensaje = f"¿Está seguro de que desea enviar {len(ids_para_eliminar)} cliente(s) a la papelera?\n\n- {', '.join(nombres_para_mostrar[:5])}"
        if len(nombres_para_mostrar) > 5:
            mensaje += ", ..."

        confirm = QMessageBox.question(self, "Confirmar Eliminación", mensaje,
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if confirm == QMessageBox.Yes:
            # 4. Pasamos la LISTA completa de IDs al modelo para que los elimine
            self.clientes_model.marcar_como_eliminado(ids_para_eliminar)
        # --- FIN DEL CÓDIGO FALTANTE ---