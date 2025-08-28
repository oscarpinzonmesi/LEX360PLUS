# SELECTA_SCAM/usuarios/change_password.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

from SELECTA_SCAM.db.usuarios_db import UsuariosDB
# Importamos SessionLocal del nuevo conector SQLAlchemy
# Añade esta nueva línea:
from SELECTA_SCAM.utils.db_manager import get_db_session
class ChangePasswordDialog(QDialog):
    def __init__(self, username: str, parent=None): # Ya no necesita usuarios_db como argumento
        super().__init__(parent)
        self.setWindowTitle(f"Cambiar Contraseña para {username}")
        self.setFixedSize(350, 250)
        self.username = username
        
        # No se pasa usuarios_db al constructor, se creará una sesión internamente.
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)

        title_label = QLabel(f"Cambiar Contraseña para\n'{self.username}'")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        self.old_password_input = QLineEdit()
        self.old_password_input.setPlaceholderText("Contraseña Actual")
        self.old_password_input.setEchoMode(QLineEdit.Password)
        self.old_password_input.setFixedHeight(30)
        layout.addWidget(self.old_password_input)

        self.new_password_input = QLineEdit()
        self.new_password_input.setPlaceholderText("Nueva Contraseña")
        self.new_password_input.setEchoMode(QLineEdit.Password)
        self.new_password_input.setFixedHeight(30)
        layout.addWidget(self.new_password_input)

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirmar Nueva Contraseña")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setFixedHeight(30)
        layout.addWidget(self.confirm_password_input)

        change_button = QPushButton("Cambiar Contraseña")
        change_button.setFont(QFont("Arial", 12, QFont.Bold))
        change_button.setFixedHeight(35)
        change_button.setStyleSheet("""
            QPushButton {
                background-color: #2E86C1;
                color: white;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #1B4F72;
            }
        """)
        change_button.clicked.connect(self.change_password)
        layout.addWidget(change_button)

        self.setLayout(layout)

    def change_password(self):
        old_password = self.old_password_input.text()
        new_password = self.new_password_input.text()
        confirm_password = self.confirm_password_input.text()

        if not old_password or not new_password or not confirm_password:
            QMessageBox.warning(self, "Error", "Todos los campos son obligatorios.")
            return

        if new_password != confirm_password:
            QMessageBox.warning(self, "Error", "Las nuevas contraseñas no coinciden.")
            return

        # Creamos una sesión de DB para esta operación
        # --- INICIO DE LA CORRECCIÓN ---
        # 1. Creamos una instancia de UsuariosDB sin pasarle nada
        usuarios_db = UsuariosDB()
        
        # 2. Obtenemos una sesión del gestor central
        session = get_db_session()
        
        try:
            # 3. Verificamos la contraseña actual usando la sesión
            success_old_password, _ = usuarios_db.verificar_usuario(session, self.username, old_password)

            if not success_old_password:
                QMessageBox.warning(self, "Error", "La contraseña actual es incorrecta.")
                return

            # 4. Si es correcta, actualizamos la contraseña usando la misma sesión
            if usuarios_db.actualizar_contrasena(session, self.username, new_password):
                QMessageBox.information(self, "Éxito", "Contraseña cambiada correctamente.")
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "No se pudo cambiar la contraseña.")
        finally:
            # 5. Cerramos la sesión sin importar lo que pase
            session.close()
        # --- FIN DE LA CORRECCIÓN ---