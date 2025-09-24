from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID

class UsuarioCreate(BaseModel):
    nombre: str
    correo: str
    contrasena: str
    class Config:
        from_attributes = True

class UsuarioResponse(BaseModel):
    id_usuario: int
    nombre: str
    correo: str
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    correo: str
    contrasena: str

class VideoCreate(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    id_usuario: int
    class Config:
        from_attributes = True

class VideoResponse(BaseModel):
    id_video: UUID
    titulo: str
    descripcion: Optional[str]
    id_usuario: int
    class Config:
        from_attributes = True

class InteraccionCreate(BaseModel):
    id_video: UUID
    total_vistas: Optional[int] = 0
    total_likes: Optional[int] = 0
    class Config:
        from_attributes = True

class InteraccionResponse(BaseModel):
    id_interaccion: int
    id_video: UUID
    total_vistas: int
    total_likes: int
    promedio_porcentaje_visto: Optional[int] = 0
    promedio_tiempo_visto: Optional[str] = None
    class Config:
        from_attributes = True

class EtiquetaCreate(BaseModel):
    nombre: str
    id_video: UUID
    class Config:
        from_attributes = True

class EtiquetaResponse(BaseModel):
    id_etiqueta: int
    nombre: str
    id_video: UUID
    class Config:
        from_attributes = True
