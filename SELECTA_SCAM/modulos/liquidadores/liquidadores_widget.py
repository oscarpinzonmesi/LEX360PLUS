# SELECTA_SCAM/modulos/liquidadores/liquidadores_widget.py
import sys # Needed for sys.executable (used in controller)
import os # Could be useful for validating paths before passing to controller
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QComboBox, QMessageBox, QHeaderView, QFormLayout,
    QTextEdit, QLabel
)
from PyQt5.QtCore import QDate, Qt, pyqtSignal # Import pyqtSignal
from PyQt5.QtGui import QFont, QColor # Import QColor for colors

# Import the controller
from SELECTA_SCAM.modulos.liquidadores.liquidadores_controller import LiquidadoresController
# Assume LiquidadoresDB is imported in the controller, not directly here
from SELECTA_SCAM.modulos.liquidadores.liquidadores_db import LiquidadoresDB # Keep the import to instantiate the DB and pass it


# Centralized styles for buttons (similar to DocumentosWidget)
BOTON_ESTILOS = {
    "default": "background-color: #6c757d; color: white; border-radius: 8px; padding: 8px 16px; font-weight: bold;",
    "agregar": "background-color: #2ecc71; color: white; border-radius: 8px; padding: 8px 16px; font-weight: bold;",
    "editar": "background-color: #f39c12; color: white; border-radius: 8px; padding: 8px 16px; font-weight: bold;",
    "eliminar": "background-color: #e74c3c; color: white; border-radius: 8px; padding: 8px 16px; font-weight: bold;",
    "ejecutar": "background-color: #3498db; color: white; border-radius: 8px; padding: 8px 16px; font-weight: bold;",
    "volver": "background-color: #95a5a6; color: white; border-radius: 8px; padding: 8px 16px; font-weight: bold;",
    "deshabilitado": "background-color: #bdc3c7; color: #6c757d; border-radius: 8px; padding: 8px 16px; font-weight: bold;"
}

