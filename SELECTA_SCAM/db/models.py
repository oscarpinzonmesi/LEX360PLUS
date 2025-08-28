# SELECTA_SCAM/db/models.py
from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from datetime import date, datetime 
from sqlalchemy.ext.declarative import declarative_base

# Asumo que Base se define en SELECTA_SCAM/db/base.py.
# Si estás definiendo declarative_base() en este archivo,
# entonces deberías quitar 'from .base import Base' y dejar 'Base = declarative_base()'.
# Por el contexto, parece que 'Base' viene de un archivo 'base.py'.
from .base import Base 


class Cliente(Base):
    __tablename__ = 'clientes'

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True, nullable=False)
    tipo_identificacion = Column(String, nullable=False)
    numero_identificacion = Column(String, unique=True, index=True, nullable=False)
    telefono = Column(String)
    direccion = Column(String)
    email = Column(String, unique=True)
    tipo_cliente = Column(String)
    fecha_creacion = Column(DateTime, default=datetime.now)
    eliminado = Column(Boolean, default=False)

    procesos = relationship('Proceso', back_populates='cliente')
    contabilidad = relationship('Contabilidad', back_populates='cliente')
    documentos = relationship('Documento', back_populates='cliente')

    def __repr__(self):
        return f"<Cliente(id={self.id}, nombre='{self.nombre}', identificacion='{self.numero_identificacion}')>"


class Proceso(Base):
    __tablename__ = 'procesos'

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey('clientes.id'), nullable=False)
    radicado = Column(String, unique=True, index=True, nullable=False)
    tipo = Column(String, nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=True)
    estado = Column(String, nullable=False)
    juzgado = Column(String, nullable=False)
    observaciones = Column(Text, nullable=True)
    fecha_creacion = Column(Date, default=date.today)
    eliminado = Column(Boolean, default=False)

    cliente = relationship('Cliente', back_populates='procesos')
    documentos = relationship('Documento', back_populates='proceso', cascade="all, delete-orphan")
    contabilidad = relationship('Contabilidad', back_populates='proceso', cascade="all, delete-orphan")
    actuaciones = relationship('Actuacion', back_populates='proceso', cascade="all, delete-orphan")
    robot_busquedas = relationship('RobotBusqueda', back_populates='proceso', cascade="all, delete-orphan")
    eventos = relationship('Evento', back_populates='proceso', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Proceso(id={self.id}, radicado='{self.radicado}', cliente_id={self.cliente_id})>"


class Documento(Base):
    __tablename__ = 'documentos'

    id = Column(Integer, primary_key=True, index=True)
    proceso_id = Column(Integer, ForeignKey('procesos.id'), nullable=True)
    cliente_id = Column(Integer, ForeignKey('clientes.id'), nullable=False)
    nombre = Column(String, index=True, nullable=False)
    archivo = Column(String, nullable=False)
    ubicacion_archivo = Column(String, nullable=False)
    tipo_documento = Column(String)
    fecha_subida = Column(DateTime, default=datetime.now)
    eliminado = Column(Boolean, default=False)

    proceso = relationship('Proceso', back_populates='documentos')
    cliente = relationship('Cliente', back_populates='documentos')

    def __repr__(self):
        return f"<Documento(id={self.id}, nombre='{self.nombre}', proceso_id={self.proceso_id})>"


class TipoContable(Base):
    __tablename__ = 'tipos_contables'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String, unique=True, nullable=False)
    es_ingreso = Column(Boolean, default=False)
    def __repr__(self):
        return f"<TipoContable(id={self.id}, nombre='{self.nombre}')>"


