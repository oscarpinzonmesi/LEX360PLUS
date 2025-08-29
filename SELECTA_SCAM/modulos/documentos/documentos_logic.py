import logging
import os
from .documentos_db import DocumentosDB

logger = logging.getLogger(__name__)

class DocumentosLogic:
    def __init__(self, documentos_db_instance: DocumentosDB):
        """Inicializa la capa de lógica con una instancia de la capa de base de datos."""
        self.db = documentos_db_instance
        self.logger = logger

    def get_documentos_para_tabla(self, **filters):
        """Normaliza los nombres de filtros que vienen del widget/controlador y los adapta a la DB."""
        eliminado = bool(filters.get('mostrando_papelera', False))
        tipo_documento = filters.get('tipo_documento_filtro') or filters.get('tipo_documento')
        documento_id = filters.get('documento_id_filtro') or filters.get('documento_id')
        documento_nombre = filters.get('documento_nombre_filtro') or filters.get('documento_nombre')
        cliente_ids = filters.get('cliente_ids')

        db_filters = {
            'eliminado': eliminado,
            'tipo_documento': tipo_documento,
            'documento_id': documento_id,
            'documento_nombre': documento_nombre,
            'cliente_ids': cliente_ids,
        }
        db_filters = {k: v for k, v in db_filters.items() if v not in (None, '', [])}

        return self.db.get_documentos_filtered_as_tuples(**db_filters)

    def agregar_documento(self, **data) -> int | None:
        """Agrega un nuevo documento."""
        return self.db.add_documento(**data)

    def editar_documento(self, doc_id: int, **data) -> bool:
        """Actualiza los detalles de un documento."""
        return self.db.update_documento(doc_id, **data)

    def get_documento_por_id(self, doc_id: int) -> dict | None:
        """
        Obtiene los datos de un documento como un diccionario.
        Ideal para pre-llenar el diálogo de edición.
        """
        try:
            return self.db.get_documento_details_as_dict(doc_id)
        except Exception as e:
            self.logger.error(f"Error al obtener documento por ID {doc_id}: {e}", exc_info=True)
            return None

    def mover_a_papelera(self, doc_ids: list) -> bool:
        """Marca documentos como eliminados (papelera)."""
        try:
            for doc_id in doc_ids:
                self.db.update_documento(doc_id, eliminado=True)
            return True
        except Exception as e:
            self.logger.error("Error al mover documentos a la papelera: %s", e)
            return False

    def recuperar_de_papelera(self, doc_ids: list) -> bool:
        """Restaura documentos desde la papelera."""
        try:
            for doc_id in doc_ids:
                self.db.update_documento(doc_id, eliminado=False)
            return True
        except Exception as e:
            self.logger.error("Error al recuperar documentos de la papelera: %s", e)
            return False

    def eliminar_documento_definitivamente(self, doc_ids: list) -> bool:
        """Elimina documentos de forma permanente."""
        try:
            for doc_id in doc_ids:
                documento = self.db.get_documento_por_id(doc_id)
                if documento and documento.ubicacion_archivo and os.path.exists(documento.ubicacion_archivo):
                    os.remove(documento.ubicacion_archivo)
                self.db.eliminar_documento_por_id(doc_id)
            return True
        except Exception as e:
            self.logger.error("Error al eliminar documentos permanentemente: %s", e)
            return False
    #el mejor del los cambios 