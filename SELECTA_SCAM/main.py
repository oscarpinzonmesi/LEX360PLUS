# SELECTA_SCAM/main.py
# -*- coding: utf-8 -*-
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QDesktopWidget, QDialog, QMessageBox
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt
import os
import logging # Importar el módulo de logging
import inspect
# Configuración básica del logger para main.py
# Cambia el nivel a DEBUG para ver todos los mensajes
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# Resto de tu código en main.py...
# Importaciones de clientes
from SELECTA_SCAM.modulos.clientes.clientes_model import ClientesModel
from SELECTA_SCAM.modulos.clientes.clientes_widget import ClientesWidget
from SELECTA_SCAM.modulos.clientes.clientes_db import ClientesDB 
from SELECTA_SCAM.modulos.clientes.clientes_logic import ClientesLogic 

# Importaciones de procesos
from SELECTA_SCAM.modulos.procesos.procesos_widget import ProcesosWidget
from SELECTA_SCAM.modulos.procesos.procesos_model import ProcesosModel
from SELECTA_SCAM.modulos.procesos.procesos_db import ProcesosDB
from SELECTA_SCAM.modulos.procesos.procesos_logic import ProcesosLogic 

# Importaciones de documentos
from SELECTA_SCAM.modulos.documentos.documentos_widget import DocumentosModule
from SELECTA_SCAM.modulos.documentos.documentos_db import DocumentosDB
# Importar DocumentosController aquí para usarlo en la instanciación
from SELECTA_SCAM.modulos.documentos.documentos_controller import DocumentosController 

# Importaciones de contabilidad
from SELECTA_SCAM.modulos.contabilidad.contabilidad_model import ContabilidadModel
from SELECTA_SCAM.modulos.contabilidad.contabilidad_widget import ContabilidadWidget
from SELECTA_SCAM.modulos.contabilidad.contabilidad_db import ContabilidadDB
from SELECTA_SCAM.modulos.contabilidad.contabilidad_logic import ContabilidadLogic
from SELECTA_SCAM.modulos.contabilidad.contabilidad_controller import ContabilidadController
# Importaciones de calendario
from SELECTA_SCAM.modulos.calendario.calendario_widget import CalendarioWidget
from SELECTA_SCAM.modulos.calendario.calendario_db import CalendarioDB

# Importaciones de liquidadores
from SELECTA_SCAM.modulos.liquidadores.liquidadores_widget import LiquidadoresWidget
from SELECTA_SCAM.modulos.liquidadores.liquidadores_db import LiquidadoresDB

# Importaciones de usuarios
from SELECTA_SCAM.usuarios.login import LoginWindow
from SELECTA_SCAM.usuarios.change_password import ChangePasswordDialog
from SELECTA_SCAM.usuarios.register_user import RegisterUserDialog
from SELECTA_SCAM.db.usuarios_db import UsuariosDB

# Importación del conector de base de datos de SQLAlchemy y settings
from SELECTA_SCAM.config import settings 


