import re
import sqlite3
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QMessageBox, QSpacerItem, QSizePolicy, QComboBox, QDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from .clientes_model import ClientesModel
from .cliente_editor_dialog import ClienteEditorDialog
from utils.db_manager import DBManager
from utils.documentos_db import DocumentosDB
from PyQt5.QtWidgets import QMessageBox
from modulos.clientes.clientes_db import ClientesDB

class ClientesWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(self.styleSheet() + """
            QWidget {
                background-color: #f5f6fa;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #dcdde1;
            }
        """)

        self.setWindowTitle("Gestión de Clientes")
        # Aplicar fuente más grande para todos los elementos
        self.setStyleSheet("font-size: 20px;")  # Aumentar el tamaño de la fuente a 20px

        self.mostrando_papelera = False

        layout = QVBoxLayout(self)
        self.label = QLabel("Lista de Clientes")

        self.btn_toggle_form = QPushButton("+ Nuevo Cliente")
        self.btn_toggle_form.setFont(QFont("Arial", 14))
        self.btn_toggle_form.setStyleSheet("""
            QPushButton {
                background-color: #4a4a4a;
                color: white;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
                border: 2px solid #2c2c2c; /* efecto de contorno en lugar de sombra */
            }
            QPushButton:hover {
                background-color: #6b6b6b;
                border: 2px solid #1e1e1e;
            }
        """)

        layout.addWidget(self.btn_toggle_form)

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por ID o Nombre...")
        search_layout.addWidget(self.search_input)
        search_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        layout.addWidget(self.label)
        layout.addLayout(search_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Nombre", "Tipo ID", "Identificación", "Correo", "Teléfono", "Dirección"
        ])
        # Fuente más grande para la tabla
        self.table.setStyleSheet("QTableWidget { font-size: 20px; }")  # Aumenta el tamaño de la fuente en la tabla

        self.table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #d3d3d3;
                color: black;
                font-size: 18px;
                font-weight: bold;
                border-bottom: 2px solid #7f8c8d;
            }
        """)
        self.table.setSelectionBehavior(self.table.SelectRows)

        layout.addWidget(self.table)

        botones_layout = QHBoxLayout()

        self.btn_eliminar = QPushButton("Eliminar")
        self.btn_eliminar.setFixedHeight(40)
        self.btn_eliminar.setFont(QFont("Arial", 14))
        self.btn_eliminar.setStyleSheet("""
            QPushButton {
                background-color: #4a4a4a;
                color: white;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
                border: 2px solid #2c2c2c; /* efecto de contorno en lugar de sombra */
            }
            QPushButton:hover {
                background-color: #6b6b6b;
                border: 2px solid #1e1e1e;
            }
        """)



        self.btn_papelera = QPushButton("Papelera")
        self.btn_papelera.setFixedHeight(40)
        self.btn_papelera.setFont(QFont("Arial", 14))
        self.btn_papelera.setStyleSheet("""
            QPushButton {
                background-color: #4a4a4a;
                color: white;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
                border: 2px solid #2c2c2c; /* efecto de contorno en lugar de sombra */
            }
            QPushButton:hover {
                background-color: #6b6b6b;
                border: 2px solid #1e1e1e;
            }
        """)




        self.btn_recuperar = QPushButton("Recuperar")
        self.btn_recuperar.setFixedHeight(40)
        self.btn_recuperar.setFont(QFont("Arial", 14))
        self.btn_recuperar.setStyleSheet("""
            QPushButton {
                background-color: #4a4a4a;
                color: white;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
                border: 2px solid #2c2c2c; /* efecto de contorno en lugar de sombra */
            }
            QPushButton:hover {
                background-color: #6b6b6b;
                border: 2px solid #1e1e1e;
            }
        """)




        self.btn_eliminar_def = QPushButton("Eliminar Definitivamente")
        self.btn_eliminar_def.setFixedHeight(40)
        self.btn_eliminar_def.setFont(QFont("Arial", 14))
        self.btn_eliminar_def.setStyleSheet("""
            QPushButton {
                background-color: #4a4a4a;
                color: white;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
                border: 2px solid #2c2c2c; /* efecto de contorno en lugar de sombra */
            }
            QPushButton:hover {
                background-color: #6b6b6b;
                border: 2px solid #1e1e1e;
            }
        """)




        self.btn_editar = QPushButton("Editar")
        self.btn_editar.setFixedHeight(40)
        self.btn_editar.setFont(QFont("Arial", 14))
        self.btn_editar.setStyleSheet("""
            QPushButton {
                background-color: #4a4a4a;
                color: white;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
                border: 2px solid #2c2c2c; /* efecto de contorno en lugar de sombra */
            }
            QPushButton:hover {
                background-color: #6b6b6b;
                border: 2px solid #1e1e1e;
            }
        """)




        botones_layout.addWidget(self.btn_editar)
        botones_layout.addWidget(self.btn_eliminar)
        botones_layout.addWidget(self.btn_papelera)
        botones_layout.addWidget(self.btn_recuperar)
        botones_layout.addWidget(self.btn_eliminar_def)
        layout.addLayout(botones_layout)

        # Conectar botones
        self.btn_editar.clicked.connect(self.editar_cliente)
        self.btn_toggle_form.clicked.connect(self.open_nuevo_cliente_dialog)
        self.table.itemSelectionChanged.connect(self.activar_editar_boton)
        self.db = ClientesDB(lambda: sqlite3.connect("data/base_datos.db"))

        # Eventos
        self.search_input.textChanged.connect(self.filtrar_clientes)
        self.btn_eliminar.clicked.connect(self.eliminar_cliente)
        self.btn_papelera.clicked.connect(self.toggle_papelera)
        self.btn_recuperar.clicked.connect(self.recuperar_cliente)  # Línea agregada aquí
        self.btn_eliminar_def.clicked.connect(self.eliminar_cliente_definitivo)
        self.btn_recuperar.setVisible(False)
        self.btn_eliminar_def.setVisible(False)
        self.mostrar_clientes()

    def showEvent(self, event):
        super().showEvent(event)
        self.search_input.setFocus()
   
    def mostrar_clientes(self, datos=None):
        """Optimizada para actualizar solo las filas necesarias."""
        # Si no se proporcionan datos, los obtenemos de la base de datos
        if datos is None:
            datos = self.db.get_clientes(incluir_eliminados=self.mostrando_papelera)

        # Limpia todas las filas de la tabla
        self.table.setRowCount(0)

        # Si no hay datos, no continuamos
        if not datos:
            return

        # Insertar filas con datos
        for row_data in datos:
            id_, nombre, tipo_id, identificacion, correo, telefono, direccion, eliminado = row_data

            # Verifica si alguno de los campos está vacío. Si es así, omite la fila
            if not any([id_, nombre, tipo_id, identificacion, correo, telefono, direccion]):
                continue

            # Agregamos una nueva fila
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Lista de valores a insertar
            values = [id_, nombre, tipo_id, identificacion, correo, telefono, direccion]

            # Insertar datos en cada columna
            for col, val in enumerate(values):
                item = QTableWidgetItem(str(val))
                item.setFont(QFont())
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)

                # Estilo para eliminados    
                if eliminado:
                    item.setForeground(Qt.gray)
                else:
                    item.setForeground(Qt.black)

                self.table.setItem(row, col, item)

            # Ajustar la altura de la fila (puedes cambiar el valor 40 a lo que desees)
            self.table.setRowHeight(row, 40)  # Ajusta la altura de las filas

        # Ajustar el tamaño de las columnas
        self.table.resizeColumnsToContents()

    def get_row_by_id(self, id_cliente):
        """Obtiene la fila de la tabla donde está un cliente por su ID"""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            # Verifica si el item existe antes de intentar acceder a .text()
            if item is not None and item.text() == str(id_cliente):
                return row
        return None


    def filtrar_clientes(self, texto):
        if self.mostrando_papelera:
            resultados = self.db.buscar_eliminados(texto)
        else:
            resultados = self.db.buscar_por_id_o_nombre(texto)
        self.mostrar_clientes(resultados)
    def eliminar_cliente(self):
        fila = self.table.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Advertencia", "Selecciona un cliente para eliminar.")
            return

        cliente_id = self.table.item(fila, 0)
        if cliente_id is not None:
            cliente_id = int(cliente_id.text())
        else:
            QMessageBox.warning(self, "Advertencia", "No se pudo obtener el ID del cliente.")
            return

        # Cambiar temporalmente el color de la fila a rojo para indicar eliminación
        for col in range(self.table.columnCount()):
            item = self.table.item(fila, col)
            if item:
                item.setBackground(Qt.red)

        # Confirmación de eliminación
        confirm = QMessageBox.question(
            self, "Confirmar eliminación",
            "¿Estás seguro de enviar este cliente a la papelera?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            self.db.marcar_como_eliminado(cliente_id)
            self.mostrar_clientes()
            QMessageBox.information(self, "Eliminado", "Cliente enviado a la papelera.")

    def toggle_papelera(self):
        self.mostrando_papelera = not self.mostrando_papelera

        # Obtener los clientes (todos si estamos en modo papelera, solo activos si no)
        datos = self.db.get_clientes(incluir_eliminados=True) if self.mostrando_papelera else self.db.get_clientes()

        # Verificar si hay elementos eliminados
        hay_eliminados = any(cliente[-1] for cliente in datos) if self.mostrando_papelera else False

        if self.mostrando_papelera:
            if not hay_eliminados:
                QMessageBox.information(self, "Papelera Vacía", "No hay documentos en la papelera.")
                # Revertir a modo activos automáticamente
                self.mostrando_papelera = False
                self.btn_papelera.setText("Papelera")
                self.btn_recuperar.setVisible(False)
                self.btn_eliminar_def.setVisible(False)
            else:
                self.btn_papelera.setText("Volver a Activos")
                self.btn_recuperar.setVisible(True)
                self.btn_eliminar_def.setVisible(True)
        else:
            self.btn_papelera.setText("Papelera")
            self.btn_recuperar.setVisible(False)
            self.btn_eliminar_def.setVisible(False)

        # Actualizar la tabla con los datos correspondientes
        datos = self.db.get_clientes(incluir_eliminados=self.mostrando_papelera)

        # Filtrar los datos: solo mostrar eliminados en modo papelera
        if self.mostrando_papelera:
            datos = [cliente for cliente in datos if cliente[-1]]  # Solo los eliminados

        self.mostrar_clientes(datos)


    def get_selected_cliente(self):
        fila = self.table.currentRow()
        if fila < 0:
            return None
        cliente = []
        for col in range(self.table.columnCount()):
            item = self.table.item(fila, col)
            cliente.append(item.text() if item else "")
        return cliente
    
    def open_nuevo_cliente_dialog(self):
        dialog = ClienteEditorDialog(
            campos=["Nombre", "Tipo ID", "Identificación", "Correo", "Teléfono", "Dirección"],
            valores=[""] * 6,
            parent=self
        )
        if dialog.exec_() == QDialog.Accepted:
            vals = dialog.get_values()
            nombre = vals["Nombre"]
            tipo_id = vals["Tipo ID"]
            identificacion = vals["Identificación"]
            correo = vals["Correo"]
            telefono = vals["Teléfono"]
            direccion = vals["Dirección"]

            try:
                self.db.agregar_cliente(nombre, tipo_id, identificacion, correo, telefono, direccion)
                QMessageBox.information(self, "Agregado", "Cliente agregado correctamente.")
                self.mostrar_clientes()
            except Exception as e:
                QMessageBox.critical(self, "Error al agregar", str(e))


    def recuperar_cliente(self):
        fila = self.table.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Advertencia", "Selecciona un cliente para recuperar.")
            return

        cliente_id = int(self.table.item(fila, 0).text())

        confirm = QMessageBox.question(
            self, "Confirmar recuperación",
            "¿Estás seguro de recuperar este cliente?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            self.db.marcar_como_recuperado(cliente_id)
            self.mostrando_papelera = True  # Asegura que toggle funcione correctamente
            self.toggle_papelera()          # Cambia a vista activa
            QMessageBox.information(self, "Recuperado", "Cliente recuperado correctamente.")

    
    def eliminar_cliente_definitivo(self):
        fila = self.table.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Advertencia", "Selecciona un cliente para eliminar definitivamente.")
            return

        cliente_id = int(self.table.item(fila, 0).text())
        confirm = QMessageBox.question(
            self, "Confirmar eliminación definitiva",
            "¿Estás seguro de eliminar definitivamente este cliente?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            self.db.eliminar_cliente_definitivo(cliente_id)
            self.mostrar_clientes()
            QMessageBox.information(self, "Eliminado", "Cliente eliminado permanentemente.")
    
    def activar_editar_boton(self):
        # Activar el botón de editar solo si se seleccionó una fila
        self.btn_editar.setEnabled(self.table.currentRow() >= 0)


    def editar_cliente(self):
        fila = self.table.currentRow()

        if fila < 0:
            QMessageBox.warning(self, "Advertencia", "Selecciona un cliente para editar.")
            return

        # Obtener el ID del cliente
        cliente_id_item = self.table.item(fila, 0)

        if cliente_id_item is not None:
            cliente_id = int(cliente_id_item.text())
        else:
            QMessageBox.warning(self, "Advertencia", "No se pudo obtener el ID del cliente.")
            return

        # Obtener los valores del cliente seleccionado
        cliente = self.get_selected_cliente()

        if not cliente:
            QMessageBox.warning(self, "Advertencia", "No se obtuvieron los datos del cliente.")
            return

        # Crear y mostrar el diálogo de edición
        dialog = ClienteEditorDialog(
            campos=["Nombre", "Tipo ID", "Identificación", "Correo", "Teléfono", "Dirección"],
            valores=cliente[1:],  # Excluimos el ID
            parent=self
        )

        # Si se acepta el diálogo
        if dialog.exec_() == QDialog.Accepted:
            nuevos_valores = dialog.get_values()

            # Reemplazar solo si hay cambios y no está vacío
            datos_actualizados = []
            # Aquí, accedemos a los valores del diccionario usando las claves del formulario
            for campo, nuevo in nuevos_valores.items():
                # Obtenemos el índice del campo original para obtener su valor original de la lista
                index = ["Nombre", "Tipo ID", "Identificación", "Correo", "Teléfono", "Dirección"].index(campo) + 1
                original = cliente[index]

                # Si el nuevo valor no está vacío, lo reemplazamos
                if nuevo.strip():
                    datos_actualizados.append(nuevo)
                else:
                    # Si el nuevo valor está vacío, mantenemos el valor original
                    datos_actualizados.append(original)

            try:
                self.db.editar_cliente(cliente_id, *datos_actualizados)
                self.mostrar_clientes()  # Actualiza la lista de clientes sin mensaje adicional
            except Exception as e:
                QMessageBox.critical(self, "Error al editar", str(e))



    def editar_cliente_db(self, cliente_id, nombre, tipo_id, identificacion, correo, telefono, direccion):
        query = """UPDATE clientes SET nombre=?, tipo_id=?, identificacion=?, correo=?, telefono=?, direccion=? WHERE id=?"""
        conn = self.db.conexion_func()
        cursor = conn.cursor()
        cursor.execute(query, (nombre, tipo_id, identificacion, correo, telefono, direccion, cliente_id))
        conn.commit()
        conn.close()
