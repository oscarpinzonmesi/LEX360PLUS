# -*- coding: utf-8 -*-
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QDesktopWidget, QDialog
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt
import os

# Model y widgets
from modulos.clientes.clientes_model import ClientesModel
from modulos.clientes.clientes_widget import ClientesWidget

from modulos.procesos.procesos_widget import ProcesosWidget
from modulos.procesos.procesos_documentos import DocumentosTab
from modulos.documentos.documentos_widget import DocumentosWidget
from modulos.documentos.documentos_widget import DocumentosWidget
from modulos.contabilidad.contabilidad_widget import ContabilidadWidget
from modulos.calendario.calendario_widget import CalendarioWidget
from modulos.liquidadores.liquidadores_widget import LiquidadoresWidget
from modulos.procesos.procesos_model import ProcesosModel
# Usuarios
from usuarios.login import LoginWindow
from usuarios.change_password import ChangePasswordDialog
# Base de datos
from utils.db_manager import DBManager
from modulos.documentos.documentos_controller import *  # Para importar todofrom modulos.documentos.documentos_widget import DocumentosWidget








db = DBManager()
#db.migrar_columna_cedula_a_identificacion()
db.create_tables()

def limpiar_clientes_de_prueba():
    conn = db.conectar()
    cursor = conn.cursor()
    
    cursor.execute("""
        DELETE FROM clientes
        WHERE LENGTH(nombre) < 5
           OR nombre IN ('hdfshdj', 'shdhh')
           OR numero_identificacion IN ('43432', 'dkfsafd')
    """)
    
    conn.commit()
    conn.close()


