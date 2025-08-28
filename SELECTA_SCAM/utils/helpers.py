# utils/helpers.py

from PyQt5.QtWidgets import QMessageBox

def show_error(message):
    QMessageBox.critical(None, "Error", message)

def show_info(message):
    QMessageBox.information(None, "Información", message)
