# =====================================================
# ⚙️ CRUD (Create, Read, Update, Delete)
# =====================================================
# Este módulo contiene todas las funciones que interactúan
# directamente con la base de datos a través de SQLAlchemy.
#
# Cada función corresponde a una operación de lectura o
# escritura sobre las tablas definidas en `models.py`.
#
# Funcionalidad cubierta:
#  - Usuarios: creación y listado
#  - Videos: creación, lectura, eliminación
#  - Etiquetas: creación, listado, obtención por video
#  - Likes: crear, eliminar, contar, verificar estado
#  - Interacciones: vistas, promedio de tiempo, etc.
# =====================================================

from sqlalchemy.orm import Session
from datetime import timedelta
import models
import schemas


# =====================================================
# 🧍‍♂️ USUARIOS
# =====================================================

def listar_usuarios(db: Session):
    """Obtiene todos los usuarios registrados."""
    return db.query(models.UsuarioApp).all()


def get_usuario_by_correo(db: Session, correo: str):
    """Busca un usuario por su correo electrónico."""
    return db.query(models.UsuarioApp).filter(models.UsuarioApp.correo == correo).first()


def get_usuario_by_id(db: Session, id_usuario: int):
    """Busca un usuario por su ID."""
    return db.query(models.UsuarioApp).filter(models.UsuarioApp.id_usuario == id_usuario).first()


def crear_usuario(db: Session, nombre: str, correo: str, contrasena: str):
    """Crea un nuevo usuario."""
    usuario = models.UsuarioApp(nombre=nombre, correo=correo, contrasena=contrasena)
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


# =====================================================
# 🎥 VIDEOS
# =====================================================

def get_videos(db: Session, skip: int = 0, limit: int = 10):
    """Devuelve una lista paginada de videos ordenados por fecha."""
    return db.query(models.Video).order_by(models.Video.fecha_subida.asc()).offset(skip).limit(limit).all()


def contar_videos(db: Session):
    """Cuenta la cantidad total de videos."""
    return db.query(models.Video).count()


def get_video_by_id(db: Session, id_video):
    """Busca un video por su ID."""
    return db.query(models.Video).filter(models.Video.id_video == id_video).first()


def crear_video(db: Session, nuevo_video: models.Video):
    """Crea un nuevo registro de video."""
    db.add(nuevo_video)
    db.commit()
    db.refresh(nuevo_video)

    # Crear registro de interacción base
    interaccion = models.Interaccion(id_video=nuevo_video.id_video)
    db.add(interaccion)
    db.commit()

    return nuevo_video


def eliminar_video(db: Session, id_video):
    """Elimina un video (y sus relaciones por cascada)."""
    video = get_video_by_id(db, id_video)
    if video:
        db.delete(video)
        db.commit()
        return True
    return False


# =====================================================
# 🏷️ ETIQUETAS
# =====================================================

def listar_etiquetas(db: Session):
    """Devuelve todas las etiquetas existentes."""
    return db.query(models.Etiqueta).all()


def crear_etiqueta(db: Session, nombre: str, id_video):
    """Crea una nueva etiqueta asociada a un video."""
    etiqueta = models.Etiqueta(nombre=nombre, id_video=id_video)
    db.add(etiqueta)
    db.commit()
    db.refresh(etiqueta)
    return etiqueta


def get_etiqueta_por_video(db: Session, id_video):
    """Obtiene la etiqueta asociada a un video."""
    return db.query(models.Etiqueta).filter(models.Etiqueta.id_video == id_video).first()


# =====================================================
# ❤️ LIKES
# =====================================================

def get_like(db: Session, id_usuario: int, id_video):
    """Obtiene el registro de like (puede estar activo o no)."""
    return db.query(models.Like).filter(
        models.Like.id_usuario == id_usuario,
        models.Like.id_video == id_video
    ).first()

