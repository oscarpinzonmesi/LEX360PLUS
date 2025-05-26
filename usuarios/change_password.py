from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox
from utils.db_manager import DBManager

class ChangePasswordDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cambiar Contraseña")
        self.resize(400, 250)

        layout = QVBoxLayout(self)

        self.lbl_user = QLabel("Usuario:")
        self.input_user = QLineEdit()

        self.lbl_old_pass = QLabel("Contraseña Actual:")
        self.input_old_pass = QLineEdit()
        self.input_old_pass.setEchoMode(QLineEdit.Password)

        self.lbl_new_pass = QLabel("Nueva Contraseña:")
        self.input_new_pass = QLineEdit()
        self.input_new_pass.setEchoMode(QLineEdit.Password)

        self.btn_change = QPushButton("Cambiar Contraseña")
        self.btn_change.clicked.connect(self.handle_change)

        layout.addWidget(self.lbl_user)
        layout.addWidget(self.input_user)
        layout.addWidget(self.lbl_old_pass)
        layout.addWidget(self.input_old_pass)
        layout.addWidget(self.lbl_new_pass)
        layout.addWidget(self.input_new_pass)
        layout.addWidget(self.btn_change)

        self.db = DBManager()

    def handle_change(self):
        user = self.input_user.text().strip()
        old_pass = self.input_old_pass.text().strip()
        new_pass = self.input_new_pass.text().strip()

        if not user or not old_pass or not new_pass:
            QMessageBox.warning(self, "Campos incompletos", "Por favor completa todos los campos.")
            return

        # Verificar usuario y contraseña actual
        success, _ = self.db.verify_user(user, old_pass)
        if success:
            # Solo enviamos el texto plano de la nueva contraseña
            self.db.update_password(user, new_pass)
            QMessageBox.information(self, "Éxito", "Contraseña actualizada correctamente.")
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Usuario o contraseña actual incorrectos.")
