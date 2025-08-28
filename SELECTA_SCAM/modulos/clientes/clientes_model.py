# SELECTA_SCAM/modulos/clientes/clientes_model.py
import logging
from PyQt5.QtCore import QAbstractTableModel, QVariant, Qt, pyqtSignal
from PyQt5.QtGui import QColor
from datetime import datetime

logger = logging.getLogger(__name__)

class ClientesModel(QAbstractTableModel):
    HEADERS = ['ID', 'Nombre', 'Tipo ID', 'Identificación', 'Correo', 'Teléfono', 'Dirección', 'Tipo Cliente', 'Fecha Creación', 'Eliminado']
    error_occurred = pyqtSignal(str)
    return_to_active_view = pyqtSignal()

    def __init__(self, clientes_logic_instance, parent=None):
        super().__init__(parent)
        self.clientes_logic = clientes_logic_instance
        self._data = []
        #self.load_data()

    def rowCount(self, parent=None): return len(self._data)
    def columnCount(self, parent=None): return len(self.HEADERS)

    # En: clientes_model.py

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._data)):
            return QVariant()

        # Obtenemos la tupla de datos para la fila actual
        cliente_tuple = self._data[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            try:
                # Accedemos a los datos por el índice de la tupla
                value = cliente_tuple[col]
                if isinstance(value, datetime):
                    return value.strftime("%Y-%m-%d")
                if isinstance(value, bool):
                    return "Sí" if value else "No"
                return str(value if value is not None else "")
            except IndexError:
                return ""

        elif role == Qt.BackgroundRole:
            # Leemos el estado 'eliminado' desde la tupla (índice 9)
            if cliente_tuple[9]:
                return QColor("#ffe6e6")
        
        return QVariant()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.HEADERS[section]
        return QVariant()

    def flags(self, index): return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    # En: SELECTA_SCAM/modulos/clientes/clientes_model.py

    def load_data(self, incluir_eliminados: bool = False, solo_eliminados: bool = False, query: str = None):
        """Refresca la tabla y emite una señal si la papelera queda vacía."""
        self.beginResetModel()
        self._data = self.clientes_logic.get_clientes_data(
            incluir_eliminados=incluir_eliminados,
            solo_eliminados=solo_eliminados,
            query=query
        )
        self.endResetModel()

        # --- LÓGICA DE RETORNO AUTOMÁTICO ---
        # Si estábamos en la papelera y ahora no hay datos, emite la señal.
        if solo_eliminados and not self._data:
            self.return_to_active_view.emit()

    def agregar_cliente(self, **data):
        if self.clientes_logic.add_new_cliente(**data):
            self.load_data()

    # Pega estos dos métodos dentro de la clase ClientesModel

    def get_cliente_para_editar(self, row: int):
        """
        Obtiene un diccionario con los datos de un cliente para el diálogo de edición.
        """
        if 0 <= row < len(self._data):
            # Obtenemos el ID de la tupla (siempre en la primera posición)
            cliente_id = self._data[row][0]
            return self.clientes_logic.get_cliente_details_for_edit(cliente_id)
        return None

    # En: SELECTA_SCAM/modulos/clientes/clientes_model.py

    def actualizar_cliente(self, cliente_id, **data):
        if self.clientes_logic.update_cliente_details(cliente_id, **data):
            self.load_data()

    def get_cliente_para_editar(self, row: int):
        if 0 <= row < len(self._data):
            # Obtenemos el ID de la tupla (siempre en la primera posición)
            cliente_id = self._data[row][0]
            return self.clientes_logic.get_cliente_details_for_edit(cliente_id)
        return None

    # En: SELECTA_SCAM/modulos/clientes/clientes_model.py
# Añade estos métodos a la clase ClientesModel

    def marcar_como_eliminado(self, cliente_ids: list):
        """Marca uno o varios clientes como eliminados y refresca la vista."""
        if self.clientes_logic.marcar_multiples_como_eliminados(cliente_ids):
            self.load_data() # Recarga la lista de clientes activos

    def restaurar_clientes(self, cliente_ids: list):
        """Restaura uno o varios clientes y refresca la vista de la papelera."""
        if self.clientes_logic.restaurar_clientes(cliente_ids):
            self.load_data(solo_eliminados=True)

    def eliminar_definitivo(self, cliente_ids: list):
        """Elimina clientes permanentemente y refresca la vista de la papelera."""
        if self.clientes_logic.eliminar_clientes_definitivo(cliente_ids):
            # Recarga la lista de la papelera para mostrar que se han ido.
            # La lógica de retorno automático se activará aquí si la papelera queda vacía.
            self.load_data(solo_eliminados=True)