import os
import mimetypes
import sqlite3
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QFileDialog,
    QLineEdit, QTableWidget, QTableWidgetItem, QMessageBox, QComboBox, QDateEdit,
    QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QFont
from .documentos_controller import (
    obtener_documentos_por_cliente,
    insertar_documento,
    editar_documento,
    eliminar_documento_por_id,
    restaurar_documento,
    verificar_documento_existente,
    obtener_documento_por_id
)
from modulos.documentos.documentos_utils import (
    abrir_archivo, color_por_extension, copiar_archivo_a_destino, cargar_datos_iniciales
)
from config import DATABASE_PATH
from functools import partial


# Estilos centralizados para botones
BOTON_ESTILOS = {
    "guardar_default": "background-color: #007BFF; color: white; border-radius: 5px; padding: 8px 16px;",
    "guardar_activo": "background-color: #28A745; color: white; border-radius: 5px; padding: 8px 16px;",
    "abrir": "background-color: #95a5a6; color: white; border-radius: 5px; padding: 8px 16px;",
    "editar": "background-color: #FD7E14; color: black; border-radius: 5px; padding: 8px 16px;",
    "borrar": "background-color: #DC3545; color: white; border-radius: 5px; padding: 8px 16px;",
    "restaurar": "background-color: #17A2B8; color: white; border-radius: 5px; padding: 8px 16px;",
    "volver": "background-color: #6C757D; color: white; border-radius: 5px; padding: 8px 16px;",
    "guardando": "background-color: #FFC107; color: black;",
    "guardar_ok": "background-color: #2196F3; color: white;",
    "abrir_activo": "background-color: #1ABC9C; color: white; border-radius: 5px; padding: 8px 16px;",
    "oscuro": """QPushButton { background-color: #4a4a4a; color: white; border-radius: 8px; padding: 8px 16px; font-weight: bold; } QPushButton:hover { background-color: #6b6b6b; }""",
}


class DocumentosWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión de Documentos")
        self.setStyleSheet("font-size: 20px;")

        # Variables de estado
        self.mostrando_papelera = False
        self.ruta_archivo = ""
        self.documento_en_edicion = None

        # Atributos para guardar contexto de edición
        self.cliente_en_edicion = None
        self.proceso_en_edicion = None
        self.fecha_en_edicion = None
        self.ruta_en_edicion = None

        self.clientes_dict = {}
        self.documentos = []
        self.init_ui()
        self.cargar_datos()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # --- Contenedor principal ---
        contenedor = QWidget()
        contenedor_layout = QVBoxLayout()
        contenedor.setLayout(contenedor_layout)
        layout.addWidget(contenedor)

        # Título
        titulo = QLabel("Gestión de Documentos")
        titulo.setFont(QFont("Arial", 16, QFont.Bold))
        contenedor_layout.addWidget(titulo)

        # --- Filtros de cliente y documento ---
        filtro_layout = QHBoxLayout()
        filtro_layout.addWidget(QLabel("Filtrar cliente (nombre o ID):"))
        self.filtro_cliente = QLineEdit()
        self.filtro_cliente.setPlaceholderText("Escribe nombre o ID de cliente...")
        self.filtro_cliente.textChanged.connect(self.filtrar_documentos)
        filtro_layout.addWidget(self.filtro_cliente)

        filtro_layout.addWidget(QLabel("Filtrar por documento:"))
        self.filtro_documento = QLineEdit()
        self.filtro_documento.setPlaceholderText("Escribe nombre del documento...")
        self.filtro_documento.textChanged.connect(self.filtrar_documentos)
        filtro_layout.addWidget(self.filtro_documento)

        contenedor_layout.addLayout(filtro_layout)

        # --- Botones papelera definitiva / recuperar (ocultos al inicio) ---
        self.btn_eliminar_definitivo = QPushButton("Eliminar definitivamente")
        self.btn_eliminar_definitivo.setFont(QFont("Arial", 14))
        self.btn_eliminar_definitivo.setFixedHeight(40)
        self.btn_eliminar_definitivo.setStyleSheet("""
            QPushButton {
                background-color: #c0392b;
                color: white;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e74c3c;
            }
        """)
        self.btn_eliminar_definitivo.clicked.connect(self.eliminar_definitivamente)
        self.btn_eliminar_definitivo.hide()
        contenedor_layout.addWidget(self.btn_eliminar_definitivo)

        self.btn_recuperar = QPushButton("Recuperar")
        self.btn_recuperar.setFont(QFont("Arial", 14))
        self.btn_recuperar.setFixedHeight(40)
        self.btn_recuperar.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        self.btn_recuperar.clicked.connect(self.recuperar_documento)
        self.btn_recuperar.hide()
        contenedor_layout.addWidget(self.btn_recuperar)

        # --- Formulario de carga / edición ---
        form_layout = QHBoxLayout()
        self.cliente_combo = QComboBox()
        self.cliente_combo.setFont(QFont("Arial", 14))
        form_layout.addWidget(self.cliente_combo)

        self.nombre_input = QLineEdit()
        self.nombre_input.setFont(QFont("Arial", 14))
        self.nombre_input.setPlaceholderText("Nombre del documento")
        form_layout.addWidget(self.nombre_input)

        self.fecha_input = QDateEdit()
        self.fecha_input.setFont(QFont("Arial", 14))
        self.fecha_input.setCalendarPopup(True)
        self.fecha_input.setDate(QDate.currentDate())
        form_layout.addWidget(self.fecha_input)

        self.btn_archivo = QPushButton("Seleccionar archivo")
        self.btn_archivo.setStyleSheet(BOTON_ESTILOS["oscuro"])
        self.btn_archivo.clicked.connect(self.seleccionar_archivo)
        form_layout.addWidget(self.btn_archivo)

        self.btn_guardar = QPushButton("Guardar")
        self.btn_guardar.setStyleSheet(BOTON_ESTILOS["oscuro"])
        self.btn_guardar.clicked.connect(self.guardar_documento)
        form_layout.addWidget(self.btn_guardar)

        contenedor_layout.addLayout(form_layout)

        # --- Tabla de documentos activos / papelera ---
        self.tabla = QTableWidget()
        # Seis columnas: ID, Cliente, Nombre, Fecha, Formato, Abrir
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels([
            "ID", "Cliente", "Nombre del Documento", "Fecha", "Formato", "Abrir",
        ])
        contenedor_layout.addWidget(self.tabla)

        # Configuración visual de la tabla
        self.tabla.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #d3d3d3;
                color: black;
                font-size: 16px;
                font-weight: bold;
                border-bottom: 2px solid #7f8c8d;
            }
        """)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # Conectar eventos de selección
        self.tabla.itemSelectionChanged.connect(self._on_seleccion_cambiada)
        self.tabla.itemSelectionChanged.connect(self._actualizar_botones_papelera)

        # --- Botones globales debajo de la tabla ---
        botones_layout = QHBoxLayout()

        self.btn_editar = QPushButton("Editar")
        self.btn_editar.setFont(QFont("Arial", 14))
        self.btn_editar.setFixedHeight(40)
        self.btn_editar.setEnabled(False)
        self.btn_editar.setStyleSheet("""
            QPushButton {
                background-color: #4a4a4a;
                color: white;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #6b6b6b;
            }
        """)
        self.btn_editar.clicked.connect(self._editar_seleccionado)
        botones_layout.addWidget(self.btn_editar)

        self.btn_eliminar = QPushButton("Eliminar")
        self.btn_eliminar.setFont(QFont("Arial", 14))
        self.btn_eliminar.setFixedHeight(40)
        self.btn_eliminar.setEnabled(False)
        self.btn_eliminar.setStyleSheet("""
            QPushButton {
                background-color: #4a4a4a;
                color: white;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #6b6b6b;
            }
        """)
        self.btn_eliminar.clicked.connect(self._eliminar_seleccionado)
        botones_layout.addWidget(self.btn_eliminar)

        self.btn_papelera = QPushButton("Papelera")
        self.btn_papelera.setFont(QFont("Arial", 14))
        self.btn_papelera.setFixedHeight(40)
        self.btn_papelera.setStyleSheet("""
            QPushButton {
                background-color: #4a4a4a;
                color: white;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #6b6b6b;
            }
        """)
        self.btn_papelera.clicked.connect(self._toggle_papelera)
        botones_layout.addWidget(self.btn_papelera)

        layout.addLayout(botones_layout)

    def cargar_datos(self):
        # Carga únicamente la lista de clientes (sin procesos/radicados)
        self.clientes, _ = cargar_datos_iniciales()
        self.clientes_dict = {cid: nombre for cid, nombre in self.clientes}

        # Poblar combo de clientes
        self.cliente_combo.clear()
        self.cliente_combo.addItem("Todos los clientes", None)
        for cid, nombre in self.clientes:
            self.cliente_combo.addItem(nombre, cid)

        # Cada vez que cambie el cliente, recargar la tabla
        self.cliente_combo.currentIndexChanged.connect(self.cargar_documentos)
        self.cargar_documentos()

    def _abrir_archivo_por_ruta(self, ruta):
        try:
            abrir_archivo(ruta, self)
        except Exception as e:
            QMessageBox.critical(self, "Error al abrir archivo", str(e))

    def seleccionar_archivo(self):
        # Antes de permitir seleccionar archivo, debe existir un cliente seleccionado
        if not self.cliente_combo.currentData():
            QMessageBox.warning(self, "Cliente requerido", "Por favor seleccione primero un cliente.")
            self.btn_guardar.setStyleSheet(BOTON_ESTILOS["oscuro"])
            return

        # Mostrar diálogo para elegir archivo
        self.btn_guardar.setStyleSheet(BOTON_ESTILOS["guardando"])
        ruta, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo",
            "",
            "Todos los archivos (*.*)"
        )
        if ruta:
            self.ruta_archivo = ruta
            self.btn_archivo.setText(os.path.basename(ruta))
            self.btn_archivo.setStyleSheet(BOTON_ESTILOS["oscuro"])
        else:
            self.btn_guardar.setStyleSheet(BOTON_ESTILOS["oscuro"])

    def guardar_documento(self):
        try:
            if not self._validar_campos():
                return

            if self.documento_en_edicion:
                self._procesar_edicion()
            else:
                self._procesar_creacion()
        finally:
            self.reset_btn_archivo()

    def _validar_campos(self) -> bool:
        nombre = self.nombre_input.text().strip()
        if self.documento_en_edicion and not nombre:
            QMessageBox.warning(self, "Campo requerido", "Debe ingresar un nuevo nombre para el documento.")
            return False
        if not self.documento_en_edicion and (not self.cliente_combo.currentData() or not self.ruta_archivo):
            QMessageBox.warning(self, "Campos incompletos", "Debe seleccionar un cliente y un archivo para continuar.")
            return False
        return True

    def _procesar_creacion(self):
        try:
            self.btn_guardar.setStyleSheet(BOTON_ESTILOS["guardando"])

            # Determinar extensión y nombre final
            _, ext = os.path.splitext(self.ruta_archivo)
            nombre_input = self.nombre_input.text().strip()
            if nombre_input:
                nombre_archivo = f"{nombre_input}{ext}"
            else:
                nombre_archivo = os.path.basename(self.ruta_archivo)

            # Copiar archivo a destino
            try:
                ruta_destino = copiar_archivo_a_destino(self.ruta_archivo, nombre_archivo)
            except FileExistsError:
                # Si ya existe, usar ruta fija como fallback
                ruta_destino = os.path.join(r"C:/Users/oscar/Claro drive2/LEX360", nombre_archivo)

            # Insertar en BD (sin radicado)
            tipo_mime, _ = mimetypes.guess_type(ruta_destino)
            tipo_doc = tipo_mime.split("/")[-1] if tipo_mime else "desconocido"

            insertar_documento(
                nombre_archivo,
                self.cliente_combo.currentData(),
                None,
                self.fecha_input.date().toString("yyyy-MM-dd"),
                ruta_destino,
                tipo_doc
            )
            QMessageBox.information(self, "Éxito", "Documento guardado correctamente.")
            self._post_guardado()
        except Exception as e:
            QMessageBox.critical(self, "Error inesperado", f"Ocurrió un error al guardar el documento:\n{e}")
            self.btn_guardar.setStyleSheet(BOTON_ESTILOS["guardar_default"])

    def _procesar_edicion(self):
        try:
            nuevo_nombre = self.nombre_input.text().strip()

            # Llamar a la función del controlador con los 6 parámetros que exige:
            # (id_documento, nuevo_nombre, cliente_id, proceso_id, fecha, ruta_archivo)
            editar_documento(
                self.documento_en_edicion,
                nuevo_nombre,
                self.cliente_en_edicion,
                self.proceso_en_edicion,
                self.fecha_en_edicion,
                self.ruta_en_edicion
            )
            QMessageBox.information(self, "Éxito", "Documento editado correctamente.")
            self._restaurar_estado_campos()
            self._post_guardado()
        except Exception as e:
            QMessageBox.critical(self, "Error al editar el documento", str(e))
            self._restaurar_estado_campos()

    def _post_guardado(self):
        self.limpiar_formulario()
        self.cargar_documentos()
        self.btn_guardar.setStyleSheet(BOTON_ESTILOS["oscuro"])

    def _restaurar_estado_campos(self):
        self.cliente_combo.setEnabled(True)
        self.fecha_input.setEnabled(True)
        self.btn_archivo.setEnabled(True)
        self.btn_guardar.setStyleSheet(BOTON_ESTILOS["guardar_default"])

    def cargar_documentos(self):
        cliente_id = self.cliente_combo.currentData()

        # Obtener documentos activos por cliente (o todos)
        if cliente_id is None:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT d.id, d.nombre, d.cliente_id, d.proceso_id, d.fecha, d.ruta_archivo
                FROM documentos d
                WHERE d.eliminado = 0
            """)
            documentos = cursor.fetchall()
            conn.close()
        else:
            # Esta lista tiene 9 columnas: (id, proceso_id, nombre, archivo, fecha,
            # ruta_archivo, eliminado, cliente_id, cliente_nombre)
            documentos = obtener_documentos_por_cliente(cliente_id)

        # Limpiar tabla
        self.tabla.setRowCount(0)
        row = 0

        for doc in documentos:
            if len(doc) == 6:
                # Caso: datos desde consulta SQL directa
                # doc = (id, nombre, cliente_id, proceso_id, fecha, ruta_archivo)
                doc_id, nombre, cli_id, proc_id, fecha, ruta_real = doc
                cliente_nombre = self.clientes_dict.get(cli_id, "N/A")
                eliminado = 0
            else:
                # Caso: datos desde controlador (9 campos)
                # doc = (id, proceso_id, nombre, archivo, fecha, ruta_archivo, eliminado, cliente_id, cliente_nombre)
                doc_id, proc_id, nombre, _, fecha, ruta_real, eliminado, cli_id, cliente_nombre = doc

            # Solo mostrar los que no estén en papelera (eliminado == 0)
            if eliminado != 0:
                continue

            self.tabla.insertRow(row)
            # Columna ID
            self.tabla.setItem(row, 0, QTableWidgetItem(str(doc_id)))
            # Columna Cliente (solo nombre)
            item_cli = QTableWidgetItem(cliente_nombre)
            item_cli.setData(Qt.UserRole, cli_id)
            self.tabla.setItem(row, 1, item_cli)
            # Columna Nombre del documento
            self.tabla.setItem(row, 2, QTableWidgetItem(nombre))
            # Columna Fecha
            self.tabla.setItem(row, 3, QTableWidgetItem(fecha))
            # Columna Formato (extensión)
            ext = os.path.splitext(ruta_real)[1].lower() if ruta_real else "N/A"
            fmt_item = QTableWidgetItem(ext)
            fmt_item.setForeground(color_por_extension(ext))
            self.tabla.setItem(row, 4, fmt_item)

            # ————— Botón “Abrir” por fila —————
            btn_abrir = QPushButton("Abrir")
            btn_abrir.setStyleSheet(BOTON_ESTILOS["abrir"])
            if ruta_real:
                def manejar_apertura(boton, ruta):
                    boton.setStyleSheet(BOTON_ESTILOS["abrir_activo"])
                    abrir_archivo(ruta, self)
                    boton.setStyleSheet(BOTON_ESTILOS["abrir"])
                btn_abrir.clicked.connect(partial(manejar_apertura, btn_abrir, ruta_real))
            else:
                btn_abrir.setEnabled(False)
                btn_abrir.setToolTip("No hay archivo disponible")
            self.tabla.setCellWidget(row, 5, btn_abrir)

            row += 1

        # Aplicar filtros activos
        self.filtrar_documentos()

    def filtrar_documentos(self):
        texto_libre = self.filtro_cliente.text().strip().lower()
        texto_documento = self.filtro_documento.text().strip().lower()
        cliente_combo = self.cliente_combo.currentText().strip().lower()

        for fila in range(self.tabla.rowCount()):
            item_id = self.tabla.item(fila, 0)
            item_cli = self.tabla.item(fila, 1)
            item_doc = self.tabla.item(fila, 2)

            if not item_id or not item_cli or not item_doc:
                self.tabla.setRowHidden(fila, True)
                continue

            doc_id_str = item_id.text().strip().lower()
            nombre_cli = item_cli.text().strip().lower()
            id_cli = str(item_cli.data(Qt.UserRole) or "").strip().lower()
            nombre_doc = item_doc.text().strip().lower()

            mostrar = True

            # 1) Filtro libre (cliente nombre/ID o documento ID)
            if texto_libre:
                match_cli = (texto_libre in nombre_cli) or (texto_libre in id_cli)
                match_doc_id = (texto_libre == doc_id_str)
                mostrar &= (match_cli or match_doc_id)

            # 2) Filtro libre por nombre de documento
            if texto_documento:
                mostrar &= (texto_documento in nombre_doc)

            # 3) Filtro por combo de cliente
            if cliente_combo != "todos los clientes":
                mostrar &= (cliente_combo == nombre_cli)

            self.tabla.setRowHidden(fila, not mostrar)

    def _on_seleccion_cambiada(self):
        has = bool(self.tabla.selectedItems())
        self.btn_editar.setEnabled(has)
        self.btn_eliminar.setEnabled(has)

    def _editar_seleccionado(self):
        fila = self.tabla.currentRow()
        if fila == -1:
            return

        # Obtener ID y pedir datos completos al controlador
        doc_id = int(self.tabla.item(fila, 0).text())
        documento = obtener_documento_por_id(doc_id)
        if not documento:
            QMessageBox.warning(self, "Aviso", "No se pudo cargar el documento para edición.")
            return

        try:
            # La tupla de 6 ó 9 elementos NO incluye el nombre en el primer puesto,
            # el “nombre” está en posición 2 si vienen 9 elementos, o en posición 1 si vienen 6.
            if len(documento) == 6:
                # doc = (id, proceso_id, nombre, fecha, ruta_archivo, cliente_id)
                _, proc_id, nombre_ctrl, fecha, ruta_archivo, cliente_id = documento
            else:
                # doc = (id, proceso_id, nombre, archivo, fecha, ruta_archivo, eliminado, cliente_id, cliente_nombre)
                _, proc_id, nombre_ctrl, _, fecha, ruta_archivo, _, cliente_id, _ = documento
        except ValueError as e:
            QMessageBox.critical(self, "Error", f"Datos incompletos del documento:\n{e}")
            return

        # Guardar contexto para _procesar_edicion
        self.documento_en_edicion = doc_id
        self.cliente_en_edicion = cliente_id
        self.proceso_en_edicion = proc_id
        self.fecha_en_edicion = fecha
        self.ruta_en_edicion = ruta_archivo

        # Cargar en los campos (ahora nombre_ctrl es str)
        self.nombre_input.setText(nombre_ctrl)
        self.fecha_input.setDate(QDate.fromString(fecha, "yyyy-MM-dd"))
        self.btn_archivo.setText(
            os.path.basename(ruta_archivo) if ruta_archivo and os.path.exists(ruta_archivo) else "Ruta no disponible"
        )

        # Deshabilitar todo excepto el campo “Nombre”
        self.nombre_input.setEnabled(True)
        self.cliente_combo.setEnabled(False)
        self.fecha_input.setEnabled(False)
        self.btn_archivo.setEnabled(False)

        # Marcar botón “Guardar” en amarillo (modo edición)
        self.btn_guardar.setStyleSheet("background-color: yellow; color: black; font-weight: bold;")

    def _eliminar_seleccionado(self):
        fila = self.tabla.currentRow()
        if fila == -1:
            return

        doc_id = int(self.tabla.item(fila, 0).text())
        reply = QMessageBox.question(
            self, "Confirmar eliminación",
            "¿Seguro que quieres enviar este documento a la papelera?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            conn = sqlite3.connect(DATABASE_PATH)
            cur = conn.cursor()
            cur.execute("UPDATE documentos SET eliminado = 1 WHERE id = ?", (doc_id,))
            conn.commit()
            conn.close()
            self.cargar_documentos()

    def _toggle_papelera(self):
        # Alternar entre vista activa y papelera
        self.mostrando_papelera = not self.mostrando_papelera

        # Mostrar u ocultar formulario de carga
        for w in (
            self.cliente_combo,
            self.nombre_input,
            self.fecha_input,
            self.btn_archivo,
            self.btn_guardar
        ):
            w.setVisible(not self.mostrando_papelera)

        if self.mostrando_papelera:
            # Modo papelera
            self.btn_papelera.setText("Ver Activos")
            self.btn_eliminar_definitivo.show()
            self.btn_recuperar.show()
            self.btn_eliminar.hide()

            # Traer documentos eliminados (6 columnas)
            conn = sqlite3.connect(DATABASE_PATH)
            cur = conn.cursor()
            cur.execute("""
                SELECT id, nombre, cliente_id, proceso_id, fecha, ruta_archivo
                FROM documentos
                WHERE eliminado = 1
            """)
            self.documentos = cur.fetchall()
            conn.close()
        else:
            # Volver a modo activo
            self.btn_papelera.setText("Papelera")
            self.btn_eliminar_definitivo.hide()
            self.btn_recuperar.hide()
            self.btn_eliminar.show()
            self.cargar_documentos()
            return

        # Llenar la tabla con la papelera
        self.tabla.setRowCount(0)
        for row, doc in enumerate(self.documentos):
            # doc = (id, nombre, cliente_id, proceso_id, fecha, ruta_archivo)
            doc_id, nombre, cli_id, proc_id, fecha, ruta_real = doc
            self.tabla.insertRow(row)

            # 0: ID
            self.tabla.setItem(row, 0, QTableWidgetItem(str(doc_id)))
            # 1: Cliente (solo nombre)
            cliente_nombre = self.clientes_dict.get(cli_id, "N/A")
            item_cli = QTableWidgetItem(cliente_nombre)
            item_cli.setData(Qt.UserRole, cli_id)
            self.tabla.setItem(row, 1, item_cli)
            # 2: Nombre
            self.tabla.setItem(row, 2, QTableWidgetItem(nombre))
            # 3: Fecha
            self.tabla.setItem(row, 3, QTableWidgetItem(fecha))
            # 4: Formato (extensión)
            ext = os.path.splitext(ruta_real)[1].lower() if ruta_real else "N/A"
            fmt_item = QTableWidgetItem(ext)
            fmt_item.setForeground(color_por_extension(ext))
            self.tabla.setItem(row, 4, fmt_item)
            # 5: Botón Abrir
            if ruta_real:
                btn_abrir = QPushButton("Abrir")
                btn_abrir.setStyleSheet(BOTON_ESTILOS["abrir"])
                btn_abrir.clicked.connect(partial(self._abrir_archivo_por_ruta, ruta_real))
                self.tabla.setCellWidget(row, 5, btn_abrir)

            # Pintar fila entera de gris (papelera)
            for col in range(6):
                itm = self.tabla.item(row, col)
                if itm:
                    itm.setBackground(Qt.lightGray)
                    itm.setToolTip("Documento eliminado")

        self.filtrar_documentos()

    def eliminar_documento(self, doc_id):
        eliminar_documento_por_id(doc_id)
        self.cargar_documentos()

    def restaurar_documento(self, doc_id):
        restaurar_documento(doc_id)
        self.cargar_documentos()

    def limpiar_formulario(self):
        self.nombre_input.clear()
        self.fecha_input.setDate(QDate.currentDate())
        self.ruta_archivo = ""
        self.documento_en_edicion = None
        self.cliente_en_edicion = None
        self.proceso_en_edicion = None
        self.fecha_en_edicion = None
        self.ruta_en_edicion = None

        self.cliente_combo.setEnabled(True)
        self.fecha_input.setEnabled(True)
        self.btn_archivo.setEnabled(True)
        self.nombre_input.setEnabled(True)
        self.btn_guardar.setStyleSheet(BOTON_ESTILOS["guardar_default"])
        self.reset_btn_archivo()

    def eliminar_definitivamente(self):
        fila = self.tabla.currentRow()
        if fila == -1:
            return

        doc_id = int(self.tabla.item(fila, 0).text())
        reply = QMessageBox.question(
            self, "Confirmar eliminación",
            "¿Estás seguro de que quieres eliminar este documento *definitivamente*?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            conn = sqlite3.connect(DATABASE_PATH)
            cur = conn.cursor()
            cur.execute("DELETE FROM documentos WHERE id = ?", (doc_id,))
            conn.commit()
            conn.close()
            self.refrescar_papelera()

    def recuperar_documento(self):
        fila = self.tabla.currentRow()
        if fila == -1:
            return

        doc_id = int(self.tabla.item(fila, 0).text())
        conn = sqlite3.connect(DATABASE_PATH)
        cur = conn.cursor()
        cur.execute("UPDATE documentos SET eliminado = 0 WHERE id = ?", (doc_id,))
        conn.commit()
        conn.close()
        self.refrescar_papelera()

    def _actualizar_botones_papelera(self):
        fila = self.tabla.currentRow()
        if fila == -1 or not self.mostrando_papelera:
            self.btn_eliminar_definitivo.setEnabled(False)
            self.btn_recuperar.setEnabled(False)
        else:
            self.btn_eliminar_definitivo.setEnabled(True)
            self.btn_recuperar.setEnabled(True)

    def refrescar_papelera(self):
        conn = sqlite3.connect(DATABASE_PATH)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, nombre, cliente_id, proceso_id, fecha, ruta_archivo
            FROM documentos
            WHERE eliminado = 1
        """)
        self.documentos = cur.fetchall()
        conn.close()

        self.tabla.setRowCount(0)
        for row, doc in enumerate(self.documentos):
            # doc = (id, nombre, cliente_id, proceso_id, fecha, ruta_archivo)
            doc_id, nombre, cli_id, proc_id, fecha, ruta_real = doc
            self.tabla.insertRow(row)

            # 0: ID
            self.tabla.setItem(row, 0, QTableWidgetItem(str(doc_id)))
            # 1: Cliente
            cliente_nombre = self.clientes_dict.get(cli_id, "N/A")
            item_cli = QTableWidgetItem(cliente_nombre)
            item_cli.setData(Qt.UserRole, cli_id)
            self.tabla.setItem(row, 1, item_cli)
            # 2: Nombre
            self.tabla.setItem(row, 2, QTableWidgetItem(nombre))
            # 3: Fecha
            self.tabla.setItem(row, 3, QTableWidgetItem(fecha))
            # 4: Formato
            ext = os.path.splitext(ruta_real)[1].lower() if ruta_real else "N/A"
            fmt_item = QTableWidgetItem(ext)
            fmt_item.setForeground(color_por_extension(ext))
            self.tabla.setItem(row, 4, fmt_item)
            # 5: Botón Abrir
            if ruta_real:
                btn_abrir = QPushButton("Abrir")
                btn_abrir.setStyleSheet(BOTON_ESTILOS["abrir"])
                btn_abrir.clicked.connect(partial(self._abrir_archivo_por_ruta, ruta_real))
                self.tabla.setCellWidget(row, 5, btn_abrir)

            # Pintar fila entera de gris (papelera)
            for col in range(6):
                itm = self.tabla.item(row, col)
                if itm:
                    itm.setBackground(Qt.lightGray)
                    itm.setToolTip("Documento eliminado")

        self.filtrar_documentos()

    def editar_documento(self):
        # (Este método ya no se usa, pues la edición se maneja con
        #  _editar_seleccionado() + _procesar_edicion())
        pass

    def reset_btn_archivo(self):
        self.ruta_archivo = ""
        self.btn_archivo.setText("Seleccionar archivo")
        self.btn_archivo.setStyleSheet(BOTON_ESTILOS["oscuro"])
