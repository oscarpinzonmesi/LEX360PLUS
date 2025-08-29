# SELECTA_SCAM/modulos/documentos/documentos_db.py

import logging
from contextlib import contextmanager
from sqlalchemy.orm import joinedload
from ...db.models import Documento, Cliente
from ...utils.db_manager import get_db_session
from datetime import datetime

logger = logging.getLogger(__name__)

class DocumentosDB:
    def __init__(self):
        """El constructor ya no necesita argumentos."""
        self.logger = logger

    @contextmanager
    def get_session(self):
        """Usa la sesión global del db_manager para garantizar una única conexión."""
        session = get_db_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            self.logger.error("Error en transacción de DocumentosDB, haciendo rollback: %s", e, exc_info=True)
            session.rollback()
            raise
        finally:
            session.close()

        # En: SELECTA_SCAM/modulos/documentos/documentos_db.py

    # SELECTA_SCAM/modulos/documentos/documentos_db.py

    def add_documento(self, cliente_id: int, nombre: str, ubicacion_archivo: str,
                    tipo_documento: str = None, fecha_subida: datetime = None,
                    archivo: str = None, ruta_completa: str = None) -> Documento | None:
        """
        Agrega un nuevo documento a la base de datos.
        """
        from ...db.models import Documento
        import os

        if fecha_subida is None:
            fecha_subida = datetime.now()

        # si no viene 'archivo', usamos el mismo nombre de ubicacion_archivo
        if not archivo:
            archivo = ubicacion_archivo

        try:
            with self.get_session() as session:
                nuevo_doc = Documento(
                    cliente_id=cliente_id,
                    nombre=nombre,
                    archivo=archivo,                # 👈 importante para NOT NULL
                    ubicacion_archivo=ubicacion_archivo,
                    tipo_documento=tipo_documento,
                    fecha_subida=fecha_subida,
                    eliminado=False
                )
                session.add(nuevo_doc)
                session.flush()
                self.logger.info(f"Documento agregado con ID {nuevo_doc.id}")
                return nuevo_doc
        except Exception as e:
            self.logger.error(f"Error al agregar documento: {e}", exc_info=True)
            return None



    def get_documentos_filtered_as_tuples(self, **filters) -> list:
        """
        Obtiene los documentos como tuplas, con las columnas en el orden exacto que la tabla necesita.
        Filtros soportados:
        - eliminado: bool
        - cliente_ids: list[int]
        - tipo_documento: str | None
        - documento_id: int | None
        - documento_nombre: str | None
        """
        from ...config import settings  # o la ruta donde tengas DOCUMENTOS_GUARDADOS_PATH
        import os

        base_path = os.path.join(os.getcwd(), "Documentos_Guardados")

        with self.get_session() as session:
            query = session.query(
                Documento.cliente_id,        # 0: ID Cliente
                Documento.id,                # 1: ID Documento
                Cliente.nombre.label("cliente_nombre"),   # 2: Cliente
                Documento.nombre,            # 3: Nombre Documento
                Documento.ubicacion_archivo, # 4: Ubicación (ej: archivo.pdf)
                Documento.tipo_documento,    # 5: Tipo Documento
                Documento.fecha_subida,      # 6: Fecha Carga
                Documento.eliminado          # 7: Eliminado
            ).join(Cliente, Cliente.id == Documento.cliente_id)

            # aplicar filtros...
            if "eliminado" in filters:
                query = query.filter(Documento.eliminado == filters["eliminado"])
            if "cliente_ids" in filters and filters["cliente_ids"]:
                query = query.filter(Documento.cliente_id.in_(filters["cliente_ids"]))
            if "tipo_documento" in filters and filters["tipo_documento"]:
                query = query.filter(Documento.tipo_documento == filters["tipo_documento"])
            if "documento_id" in filters and filters["documento_id"]:
                query = query.filter(Documento.id == filters["documento_id"])
            if "documento_nombre" in filters and filters["documento_nombre"]:
                query = query.filter(Documento.nombre.ilike(f"%{filters['documento_nombre']}%"))

            resultados = []
            for row in query.all():
                ruta_completa = os.path.join(base_path, row.ubicacion_archivo or "")
                resultados.append((
                    row.cliente_id,
                    row.id,
                    row.cliente_nombre,
                    row.nombre,
                    row.ubicacion_archivo,
                    row.tipo_documento,
                    row.fecha_subida,
                    ruta_completa,     # 7: ruta completa en memoria
                    row.eliminado      # 8: eliminado
                ))
            return resultados


    def get_documento_details_as_dict(self, doc_id: int) -> dict | None:
        """
        Obtiene los datos de un documento y los devuelve como un diccionario seguro,
        evitando el DetachedInstanceError.
        """
        with self.get_session() as session:
            documento = session.query(Documento).get(doc_id)
            if documento:
                # Convertimos el objeto a un diccionario ANTES de que se cierre la sesión
                return {
                    'id': documento.id,
                    'nombre': documento.nombre,
                    'tipo_documento': documento.tipo_documento,
                    'fecha_subida': documento.fecha_subida,
                    'cliente_id': documento.cliente_id,
                    'proceso_id': documento.proceso_id,
                    'ubicacion_archivo': documento.ubicacion_archivo
                }
            return None

    def update_documento(self, doc_id: int, **kwargs) -> bool:
        """Actualiza un documento existente."""
        with self.get_session() as session:
            documento = session.query(Documento).get(doc_id)
            if documento:
                for key, value in kwargs.items():
                    if hasattr(documento, key) and value is not None:
                        # Si es string con fecha, intenta convertir
                        if key in ("fecha_subida", "fecha_expiracion") and isinstance(value, str):
                            try:
                                value = datetime.fromisoformat(value)
                            except ValueError:
                                pass  # Si falla la conversión, lo deja como string
                        setattr(documento, key, value)
                session.commit()
                return True
            return False

    def mover_a_papelera(self, doc_ids: list[int]) -> bool:
        """Marca uno o varios documentos como eliminados (papelera)."""
        with self.get_session() as session:
            try:
                session.query(Documento).filter(
                    Documento.id.in_(doc_ids)
                ).update({Documento.eliminado: True}, synchronize_session=False)
                session.commit()
                return True
            except Exception as e:
                logger.error(f"Error al mover documentos a la papelera: {e}", exc_info=True)
                session.rollback()
                return False

    def restaurar_desde_papelera(self, doc_ids: list[int]) -> bool:
        """Restaura documentos desde la papelera."""
        with self.get_session() as session:
            try:
                result = (
                    session.query(Documento)
                    .filter(Documento.id.in_(doc_ids))
                    .update({Documento.eliminado: False}, synchronize_session=False)
                )
                session.commit()
                return result > 0
            except Exception as e:
                logger.error(f"Error al restaurar documentos de la papelera: {e}", exc_info=True)
                session.rollback()
                return False



    def get_documento_por_id(self, doc_id: int) -> Documento | None:
        """Obtiene un objeto de documento completo por su ID."""
        with self.get_session() as session:
            return session.query(Documento).options(
                joinedload(Documento.cliente), 
                joinedload(Documento.proceso)
            ).filter(Documento.id == doc_id).first()

    def eliminar_documento_por_id(self, documento_id: int) -> bool:
        """Elimina un documento de forma permanente."""
        with self.get_session() as session:
            documento = session.query(Documento).get(documento_id)
            if documento:
                session.delete(documento)
                return True
            return False