def create_like(db: Session, id_usuario: int, id_video):
    """
    Si no existe el registro, lo crea con activo=True y genera like_id (UUID).
    Si existe y activo=False, lo pone en activo=True.
    Si existe y activo=True, lo pone en activo=False (quita el like).
    No elimina el registro.
    """
    import uuid
    like = get_like(db, id_usuario, id_video)
    interaccion = get_interaccion_por_video(db, id_video)
    if like:
        if like.activo:
            # Quitar el like
            like.activo = False
            if interaccion and interaccion.total_likes > 0:
                interaccion.total_likes -= 1
            db.commit()
            return like
        else:
            # Dar el like
            like.activo = True
            if interaccion:
                interaccion.total_likes += 1
            db.commit()
            return like
    # Si no existe, crear nuevo registro con activo=True y like_id (UUID)
    like = models.Like(
        like_id=uuid.uuid4(),  # <-- Esto es correcto si la columna en la BD es tipo UUID
        id_usuario=id_usuario,
        id_video=id_video,
        activo=True
    )
    db.add(like)
    if not interaccion:
        interaccion = crear_interaccion(db, id_video)
    interaccion.total_likes += 1
    db.commit()
    db.refresh(like)
    return like

def delete_like(db: Session, id_usuario: int, id_video):
    """No elimina el registro, solo lo pone en activo=False."""
    like = get_like(db, id_usuario, id_video)
    if like and like.activo:
        like.activo = False
        interaccion = get_interaccion_por_video(db, id_video)
        if interaccion and interaccion.total_likes > 0:
            interaccion.total_likes -= 1
        db.commit()
        return True
    return False

def actualizar_estado_like(db: Session, id_usuario: int, id_video, activo: bool):
    """Actualiza el campo activo de un registro Like existente."""
    like = db.query(models.Like).filter_by(id_usuario=id_usuario, id_video=id_video).first()
    if like:
        like.activo = activo
        db.commit()
        db.refresh(like)
        return like
    return None

def get_total_likes(db: Session, id_video):
    """Cuenta los likes activos de un video."""
    return db.query(models.Like).filter(
        models.Like.id_video == id_video,
        models.Like.activo == True
    ).count()


# =====================================================
# 📊 INTERACCIONES (Vistas y analítica)
# =====================================================

def get_interaccion_por_video(db: Session, id_video):
    """Obtiene el registro de interacción de un video."""
    return db.query(models.Interaccion).filter(models.Interaccion.id_video == id_video).first()


def crear_interaccion(db: Session, id_video):
    """Crea un registro de interacción para un video."""
    interaccion = models.Interaccion(id_video=id_video, total_vistas=0, total_likes=0)
    db.add(interaccion)
    db.commit()
    db.refresh(interaccion)
    return interaccion


def registrar_vista(db: Session, id_video):
    """Incrementa el contador de vistas de un video."""
    interaccion = get_interaccion_por_video(db, id_video)
    if not interaccion:
        interaccion = crear_interaccion(db, id_video)
    interaccion.total_vistas += 1
    db.commit()
    db.refresh(interaccion)
    return interaccion


def registrar_progreso(db: Session, id_video, segundos_vistos: float, duracion_total: float):
    """
    Actualiza el promedio de tiempo visto según la duración visualizada por el usuario.
    Similar al modelo usado por TikTok / Instagram Reels.
    """
    interaccion = get_interaccion_por_video(db, id_video)
    if not interaccion:
        interaccion = crear_interaccion(db, id_video)
    interaccion.total_vistas += 1

    # Calcular nuevo promedio (ponderado)
    vistas_previas = max(1, interaccion.total_vistas)
    nuevo_promedio = (
        (interaccion.promedio_tiempo_visto.total_seconds() * (vistas_previas - 1) + segundos_vistos)
        / vistas_previas
    )

    interaccion.promedio_tiempo_visto = timedelta(seconds=nuevo_promedio)

    db.commit()
    db.refresh(interaccion)
    return interaccion
