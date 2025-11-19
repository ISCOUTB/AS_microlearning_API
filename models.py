# =====================================================
# 📦 MODELOS DE BASE DE DATOS
# =====================================================
# Define las tablas principales de la plataforma usando SQLAlchemy ORM.
# Incluye usuarios, videos, etiquetas, likes e interacciones.
# =====================================================

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    Boolean,
    Interval,
    TIMESTAMP,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
import uuid


# =====================================================
# 🧍‍♂️ USUARIO APP
# =====================================================
class UsuarioApp(Base):
    """
    Representa a los usuarios registrados en la plataforma.
    Cada usuario puede subir varios videos y dar 'like' a otros.
    """

    __tablename__ = "usuario_app"

    id_usuario = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    correo = Column(String(150), unique=True, nullable=False)
    contrasena = Column(String(255), nullable=False)
    fecha_registro = Column(TIMESTAMP, server_default=func.now())

    # Relaciones
    videos = relationship("Video", back_populates="usuario", cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="usuario", cascade="all, delete-orphan")


# =====================================================
# 🎥 VIDEO
# =====================================================
class Video(Base):
    """
    Representa los videos subidos por los usuarios.
    Incluye metadatos como duración, descripción y la ruta del archivo.
    """

    __tablename__ = "video"

    id_video = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    titulo = Column(String(200), nullable=False)
    descripcion = Column(Text)
    duracion = Column(Interval, nullable=False)  # formato hh:mm:ss
    fecha_subida = Column(TIMESTAMP, server_default=func.now())
    id_usuario = Column(Integer, ForeignKey("usuario_app.id_usuario", ondelete="CASCADE"), nullable=False)
    ruta = Column(String(500), nullable=False)
    id_iteracion = Column(Integer, unique=True)

    # Relaciones
    usuario = relationship("UsuarioApp", back_populates="videos")
    etiquetas = relationship("Etiqueta", back_populates="video", cascade="all, delete-orphan")
    interaccion = relationship("Interaccion", back_populates="video", uselist=False, cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="video", cascade="all, delete-orphan")


# =====================================================
# 🏷️ ETIQUETA
# =====================================================
class Etiqueta(Base):
    """
    Define una etiqueta o categoría asociada a un video.
    Por ejemplo: 'educación', 'tutorial', 'entretenimiento'.
    """

    __tablename__ = "etiqueta"

    id_etiqueta = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    id_video = Column(UUID(as_uuid=True), ForeignKey("video.id_video", ondelete="CASCADE"), nullable=False)

    # Relaciones
    video = relationship("Video", back_populates="etiquetas")


# =====================================================
# ❤️ LIKE
# =====================================================
class Like(Base):
    """
    Representa un 'me gusta' dado por un usuario a un video.
    Puede activarse o desactivarse sin eliminar el registro.
    """

    __tablename__ = "likes"

    like_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_usuario = Column(Integer, ForeignKey("usuario_app.id_usuario", ondelete="CASCADE"))
    id_video = Column(UUID(as_uuid=True), ForeignKey("video.id_video", ondelete="CASCADE"))
    activo = Column(Boolean, default=True)

    # Relaciones
    usuario = relationship("UsuarioApp", back_populates="likes")
    video = relationship("Video", back_populates="likes")


# =====================================================
# 📊 INTERACCIÓN
# =====================================================
class Interaccion(Base):
    """
    Contiene métricas y analíticas de cada video.
    Se actualiza automáticamente cuando hay nuevas vistas o likes.
    """

    __tablename__ = "interaccion"

    id_interaccion = Column(Integer, primary_key=True, index=True)
    id_video = Column(UUID(as_uuid=True), ForeignKey("video.id_video", ondelete="CASCADE"), unique=True, nullable=False)
    total_vistas = Column(Integer, default=0)
    total_likes = Column(Integer, default=0)
    promedio_tiempo_visto = Column(Interval, default="00:00:00")  # Duración promedio vista

    # Relaciones
    video = relationship("Video", back_populates="interaccion")
