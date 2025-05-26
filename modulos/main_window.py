from PyQt5.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QMessageBox
from PyQt5.QtCore import Qt
from modulos.clientes.clientes import ClientesWindow
from modulos.procesos.procesos_widget import ProcesosWidget
from modulos.procesos.procesos_model import ProcesosModel
from utils.db_manager import DBManager
from modulos.documentos.documentos_widget import DocumentosWidget
from modulos.contabilidad import ContabilidadWindow
from modulos.liquidadores import LiquidadoresWindow
from modulos.calendario import CalendarioWindow
from usuarios.permisos import PERMISOS
import os
from PyQt5.QtGui import QPixmap
from modulos.clientes.clientes_widget import ClientesWidget  # <-- Asegúrate de importar la clase correcta arriba

class MainWindow(QMainWindow):
    def __init__(self, role):
        super().__init__()
        self.setWindowTitle("LEX360PLUS - Panel Principal")
        self.user_role = role

        # Establecer tamaño mínimo
        self.setMinimumSize(1600, 800)

        # Layout principal con sidebar y área de contenido
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Sidebar (izquierda)
        sidebar = QWidget()
        sidebar.setFixedWidth(150)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 10, 10, 10)
        sidebar_layout.setSpacing(10)

        # Botones de navegación
        self.btn_clientes = QPushButton("Clientes")
        self.btn_procesos = QPushButton("Procesos")
        self.btn_documentos = QPushButton("Documentos")
        self.btn_contabilidad = QPushButton("Contabilidad")
        self.btn_liquidadores = QPushButton("Liquidadores")
        self.btn_calendario = QPushButton("Calendario")
        self.btn_logout = QPushButton("Cerrar Sesión")

        # Agregar los botones al layout del sidebar
        for btn in [self.btn_clientes, self.btn_procesos, self.btn_documentos, self.btn_contabilidad, self.btn_liquidadores, self.btn_calendario, self.btn_logout]:
            btn.setFixedHeight(40)
            sidebar_layout.addWidget(btn)
        sidebar_layout.addStretch()

        # Contenedor del contenido dinámico
        self.content_container = QWidget()
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setAlignment(Qt.AlignCenter)

        # Mostrar logo y mensaje de bienvenida por defecto
        self.logo_label = QLabel()
        current_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(current_dir, "assets", "logoapp.jpeg")
        pixmap = QPixmap(logo_path)
        if pixmap.isNull():
            print(f"Error: No se pudo cargar la imagen desde {logo_path}")
        else:
            self.logo_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio))

        self.content_label = QLabel("Bienvenido a LEX360PLUS")
        self.content_label.setAlignment(Qt.AlignCenter)
        self.content_label.setStyleSheet("font-size: 36px; font-weight: bold; color: #333;")

        self.content_layout.addWidget(self.logo_label)
        self.content_layout.addWidget(self.content_label)

        # Añadir widgets al layout principal
        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.content_container)

        # Conectar botones a funciones
        self.btn_clientes.clicked.connect(self.open_clientes)
        self.btn_procesos.clicked.connect(self.open_procesos)
        self.btn_documentos.clicked.connect(self.open_documentos)
        self.btn_contabilidad.clicked.connect(self.open_contabilidad)
        self.btn_liquidadores.clicked.connect(self.open_liquidadores)
        self.btn_calendario.clicked.connect(self.open_calendario)
        self.btn_logout.clicked.connect(self.logout)

        # Aplicar permisos según rol
        allowed = PERMISOS.get(self.user_role, [])
        if "contabilidad" not in allowed:
            self.btn_contabilidad.setEnabled(False)
        if "liquidadores" not in allowed:
            self.btn_liquidadores.setEnabled(False)

        self.showMaximized()

    def set_main_content(self, widget):
        # Limpiar contenido anterior
        for i in reversed(range(self.content_layout.count())):
            item = self.content_layout.takeAt(i)
            widget_to_remove = item.widget()
            if widget_to_remove:
                widget_to_remove.setParent(None)

        # Añadir nuevo widget
        self.content_layout.addWidget(widget)

    def open_clientes(self):
        widget = ClientesWidget()  # <-- Usa la clase que sí contiene la lógica y la interfaz correctas
        self.set_main_content(widget)
 
    def open_procesos(self):
        db = DBManager()
        model = ProcesosModel(db)
        widget = ProcesosWidget(db, model)
        self.set_main_content(widget)

    def open_documentos(self):
        widget = DocumentosWidget()
        self.set_main_content(widget)



    def open_contabilidad(self):
        widget = ContabilidadWindow()
        self.set_main_content(widget)

    def open_liquidadores(self):
        widget = LiquidadoresWindow()
        self.set_main_content(widget)

    def open_calendario(self):
        widget = CalendarioWindow()
        self.set_main_content(widget)

    def logout(self):
        self.close()
