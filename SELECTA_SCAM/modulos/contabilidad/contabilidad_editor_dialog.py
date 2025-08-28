# Contenido actualizado de ContabilidadEditorDialog.py

from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QComboBox, QLineEdit, QDateEdit, QDialogButtonBox, QMessageBox, QLabel,
    QListWidget, QListWidgetItem, QGridLayout, QVBoxLayout, QWidget, QHBoxLayout
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal, QVariant
import logging
from PyQt5.QtGui import QFont
logger = logging.getLogger(__name__)

# Definir una constante para el modo de búsqueda
SEARCH_MODE = "SEARCH_MODE"

class ContabilidadEditorDialog(QDialog):
    cliente_selected = pyqtSignal(int)
    
    def __init__(self, contabilidad_data=None, clientes_data=None, procesos_data=None, tipos_data=None, clientes_logic=None, parent=None):
        # IMPORTANTE: Llamar a super().__init__(parent) primero
        super().__init__(parent)
        self.input_font = QFont()
        self.input_font.setPointSize(22)

        # Inicializar otros atributos
        self.contabilidad_data = contabilidad_data
        self.clientes_data = clientes_data
        self.procesos_data = procesos_data
        self.tipos_data = tipos_data
        self.clientes_logic = clientes_logic
        self.parent_widget = parent
        
        self.setWindowTitle("Editar Registro de Contabilidad" if contabilidad_data else "Agregar Registro de Contabilidad")
        self.setMinimumSize(700, 700)
        
        self.contabilidad_data = contabilidad_data
        self.clientes_data = clientes_data if clientes_data is not None else []
        self.procesos_initial_data = procesos_data if procesos_data is not None else []
        self.tipos_data = tipos_data if tipos_data is not None else []
        self.clientes_logic = clientes_logic # Almacenar la instancia de ClientesLogic

        self.init_ui()
        self.load_data_into_form()
        
        self.setFont(self.input_font)
        self.connect_search_signals()
        
        self.setStyleSheet("""
            QDialog {
                background-color: #F8F0F5;
                color: #333333;
                font-family: 'Segoe UI', 'Arial', sans-serif;
            }
            QLabel {
                color: #5D566F;
                font-size: 15px;
                font-weight: 700;
                padding-right: 5px;
            }
           
            #dialogoInput {
                font-size: 30px; /* <-- ¡EL TAMAÑO QUE QUIERES! */
                padding: 8px 12px;
                border: 1px solid #CED4DA;
                border-radius: 5px;
                color: #495057;
                background-color: white;
            }
            QLineEdit::placeholder {
                color: #ADB5BD;
            }
            QDateEdit::drop-down {
                border-left: 1px solid #CED4DA;
                width: 20px;
            }
            QComboBox::drop-down {
                border-left: 1px solid #CED4DA;
                width: 20px;
            }
            QDialogButtonBox QPushButton {
                background-color: #D36B92;
                color: white;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 600;
                border: none;
            }
            QDialogButtonBox QPushButton:hover {
                background-color: #E279A1;
            }
            QDialogButtonBox QPushButton:pressed {
                background-color: #B85F7F;
            }
            
            /* Estilos específicos para la búsqueda de clientes */
            QLineEdit#cliente_search_input {
                
            }
            QListWidget#cliente_search_results_list {
                border: 1px solid #CED4DA;
                border-radius: 5px;
                background-color: #FFFFFF;
                padding: 5px;
            }
            QListWidget#cliente_search_results_list::item {
                padding: 5px;
            }
            QListWidget#cliente_search_results_list::item:hover {
                background-color: #F8F0F5;
            }
        """)

    # Dentro de ContabilidadEditorDialog.py

    def init_ui(self):
        """
        Configuración de la interfaz de usuario del diálogo, incluyendo los elementos de búsqueda.
        """
        # IMPORTANTE: Inicializar el layout sin pasar 'self' para evitar el error QLayout
        self.main_layout = QVBoxLayout()
        
        # Layout para los campos del formulario
        form_layout = QFormLayout()
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(15)

        # Sección de Cliente (Incluye el QComboBox principal y la sección de búsqueda oculta)
        self.cliente_section_layout = QVBoxLayout()
        
        # 1. QComboBox principal para Cliente
        self.cliente_input = QComboBox()
        self.cliente_input.setObjectName("dialogoInput")
        self.cliente_input.setPlaceholderText("Seleccione cliente")
        # Usar self.input_font
        self.cliente_input.setFont(self.input_font) 
        self.cliente_input.currentIndexChanged.connect(self.on_cliente_selected)
        self.cliente_input.activated.connect(self.on_cliente_combo_changed) 
        self.populate_cliente_combo()
        
        # 2. Widgets de búsqueda (inicialmente ocultos)
        self.cliente_search_input = QLineEdit()
        self.cliente_search_input.setObjectName("dialogoInput")
        self.cliente_search_input.setObjectName("cliente_search_input")
        self.cliente_search_input.setPlaceholderText("Buscar cliente por nombre o ID...")
        # Usar self.search_input_font
        self.cliente_search_input.setFont(self.input_font   ) 
        self.cliente_search_input.hide()
        
        self.cliente_search_results_list = QListWidget()
        self.cliente_search_results_list.setObjectName("dialogoInput")
        self.cliente_search_results_list.setObjectName("cliente_search_results_list")
        self.cliente_search_results_list.setMaximumHeight(300)
        # Usar self.input_font
        self.cliente_search_results_list.setFont(self.input_font) 
        self.cliente_search_results_list.setSizePolicy(
            self.cliente_search_results_list.sizePolicy().Expanding, 
            self.cliente_search_results_list.sizePolicy().Expanding
        )
        self.cliente_search_results_list.hide()

        # Añadir los widgets al layout de sección de cliente
        self.cliente_section_layout.addWidget(self.cliente_input)
        self.cliente_section_layout.addWidget(self.cliente_search_input)
        self.cliente_section_layout.addWidget(self.cliente_search_results_list)

        # Añadir la sección completa de cliente al layout principal del formulario
        form_layout.addRow("Cliente:", self.cliente_section_layout)

        # Resto de campos (Proceso, Tipo, Descripción, Valor, Fecha)
        # Asegurarse de usar self.input_font para todos estos campos
        self.proceso_input = QComboBox()
        self.proceso_input.setObjectName("dialogoInput")
        self.proceso_input.setPlaceholderText("Seleccione proceso (opcional)")
        self.populate_proceso_combo(self.procesos_initial_data)
        self.proceso_input.setFont(self.input_font)
        form_layout.addRow("Proceso:", self.proceso_input)

        self.tipo_input = QComboBox()
        self.tipo_input.setObjectName("dialogoInput")
        self.tipo_input.setPlaceholderText("Seleccione tipo")
        self.populate_tipo_combo()
        self.tipo_input.setFont(self.input_font)
        form_layout.addRow("Tipo:", self.tipo_input)

        self.descripcion_input = QLineEdit()
        self.descripcion_input.setObjectName("dialogoInput")
        self.descripcion_input.setPlaceholderText("Ingrese descripción")
        self.descripcion_input.setFont(self.input_font)
        form_layout.addRow("Descripción:", self.descripcion_input)

        self.valor_input = QLineEdit()
        self.valor_input.setObjectName("dialogoInput")
        self.valor_input.setPlaceholderText("Ingrese valor")
        self.valor_input.setFont(self.input_font)
        form_layout.addRow("Valor ($):", self.valor_input)

        self.fecha_input = QDateEdit()
        self.fecha_input.setObjectName("dialogoInput")
        self.fecha_input.setFont(self.input_font)
        self.fecha_input.setCalendarPopup(True)
        self.fecha_input.setDisplayFormat("yyyy-MM-dd")
        self.fecha_input.setDate(QDate.currentDate())
        form_layout.addRow("Fecha:", self.fecha_input)
        
        self.main_layout.addLayout(form_layout)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.main_layout.addWidget(self.buttons)
        
        # IMPORTANTE: Asignar el layout al diálogo aquí
        self.setLayout(self.main_layout)

    def validate_and_accept(self):
        """
        Método que valida los datos del formulario.
        Si la validación es exitosa, cierra el diálogo con QDialog.Accepted.
        """
        data = self.get_values()
        if data:
            self.accept() # Esto cierra el diálogo si get_values retorna datos válidos.
        # Si get_values() retorna None (datos inválidos), el diálogo no se cierra.
        
    def connect_search_signals(self):
        """Conecta las señales para la funcionalidad de búsqueda."""
        self.cliente_search_input.textChanged.connect(self.on_cliente_search_input_changed)
        self.cliente_search_results_list.itemClicked.connect(self.on_cliente_search_result_selected)
   
    def populate_cliente_combo(self):
        """
        Popula el QComboBox de clientes, añadiendo la opción de búsqueda.
        """
        self.cliente_input.blockSignals(True)
        self.cliente_input.clear()
        
        # Añadir la opción de búsqueda
        self.cliente_input.addItem("🔍 Buscar Cliente...", SEARCH_MODE)
        
        # Añadir clientes existentes
        # Los clientes_data ya deberían tener el formato [(id, nombre)]
        for cliente_id, nombre in self.clientes_data:
            self.cliente_input.addItem(nombre, cliente_id)
            
        self.cliente_input.setCurrentIndex(0) # Seleccionar "Buscar Cliente..." por defecto
        self.cliente_input.blockSignals(False)

    def populate_proceso_combo(self, procesos_data: list):
        self.proceso_input.blockSignals(True)
        self.proceso_input.clear()
        self.proceso_input.addItem("Sin proceso asociado (opcional)", None)
        for proceso_id, radicado in procesos_data:
            self.proceso_input.addItem(radicado, proceso_id)
        self.proceso_input.setCurrentIndex(0)
        self.proceso_input.blockSignals(False)

    def populate_tipo_combo(self):
        self.tipo_input.blockSignals(True)
        self.tipo_input.clear()
        # Añadir un item por defecto con ID None
        self.tipo_input.addItem("Seleccione tipo...", None)
        # Iterar sobre los datos de tipo y guardar el ID en `userData`
        for tipo in self.tipos_data:
            self.tipo_input.addItem(tipo.nombre, tipo.id)
        self.tipo_input.setCurrentIndex(0)
        self.tipo_input.blockSignals(False)
    def update_proceso_combo_dialog(self, procesos_data: list):
        self.populate_proceso_combo(procesos_data)
        # Si estamos editando y el proceso ya existía, intentamos seleccionarlo
        if self.contabilidad_data and self.contabilidad_data[2]: # contabilidad_data[2] es el nombre del proceso
            index = self.proceso_input.findText(self.contabilidad_data[2])
            if index != -1:
                self.proceso_input.setCurrentIndex(index)

    def on_cliente_selected(self, index):
        """
        Maneja la selección de un cliente. Si no está en modo búsqueda, 
        emite la señal para cargar procesos.
        """
        cliente_id = self.cliente_input.currentData()
        
        # Solo emitir la señal si se ha seleccionado un cliente real, no el modo búsqueda
        if cliente_id is not None and cliente_id != SEARCH_MODE:
            self.cliente_selected.emit(cliente_id)
        elif cliente_id is None:
            # Si se selecciona el placeholder "Seleccione cliente...", limpiar procesos
            self.populate_proceso_combo([])

    def load_data_into_form(self):
        # Esta función necesita ajustarse para manejar el caso de edición
        # cuando un cliente ya ha sido seleccionado en el diálogo.
        if self.contabilidad_data:
            # contabilidad_data = (id, cliente_nombre, proceso_radicado, tipo, descripcion, valor, fecha)
            
            # Cargar Cliente: Intentar encontrar el nombre del cliente en el QComboBox
            cliente_nombre_a_seleccionar = self.contabilidad_data[1]
            index_cliente = self.cliente_input.findText(cliente_nombre_a_seleccionar)
            
            if index_cliente != -1:
                self.cliente_input.setCurrentIndex(index_cliente)
                # NOTA: on_cliente_selected se dispara aquí y pedirá los procesos
            else:
                self.cliente_input.setCurrentIndex(0) # Si no se encuentra, seleccionar "Buscar Cliente..."

            # Cargar Proceso: Esto se manejará en update_proceso_combo_dialog.

            # Cargar Tipo
            tipo_a_seleccionar = self.contabilidad_data[3]
            index_tipo = self.tipo_input.findText(tipo_a_seleccionar)
            if index_tipo != -1:
                self.tipo_input.setCurrentIndex(index_tipo)
            else:
                self.tipo_input.setCurrentIndex(0)
            
            self.descripcion_input.setText(self.contabilidad_data[4])
            
            valor_str = str(self.contabilidad_data[5]).replace("$", "").replace(",", "")
            self.valor_input.setText(valor_str)
            
            fecha_qdate = QDate.fromString(self.contabilidad_data[6], "yyyy-MM-dd")
            if fecha_qdate.isValid():
                self.fecha_input.setDate(fecha_qdate)

    def get_values(self):
        cliente_id = self.cliente_input.currentData()
        if cliente_id == SEARCH_MODE or cliente_id is None:
            QMessageBox.warning(self, "Advertencia", "Debe seleccionar un cliente válido para guardar el registro.")
            return None
        
        # Validación del tipo
        tipo_id = self.tipo_input.currentData()
        if tipo_id is None:
            QMessageBox.warning(self, "Advertencia", "Debe seleccionar un tipo de registro válido.")
            return None
        
        valor_str = self.valor_input.text().strip()
        
        if not valor_str:
            QMessageBox.warning(self, "Advertencia", "El campo Valor no puede estar vacío.")
            return None

        try:
            valor_numeric = float(valor_str)
        except ValueError:
            QMessageBox.warning(self, "Advertencia", "El campo Valor debe ser un número válido.")
            return None

        # Crea el diccionario con los datos
        datos = {
            "cliente_id": cliente_id,
            "proceso_id": self.proceso_input.currentData(),
            "tipo_id": tipo_id,
            "descripcion": self.descripcion_input.text().strip(),
            "valor": valor_numeric,
            "fecha": self.fecha_input.date().toString("yyyy-MM-dd")
        }
        
        # Ahora, el `print` se ejecutará correctamente
        print(f"DEBUG DIALOG: Valores devueltos: {datos}")

        return datos
    def on_cliente_combo_changed(self, index):
        """
        Activa o desactiva el modo de búsqueda de cliente si se selecciona 
        la opción 'Buscar Cliente...' en el QComboBox.
        """
        selected_data = self.cliente_input.itemData(index)
        
        # Comprobar si se ha seleccionado la opción de búsqueda
        if selected_data == SEARCH_MODE:
            logger.debug("ContabilidadEditorDialog: Activando modo de búsqueda de cliente.")
            self.toggle_cliente_search_mode(True)
            self.cliente_search_input.setFocus() # Poner el foco en el campo de búsqueda
        else:
            logger.debug("ContabilidadEditorDialog: Desactivando modo de búsqueda de cliente.")
            self.toggle_cliente_search_mode(False)

    def toggle_cliente_search_mode(self, enable: bool):
        """
        Muestra u oculta los campos de búsqueda de cliente y la lista de resultados.
        Asegura la visibilidad y el estado de los widgets.
        """
        if enable:
            logger.debug("ContabilidadEditorDialog: Activando modo de búsqueda de cliente.")
            # Ocultar el QComboBox principal y deshabilitarlo
            self.cliente_input.setVisible(False)
            self.cliente_input.setEnabled(False)
            
            # Mostrar el campo de búsqueda y la lista de resultados
            self.cliente_search_input.setVisible(True)
            self.cliente_search_results_list.setVisible(True)
            
            # Limpiar y preparar la búsqueda
            self.cliente_search_input.clear()
            self.cliente_search_input.setFocus() # Poner el foco en el campo de búsqueda
            self.cliente_search_results_list.clear()
            self.cliente_search_results_list.addItem("Comience a escribir para buscar clientes...")
        else:
            logger.debug("ContabilidadEditorDialog: Desactivando modo de búsqueda de cliente.")
            # Mostrar el QComboBox principal y habilitarlo
            self.cliente_input.setVisible(True)
            self.cliente_input.setEnabled(True)
            
            # Ocultar el campo de búsqueda y la lista de resultados
            self.cliente_search_input.setVisible(False)
            self.cliente_search_results_list.setVisible(False)
            
            # Limpiar el campo de búsqueda (opcional, pero buena práctica)
            self.cliente_search_input.clear()
            self.cliente_search_results_list.clear()


    def on_cliente_search_input_changed(self, text: str):
        """
        Realiza la búsqueda de clientes y actualiza la QListWidget.
        """
        self.cliente_search_results_list.clear() # Limpiar resultados anteriores
        
        # CAMBIO 1: Iniciar búsqueda con el primer carácter (len(text) >= 1)
        if len(text) >= 1 and self.clientes_logic: 
            try:
                matching_clients = self.clientes_logic.search_clientes(text)
                
                if matching_clients:
                    for client in matching_clients:
                        # Acceder a los elementos por índice de tupla (0=ID, 1=Nombre)
                        client_id = client[0] 
                        client_name = client[1]
                        
                        item = QListWidgetItem(f"{client_name} (ID: {client_id})")
                        item.setData(Qt.UserRole, client_id)
                        self.cliente_search_results_list.addItem(item)
                else:
                    self.cliente_search_results_list.addItem("No se encontraron clientes.")
            except Exception as e:
                logger.error(f"Error al buscar clientes en el diálogo: {e}")
                self.cliente_search_results_list.addItem("Error al buscar.")
        elif len(text) < 1:
            # CAMBIO 2: Si el texto está vacío, asegúrate de que la lista esté vacía
            self.cliente_search_results_list.addItem("Comience a escribir para buscar clientes...")
    def on_cliente_search_result_selected(self, item: QListWidgetItem):
        """
        Maneja la selección de un cliente de la lista de resultados de búsqueda.
        Inserta el cliente seleccionado en el QComboBox y vuelve al modo normal.
        """
        cliente_id = item.data(Qt.UserRole)
        if cliente_id is None:
            logger.warning("ContabilidadEditorDialog: Selección de búsqueda inválida (ID no encontrado).")
            return

        cliente_nombre = item.text() # El texto del ítem ahora es solo el nombre.

        # Buscar si el cliente ya existe en el ComboBox
        index = self.cliente_input.findData(cliente_id)

        if index == -1:
            # Si no existe, agregarlo al final del ComboBox
            self.cliente_input.addItem(cliente_nombre, cliente_id)
            index = self.cliente_input.findData(cliente_id)

        # Bloquear señales temporalmente para evitar disparar on_cliente_selected
        self.cliente_input.blockSignals(True)
        self.cliente_input.setCurrentIndex(index)
        self.cliente_input.blockSignals(False)

        # Volver al modo normal (ocultar campos de búsqueda)
        self.toggle_cliente_search_mode(False)
        
        # Emitir la señal para que el controlador principal cargue los procesos
        self.cliente_selected.emit(cliente_id)
