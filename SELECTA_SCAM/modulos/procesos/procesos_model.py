# SELECTA_SCAM/modulos/procesos/procesos_model.py
from PyQt5.QtCore import QAbstractTableModel, QVariant, Qt, pyqtSignal
from PyQt5.QtGui import QFont
from SELECTA_SCAM.modulos.procesos.procesos_db import ProcesosDB
from SELECTA_SCAM.modulos.clientes.clientes_db import ClientesDB
# Importar las clases DB necesarias (asumo que se crearán o modificarán)
from SELECTA_SCAM.modulos.documentos.documentos_db import DocumentosDB
from SELECTA_SCAM.modulos.contabilidad.contabilidad_db import ContabilidadDB
from SELECTA_SCAM.db.models import Proceso, Cliente # Importar los modelos ORM directamente para tipado y acceso a atributos
from datetime import datetime, date # Para manejar fechas

# SELECTA_SCAM/modulos/procesos/procesos_model.py
# ... (tus importaciones existentes)

class ProcesosModel(QAbstractTableModel):
    # Define tus encabezados aquí
    HEADERS = [
        'ID', 'Radicado', 'Tipo', 'Cliente', 'Fecha Inicio', 'Fecha Fin',
        'Estado', 'Juzgado', 'Observaciones', 'Fecha Creación', 'Eliminado'
    ]
    error_occurred = pyqtSignal(str) # <--- ¡Asegúrate de que esta línea esté aquí!

    def __init__(self, procesos_db: ProcesosDB,
                 documentos_db=None,
                 contabilidad_db=None,
                 clientes_db=None,
                 parent=None):
        """
        Inicializa el modelo de Procesos con instancias de las clases DB necesarias.
        """
        super().__init__(parent)
        self.procesos_db = procesos_db
        self.documentos_db = documentos_db # Asegúrate de que coincida con el nombre del parámetro
        self.contabilidad_db = contabilidad_db # Asegúrate de que coincida con el nombre del parámetro
        self.clientes_db = clientes_db # Asegúrate de que coincida con el nombre del parámetro
        self._data = []
        self.load_data()


    def load_data(self, incluir_eliminados: bool = False, query: str = None):
        self.beginResetModel()

        if query:
            # Si hay una consulta, usar buscar_procesos.
            # Pasar 'incluir_eliminados' a buscar_procesos para que la DB se encargue del filtro inicial.
            raw_data = self.procesos_db.buscar_procesos(query, include_deleted=incluir_eliminados)
        elif incluir_eliminados:
            # Si se quiere incluir eliminados y no hay query, obtener TODOS los procesos.
            raw_data = self.procesos_db.get_all_procesos_including_deleted()
        else:
            # Por defecto, obtener solo los procesos no eliminados.
            raw_data = self.procesos_db.get_all_procesos() # <<-- CORREGIDO, USAMOS self.procesos_db directamente

        self._data = raw_data # Asignamos los datos ya filtrados desde la DB
        self.endResetModel() # Notifica a la vista que los datos han cambiado # Notifica a la vista que los datos han cambiado

    def rowCount(self, parent=None):
        """Retorna el número de filas (procesos)."""
        return len(self._data)

    def columnCount(self, parent=None):
        """Retorna el número de columnas."""
        return len(self.HEADERS)

    def data(self, index, role=Qt.DisplayRole):
        """Proporciona los datos para cada celda de la tabla."""
        if not index.isValid():
            return QVariant()

        proceso = self._data[index.row()]
        col = index.column()

        if role == Qt.DisplayRole or role == Qt.EditRole:
            # Mapeo de columnas a atributos del objeto Proceso
            if col == 0: return proceso.id
            elif col == 1: return proceso.radicado
            elif col == 2: return proceso.tipo
            elif col == 3: # Columna 'Cliente'
                # Accede al nombre del cliente a través de la relación ORM
                return proceso.cliente.nombre if proceso.cliente else "N/A"
            elif col == 4: return proceso.fecha_inicio.strftime('%Y-%m-%d') if proceso.fecha_inicio else ''
            elif col == 5: return proceso.fecha_fin.strftime('%Y-%m-%d') if proceso.fecha_fin else ''
            elif col == 6: return proceso.estado
            elif col == 7: return proceso.juzgado
            elif col == 8: return proceso.observaciones
            elif col == 9: return proceso.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S') if proceso.fecha_creacion else ''
            elif col == 10: return "Sí" if proceso.eliminado else "No"

        if role == Qt.FontRole:
            font = QFont()
            font.setPointSize(14)
            return font

        if role == Qt.ForegroundRole:
            if proceso.eliminado:
                return QVariant(Qt.gray) # Procesos eliminados en gris
            else:
                return QVariant(Qt.black) # Procesos activos en negro

        return QVariant()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Proporciona los nombres de las cabeceras de las columnas."""
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.HEADERS[section]
        return QVariant()

    def flags(self, index):
        """Define si una celda es seleccionable o editable."""
        if not index.isValid():
            return Qt.NoItemFlags
        # Hacemos editable solo las columnas específicas: Radicado, Tipo, Fechas, Estado, Juzgado, Observaciones
        if index.column() in [1, 2, 4, 5, 6, 7, 8]:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def setData(self, index, value, role=Qt.EditRole):
        """
        Establece los datos de una celda y actualiza el proceso en la base de datos.
        """
        if role == Qt.EditRole:
            if index.isValid():
                proceso = self._data[index.row()]
                col = index.column()

                # Diccionario para mapear columna a nombre de atributo del modelo Proceso
                col_to_attr = {
                    1: 'radicado',
                    2: 'tipo',
                    4: 'fecha_inicio',
                    5: 'fecha_fin',
                    6: 'estado',
                    7: 'juzgado',
                    8: 'observaciones'
                }

                attr_name = col_to_attr.get(col)
                if attr_name:
                    original_value = getattr(proceso, attr_name) # Guardar valor original para revertir

                    # Convertir fechas si la columna es de fecha (espera AAAA-MM-DD o objeto date)
                    if attr_name in ['fecha_inicio', 'fecha_fin']:
                        try:
                            if isinstance(value, str):
                                value = datetime.strptime(value, '%Y-%m-%d').date() # Convertir a objeto date
                            elif not isinstance(value, date): # Si no es str ni date, es un formato inválido
                                raise ValueError("Formato de fecha inválido.")
                        except ValueError:
                            self.error_occurred.emit(f"Formato de fecha inválido para '{self.HEADERS[col]}'. Use AAAA-MM-DD.")
                            return False # No actualizar si la fecha es inválida

                    # Actualiza el atributo en el objeto proceso localmente
                    setattr(proceso, attr_name, value)

                    # Preparar los datos a enviar para la actualización en la DB
                    # Se envían todos los campos necesarios para update_proceso
                    updated_data = {
                        'cliente_id': proceso.cliente_id,
                        'radicado': proceso.radicado,
                        'tipo': proceso.tipo,
                        'fecha_inicio': proceso.fecha_inicio,
                        'fecha_fin': proceso.fecha_fin,
                        'estado': proceso.estado,
                        'juzgado': proceso.juzgado,
                        'observaciones': proceso.observaciones
                    }

                    try:
                        success = self.procesos_db.update_proceso(proceso.id, **updated_data)
                        if success:
                            self.dataChanged.emit(index, index, [role]) # Notifica que la celda ha cambiado
                            return True
                        else:
                            # Revertir el cambio local si la actualización en DB falla
                            setattr(proceso, attr_name, original_value)
                            self.error_occurred.emit(f"Error al actualizar proceso ID {proceso.id} en la base de datos.")
                            self.dataChanged.emit(index, index, [role]) # Notificar para refrescar la celda
                            return False
                    except Exception as e:
                        setattr(proceso, attr_name, original_value) # Revertir cambio local
                        self.error_occurred.emit(f"Error desconocido al actualizar proceso: {e}")
                        self.dataChanged.emit(index, index, [role]) # Notificar para refrescar la celda
                        return False
        return False

    # --- Métodos para la gestión de procesos (CRUD) ---
    # Los parámetros de estos métodos están alineados con los métodos en `procesos_db.py`

    def agregar_proceso(self, cliente_id: int, radicado: str, tipo: str, fecha_inicio: datetime,
                        fecha_fin: datetime, estado: str, juzgado: str, observaciones: str) -> bool:
        """Agrega un nuevo proceso a través de ProcesosDB y recarga los datos."""
        try:
            success = self.procesos_db.insertar_proceso(
                cliente_id=cliente_id,
                radicado=radicado,
                tipo=tipo,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                estado=estado,
                juzgado=juzgado,
                observaciones=observaciones
            )
            if success:
                # Recarga los datos para actualizar la tabla. Asume que parent tiene search_input y check_eliminados.
                # Estas llamadas a parent() deben manejarse en la vista, o pasar estos valores como argumentos.
                current_query = self.parent().search_input.text().strip() if self.parent() and hasattr(self.parent(), 'search_input') else None
                current_include_deleted = self.parent().check_eliminados.isChecked() if self.parent() and hasattr(self.parent(), 'check_eliminados') else False
                self.load_data(incluir_eliminados=current_include_deleted, query=current_query)
            return success
        except Exception as e:
            self.error_occurred.emit(f"Error al agregar proceso: {e}")
            return False

    def actualizar_proceso_por_id(self, proceso_id: int, cliente_id: int = None, radicado: str = None, tipo: str = None,
                                 fecha_inicio: datetime = None, fecha_fin: datetime = None, estado: str = None,
                                 juzgado: str = None, observaciones: str = None) -> bool:
        """Actualiza los datos de un proceso existente a través de ProcesosDB y recarga los datos."""
        try:
            success = self.procesos_db.update_proceso(
                proceso_id=proceso_id,
                cliente_id=cliente_id,
                radicado=radicado,
                tipo=tipo,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                estado=estado,
                juzgado=juzgado,
                observaciones=observaciones
            )
            if success:
                current_query = self.parent().search_input.text().strip() if self.parent() and hasattr(self.parent(), 'search_input') else None
                current_include_deleted = self.parent().check_eliminados.isChecked() if self.parent() and hasattr(self.parent(), 'check_eliminados') else False
                self.load_data(incluir_eliminados=current_include_deleted, query=current_query)
            return success
        except Exception as e:
            self.error_occurred.emit(f"Error al actualizar proceso: {e}")
            return False

    def marcar_como_eliminado(self, proceso_id: int) -> bool:
        """Marca un proceso como eliminado (lógicamente) y recarga los datos."""
        success = self.db_operations.eliminar_proceso(proceso_id) # Usar db_operations
        if success:
            current_query = self.parent().search_input.text().strip() if self.parent() and hasattr(self.parent(), 'search_input') else None
            current_include_deleted = self.parent().check_eliminados.isChecked() if self.parent() and hasattr(self.parent(), 'check_eliminados') else False
            self.load_data(incluir_eliminados=current_include_deleted, query=current_query)
        return success

    def restaurar_procesos(self, proceso_ids: list) -> bool:
        """Restaura una lista de procesos marcados como eliminados y recarga los datos."""
        success_count = 0
        for proceso_id in proceso_ids:
            if self.db_operations.restaurar_proceso(proceso_id): # Usar db_operations
                success_count += 1

        if success_count > 0:
            current_query = self.parent().search_input.text().strip() if self.parent() and hasattr(self.parent(), 'search_input') else None
            current_include_deleted = self.parent().check_eliminados.isChecked() if self.parent() and hasattr(self.parent(), 'check_eliminados') else False
            self.load_data(incluir_eliminados=current_include_deleted, query=current_query)
            return True if success_count == len(proceso_ids) else False
        return False

    def eliminar_proceso_definitivo(self, proceso_id: int) -> bool:
        """Elimina un proceso de forma permanente y recarga los datos."""
        success = self.db_operations.eliminar_proceso_definitivo(proceso_id) # Usar db_operations
        if success:
            current_query = self.parent().search_input.text().strip() if self.parent() and hasattr(self.parent(), 'search_input') else None
            current_include_deleted = self.parent().check_eliminados.isChecked() if self.parent() and hasattr(self.parent(), 'check_eliminados') else False
            self.load_data(incluir_eliminados=current_include_deleted, query=current_query)
        return success

    def get_proceso_by_id(self, proceso_id: int):
        """Obtiene un proceso por su ID a través de ProcesosDB."""
        return self.procesos_db.get_proceso_by_id(proceso_id)

    # --- Métodos de apoyo para acceder a datos relacionados (Documentos, Contabilidad, etc.) ---

    # Diccionario de tipos de actuación (como atributo de clase)
    _TIPOS_ACTUACION = {
        "Notificaciones y Comunicaciones": [
            "Notificación Personal", "Notificación por Estado", "Notificación por Aviso",
            "Notificación por Edicto", "Notificación por Estrados", "Notificación por Correo Certificado",
            "Certificado de Entrega / Acuse de Recibo"
        ],
        "Providencias Judiciales": [
            "Auto de Admisión de Demanda", "Auto de Mandamiento de Pago", "Auto de Emplazamiento",
            "Auto Interlocutorio", "Sentencia de Primera Instancia", "Sentencia de Segunda Instancia",
            "Resoluciones de Pruebas", "Resoluciones de Medidas Cautelares", "Oficios Judiciales",
            "Exhortos / Cartas Rogatorias / Comisiones"
        ],
        "Medidas Cautelares y Precautelativas": [
            "Auto de Embargo", "Acta de Secuestro", "Acta de Inscripción de Medida Cautelar",
            "Acta de Levantamiento de Medida", "Constancia de Entrega de Bienes",
            "Informe del Secuestre o Depositario", "Inventario de Bienes Embargados o Secuestrados"
        ],
        "Actuaciones Probatorias": [
            "Acta de Testimonios", "Dictamen Pericial", "Auto que Decreta Prueba",
            "Acta de Inspección Judicial", "Acta de Interrogatorio de Parte",
            "Solicitud de Documentos", "Oficio para Práctica de Pruebas", "Respuesta a Oficio / Informe Pericial"
        ],
        "Ejecución y Cumplimiento de Sentencias": [
            "Auto de Ejecución", "Auto de Liquidación de Costas", "Acta de Remate / Subasta",
            "Acta de Entrega de Bienes", "Oficio de Desembolso (dinero embargado)",
            "Informe de Cumplimiento de Medidas"
        ],
        "Recursos e Impugnaciones": [
            "Recurso de Reposición", "Recurso de Apelación", "Recurso de Queja",
            "Recurso de Revisión", "Providencia que Resuelve el Recurso", "Notificación del Recurso"
        ],
        "Terminación y Archivo del Proceso": [
            "Auto de Terminación del Proceso", "Auto de Archivo del Expediente",
            "Liquidación de Costas", "Auto de Desistimiento / Transacción",
            "Oficio de Cancelación de Medidas Cautelares", "Constancia de Entrega de Copias",
            "Informe de Archivo"
        ],
        "Conciliación y Mediación": [
            "Solicitud de Conciliación", "Acta de Conciliación", "Constancia de No Acuerdo",
            "Informe del Centro de Conciliación", "Auto que Homologa el Acuerdo"
        ],
        "Documentos Personales y Administrativos": [
            "Documento de Identidad", "Certificado de Existencia y Representación Legal",
            "Poderes y Mandatos", "Contratos y Acuerdos", "Certificados Bancarios",
            "Certificados de Tradición y Libertad", "Cartas de Instrucción",
            "Recibos de Pago", "Autorizaciones"
        ],
        "Otros Documentos": [
            "Comunicaciones Privadas", "Correspondencia (Correos, Cartas)",
            "Documentos Informativos (Circular, Boletín)",
            "Documentos Externos (No relacionados con el proceso)",
            "Fotografías y Evidencias", "Audios y Videos"
        ]
    }

    def get_tipos_actuacion(self) -> dict:
        """
        Devuelve el diccionario de tipos de actuación definido en la clase.
        """
        return self._TIPOS_ACTUACION

    def obtener_radicado_por_id(self, proceso_id: int) -> str | None:
        """
        Obtiene el número de radicado de un proceso por su ID.
        """
        proceso_orm = self.procesos_db.get_proceso_by_id(proceso_id)
        return proceso_orm.radicado if proceso_orm else None

    def obtener_documentos_por_proceso(self, proceso_id: int) -> list[dict]:
        """
        Retorna lista de diccionarios con los documentos asociados al proceso.
        Delegado a DocumentosDB (asumiendo método get_documentos_by_proceso_id existe).
        """
        # Asumiendo que DocumentosDB tendrá un método get_documentos_by_proceso_id
        documentos_orm = self.documentos_db.get_documentos_by_proceso_id(proceso_id) 
        documentos_formateados = []
        for doc in documentos_orm:
            documentos_formateados.append({
                'id': doc.id,
                'proceso_id': doc.proceso_id,
                'cliente_id': doc.cliente_id,
                'nombre': doc.nombre,
                'archivo': doc.archivo,
                'ruta': doc.ruta,
                'fecha_subida': doc.fecha_subida.isoformat() if doc.fecha_subida else None,
                'tipo_documento': doc.tipo_documento,
                'eliminado': doc.eliminado
            })
        return documentos_formateados

    def insertar_documento(self, proceso_id: int, cliente_id: int, nombre: str, archivo: str, ruta: str, tipo_documento: str = None) -> int | None:
        """
        Inserta un nuevo documento asociado a un proceso.
        Delegado a DocumentosDB.
        Retorna el ID del documento insertado.
        """
        # Asumiendo que DocumentosDB tendrá un método insertar_documento
        documento_creado = self.documentos_db.insertar_documento(
            proceso_id=proceso_id,
            cliente_id=cliente_id,
            nombre=nombre,
            archivo=archivo,
            ruta=ruta,
            tipo_documento=tipo_documento
        )
        return documento_creado.id if documento_creado else None

    def eliminar_documento(self, documento_id: int) -> bool:
        """
        Elimina un documento por su ID.
        Delegado a DocumentosDB.
        """
        return self.documentos_db.eliminar_documento(documento_id)

    def obtener_movimientos_contables_por_proceso(self, proceso_id: int) -> list[dict]:
        """
        Retorna lista de diccionarios con los movimientos contables asociados al proceso.
        Delegado a ContabilidadDB (asumiendo método get_movimientos_by_proceso_id existe).
        """
        # Asumiendo que ContabilidadDB tendrá un método get_movimientos_by_proceso_id
        movimientos_orm = self.contabilidad_db.get_movimientos_by_proceso_id(proceso_id)
        movimientos_formateados = []
        for mov in movimientos_orm:
            movimientos_formateados.append({
                'id': mov.id,
                'cliente_id': mov.cliente_id,
                'proceso_id': mov.proceso_id,
                'tipo': mov.tipo,
                'descripcion': mov.descripcion,
                'valor': mov.valor,
                'fecha': mov.fecha.isoformat() if mov.fecha else None,
            })
        return movimientos_formateados

    def insertar_movimiento_contable(self, cliente_id: int, proceso_id: int = None, tipo: str = None, descripcion: str = None, valor: float = None, fecha: str = None) -> int | None:
        """
        Inserta un nuevo movimiento contable asociado a un proceso.
        Delegado a ContabilidadDB.
        Retorna el ID del movimiento insertado.
        """
        # Convertir fecha si es string
        if isinstance(fecha, str):
            try:
                fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
            except ValueError:
                self.error_occurred.emit("Formato de fecha inválido para movimiento contable. Use AAAA-MM-DD.")
                return None

        # Asumiendo que ContabilidadDB tendrá un método insertar_movimiento
        movimiento_creado = self.contabilidad_db.insertar_movimiento(
            cliente_id=cliente_id,
            proceso_id=proceso_id,
            tipo=tipo,
            descripcion=descripcion,
            valor=valor,
            fecha=fecha
        )
        return movimiento_creado.id if movimiento_creado else None

    def actualizar_movimiento_contable(self, movimiento_id: int, cliente_id: int = None, proceso_id: int = None, tipo: str = None, descripcion: str = None, valor: float = None, fecha: str = None) -> bool:
        """
        Actualiza un movimiento contable existente.
        Delegado a ContabilidadDB.
        """
        # Convertir fecha si es string
        if isinstance(fecha, str):
            try:
                fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
            except ValueError:
                self.error_occurred.emit("Formato de fecha inválido para movimiento contable. Use AAAA-MM-DD.")
                return False

        # Asumiendo que ContabilidadDB tendrá un método actualizar_movimiento
        return self.contabilidad_db.actualizar_movimiento(
            movimiento_id=movimiento_id,
            cliente_id=cliente_id,
            proceso_id=proceso_id,
            tipo=tipo,
            descripcion=descripcion,
            valor=valor,
            fecha=fecha
        )
# --- Método adicional para obtener categorías de actuación ---
    def obtener_actuaciones_por_categoria(self) -> dict:
        """
        Devuelve el diccionario de tipos de actuación.
        Este método es usado por ProcesosWidget para poblar los comboboxes de actuación.
        """
        return self._TIPOS_ACTUACION
        
    def eliminar_movimiento_contable(self, movimiento_id: int) -> bool:
        """
        Elimina un movimiento contable por su ID.
        Delegado a ContabilidadDB.
        """
        return self.contabilidad_db.eliminar_movimiento(movimiento_id)