from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QMessageBox
from utils.db_manager import DBManager
from utils.usuarios_db import UsuariosDB  # <- Importa correctamente

class RegisterUserDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Registrar Nuevo Usuario")
        self.resize(300, 200)

        layout = QVBoxLayout(self)

        self.label_user = QLabel("Usuario:")
        self.input_user = QLineEdit()

        self.label_pass = QLabel("Contraseña:")
        self.input_pass = QLineEdit()
        self.input_pass.setEchoMode(QLineEdit.Password)

        self.label_role = QLabel("Rol:")
        self.combo_role = QComboBox()
        self.combo_role.addItems(["admin", "usuario"])

        self.btn_register = QPushButton("Registrar")
        self.btn_register.clicked.connect(self.register_user)

        layout.addWidget(self.label_user)
        layout.addWidget(self.input_user)
        layout.addWidget(self.label_pass)
        layout.addWidget(self.input_pass)
        layout.addWidget(self.label_role)
        layout.addWidget(self.combo_role)
        layout.addWidget(self.btn_register)

        self.db = DBManager()
        self.usuarios_db = UsuariosDB(self.db.conectar)  # <- Instancia UsuariosDB correctamente

    def register_user(self):
        usuario = self.input_user.text()
        contrasena = self.input_pass.text()
        rol = self.combo_role.currentText()

        if not usuario or not contrasena:
            QMessageBox.warning(self, "Error", "Debe ingresar usuario y contraseña.")
            return

        try:
            if self.usuarios_db.usuario_existe(usuario):
                QMessageBox.warning(self, "Error", "El usuario ya existe.")
                return

            self.usuarios_db.insertar_usuario(usuario, contrasena, rol)
            QMessageBox.information(self, "Éxito", "Usuario registrado correctamente.")
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Ocurrió un error: {e}")
