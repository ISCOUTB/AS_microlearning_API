# =====================================================
# 🧾 SCHEMAS (Pydantic Models)
# =====================================================
# Este archivo define los modelos de datos que se utilizan
# para validar la entrada y salida de información entre el
# backend (FastAPI) y el frontend o cliente (por ejemplo, JS).
#
# Relación directa con los modelos ORM definidos en `models.py`.
# =====================================================

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, timedelta
from uuid import UUID


# =====================================================
# 🧍‍♂️ USUARIO APP
# =====================================================

class UsuarioBase(BaseModel):
    """Datos básicos del usuario."""
    nombre: str
    correo: EmailStr


class UsuarioCreate(UsuarioBase):
    """Datos requeridos al crear un usuario nuevo."""
    contrasena: str


class UsuarioResponse(UsuarioBase):
    """Datos devueltos por la API al listar o consultar usuarios."""
    id_usuario: int
    fecha_registro: datetime

    class Config:
        from_attributes = True


# =====================================================
# 🔐 LOGIN
# =====================================================

class LoginRequest(BaseModel):
    """Datos requeridos para iniciar sesión."""
    correo: EmailStr
    contrasena: str


class LoginResponse(BaseModel):
    """Respuesta al iniciar sesión exitosamente."""
    message: str
    id_usuario: int
    nombre: str


# =====================================================
# 🎥 VIDEO
# =====================================================

class VideoBase(BaseModel):
    """Datos básicos de un video."""
    titulo: str
    descripcion: Optional[str] = ""
    duracion: Optional[str] = None  # en formato hh:mm:ss
    ruta: Optional[str] = None


class VideoCreate(VideoBase):
    """Datos requeridos al subir un nuevo video."""
    id_usuario: int


class VideoResponse(VideoBase):
    """Datos devueltos por la API al listar videos."""
    id_video: UUID
    fecha_subida: datetime
    usuario: str
    etiqueta: Optional[str] = None
    likes: int = 0
    liked: bool = False

    class Config:
        from_attributes = True


# =====================================================
# 🏷️ ETIQUETA
# =====================================================

class EtiquetaBase(BaseModel):
    """Datos básicos de una etiqueta."""
    nombre: str


class EtiquetaCreate(EtiquetaBase):
    """Datos requeridos para crear una etiqueta."""
    id_video: UUID


class EtiquetaResponse(EtiquetaBase):
    """Datos devueltos por la API al listar etiquetas."""
    id_etiqueta: int
    id_video: UUID

    class Config:
        from_attributes = True


# =====================================================
# ❤️ LIKE
# =====================================================

class LikeResponse(BaseModel):
    """Datos que representan el estado de un 'like'."""
    likes: int
    liked: bool
    # Opcional: incluir el id del like si lo necesitas en el frontend
    like_id: Optional[UUID] = None


# =====================================================
# 📊 INTERACCIÓN (Analítica de videos)
# =====================================================

class InteraccionBase(BaseModel):
    """Modelo base para analíticas de video."""
    total_vistas: int = 0
    total_likes: int = 0
    promedio_tiempo_visto: Optional[str] = "00:00:00"


class InteraccionResponse(InteraccionBase):
    """Datos devueltos al consultar métricas de un video."""
    id_video: UUID

    class Config:
        from_attributes = True


# =====================================================
# 🧩 RESPUESTAS AGRUPADAS / PAGINADAS
# =====================================================

class PaginacionVideos(BaseModel):
    """Modelo de respuesta para listas paginadas de videos."""
    page: int
    has_more: bool
    videos: List[VideoResponse]
