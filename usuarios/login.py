from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox
from utils.usuarios_db import verificar_usuario
from usuarios.change_password import ChangePasswordDialog

class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login LEX360PLUS")
        self.resize(500, 300)
        layout = QVBoxLayout(self)

        self.lbl_user = QLabel("Usuario:")
        self.lbl_pass = QLabel("Contraseña:")

        self.input_user = QLineEdit()
        self.input_pass = QLineEdit()
        self.input_pass.setEchoMode(QLineEdit.Password)

        self.btn_login = QPushButton("Iniciar Sesión")
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_change_pass = QPushButton("Cambiar Contraseña")

        # Estilos
        self.input_user.setStyleSheet("color: red;")
        self.btn_login.setStyleSheet("background-color: #3498db; color: white; border-radius: 8px;")
        self.btn_cancel.setStyleSheet("background-color: #e74c3c; color: white; border-radius: 8px;")
        self.btn_change_pass.setStyleSheet("background-color: #f39c12; color: white; border-radius: 8px;")

        # Layout
        layout.addWidget(self.lbl_user)
        layout.addWidget(self.input_user)
        layout.addWidget(self.lbl_pass)
        layout.addWidget(self.input_pass)
        layout.addWidget(self.btn_login)
        layout.addWidget(self.btn_change_pass)
        layout.addWidget(self.btn_cancel)

        # Conexiones
        self.btn_login.clicked.connect(self.handle_login)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_change_pass.clicked.connect(self.open_change_password_dialog)

        self.username = None
        self.user_role = None

    def handle_login(self):
        username = self.input_user.text().strip()
        password = self.input_pass.text()

        if not username or not password:
            QMessageBox.warning(self, "Campos requeridos", "Debes ingresar usuario y contraseña.")
            return

        success, role = verificar_usuario(username, password)
        if success:
            self.username = username
            self.user_role = role
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Usuario o contraseña incorrectos.")

    def open_change_password_dialog(self):
        dlg = ChangePasswordDialog()
        dlg.exec_()
