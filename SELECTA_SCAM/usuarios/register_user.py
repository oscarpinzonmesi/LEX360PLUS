# SELECTA_SCAM/usuarios/register_user.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox, QComboBox
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

from SELECTA_SCAM.db.usuarios_db import UsuariosDB
# Importamos SessionLocal del nuevo conector SQLAlchemy
from SELECTA_SCAM.utils.db_manager import get_db_session


class RegisterUserDialog(QDialog):
    def __init__(self, parent=None): # Ya no necesita usuarios_db como argumento
        super().__init__(parent)
        self.setWindowTitle("Registrar Nuevo Usuario")
        self.setFixedSize(350, 300)
        
        # No se pasa usuarios_db al constructor, se creará una sesión internamente.

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)

        title_label = QLabel("Registro de Usuario")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Nombre de Usuario")
        self.username_input.setFixedHeight(30)
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Contraseña")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(30)
        layout.addWidget(self.password_input)

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirmar Contraseña")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setFixedHeight(30)
        layout.addWidget(self.confirm_password_input)

        # Combo Box para seleccionar el rol
        self.role_combobox = QComboBox()
        self.role_combobox.addItem("Usuario Estándar", False) # False para es_admin
        self.role_combobox.addItem("Administrador", True) # True para es_admin
        self.role_combobox.setFixedHeight(30)
        layout.addWidget(self.role_combobox)

        register_button = QPushButton("Registrar Usuario")
        register_button.setFont(QFont("Arial", 12, QFont.Bold))
        register_button.setFixedHeight(35)
        register_button.setStyleSheet("""
            QPushButton {
                background-color: #28B463;
                color: white;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #1D8348;
            }
        """)
        register_button.clicked.connect(self.register_user)
        layout.addWidget(register_button)

        self.setLayout(layout)

    def register_user(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        es_admin = self.role_combobox.currentData() # Obtiene el valor True/False asociado al ítem

        if not username or not password or not confirm_password:
            QMessageBox.warning(self, "Error", "Todos los campos son obligatorios.")
            return

        if password != confirm_password:
            QMessageBox.warning(self, "Error", "Las contraseñas no coinciden.")
            return
        
        # Creamos una sesión de DB para esta operación
       # --- INICIO DE LA CORRECCIÓN ---
        # 1. Creamos una instancia de UsuariosDB sin pasarle nada
        usuarios_db = UsuariosDB()
        
        # 2. Obtenemos una sesión del gestor central
        session = get_db_session()
        
        try:
            # 3. Verificamos si el usuario existe usando la sesión
            if usuarios_db.usuario_existe(session, username):
                QMessageBox.warning(self, "Error", "El nombre de usuario ya existe.")
                return

            # 4. Si no existe, lo insertamos usando la misma sesión
            if usuarios_db.insertar_usuario(session, username, password, es_admin):
                QMessageBox.information(self, "Éxito", "Usuario registrado exitosamente.")
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "No se pudo registrar el usuario.")
        finally:
            # 5. Cerramos la sesión
            session.close()
        # --- FIN DE LA CORRECCIÓN ---