class MainApp(QMainWindow):
    def __init__(self, username, role):
        super().__init__()
        self.setWindowTitle("SELECTA_SCAM - Panel Principal")
        self.setMinimumSize(1000, 800)
        self.username = username
        self.user_role = role
        self.current_user_data = {'username': username, 'role': role}
        self.active_button = None
        #logger.info(f"MainApp iniciada para el usuario: {username} ({role})")

        central = QWidget()
        self.setCentralWidget(central)
        
        # --- Estilo general para la ventana principal ---
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F8F0F5;
                color: #333333;
                font-family: 'Segoe UI', 'Arial', sans-serif;
            }
        """)

        self.main_layout = QHBoxLayout(central)

        # --- Estilos de los botones del sidebar ---
        self.estilo_boton = """
            QPushButton {
                background-color: #5D566F;
                color: #F8F8F8;
                font-size: 15px;
                font-weight: 500;
                padding: 12px 20px;
                border: 1px solid #7B718D;
                border-radius: 5px;
                outline: none;
                text-align: left;
                padding-left: 25px;
            }
            QPushButton:hover {
                background-color: #7B718D;
                border-color: #9A91A8;
                color: #FFFFFF;
            }
            QPushButton:pressed {
                background-color: #4A445C;
                border-color: #6D657A;
            }
        """
        self.estilo_boton_activo = """
            QPushButton {
                background-color: #D36B92;
                color: white;
                font-size: 15px;
                font-weight: 600;
                padding: 12px 20px;
                border: 1px solid #D36B92;
                border-radius: 5px;
                outline: none;
                text-align: left;
                padding-left: 25px;
            }
            QPushButton:hover {
                background-color: #E279A1;
                border-color: #E279A1;
            }
            QPushButton:pressed {
                background-color: #B85F7F;
            }
        """
        self.estilo_boton_usuario = """
            QPushButton {
                background-color: #5AA1B9;
                color: #FFFFFF;
                font-size: 15px;
                font-weight: 500;
                padding: 12px 20px;
                border: 1px solid #7BC2DA;
                border-radius: 5px;
                outline: none;
                text-align: left;
                padding-left: 25px;
            }
            QPushButton:hover {
                background-color: #7BC2DA;
                border-color: #9CDFEB;
            }
            QPushButton:pressed {
                background-color: #4E8BA3;
            }
        """

                # --- INICIO DE LA CORRECCIÓN DE ARQUITECTURA ---

        # 1. Instancias de la capa de Base de Datos (DB) - ya no necesitan argumentos
        self.clientes_db_instance = ClientesDB()
        self.documentos_db_instance = DocumentosDB()
        self.procesos_db_instance = ProcesosDB()
        self.contabilidad_db_instance = ContabilidadDB()
        self.calendario_db_instance = CalendarioDB()
        self.liquidadores_db_instance = LiquidadoresDB()
        self.usuarios_db_instance = UsuariosDB()

        # 2. Instancias de la capa de Lógica - se les "inyecta" la capa de DB que necesitan
        self.clientes_logic_instance = ClientesLogic(self.clientes_db_instance)
        self.procesos_logic_instance = ProcesosLogic(self.procesos_db_instance)
        # (La lógica de Documentos, si la tienes, iría aquí)

        # 3. Instancias de la capa de Modelo - se les "inyecta" la lógica o la DB
        self.clientes_model_instance = ClientesModel(self.clientes_logic_instance, self)
        self.procesos_model_instance = ProcesosModel(
            self.procesos_db_instance, 
            clientes_db=self.clientes_db_instance # ProcesosModel necesita acceso directo a ClientesDB
        )
        self.contabilidad_model_instance = ContabilidadModel(self.contabilidad_db_instance)

        # 4. Instancias de Controladores (si se usan, como en Contabilidad)
        self.contabilidad_logic_instance = ContabilidadLogic(
            contabilidad_db=self.contabilidad_db_instance,
            clientes_logic=self.clientes_logic_instance,
            contabilidad_model=self.contabilidad_model_instance,
            procesos_logic=self.procesos_logic_instance
        )
        self.contabilidad_controller_instance = ContabilidadController(
            model=self.contabilidad_model_instance,
            contabilidad_logic=self.contabilidad_logic_instance,
            clientes_logic=self.clientes_logic_instance,
            procesos_logic=self.procesos_logic_instance
        )
        # --- FIN DE LA CORRECCIÓN DE ARQUITECTURA ---
        self.procesos_model_instance = ProcesosModel(
            self.procesos_db_instance, 
            clientes_db=self.clientes_db_instance, 
            documentos_db=self.documentos_db_instance, 
            contabilidad_db=self.contabilidad_db_instance 
        ) 
        # ContabilidadModel ya no se instancia aquí directamente, se instancia dentro del Controller.
        #logger.info("Instancias de modelos de negocio (Clientes, Procesos) creadas.")

        # Instancia del Controlador de Contabilidad (NUEVO)
        # MODIFICADO: ContabilidadController ahora recibe las instancias de lógica directamente
        # Instancia del Controlador de Contabilidad
        self.contabilidad_controller_instance = ContabilidadController(
            model=self.contabilidad_model_instance,
            contabilidad_logic=self.contabilidad_logic_instance, # Aquí y en los siguientes, debes usar el nombre
            clientes_logic=self.clientes_logic_instance,
            procesos_logic=self.procesos_logic_instance,
            #parent=self # Pasa el padre si es necesario para señales/slots
        )
        #logger.info("Instancia de ContabilidadController creada.")
    
        sidebar = QWidget()
        sidebar.setFixedWidth(220)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(15, 15, 15, 15)
        side_layout.setSpacing(10)
        # --- Estilo del Sidebar ---
        sidebar.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border-radius: 8px;
                border: 1px solid #E0E0E0;
            }
        """)

        self.btn_inicio = QPushButton("Volver al Inicio")
        self.btn_clientes = QPushButton("Clientes")
        self.btn_procesos = QPushButton("Procesos")
        self.btn_documentos = QPushButton("Documentos")
        self.btn_contabilidad = QPushButton("Contabilidad")
        self.btn_calendario = QPushButton("Calendario")
        self.btn_liquidadores = QPushButton("Liquidadores")

        for btn in [self.btn_inicio, self.btn_clientes, self.btn_procesos, self.btn_documentos,
                     self.btn_contabilidad, self.btn_calendario, self.btn_liquidadores]:
            btn.setFixedHeight(45)
            btn.setStyleSheet(self.estilo_boton)
            side_layout.addWidget(btn)

        side_layout.addStretch()

        self.btn_registrar_usuario = QPushButton("Regis. Usuario")
        self.btn_registrar_usuario.setFixedHeight(45)
        self.btn_registrar_usuario.setStyleSheet(self.estilo_boton_usuario)
        
        # --- Control de acceso para el botón de registro de usuario ---
        if self.user_role != 'admin': 
            self.btn_registrar_usuario.setVisible(False)
            self.btn_registrar_usuario.setEnabled(False) 

        self.btn_cambiar_contra = QPushButton("Cam. Contraseña")
        self.btn_cambiar_contra.setFixedHeight(45)
        self.btn_cambiar_contra.setStyleSheet(self.estilo_boton_usuario)

        side_layout.addWidget(self.btn_registrar_usuario)
        side_layout.addWidget(self.btn_cambiar_contra)

        self.main_layout.addWidget(sidebar)

        self.content_area = QWidget()
        # --- Estilo del área de contenido ---
        self.content_area.setStyleSheet("""
            QWidget {
                background-color: #F8F8F8; /* Fondo más claro para el contenido */
                border-radius: 8px;
                border: 1px solid #E0E0E0;
            }
        """)
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(30, 20, 30, 20)
        self.main_layout.addWidget(self.content_area)

        # --- CONEXIONES DE BOTONES (PASANDO LAS INSTANCIAS YA CREADAS) ---
        self.btn_inicio.clicked.connect(self.show_welcome)
        
        self.btn_clientes.clicked.connect(lambda: self.open_module(
            self.btn_clientes,
            ClientesWidget,
            self.clientes_model_instance # Pasa la instancia del modelo de Clientes
        ))
        
        # Conexión para Procesos
        self.btn_procesos.clicked.connect(lambda: self.open_module(
            self.btn_procesos,
            ProcesosWidget,
            # Asegúrate de que ProcesosWidget acepte ProcesosModel y ClientesDB/Logic
            # Según tu código, ProcesosWidget toma ProcesosModel y ClientesDB
            self.procesos_model_instance, 
            self.clientes_db_instance # O clientes_logic_instance si ProcesosWidget la necesita
        ))
        self.btn_documentos.clicked.connect(lambda: self.open_module(
                self.btn_documentos,
                DocumentosModule,
                self.documentos_db_instance,
                self.clientes_logic_instance,
                user_data=self.current_user_data # Asegúrate de que user_data se pase como keyword argument
            ))
        
        self.btn_contabilidad.clicked.connect(lambda: self.open_module(
            self.btn_contabilidad,
            ContabilidadWidget,
            self.contabilidad_controller_instance,
            self.clientes_logic_instance, 
            self.procesos_logic_instance 
        ))
        
        self.btn_calendario.clicked.connect(lambda: self.open_module(
            self.btn_calendario,
            CalendarioWidget,
            self.calendario_db_instance # Pasa la instancia de la DB de Calendario
        ))
        
        self.btn_liquidadores.clicked.connect(lambda: self.open_module(
            self.btn_liquidadores,
            LiquidadoresWidget,
            self.liquidadores_db_instance # Pasa la instancia de la DB de Liquidadores
        ))
        
        self.btn_cambiar_contra.clicked.connect(self.cambiar_contrasena)
        self.btn_registrar_usuario.clicked.connect(self.registrar_usuario)

        self.show_welcome()

    def show_welcome(self):
        self.clear_content()
        self.set_active_button(self.btn_inicio)
        #logger.info("Mostrando pantalla de bienvenida.")

        logo_path = settings.LOGO_PATH 

        logo_container = QWidget()
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(50, 50, 50, 50)
        logo_layout.setAlignment(Qt.AlignCenter)

        logo = QLabel()
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaledToWidth(900, Qt.SmoothTransformation) 
                logo.setPixmap(pixmap)
                #logger.info(f"Logo cargado desde: {logo_path}")
            else:
                logo.setText("No se pudo cargar el logo.")
                logger.warning(f"QPixmap no pudo cargar el logo desde: {logo_path}")
        else:
            logo.setText("Archivo de logo no encontrado.")
            logger.error(f"Archivo de logo no encontrado en: {logo_path}")
        logo.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(logo)

        # --- Estilo del contenedor del logo ---
        logo_container.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 10px;
            }
        """)

        lb = QLabel("SELECTA_SCAM")
        # --- Estilo del texto del logo ---
        lb.setStyleSheet("font-size: 80px; color: #D36B92; font-weight: bold;")
        lb.setAlignment(Qt.AlignCenter)

        self.content_layout.addWidget(logo_container)
        self.content_layout.addStretch()
        self.content_layout.addWidget(lb)
        self.content_layout.addStretch()

    def clear_content(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        #logger.debug("Contenido del área principal limpiado.")

    def set_active_button(self, button):
        # Restaura todos los botones a su estilo base primero
        for btn in [self.btn_inicio, self.btn_clientes, self.btn_procesos, self.btn_documentos,
                     self.btn_contabilidad, self.btn_calendario, self.btn_liquidadores]:
            btn.setStyleSheet(self.estilo_boton)
        
        # Los botones de usuario tienen su propio estilo base, no el general
        # Solo restaura si el botón activo previo NO era uno de usuario, para evitar sobrescribir su estilo
        if self.active_button not in [self.btn_registrar_usuario, self.btn_cambiar_contra]:
            if self.user_role == 'admin': # Solo si el botón está visible
                 self.btn_registrar_usuario.setStyleSheet(self.estilo_boton_usuario)
            self.btn_cambiar_contra.setStyleSheet(self.estilo_boton_usuario)

        # Aplica el estilo activo al botón clickeado
        button.setStyleSheet(self.estilo_boton_activo)
        self.active_button = button
        #logger.debug(f"Botón activo establecido: {button.text()}")
# SELECTA_SCAM/main.py

# ... (resto del código antes de open_module) ...

    def open_module(self, button, module_class, *args, **kwargs):
        self.clear_content()
        self.set_active_button(button)
        
        if 'user_data' not in kwargs:
            kwargs['user_data'] = self.current_user_data
        
        #logger.info(f"Intentando abrir módulo: {module_class.__name__} con args: {args} y kwargs: {kwargs}")
        if hasattr(module_class, '__init__'):
            init_signature = inspect.signature(module_class.__init__)
            #logger.info(f"DEBUG_SIG: La firma de {module_class.__name__}.__init__ es: {init_signature}")
        else:
            logger.info(f"DEBUG_SIG: {module_class.__name__} no tiene un método __init__ explícito.")
    
        try:
            widget = None 

            # --- INICIO: CAMBIOS ESPECÍFICOS PARA CADA MÓDULO ---
            if module_class.__name__ == "ContabilidadWidget":
                # ContabilidadWidget espera el controller, clientes_logic y procesos_logic
                # El controller ya viene en *args (si lo pasas así desde el .clicked.connect)
                # Eliminamos la adición de kwargs['clientes_logic'] y kwargs['procesos_logic'] ya que se pasan posicionalmente
                widget = module_class(*args, **kwargs)
            
            elif module_class.__name__ == "DocumentosModule":
                # DocumentosModule espera documentos_db_instance y clientes_logic_instance
                # Según tu .clicked.connect, ya pasas self.documentos_db_instance y self.clientes_logic_instance
                # Asegúrate de que los nombres de los parámetros en DocumentosModule.__init__ coincidan.
                # Si tu DocumentosModule.__init__ espera 'documentos_db_instance' y 'clientes_logic_instance',
                # entonces la llamada original en .clicked.connect está bien.
                # Si espera el controlador de documentos, ajusta así:
                # kwargs['documentos_controller'] = self.documentos_controller_instance
                # kwargs['clientes_logic_instance'] = self.clientes_logic_instance
                widget = module_class(*args, **kwargs) # Mantén como está si ya funciona
            
            elif module_class.__name__ == "ClientesWidget":
                # ClientesWidget espera clientes_model_instance
                widget = module_class(*args, **kwargs) # Mantén como está si ya funciona

            elif module_class.__name__ == "ProcesosWidget":
                # ProcesosWidget espera procesos_model_instance y clientes_db_instance
                widget = module_class(*args, **kwargs) # Mantén como está si ya funciona
            
            elif module_class.__name__ == "CalendarioWidget":
                # CalendarioWidget espera calendario_db_instance
                widget = module_class(*args, **kwargs) # Mantén como está si ya funciona

            elif module_class.__name__ == "LiquidadoresWidget":
                # LiquidadoresWidget espera liquidadores_db_instance
                widget = module_class(*args, **kwargs) # Mantén como está si ya funciona

            else:
                # Para cualquier otro módulo no especificado, usa la instanciación genérica
                widget = module_class(*args, **kwargs)
            # --- FIN: CAMBIOS ESPECÍFICOS PARA CADA MÓDULO ---


        except TypeError as e:
            error_message = f"Error al cargar el módulo: {module_class.__name__}. " \
                            f"Detalles: {e}. Por favor, contacte a soporte."
            error_label = QLabel(error_message)
            error_label.setStyleSheet("color: red; font-size: 18px; text-align: center;")
            self.content_layout.addWidget(error_label)
            logger.exception(f"Error de TypeError al instanciar {module_class.__name__}:")
            return
        except Exception as e:
            error_message = f"Ocurrió un error inesperado al cargar el módulo: {module_class.__name__}. " \
                            f"Detalles: {e}. Por favor, contacte a soporte."
            error_label = QLabel(error_message)
            error_label.setStyleSheet("color: red; font-size: 18px; text-align: center;")
            self.content_layout.addWidget(error_label)
            logger.exception(f"Error inesperado al instanciar {module_class.__name__}:")
            return
            
        self.content_layout.addWidget(widget)
        widget.setVisible(True)
        #logger.info(f"Módulo {module_class.__name__} cargado exitosamente.")
    def cambiar_contrasena(self):
        logger.info(f"Abriendo diálogo para cambiar contraseña para el usuario: {self.username}")
        dialog = ChangePasswordDialog(self.username, usuarios_db=self.usuarios_db_instance) 
        dialog.exec_()
        logger.debug("Diálogo de cambio de contraseña cerrado.")

    def registrar_usuario(self):
        #logger.info(f"Intentando abrir diálogo de registro de usuario. Rol: {self.user_role}")
        if self.user_role == 'admin':
            dialog = RegisterUserDialog(usuarios_db=self.usuarios_db_instance) 
            dialog.exec_()
            logger.debug("Diálogo de registro de usuario cerrado.")
        else:
            QMessageBox.warning(self, "Acceso Denegado", "No tiene permisos para registrar nuevos usuarios.")
            logger.warning(f"Acceso denegado a registro de usuario para rol: {self.user_role}")


# --- Lanzador Principal de la Aplicación ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    login = LoginWindow() 
    
    if login.exec_() == QDialog.Accepted:
        username = getattr(login, "username", None)
        user_role = getattr(login, "user_role", None)
        
        if username and user_role:
            #logger.info(f"Inicio de sesión exitoso. Lanzando MainApp para {username} ({user_role}).")
            window = MainApp(username, user_role)
            window.showMaximized() 
            sys.exit(app.exec_())
        else:
            logger.critical("Inicio de sesión exitoso pero faltan datos de usuario (username/role).")
            QMessageBox.critical(None, "Error de Inicio de Sesión", "Datos de usuario incompletos después del inicio de sesión.")
            sys.exit(1)
    else:
        logger.info("Inicio de sesión fallido o cancelado.") 
        sys.exit(0) # Salida con código 0 si el usuario cancela la aplicación