class Contabilidad(Base):
    __tablename__ = 'contabilidad'

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey('clientes.id'), nullable=False)
    proceso_id = Column(Integer, ForeignKey('procesos.id'), nullable=True)
    
    tipo_contable_id = Column(Integer, ForeignKey('tipos_contables.id'), nullable=False)
    tipo = relationship("TipoContable", backref="registros_contables")
    
    descripcion = Column(String, nullable=False)
    monto = Column(Float, nullable=False)
    
    metodo_pago = Column(String, nullable=True)
    referencia_pago = Column(String, nullable=True)
    esta_pagado = Column(Boolean, default=False)
    fecha_pago = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    fecha = Column(DateTime, default=datetime.utcnow)
    
    cliente = relationship("Cliente", back_populates="contabilidad")
    proceso = relationship("Proceso", back_populates="contabilidad")

    def __repr__(self):
        tipo_nombre = self.tipo.nombre if self.tipo else 'N/A'
        return f"<Contabilidad(id={self.id}, tipo='{tipo_nombre}', monto={self.monto})>"


class Evento(Base):
    __tablename__ = 'eventos'

    id = Column(Integer, primary_key=True, index=True)
    proceso_id = Column(Integer, ForeignKey('procesos.id'), nullable=False)
    titulo = Column(String, nullable=False)
    descripcion = Column(Text)
    fecha_evento = Column(DateTime, nullable=False)

    proceso = relationship('Proceso', back_populates='eventos')

    def __repr__(self):
        return f"<Evento(id={self.id}, titulo='{self.titulo}', proceso_id={self.proceso_id})>"


class Liquidador(Base):
    __tablename__ = 'liquidadores'
    id = Column(Integer, primary_key=True, index=True)
    nombre_herramienta = Column(String, nullable=False, unique=True)
    descripcion = Column(String, nullable=True)
    ruta_ejecutable = Column(String, nullable=False)
    area_derecho = Column(String, nullable=True)
    eliminado = Column(Boolean, default=False)

    def __repr__(self):
        return f"<Liquidador(id={self.id}, nombre_herramienta='{self.nombre_herramienta}')>"


class Usuario(Base):
    __tablename__ = 'usuarios'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    email = Column(String, unique=True)
    activo = Column(Boolean, default=True)
    es_admin = Column(Boolean, default=False)
    fecha_creacion = Column(Date, default=date.today)
    eliminado = Column(Boolean, default=False)

    def __repr__(self):
        return f"<Usuario(id={self.id}, username='{self.username}')>"


class Notificacion(Base):
    __tablename__ = 'notificaciones'

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=True)
    titulo = Column(String, nullable=False)
    mensaje = Column(Text, nullable=False)
    leido = Column(Boolean, default=False)
    fecha = Column(DateTime, default=datetime.now)

    usuario = relationship('Usuario')

    def __repr__(self):
        return f"<Notificacion(id={self.id}, titulo='{self.titulo}')>"


class Actuacion(Base):
    __tablename__ = 'actuaciones'

    id = Column(Integer, primary_key=True, index=True)
    proceso_id = Column(Integer, ForeignKey('procesos.id'), nullable=False)
    fecha = Column(Date, nullable=False)
    descripcion = Column(Text, nullable=False)
    tipo_actuacion = Column(String, nullable=True)
    fecha_creacion = Column(Date, default=date.today)
    eliminado = Column(Boolean, default=False)

    proceso = relationship('Proceso', back_populates='actuaciones')

    def __repr__(self):
        return f"<Actuacion(id={self.id}, fecha='{self.fecha}', proceso_id={self.proceso_id})>"


class RobotBusqueda(Base):
    __tablename__ = 'robot_busquedas'

    id = Column(Integer, primary_key=True, index=True)
    proceso_id = Column(Integer, ForeignKey('procesos.id'), nullable=False)
    url = Column(String, nullable=False)
    fecha_busqueda = Column(DateTime, default=datetime.now)
    resultado = Column(Text)
    estado = Column(String)
    eliminado = Column(Boolean, default=False)

    proceso = relationship('Proceso', back_populates='robot_busquedas')

    def __repr__(self):
        return f"<RobotBusqueda(id={self.id}, url='{self.url}', proceso_id={self.proceso_id})>"