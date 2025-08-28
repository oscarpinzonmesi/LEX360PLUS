# SELECTA_SCAM/usuarios/login.py
import sys
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt, QSize
import os

from SELECTA_SCAM.db.usuarios_db import UsuariosDB
# Importamos SessionLocal del nuevo conector SQLAlchemy
from SELECTA_SCAM.config import settings # Para acceder a LOGO_PATH
# Añade esta nueva línea:
from SELECTA_SCAM.utils.db_manager import get_db_session
class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Iniciar Sesión")
        self.setFixedSize(400, 500) # Tamaño fijo para el diálogo de login
        self.setStyleSheet("background-color: #F8F9F9; border-radius: 10px;")

        self.username = None
        self.user_role = None

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)

        # Cargar y mostrar el logo
        logo_path = settings.LOGO_PATH # Usar la ruta del logo desde settings.py
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                # Escalar el pixmap para que encaje mejor en el diálogo
                scaled_pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                logo_label = QLabel()
                logo_label.setPixmap(scaled_pixmap)
                logo_label.setAlignment(Qt.AlignCenter)
                layout.addWidget(logo_label)
            else:
                layout.addWidget(QLabel("Error: No se pudo cargar la imagen del logo."))
        else:
            layout.addWidget(QLabel("Error: Archivo de logo no encontrado."))
        
        # Título
        title_label = QLabel("Bienvenido a LEX360PLUS")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2E86C1;")
        layout.addWidget(title_label)

        # Campos de entrada
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Nombre de Usuario")
        self.username_input.setFont(QFont("Arial", 12))
        self.username_input.setFixedHeight(40)
        self.username_input.setStyleSheet("border: 2px solid #D1D9D9; border-radius: 10px; padding: 5px;")
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Contraseña")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFont(QFont("Arial", 12))
        self.password_input.setFixedHeight(40)
        self.password_input.setStyleSheet("border: 2px solid #D1D9D9; border-radius: 10px; padding: 5px;")
        layout.addWidget(self.password_input)

        # Botón de Iniciar Sesión
        login_button = QPushButton("Iniciar Sesión")
        login_button.setFont(QFont("Arial", 14, QFont.Bold))
        login_button.setFixedHeight(45)
        login_button.setStyleSheet("""
            QPushButton {
                background-color: #28B463;
                color: white;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #1D8348;
            }
            QPushButton:pressed {
                background-color: #1D8348;
            }
        """)
        login_button.clicked.connect(self.handle_login)
        layout.addWidget(login_button)

        self.setLayout(layout)

    # En: SELECTA_SCAM/usuarios/login.py

    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Campos Vacíos", "Por favor, ingrese su nombre de usuario y contraseña.")
            return

        # --- INICIO DE LA CORRECCIÓN ---
        # 1. Creamos una instancia de UsuariosDB sin pasarle nada
        usuarios_db = UsuariosDB() 
        
        # 2. Obtenemos una sesión desde el gestor centralizado
        session = get_db_session()
        
        try:
            # 3. Verificamos el usuario usando la sesión que obtuvimos
            success, role = usuarios_db.verificar_usuario(session, username, password)
        finally:
            # 4. Cerramos la sesión
            session.close()
        # --- FIN DE LA CORRECCIÓN ---

        if success:
            self.username = username
            self.user_role = role
            self.accept()
        else:
            QMessageBox.warning(self, "Error de Inicio de Sesión", "Nombre de usuario o contraseña incorrectos.")
            self.username_input.clear()
            self.password_input.clear()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    login_window = LoginWindow()
    if login_window.exec_() == QDialog.Accepted:
        # Si el inicio de sesión es exitoso, puedes acceder a login_window.username y login_window.user_role aquí
        # Por ejemplo, para lanzar la ventana principal de la aplicación.
        print(f"Inicio de sesión exitoso para: {login_window.username} (Rol: {login_window.user_role})")
    else:
        print("Inicio de sesión cancelado o fallido.")
    sys.exit(app.exec_())