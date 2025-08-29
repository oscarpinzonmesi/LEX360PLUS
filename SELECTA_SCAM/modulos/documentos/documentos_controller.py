# SELECTA_SCAM/modulos/documentos/documentos_controller.py

import os
import shutil
from datetime import datetime
import logging
from PyQt5.QtCore import QObject, pyqtSignal

from .documentos_db import DocumentosDB
from ..clientes.clientes_logic import ClientesLogic
from .documentos_logic import DocumentosLogic
from ...db.models import Documento   # ✅ necesario para mover/eliminar documentos en la papelera


DOCUMENTOS_FOLDER = 'Documentos_Guardados'


class DocumentosController(QObject):
    operation_successful = pyqtSignal(str, str)
    documentos_cargados = pyqtSignal(list)
    clientes_cargados = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, documentos_db_instance: DocumentosDB, clientes_logic_instance: ClientesLogic, user_data=None):
        super().__init__()
        self.logger = logging.getLogger(__name__)  # ✅ Logger propio
        self.documentos_db = documentos_db_instance
        self.clientes_logic = clientes_logic_instance
        self.documentos_logic = DocumentosLogic(documentos_db_instance)
        self.user_data = user_data

        try:
            project_root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        except Exception:
            project_root_path = os.getcwd()

        self.documentos_base_path = os.path.join(project_root_path, DOCUMENTOS_FOLDER)
        self.logger.info(f"Ruta base para documentos: {self.documentos_base_path}")
        self._verificar_y_crear_carpeta_base()

    # ============================================================
    # --- Utilidades internas
    # ============================================================

    def _verificar_y_crear_carpeta_base(self):
        """Asegura que la carpeta principal de documentos exista."""
        if not os.path.exists(self.documentos_base_path):
            os.makedirs(self.documentos_base_path)

    def get_full_document_path(self, doc_id: int) -> str | None:
        """Obtiene la ruta absoluta de un documento a partir de su ID."""
        try:
            documento = self.documentos_logic.get_documento_por_id(doc_id)
            if documento and documento.get('ubicacion_archivo'):
                ruta_relativa = documento['ubicacion_archivo']
                cliente_id = documento.get('cliente_id')
                ruta_correcta = os.path.join(self.documentos_base_path, str(cliente_id), os.path.basename(ruta_relativa))

                if os.path.exists(ruta_correcta):
                    return os.path.normpath(ruta_correcta)
                else:
                    self.logger.warning(f"No se encontró el archivo físico en la ruta esperada: {ruta_correcta}")
                    return None
            return None
        except Exception as e:
            self.logger.error(f"Error al obtener la ruta del documento ID {doc_id}: {e}")
            return None

    # ============================================================
    # --- Carga inicial y búsqueda
    # ============================================================

    def cargar_datos_iniciales(self):
        """Carga los clientes y los documentos activos al iniciar el módulo."""
        try:
            clientes = self.clientes_logic.get_all_clientes_for_combobox()
            self.clientes_cargados.emit(clientes)
            documentos = self.documentos_logic.get_documentos_para_tabla(eliminado=False)
            self.documentos_cargados.emit(documentos)
        except Exception as e:
            self.error_occurred.emit("Error al cargar datos iniciales.")
            self.logger.exception("Error en cargar_datos_iniciales: %s", e)

    def buscar_documentos(self, **filters):
        """Filtra documentos según cliente, ID o nombre."""
        try:
            cliente_id_exacto = filters.pop('cliente_id_exacto', None)
            cliente_nombre = filters.pop('cliente_nombre_filtro_texto', None)
            documento_id_filtro = filters.pop('documento_id_filtro', None)
            documento_nombre_filtro = filters.pop('documento_nombre_filtro', None)

            if cliente_id_exacto:
                filters['cliente_ids'] = [cliente_id_exacto]
            elif cliente_nombre:
                clientes_encontrados = self.clientes_logic.get_clientes_data(query=cliente_nombre)
                ids_de_clientes = [c[0] for c in clientes_encontrados]
                if not ids_de_clientes:
                    self.documentos_cargados.emit([])
                    return []
                filters['cliente_ids'] = ids_de_clientes

            if documento_id_filtro:
                filters['documento_id'] = documento_id_filtro
            elif documento_nombre_filtro:
                filters['documento_nombre'] = documento_nombre_filtro

            documentos = self.documentos_logic.get_documentos_para_tabla(**filters) or []
            self.documentos_cargados.emit(documentos)

            self.logger.info(f"Buscar documentos devolvió {len(documentos)} resultados con filtros: {filters}")
            return documentos
        except Exception as e:
            self.error_occurred.emit("Error de Búsqueda")
            self.logger.exception("Error en buscar_documentos: %s", e)
            return []

    # ============================================================
    # --- Agregar / Editar
    # ============================================================

    def agregar_documento(self, **data) -> bool:
        """Gestiona la lógica de agregar un nuevo documento."""
        try:
            ruta_origen = data.pop('ruta_archivo_origen')
            cliente_id = data.get('cliente_id')
            nombre_archivo = os.path.basename(ruta_origen)

            directorio_cliente = os.path.join(self.documentos_base_path, str(cliente_id))
            os.makedirs(directorio_cliente, exist_ok=True)
            ruta_destino = os.path.join(directorio_cliente, nombre_archivo)

            shutil.copy2(ruta_origen, ruta_destino)

            data['archivo'] = nombre_archivo
            data['ubicacion_archivo'] = os.path.join(DOCUMENTOS_FOLDER, str(cliente_id), nombre_archivo)

            self.documentos_logic.agregar_documento(**data)
            return True
        except Exception as e:
            self.logger.error(f"Error al agregar nuevo documento: {e}", exc_info=True)
            return False

    def editar_documento(self, doc_id, **data) -> bool:
        """Orquesta la edición de un documento."""
        try:
            success = self.documentos_logic.editar_documento(doc_id, **data)
            if success:
                self.cargar_datos_iniciales()
                return True
            else:
                return False
        except Exception as e:
            self.error_occurred.emit("Error al editar el documento.")
            self.logger.exception("Error en editar_documento: %s", e)
            return False

    # ============================================================
    # --- Papelera
    # ============================================================

    def mover_a_papelera(self, doc_ids: list[int]) -> bool:
        """Marca documentos como eliminados (mueve a la papelera)."""
        try:
            with self.documentos_db.get_session() as session:
                for doc_id in doc_ids:
                    documento = session.query(Documento).get(doc_id)
                    if documento:
                        documento.eliminado = True
            self.logger.info(f"Documentos enviados a la papelera: {doc_ids}")
            return True
        except Exception as e:
            self.logger.error(f"Error moviendo documentos a papelera: {e}", exc_info=True)
            return False

    def recuperar_de_papelera(self, doc_ids: list[int]) -> bool:
        """Restaura documentos desde la papelera."""
        try:
            with self.documentos_db.get_session() as session:
                for doc_id in doc_ids:
                    documento = session.query(Documento).get(doc_id)
                    if documento:
                        documento.eliminado = False
            self.logger.info(f"Documentos restaurados desde papelera: {doc_ids}")
            return True
        except Exception as e:
            self.logger.error(f"Error al recuperar documentos de la papelera: {e}", exc_info=True)
            return False

    def eliminar_documentos_definitivamente(self, doc_ids: list[int]) -> bool:
        """Elimina documentos de forma permanente."""
        try:
            with self.documentos_db.get_session() as session:
                for doc_id in doc_ids:
                    documento = session.query(Documento).get(doc_id)
                    if documento:
                        session.delete(documento)
            self.logger.info(f"Documentos eliminados definitivamente: {doc_ids}")
            return True
        except Exception as e:
            self.logger.error(f"Error eliminando documentos definitivamente: {e}", exc_info=True)
            return False

    # ============================================================
    # --- Getters auxiliares
    # ============================================================

    def get_clientes(self):
        """Pide a la lógica de clientes la lista de nombres y IDs para los combos."""
        try:
            return self.clientes_logic.get_all_clientes_for_combobox()
        except Exception as e:
            self.logger.error("Error al obtener la lista de clientes: %s", e)
            return []

    def get_documentos_activos(self):
        """Carga todos los documentos que no están en la papelera."""
        try:
            return self.documentos_db.get_documentos_filtered_as_tuples(eliminado=False)
        except Exception as e:
            self.logger.error("Error al cargar documentos activos: %s", e)
            return []

    def get_document_by_id(self, doc_id: int) -> dict | None:
        """Devuelve un documento por ID en formato dict."""
        try:
            return self.documentos_logic.get_documento_por_id(doc_id)
        except Exception as e:
            self.logger.error(f"Error al obtener documento por ID ({doc_id}): {e}")
            return None
    
    
seguro qu hicite el camnsi