class LiquidadoresWidget(QWidget):
    # Signal to notify the parent that a return to home is requested
    back_requested = pyqtSignal()

    def __init__(self, db_connector: LiquidadoresDB, parent=None, user_data: dict = None):
        super().__init__(parent)
        self.db = db_connector # Passed to the controller
        self.user_data = user_data # Kept for future use (e.g., permissions)
        self.selected_row = None # Keep for table selection handling
        self.tool_in_edition_id = None # To know if we are editing or adding

        # Controller instance
        self.controller = LiquidadoresController(self.db, self)

        self.init_ui()
        self.connect_signals() # Connect signals after UI initialization
        self.controller.load_tools() # Load initial data via the controller

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # --- Module Title ---
        title_label = QLabel("Gestión de Herramientas de Liquidación")
        title_font = QFont("Arial", 18, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        layout.addSpacing(15)

        # --- Table to display Liquidation Tools ---
        self.table = QTableWidget()
        # Columns: ID, Tool Name, Description, Executable Path, Area of Law
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre Herramienta", "Descripción", "Ruta Ejecutable", "Área Derecho"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.table.cellClicked.connect(self.select_row) # Replaced by itemSelectionChanged for more robust handling
        layout.addWidget(self.table)

        # --- Input fields for adding/editing Tools ---
        form_inputs_layout = QFormLayout()
        font = QFont("Arial", 12) # Slightly smaller font for inputs

        self.nombre_herramienta_input = QLineEdit()
        self.nombre_herramienta_input.setPlaceholderText("Ej: Liquidador de Cesantías")
        self.nombre_herramienta_input.setFont(font)
        form_inputs_layout.addRow("Nombre Herramienta:", self.nombre_herramienta_input)

        self.descripcion_input = QTextEdit() # Use QTextEdit for longer descriptions
        self.descripcion_input.setPlaceholderText("Descripción de la funcionalidad de la herramienta.")
        self.descripcion_input.setFont(font)
        self.descripcion_input.setFixedHeight(70) # Fixed height for QTextEdit
        form_inputs_layout.addRow("Descripción:", self.descripcion_input)

        self.ruta_ejecutable_input = QLineEdit()
        self.ruta_ejecutable_input.setPlaceholderText("Ej: python_scripts/laboral/cesantias_calc.py")
        self.ruta_ejecutable_input.setFont(font)
        form_inputs_layout.addRow("Ruta Ejecutable:", self.ruta_ejecutable_input)

        self.area_derecho_input = QComboBox()
        self.area_derecho_input.setFont(font)
        self.area_derecho_input.setEditable(True)
        self.area_derecho_input.addItems(["Laboral", "Civil", "Comercial", "Penal", "Administrativo", "Otros"])
        form_inputs_layout.addRow("Área del Derecho:", self.area_derecho_input)

        layout.addLayout(form_inputs_layout)

        # --- Action Buttons ---
        buttons_layout = QHBoxLayout()

        self.agregar_btn = QPushButton("Agregar Herramienta")
        self.agregar_btn.setFont(font)
        self.agregar_btn.setStyleSheet(BOTON_ESTILOS["agregar"])
        buttons_layout.addWidget(self.agregar_btn)

        self.editar_btn = QPushButton("Editar Herramienta")
        self.editar_btn.setFont(font)
        self.editar_btn.setStyleSheet(BOTON_ESTILOS["deshabilitado"]) # Disabled initially
        self.editar_btn.setEnabled(False)
        buttons_layout.addWidget(self.editar_btn)

        self.eliminar_btn = QPushButton("Eliminar Herramienta")
        self.eliminar_btn.setFont(font)
        self.eliminar_btn.setStyleSheet(BOTON_ESTILOS["deshabilitado"]) # Disabled initially
        self.eliminar_btn.setEnabled(False)
        buttons_layout.addWidget(self.eliminar_btn)

        self.ejecutar_btn = QPushButton("Ejecutar Herramienta Seleccionada")
        self.ejecutar_btn.setFont(font)
        self.ejecutar_btn.setStyleSheet(BOTON_ESTILOS["deshabilitado"]) # Disabled initially
        self.ejecutar_btn.setEnabled(False)
        buttons_layout.addWidget(self.ejecutar_btn)

        layout.addLayout(buttons_layout)

        self.volver_btn = QPushButton("Volver al Inicio")
        self.volver_btn.setFont(QFont("Arial", 14))
        self.volver_btn.setStyleSheet(BOTON_ESTILOS["volver"])
        # self.volver_btn.clicked.connect(self.close) # Connect to a custom signal now
        layout.addWidget(self.volver_btn)

    def connect_signals(self):
        """Connects all UI signals to appropriate methods."""
        self.table.itemSelectionChanged.connect(self._on_table_selection_changed)
        self.agregar_btn.clicked.connect(self.on_add_tool_clicked)
        self.editar_btn.clicked.connect(self.on_edit_tool_clicked)
        self.eliminar_btn.clicked.connect(self.on_delete_tool_clicked)
        self.ejecutar_btn.clicked.connect(self.on_execute_tool_clicked)
        self.volver_btn.clicked.connect(self.back_requested.emit) # Emit back signal

    # --- Methods the controller will call to update the view (UI) ---
    def update_table(self, herramientas_data):
        """
        Updates the table with the list of tools provided by the controller.
        """
        self.table.setRowCount(0)
        for row_idx, herramienta in enumerate(herramientas_data):
            self.table.insertRow(row_idx)
            # Store the ID in Qt.UserRole for more robust access and not relying on visible text
            item_id = QTableWidgetItem(str(herramienta['id']))
            item_id.setData(Qt.UserRole, herramienta['id'])
            self.table.setItem(row_idx, 0, item_id)
            self.table.setItem(row_idx, 1, QTableWidgetItem(herramienta['nombre_herramienta']))
            self.table.setItem(row_idx, 2, QTableWidgetItem(herramienta['descripcion']))
            self.table.setItem(row_idx, 3, QTableWidgetItem(herramienta['ruta_ejecutable']))
            self.table.setItem(row_idx, 4, QTableWidgetItem(herramienta['area_derecho']))
        self.table.resizeColumnsToContents()
        self._update_button_states() # Update button states after loading data

    def load_tool_for_edit(self, tool_id, nombre, descripcion, ruta, area):
        """Loads tool data into the form for editing."""
        self.tool_in_edition_id = tool_id
        self.nombre_herramienta_input.setText(nombre)
        self.descripcion_input.setText(descripcion)
        self.ruta_ejecutable_input.setText(ruta)
        self.area_derecho_input.setCurrentText(area)
        self.agregar_btn.setText("Actualizar Herramienta") # Change button text
        self.agregar_btn.setStyleSheet(BOTON_ESTILOS["editar"]) # Change style
        # Disable edit/delete buttons during edit mode to avoid conflicts
        self.editar_btn.setEnabled(False)
        self.eliminar_btn.setEnabled(False)
        self.ejecutar_btn.setEnabled(False)

    def clear_fields(self):
        """Clears form fields and resets the editing state."""
        self.nombre_herramienta_input.clear()
        self.descripcion_input.clear()
        self.ruta_ejecutable_input.clear()
        self.area_derecho_input.setCurrentIndex(0)
        self.tool_in_edition_id = None
        self.selected_row = None # Clear internal selection

        self.agregar_btn.setText("Agregar Herramienta")
        self.agregar_btn.setStyleSheet(BOTON_ESTILOS["agregar"])
        self.table.clearSelection() # Deselect rows in the table
        self._update_button_states() # Update button states

    # --- Methods for displaying messages ---
    def show_info(self, title, message):
        QMessageBox.information(self, title, message)

    def show_warning(self, title, message):
        QMessageBox.warning(self, title, message)

    def show_error(self, title, message):
        QMessageBox.critical(self, title, message)

    def show_question(self, title, message, buttons):
        return QMessageBox.question(self, title, message, buttons)

    # --- Internal UI methods (not delegated to the controller) ---
    def _on_table_selection_changed(self):
        """Updates button states when table selection changes."""
        self.selected_row = None
        selected_items = self.table.selectedItems()
        if selected_items:
            # Get the row of the first selected item
            self.selected_row = selected_items[0].row()
            # Load selected row data into input fields
            # Only if we are not already in edit mode to avoid overwriting entries
            if self.tool_in_edition_id is None:
                self.nombre_herramienta_input.setText(self.table.item(self.selected_row, 1).text())
                self.descripcion_input.setText(self.table.item(self.selected_row, 2).text())
                self.ruta_ejecutable_input.setText(self.table.item(self.selected_row, 3).text())
                self.area_derecho_input.setCurrentText(self.table.item(self.selected_row, 4).text())
        else:
            # If no selection, clear fields if not in edit mode
            if self.tool_in_edition_id is None:
                self.clear_fields() # This will also reset tool_in_edition_id and selected_row if not in edit mode.

        self._update_button_states()


    def _update_button_states(self):
        """Enables or disables buttons based on application state."""
        has_selection = self.table.selectedItems() and len(self.table.selectedItems()) > 0
        is_editing = self.tool_in_edition_id is not None

        # Add/Update button
        self.agregar_btn.setEnabled(True) # Always enabled for adding or updating

        # Row action buttons
        self.editar_btn.setEnabled(has_selection and not is_editing)
        self.eliminar_btn.setEnabled(has_selection and not is_editing)
        self.ejecutar_btn.setEnabled(has_selection and not is_editing)

        # Apply enabled/disabled styles
        self.editar_btn.setStyleSheet(BOTON_ESTILOS["editar"] if self.editar_btn.isEnabled() else BOTON_ESTILOS["deshabilitado"])
        self.eliminar_btn.setStyleSheet(BOTON_ESTILOS["eliminar"] if self.eliminar_btn.isEnabled() else BOTON_ESTILOS["deshabilitado"])
        self.ejecutar_btn.setStyleSheet(BOTON_ESTILOS["ejecutar"] if self.ejecutar_btn.isEnabled() else BOTON_ESTILOS["deshabilitado"])

    # --- Methods to handle button click events and delegate to the controller ---
    def on_add_tool_clicked(self):
        nombre = self.nombre_herramienta_input.text().strip()
        descripcion = self.descripcion_input.toPlainText().strip()
        ruta = self.ruta_ejecutable_input.text().strip()
        area = self.area_derecho_input.currentText().strip()

        if not nombre or not ruta:
            self.show_warning("Campos Requeridos", "El 'Nombre de la Herramienta' y la 'Ruta Ejecutable' son obligatorios.")
            return

        if self.tool_in_edition_id is not None:
            # If in edit mode, call the controller to update
            self.controller.edit_tool(self.tool_in_edition_id, nombre, descripcion, ruta, area)
        else:
            # Otherwise, call the controller to add
            self.controller.add_tool(nombre, descripcion, ruta, area)

    def on_edit_tool_clicked(self):
        if self.selected_row is None:
            self.show_warning("Selección", "Por favor, seleccione una herramienta para editar.")
            return

        tool_id_item = self.table.item(self.selected_row, 0)
        if tool_id_item is None:
            self.show_error("Error", "No se pudo obtener el ID de la herramienta seleccionada.")
            return
        
        tool_id = tool_id_item.data(Qt.UserRole)
        nombre = self.table.item(self.selected_row, 1).text()
        descripcion = self.table.item(self.selected_row, 2).text()
        ruta = self.table.item(self.selected_row, 3).text()
        area = self.table.item(self.selected_row, 4).text()

        self.load_tool_for_edit(tool_id, nombre, descripcion, ruta, area)


    def on_delete_tool_clicked(self):
        if self.selected_row is None:
            self.show_warning("Selección", "Por favor, seleccione una herramienta para eliminar.")
            return

        tool_id_item = self.table.item(self.selected_row, 0)
        if tool_id_item is None:
            self.show_error("Error", "No se pudo obtener el ID de la herramienta seleccionada.")
            return

        tool_id = tool_id_item.data(Qt.UserRole)
        self.controller.delete_tool(tool_id)

    def on_execute_tool_clicked(self):
        if self.selected_row is None:
            self.show_warning("Selección", "Por favor, seleccione una herramienta para ejecutar.")
            return

        ruta_ejecutable = self.table.item(self.selected_row, 3).text().strip()
        self.controller.execute_tool(ruta_ejecutable)