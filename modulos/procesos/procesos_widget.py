
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
from utils.db_manager import DBManager
import os
from modulos.procesos.procesos_contabilidad import ContabilidadTab
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QMessageBox, QHeaderView, QComboBox, QFileDialog, QDateEdit,
    QListWidgetItem, QListWidget, QTabWidget, QStyledItemDelegate
)
from modulos.procesos.procesos_documentos import DocumentosTab

from PyQt5.QtWidgets import QCalendarWidget
from PyQt5.QtWidgets import QStyledItemDelegate
from PyQt5.QtGui import QFont
import webbrowser
from PyQt5.QtWidgets import QDialog, QFormLayout, QDialogButtonBox
class AlignedDelegate(QStyledItemDelegate):
    def __init__(self, alignment, parent=None):
        super().__init__(parent)
        self.alignment = alignment

    def paint(self, painter, option, index):
        option.displayAlignment = self.alignment  # Establecer la alineación en la opción
        super().paint(painter, option, index)


class ProcesosWidget(QWidget):
    def __init__(self, db, model):
        super().__init__()
        self.db = db
        self.model = model  # ProcesosModel

        self.selected_proceso_id = None  # <--- Aquí agregas esta línea para inicializar

        self.init_ui()  # Mover todo el layout y widgets a init_ui()
        self.load_data()  # Cargar los datos de procesos

    def init_ui(self):
        layout = QVBoxLayout()
        fuente_boton = QFont("Arial", 14)

        estilo_boton = """
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border-radius: 10px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """

        self.setMinimumSize(1000, 800)
        self.setStyleSheet("font-family: Times New Roman; font-size: 18px;")

        # Filtros
        self.filtro_estado = QComboBox()
        self.filtro_estado.addItems(["Todos", "Activo", "Finalizado", "Archivado"])
        self.filtro_estado.currentTextChanged.connect(self.filtrar_tabla)

        self.filtro_cliente = QComboBox()
        self.filtro_cliente.addItem("Todos")
        for cliente in self.db.get_clientes():
            self.filtro_cliente.addItem(cliente[1])  # Agrega el nombre del cliente
        self.filtro_cliente.currentTextChanged.connect(self.filtrar_tabla)

        self.filtro_radicado = QLineEdit()
        self.filtro_radicado.setPlaceholderText("Buscar por radicado...")
        self.filtro_radicado.textChanged.connect(self.filtrar_tabla)

        filtro_layout = QHBoxLayout()
        filtro_layout.addWidget(QLabel("Estado:"))
        filtro_layout.addWidget(self.filtro_estado)
        filtro_layout.addWidget(QLabel("Cliente:"))
        filtro_layout.addWidget(self.filtro_cliente)
        filtro_layout.addWidget(QLabel("Radicado:"))
        filtro_layout.addWidget(self.filtro_radicado)

        layout.addLayout(filtro_layout)

        # Tabla de Procesos
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Cliente", "Clase", "Radicado", "Estado", "Fecha de Inicio", "Fecha de Fin"])

        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)  # Colores alternos en las filas para mayor claridad
        self.table.setShowGrid(True)  # Mostrar la rejilla
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)  # Ajuste automático de columnas
        self.table.verticalHeader().setVisible(False)  # Ocultar el encabezado vertical si no es necesario

        # Alineación de las celdas
        self.table.setItemDelegateForColumn(0, AlignedDelegate(Qt.AlignCenter))  # ID centrado
        self.table.setItemDelegateForColumn(1, AlignedDelegate(Qt.AlignLeft))  # Cliente alineado a la izquierda
        self.table.setItemDelegateForColumn(2, AlignedDelegate(Qt.AlignLeft))  # Clase alineada a la izquierda
        self.table.setItemDelegateForColumn(4, AlignedDelegate(Qt.AlignCenter))  # Estado centrado


        layout.addWidget(self.table)
        # ComboBox para Categoría y Tipo de Actuación
        self.combo_categoria = QComboBox()
        self.combo_tipo_actuacion = QComboBox()

        # Categoría de actuación → opciones iniciales
        self.combo_categoria.addItem("Seleccione una categoría")
        self.combo_categoria.addItems(list(self.obtener_actuaciones_por_categoria().keys()))
        self.combo_categoria.currentTextChanged.connect(self.actualizar_tipos_de_actuacion)

        # Layout para Categoría y Tipo de actuación
        actuacion_layout = QHBoxLayout()
        actuacion_layout.addWidget(QLabel("Categoría de Actuación:"))
        actuacion_layout.addWidget(self.combo_categoria)
        actuacion_layout.addWidget(QLabel("Tipo de Actuación:"))
        actuacion_layout.addWidget(self.combo_tipo_actuacion)
        layout.addLayout(actuacion_layout)

        # Botón para crear un nuevo proceso

        fuente_boton = QFont("Arial", 14)
        estilo_boton = """
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border-radius: 10px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """


        self.btn_nuevo_proceso = QPushButton("Nuevo Proceso")
        self.btn_nuevo_proceso.setFont(fuente_boton)
        self.btn_nuevo_proceso.setStyleSheet(estilo_boton)
        self.btn_nuevo_proceso.clicked.connect(self.crear_nuevo_proceso)
        layout.addWidget(self.btn_nuevo_proceso)

        fuente_boton = QFont("Arial", 14)
        estilo_boton = """
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border-radius: 10px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """
        self.btn_editar_proceso = QPushButton("Editar Proceso")
        self.btn_editar_proceso.setFont(fuente_boton)
        self.btn_editar_proceso.setStyleSheet(estilo_boton)
        self.btn_editar_proceso.clicked.connect(self.editar_proceso)
        layout.addWidget(self.btn_editar_proceso)

        # Micrositios
        self.btn_micrositios = QPushButton("Micrositios")
        self.btn_micrositios.setFont(fuente_boton)
        self.btn_micrositios.setStyleSheet(estilo_boton)
        self.btn_micrositios.setEnabled(False)  # Se activa al seleccionar un proceso

        self.radicado_mostrar = QLineEdit()
        self.radicado_mostrar.setReadOnly(True)
        self.radicado_mostrar.setFont(QFont("Arial", 14))

        self.selector_micrositio = QComboBox()
        self.selector_micrositio.addItems(["Selecciona Micrositio", "Tyba", "Samai", "Fiscalía", "CPNU", "Estados"])
        self.selector_micrositio.setFont(QFont("Arial", 14))

        self.btn_micrositios.clicked.connect(self.abrir_micrositio)

        micrositios_layout = QHBoxLayout()
        micrositios_layout.addWidget(QLabel("Radicado:"))
        micrositios_layout.addWidget(self.radicado_mostrar)
        micrositios_layout.addWidget(self.selector_micrositio)
        micrositios_layout.addWidget(self.btn_micrositios)

        layout.addLayout(micrositios_layout)

        # Lista de procesos
        self.lista_procesos = QListWidget()
        self.lista_procesos.itemClicked.connect(self.seleccionar_proceso)
        layout.addWidget(self.lista_procesos)

        # Pestañas de documentos y contabilidad
        self.tabs = QTabWidget()
        self.tab_documentos = DocumentosTab(self)
        self.tab_contabilidad = ContabilidadTab(self)
        self.tabs.addTab(self.tab_documentos, "Documentos")
        self.tabs.addTab(self.tab_contabilidad, "Contabilidad")
        layout.addWidget(self.tabs)

        self.setLayout(layout)

        self.load_procesos()  # Cargar los procesos

    def obtener_actuaciones_por_categoria(self):
        return {
            "Notificaciones y Comunicaciones": [
                "Notificación Personal", "Notificación por Estado", "Notificación por Aviso",
                "Notificación por Edicto", "Notificación por Estrados", "Notificación por Correo Certificado",
                "Certificado de Entrega / Acuse de Recibo"
            ],
            "Providencias Judiciales": [
                "Auto de Admisión de Demanda", "Auto de Mandamiento de Pago", "Auto de Emplazamiento",
                "Auto Interlocutorio", "Sentencia de Primera Instancia", "Sentencia de Segunda Instancia",
                "Resoluciones de Pruebas", "Resoluciones de Medidas Cautelares", "Oficios Judiciales",
                "Exhortos / Cartas Rogatorias / Comisiones"
            ],
            "Medidas Cautelares y Precautelativas": [
                "Auto de Embargo", "Acta de Secuestro", "Acta de Inscripción de Medida Cautelar",
                "Acta de Levantamiento de Medida", "Constancia de Entrega de Bienes",
                "Informe del Secuestre o Depositario", "Inventario de Bienes Embargados o Secuestrados"
            ],
            "Actuaciones Probatorias": [
                "Acta de Testimonios", "Dictamen Pericial", "Auto que Decreta Prueba",
                "Acta de Inspección Judicial", "Acta de Interrogatorio de Parte",
                "Solicitud de Documentos", "Oficio para Práctica de Pruebas",
                "Respuesta a Oficio / Informe Pericial"
            ],
            "Ejecución y Cumplimiento de Sentencias": [
                "Auto de Ejecución", "Auto de Liquidación de Costas", "Acta de Remate / Subasta",
                "Acta de Entrega de Bienes", "Oficio de Desembolso (dinero embargado)",
                "Informe de Cumplimiento de Medidas"
            ],
            "Recursos e Impugnaciones": [
                "Recurso de Reposición", "Recurso de Apelación", "Recurso de Queja",
                "Recurso de Revisión", "Providencia que Resuelve el Recurso", "Notificación del Recurso"
            ],
            "Terminación y Archivo del Proceso": [
                "Auto de Terminación del Proceso", "Auto de Archivo del Expediente", "Liquidación de Costas",
                "Auto de Desistimiento / Transacción", "Oficio de Cancelación de Medidas Cautelares",
                "Constancia de Entrega de Copias", "Informe de Archivo"
            ],
            "Conciliación y Mediación": [
                "Solicitud de Conciliación", "Acta de Conciliación", "Constancia de No Acuerdo",
                "Informe del Centro de Conciliación", "Auto que Homologa el Acuerdo"
            ],
            "Documentos Personales y Administrativos": [
                "Documento de Identidad", "Certificado de Existencia y Representación Legal",
                "Poderes y Mandatos", "Contratos y Acuerdos", "Certificados Bancarios",
                "Certificados de Tradición y Libertad", "Cartas de Instrucción", "Recibos de Pago",
                "Autorizaciones"
            ],
            "Otros Documentos": [
                "Comunicaciones Privadas", "Correspondencia (Correos, Cartas)",
                "Documentos Informativos (Circular, Boletín)", "Documentos Externos (No relacionados con el proceso)",
                "Fotografías y Evidencias", "Audios y Videos"
            ]
        }


    def actualizar_tipos_de_actuacion(self, categoria):
        self.combo_tipo_actuacion.clear()
        if categoria and categoria != "Seleccione una categoría":
            tipos = self.obtener_actuaciones_por_categoria().get(categoria, [])
            self.combo_tipo_actuacion.addItems(tipos)


    def filtrar_tabla(self):
        filtro_estado = self.filtro_estado.currentText()
        filtro_cliente = self.filtro_cliente.currentText()
        filtro_radicado = self.filtro_radicado.text().lower()

        for row in range(self.table.rowCount()):
            item_estado = self.table.item(row, 4).text()
            item_cliente = self.table.item(row, 1).text()
            item_radicado = self.table.item(row, 3).text().lower()

            mostrar = True

            # Filtro por estado
            if filtro_estado != "Todos" and filtro_estado not in item_estado:
                mostrar = False

            # Filtro por cliente
            if filtro_cliente != "Todos" and filtro_cliente not in item_cliente:
                mostrar = False

            # Filtro por radicado
            if filtro_radicado and filtro_radicado not in item_radicado:
                mostrar = False

            self.table.setRowHidden(row, not mostrar)  # Ocultar la fila si no pasa los filtros


    def load_procesos(self):
        self.lista_procesos.clear()
        procesos = self.model.obtener_todos()
        for proceso in procesos:
            item = QListWidgetItem(f"{proceso[1]} ({proceso[2]})")  # nombre y cliente_id
            item.setData(Qt.UserRole, proceso[0])  # proceso_id
            self.lista_procesos.addItem(item)

    def seleccionar_proceso(self, item):
        proceso_id = item.data(Qt.UserRole)
        self.selected_proceso_id = proceso_id
        self.tab_documentos.load_documents(proceso_id)
        self.tab_contabilidad.load_contabilidad(proceso_id)
        self.radicado_mostrar.setText(str(self.model.obtener_radicado_por_id(proceso_id)))
        self.btn_micrositios.setEnabled(True)

    def crear_nuevo_proceso(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Nuevo Proceso")
        layout = QFormLayout(dialog)
        radicado_input = QLineEdit()
        layout.addRow("Radicado:", radicado_input)

        cliente_cb = QComboBox()
        clientes = self.db.get_clientes()
        for cliente in clientes:
            cliente_cb.addItem(cliente[1], cliente[0])  # Nombre y ID

        tipo_input = QLineEdit()
        descripcion_input = QLineEdit()
        juzgado_input = QLineEdit()

        estado_cb = QComboBox()
        estado_cb.addItems(["Activo", "Finalizado", "Archivado"])

        fecha_input = QDateEdit()
        fecha_input.setCalendarPopup(True)
        fecha_input.setDate(QDate.currentDate())
        fecha_fin_input = QLineEdit()
        fecha_fin_input.setPlaceholderText("yyyy-mm-dd (opcional)")

        btn_calendario = QPushButton("📅")
        btn_calendario.setFixedWidth(30)

        def abrir_calendario():
            calendario = QCalendarWidget()
            calendario.setGridVisible(True)
            calendario.setWindowTitle("Seleccionar Fecha Fin")
            calendario.setMinimumDate(QDate(1900, 1, 1))
            calendario.setMaximumDate(QDate(2100, 18, 31))
            calendario.setSelectedDate(QDate.currentDate())

            def seleccionar_fecha():
                fecha = calendario.selectedDate().toString("yyyy-MM-dd")
                fecha_fin_input.setText(fecha)
                calendario.close()

            calendario.clicked.connect(seleccionar_fecha)
            calendario.setWindowModality(Qt.ApplicationModal)
            calendario.show()

        btn_calendario.clicked.connect(abrir_calendario)

 # valor por defecto = vacío

        layout.addRow("Cliente:", cliente_cb)
        layout.addRow("Tipo:", tipo_input)
        layout.addRow("Descripción:", descripcion_input)
        layout.addRow("Juzgado:", juzgado_input)
        layout.addRow("Estado:", estado_cb)
        layout.addRow("Fecha Inicio:", fecha_input)
        fecha_fin_layout = QHBoxLayout()
        fecha_fin_layout.addWidget(fecha_fin_input)
        fecha_fin_layout.addWidget(btn_calendario)
        layout.addRow("Fecha Fin:", fecha_fin_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addRow(buttons)

        def aceptar():
            cliente_id = cliente_cb.currentData()
            radicado = radicado_input.text().strip()
            tipo = tipo_input.text().strip()
            descripcion = descripcion_input.text().strip()
            juzgado = juzgado_input.text().strip()
            estado = estado_cb.currentText()
            fecha_inicio = fecha_input.date().toString("yyyy-MM-dd")

            fecha_fin_str = fecha_fin_input.text().strip()
            fecha_fin = fecha_fin_str if fecha_fin_str else None



            if not all([cliente_id, radicado, tipo, descripcion, juzgado, estado, fecha_inicio]):
                QMessageBox.warning(self, "Campos incompletos", "Complete todos los campos obligatorios.")
                return


            try:
                self.model.insertar(cliente_id, radicado, tipo, descripcion, juzgado, estado, fecha_inicio, fecha_fin)
                dialog.accept()
                self.load_data()
                self.load_procesos()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo agregar el proceso: {e}")

        buttons.accepted.connect(aceptar)
        buttons.rejected.connect(dialog.reject)

        dialog.exec_()


    def _input_dialog(self, mensaje):
        from PyQt5.QtWidgets import QInputDialog
        return QInputDialog.getText(self, "Entrada", mensaje)
    def agregar_proceso(self):
        cliente_id = self.cliente_input.currentData()  # Obtener el cliente seleccionado
        tipo = self.tipo_input.text().strip()
        descripcion = self.descripcion_input.text().strip()
        juzgado = self.juzgado_input.text().strip()
        estado = self.estado_input.currentText()
        fecha_inicio = self.fecha_inicio_input.text().strip()

        if not all([cliente_id, radicado, tipo, descripcion, juzgado, estado, fecha_inicio]):
            QMessageBox.warning(self, "Campos incompletos", "Complete todos los campos obligatorios.")
            return

        try:
            # Insertar proceso en la base de datos
            self.model.insertar(cliente_id, radicado, tipo, descripcion, juzgado, estado, fecha_inicio, fecha_fin)
            self.clear_inputs()
            self.load_data()  # Recargar la tabla de procesos
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo agregar el proceso: {e}")
    def load_data(self):
        self.lista_procesos.clear()  # Limpia la lista de procesos en la interfaz
        procesos = self.model.obtener_todos()  # Llama al modelo para obtener todos los procesos

        for proceso in procesos:
            item = QListWidgetItem(f"{proceso[2]} ({proceso[1]})")  # Muestra el tipo y cliente_id
            item.setData(Qt.UserRole, proceso[0])  # Guarda el proceso_id como dato asociado
            self.lista_procesos.addItem(item)  # Añade el proceso a la lista en la interfaz
   
    def abrir_micrositio(self):
        micrositio = self.selector_micrositio.currentText()
        enlaces = {
            "Tyba": "https://procesojudicial.ramajudicial.gov.co/Justicia21/Administracion/Ciudadanos/frmConsulta.aspx",
            "Samai": "https://samai.consejodeestado.gov.co/Vistas/Casos/procesos.aspx",
            "Fiscalía": "https://www.fiscalia.gov.co/colombia/servicios-de-informacion-al-ciudadano/consultas/",
            "CPNU": "https://consultaprocesos.ramajudicial.gov.co/procesos/bienvenida",
            "Estados": "https://publicacionesprocesales.ramajudicial.gov.co/web/publicaciones-procesales/inicio?p_p_id=co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortlet_INSTANCE_qOzzZevqIWbb&p_p_lifecycle=0&p_p_state=normal&p_p_mode=view&_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortlet_INSTANCE_qOzzZevqIWbb_jspPage=%2FMETA-INF%2Fresources%2Fdetail.jsp&_co_com_avanti_efectosProcesales_PublicacionesEfectosProcesalesPortlet_INSTANCE_qOzzZevqIWbb_articleId=104964642"
        }

        if micrositio in enlaces:
            webbrowser.get("C:/Program Files/Google/Chrome/Application/chrome.exe %s").open(enlaces[micrositio])
    
    def editar_proceso(self):
        item = self.table.currentItem()
        if not item:
            QMessageBox.warning(self, 'Atención', 'No se ha seleccionado ningún proceso para editar.')
            return

        proceso_id = item.data(Qt.UserRole)

        proceso = self.model.obtener_por_id(proceso_id)
        if not proceso:
            QMessageBox.critical(self, "Error", "No se pudo cargar el proceso seleccionado.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Editar Proceso")
        layout = QFormLayout(dialog)

        cliente_cb = QComboBox()
        for cliente in self.model.obtener_clientes():
            cliente_cb.addItem(cliente[1], cliente[0])
            if cliente[0] == proceso[1]:
                cliente_cb.setCurrentIndex(cliente_cb.count() - 1)

        radicado_input = QLineEdit(str(proceso[4]))
        tipo_input = QLineEdit(proceso[2])
        descripcion_input = QLineEdit(proceso[3])
        juzgado_input = QLineEdit(proceso[4])
        estado_cb = QComboBox()
        estado_cb.addItems(["Activo", "Cerrado", "Archivado"])
        estado_cb.setCurrentText(proceso[5])

        fecha_inicio_input = QDateEdit()
        fecha_inicio_input.setCalendarPopup(True)
        fecha_inicio_input.setDate(QDate.currentDate())
        layout.addRow("Fecha Inicio:", fecha_inicio_input)

        fecha_fin_input = QDateEdit()
        fecha_fin_input.setCalendarPopup(True)
        if proceso[7]:
            fecha_cargada = QDate.fromString(proceso[7], "yyyy-MM-dd")
            if fecha_cargada.isValid():
                fecha_fin_input.setDate(fecha_cargada)

        layout.addRow("Cliente:", cliente_cb)
        layout.addRow("Radicado:", radicado_input)
        layout.addRow("Tipo:", tipo_input)
        layout.addRow("Descripción:", descripcion_input)
        layout.addRow("Juzgado:", juzgado_input)
        layout.addRow("Estado:", estado_cb)
        layout.addRow("Fecha Fin:", fecha_fin_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addRow(buttons)

        def aceptar():
            cliente_id = cliente_cb.currentData()
            radicado = radicado_input.text().strip()
            tipo = tipo_input.text().strip()
            descripcion = descripcion_input.text().strip()
            juzgado = juzgado_input.text().strip()
            estado = estado_cb.currentText()
            fecha_inicio = fecha_inicio_input.date().toString("yyyy-MM-dd")
            fecha_fin = fecha_fin_input.date().toString("yyyy-MM-dd") if fecha_fin_input.date().isValid() else None

            if not all([cliente_id, radicado, tipo, descripcion, juzgado, estado, fecha_inicio]):
                QMessageBox.warning(self, "Campos incompletos", "Complete todos los campos obligatorios.")
                return

            try:
                self.model.actualizar(proceso_id, cliente_id, tipo, descripcion, juzgado, estado, fecha_inicio, fecha_fin)
                dialog.accept()
                self.load_data()
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"No se pudo actualizar el proceso: {e}")

        buttons.accepted.connect(aceptar)
        buttons.rejected.connect(dialog.reject)

        dialog.exec_()

   
    def crear_boton(self, texto, icono, color_fondo, tooltip):
        boton = QPushButton(texto)
        boton.setIcon(QIcon(icono))
        boton.setFont(QFont("Arial", 14))
        boton.setStyleSheet(f"""
            QPushButton {{
                background-color: {color_fondo};
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: #0056b3;
            }}
        """)
        boton.setToolTip(tooltip)
        return boton

   
