from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base

class UsuarioApp(Base):
    __tablename__ = "usuario_app"
    id_usuario = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    correo = Column(String(150), unique=True, nullable=False)
    contrasena = Column(String(255), nullable=False)
    videos = relationship("Video", back_populates="usuario")

class Video(Base):
    __tablename__ = "video"
    id_video = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    titulo = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    fecha_subida = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    id_usuario = Column(Integer, ForeignKey("usuario_app.id_usuario"), nullable=False)
    ruta = Column(String(255), nullable=False)
    usuario = relationship("UsuarioApp", back_populates="videos")
    interacciones = relationship("Interaccion", back_populates="video")
    etiquetas = relationship("Etiqueta", back_populates="video")

class Interaccion(Base):
    __tablename__ = "interaccion"
    id_interaccion = Column(Integer, primary_key=True, index=True)
    id_video = Column(UUID(as_uuid=True), ForeignKey("video.id_video"), nullable=False)
    total_vistas = Column(Integer, default=0)
    total_likes = Column(Integer, default=0)
    video = relationship("Video", back_populates="interacciones")

class Etiqueta(Base):
    __tablename__ = "etiqueta"
    id_etiqueta = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    id_video = Column(UUID(as_uuid=True), ForeignKey("video.id_video"), nullable=False)
    video = relationship("Video", back_populates="etiquetas")

class Like(Base):
    __tablename__ = "like"
    id_like = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, nullable=False)
    id_video = Column(UUID(as_uuid=True), nullable=False)