#db.debug_imprimir_todos_los_clientes()
class MainApp(QMainWindow):

    def __init__(self, username, role):
        super().__init__()
        self.setWindowTitle("LEX360PLUS - Panel Principal")
        self.setMinimumSize(1000, 800)
        self.username = username
        self.user_role = role
        self.active_button = None

        central = QWidget()
        self.setCentralWidget(central)
        self.main_layout = QHBoxLayout(central)

        # Estilos de botones
        self.estilo_boton = """
            QPushButton {
                background-color: #2E86C1;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 10px 20px;
                border: 2px solid #1B4F72;
                border-radius: 15px;
            }
            QPushButton:hover {
                background-color: #1B4F72;
            }
        """

        self.estilo_boton_activo = """
            QPushButton {
                background-color: #117A65;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 10px 20px;
                border: 2px solid #0E6251;
                border-radius: 15px;
            }
        """

        self.estilo_boton_usuario = """
            QPushButton {
                background-color: #28B463;
                color: white;
                font-size: 16px;
                font-family: Times New Roman;
                font-weight: bold;
                padding: 10px 20px;
                border: 2px solid #1D8348;
                border-radius: 15px;
            }
            QPushButton:hover {
                background-color: #1D8348;
            }
        """

        # Sidebar
        sidebar = QWidget()
        sidebar.setFixedWidth(200)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(10, 10, 10, 10)
        side_layout.setSpacing(10)
        sidebar.setStyleSheet("""
            border: 5px solid #BFCF30;
            border-radius: 10px;
            background-color: #F8F9F9;
        """)

        # Botones principales
        self.btn_inicio = QPushButton("Volver al Inicio")
        self.btn_clientes = QPushButton("Clientes")
        self.btn_procesos = QPushButton("Procesos")
        self.btn_documentos = QPushButton("Documentos")
        self.btn_contabilidad = QPushButton("Contabilidad")
        self.btn_calendario = QPushButton("Calendario")
        self.btn_liquidadores = QPushButton("Liquidadores")

        for btn in [self.btn_inicio, self.btn_clientes, self.btn_procesos, self.btn_documentos,
                    self.btn_contabilidad, self.btn_calendario, self.btn_liquidadores]:
            btn.setFixedHeight(40)
            btn.setStyleSheet(self.estilo_boton)
            side_layout.addWidget(btn)

        side_layout.addStretch()

        # Estilo personalizado para botones especiales con fuente Times New Roman tamaño 20 y negrita
        self.estilo_boton_usuario = """
            QPushButton {
                background-color: #28B463;
                color: white;
                font-size: 16px;
                font-family: Times New Roman;
                font-weight: bold;
                padding: 10px 20px;
                border: 2px solid #1D8348;
                border-radius: 15px;
            }
            QPushButton:hover {
                background-color: #1D8348;
            }
        """

        self.btn_registrar_usuario = QPushButton("Regis. Usuario")
        self.btn_registrar_usuario.setFixedHeight(40)
        self.btn_registrar_usuario.setStyleSheet(self.estilo_boton_usuario)

        self.btn_cambiar_contra = QPushButton("Cam. Contraseña")
        self.btn_cambiar_contra.setFixedHeight(40)
        self.btn_cambiar_contra.setStyleSheet(self.estilo_boton_usuario)

        side_layout.addWidget(self.btn_registrar_usuario)
        side_layout.addWidget(self.btn_cambiar_contra)

        self.main_layout.addWidget(sidebar)


        # Área principal
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(100, 5, 100, 1)
        self.main_layout.addWidget(self.content_area)

        # Conexiones
        self.btn_inicio.clicked.connect(self.show_welcome)
        self.btn_clientes.clicked.connect(lambda: self.open_module(self.btn_clientes, ClientesWidget))
        self.btn_procesos.clicked.connect(
            # <-- agregamos 'checked,' para capturar el parámetro que manda Qt
            lambda checked, db=db: self.open_module(
                self.btn_procesos,
                lambda: ProcesosWidget(db, ProcesosModel(db))
            )
        )



        self.btn_documentos.clicked.connect(lambda: self.open_module(self.btn_documentos, DocumentosWidget))
        self.btn_contabilidad.clicked.connect(lambda: self.open_module(self.btn_contabilidad, ContabilidadWidget))
        self.btn_calendario.clicked.connect(lambda: self.open_module(self.btn_calendario, CalendarioWidget))
        self.btn_liquidadores.clicked.connect(lambda: self.open_module(self.btn_liquidadores, LiquidadoresWidget))
        self.btn_cambiar_contra.clicked.connect(self.cambiar_contrasena)
        self.btn_registrar_usuario.clicked.connect(self.registrar_usuario)

        self.show_welcome()

    def show_welcome(self):
        self.clear_content()
        self.set_active_button(self.btn_inicio)

        logo_path = os.path.join("assets", "logoapp.jpeg")

        logo_container = QWidget()
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(50, 1, 50, 1)
        logo_layout.setAlignment(Qt.AlignCenter)

        logo = QLabel()
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaledToWidth(1300, Qt.SmoothTransformation)
                logo.setPixmap(pixmap)
            else:
                logo.setText("No se pudo cargar el logo.")
        else:
            logo.setText("Archivo de logo no encontrado.")

        logo.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(logo)

        logo_container.setStyleSheet("""
            QWidget {
                border: 5px solid #BFCF30;
                border-radius: 10px;
                background-color: white;
            }
        """)

        lb = QLabel("LEX360PLUS MPA")
        lb.setStyleSheet("font-size: 90px;")
        lb.setAlignment(Qt.AlignCenter)

        self.content_layout.addWidget(logo_container)
        self.content_layout.addWidget(lb)

    def clear_content(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def set_active_button(self, button):
        if self.active_button:
            self.active_button.setStyleSheet(self.estilo_boton)
        button.setStyleSheet(self.estilo_boton_activo)
        self.active_button = button

    def open_module(self, button, module_class):
        self.clear_content()
        self.set_active_button(button)
        widget = module_class()
        self.content_layout.addWidget(widget)

    def cambiar_contrasena(self):
        dialog = ChangePasswordDialog()
        dialog.exec_()

    def registrar_usuario(self):
        from usuarios.register_user import RegisterUserDialog
        dialog = RegisterUserDialog()
        dialog.exec_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    login = LoginWindow()
    if login.exec_() == QDialog.Accepted:
        username = getattr(login, "username", None)
        user_role = getattr(login, "user_role", None)
        window = MainApp(username, user_role)
        screen = QDesktopWidget().screenGeometry()
        x = (screen.width() - window.width()) // 2
        y = (screen.height() - window.height()) // 2
        window.move(x, y)
        window.showMaximized()
        sys.exit(app.exec_())
