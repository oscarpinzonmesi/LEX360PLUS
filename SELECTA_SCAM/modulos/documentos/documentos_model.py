# SELECTA_SCAM/modulos/documentos/documentos_model.py

import logging
from PyQt5.QtCore import QAbstractTableModel, QVariant, Qt, pyqtSignal
from PyQt5.QtGui import QColor
from datetime import datetime

logger = logging.getLogger(__name__)

class DocumentosModel(QAbstractTableModel):
    HEADERS = ['ID', 'Nombre', 'Cliente', 'Tipo de Documento', 'Fecha de Subida', 'Eliminado']
    error_occurred = pyqtSignal(str)

    def __init__(self, documentos_logic_instance, parent=None):
        super().__init__(parent)
        self.documentos_logic = documentos_logic_instance
        self._data = [] # _data ahora será una lista de tuplas (datos simples)
        self.load_data()

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self.HEADERS)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._data)):
            return QVariant()

        # Obtenemos la tupla de datos para la fila actual
        documento_tuple = self._data[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            try:
                # Accedemos a los datos por el índice de la tupla
                value = documento_tuple[col]
                if isinstance(value, datetime):
                    return value.strftime("%Y-%m-%d")
                if isinstance(value, bool):
                    return "Sí" if value else "No"
                return str(value if value is not None else "")
            except IndexError:
                return ""

        elif role == Qt.BackgroundRole:
            # Leemos el estado 'eliminado' desde la tupla (índice 5)
            if documento_tuple[5]:
                return QColor("#ffe6e6") # Rojo pálido para filas eliminadas
        
        return QVariant()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.HEADERS[section]
        return QVariant()

    def flags(self, index):
        # La tabla es de solo lectura; la edición se maneja con un diálogo
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    # --- MÉTODOS DE MANEJO DE DATOS ---

    def load_data(self, **kwargs):
        """Refresca la tabla pidiendo a la lógica los datos más recientes."""
        self.beginResetModel()
        self._data = self.documentos_logic.get_documentos_para_tabla(**kwargs)
        self.endResetModel()

    def agregar_documento(self, **data):
        """Pide a la lógica que agregue un documento y luego refresca la tabla."""
        if self.documentos_logic.agregar_documento(**data):
            self.load_data()

    def editar_documento(self, doc_id, **data):
        """Pide a la lógica que actualice un documento y luego refresca la tabla."""
        if self.documentos_logic.editar_documento(doc_id, **data):
            self.load_data()

    def get_documento_para_editar(self, row: int):
        """Obtiene un diccionario con los datos de un documento para el diálogo de edición."""
        if 0 <= row < len(self._data):
            # Obtenemos el ID de la tupla (siempre en la primera posición)
            doc_id = self._data[row][0]
            return self.documentos_logic.get_documento_para_editar(doc_id)
        return None
    
    def mover_a_papelera(self, doc_ids: list):
        """Mueve uno o varios documentos a la papelera y refresca la vista."""
        if self.documentos_logic.mover_a_papelera(doc_ids):
            self.load_data()

    def recuperar_de_papelera(self, doc_ids: list):
        """Restaura documentos y refresca la vista de la papelera."""
        if self.documentos_logic.recuperar_de_papelera(doc_ids):
            self.load_data(eliminado=True)

    def eliminar_definitivo(self, doc_ids: list):
        """Elimina documentos permanentemente y refresca la papelera."""
        if self.documentos_logic.eliminar_documento_definitivamente(doc_ids):
            self.load_data(eliminado=True)