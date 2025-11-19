# ===================================================== # 🚀 MAIN.PY # ===================================================== # Archivo principal de la API con FastAPI. # Implementa los endpoints para: # - Usuarios (registro, login) # - Videos (subida, eliminación, listado) # - Likes (gestión de "me gusta") # - Interacciones (vistas, progreso) # - Etiquetas (asociación a videos) # Incluye manejo de archivos multimedia, paginación, # y cálculo automático de duración de video. # =====================================================
from fastapi import (
    FastAPI, Depends, HTTPException, UploadFile, File, Form, Query,
)
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pymediainfo import MediaInfo
from datetime import timedelta
import os
import random
from uuid import UUID

# Importaciones locales
import models, schemas, crud
from database import SessionLocal, engine

# ===================================================== # ⚙️ CONFIGURACIÓN INICIAL # =====================================================
# Crear las tablas en caso de que no existan
models.Base.metadata.create_all(bind=engine)

# Inicializar aplicación
app = FastAPI(title="API Plataforma de Videos", version="3.0")

# Configuración de directorios estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")

# Directorio donde se almacenan los videos
VIDEO_DIR = os.path.join(os.path.dirname(__file__), "media")
os.makedirs(VIDEO_DIR, exist_ok=True)

# ===================================================== # 📦 DEPENDENCIA DE BASE DE DATOS # =====================================================
def get_db():
    """Crea una sesión temporal a la base de datos."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ===================================================== # ⏱️ FUNCIONES AUXILIARES # =====================================================
def get_video_duration(path: str) -> str:
    """
    Obtiene la duración de un archivo de video utilizando pymediainfo.
    Retorna la duración en formato HH:MM:SS.
    """
    info = MediaInfo.parse(path)
    for track in info.tracks:
        if track.track_type == "Video" and track.duration:
            duracion_seg = track.duration / 1000
            return str(timedelta(seconds=int(duracion_seg)))
    return "00:00:00"

# ===================================================== # 🌐 RUTA PRINCIPAL # =====================================================
@app.get("/")
def root():
    """Sirve la página principal de la aplicación."""
    return FileResponse(os.path.join("static", "index.html"))

# ===================================================== # 👤 USUARIOS # =====================================================
@app.post("/usuarios", response_model=schemas.UsuarioResponse)
def crear_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    """
    Registra un nuevo usuario si el correo no está en uso.
    """
    existente = crud.get_usuario_by_correo(db, usuario.correo)
    if existente:
        raise HTTPException(status_code=400, detail="Correo ya registrado")
    nuevo = crud.crear_usuario(db, usuario.nombre, usuario.correo, usuario.contrasena)
    return schemas.UsuarioResponse.from_orm(nuevo)

@app.get("/usuarios", response_model=list[schemas.UsuarioResponse])
def listar_usuarios(db: Session = Depends(get_db)):
    """Lista todos los usuarios registrados en la base de datos."""
    return crud.listar_usuarios(db)

# ===================================================== # 🔐 LOGIN # =====================================================
@app.post("/login", response_model=schemas.LoginResponse)
def login(request: schemas.LoginRequest, db: Session = Depends(get_db)):
    """
    Valida las credenciales de acceso del usuario.
    Retorna su información básica en caso de éxito.
    """
    usuario = crud.get_usuario_by_correo(db, request.correo)
    if not usuario:
        raise HTTPException(status_code=401, detail="Correo no registrado")
    if usuario.contrasena != request.contrasena:
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")
    return schemas.LoginResponse(
        message="Login exitoso",
        id_usuario=usuario.id_usuario,
        nombre=usuario.nombre,
    )

# ===================================================== # 🎥 VIDEOS # =====================================================
@app.post("/upload_video")
def upload_video(
    titulo: str = Form(...),
    descripcion: str = Form(""),
    id_usuario: int = Form(...),
    etiqueta: str = Form(""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Sube un nuevo video, obtiene su duración automáticamente
    y registra la información en la base de datos.
    """
    usuario = crud.get_usuario_by_id(db, id_usuario)
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuario no válido")
    filename = file.filename
    save_path = os.path.join(VIDEO_DIR, filename)
    with open(save_path, "wb") as buffer:
        buffer.write(file.file.read())
    duracion = get_video_duration(save_path)
    ruta = f"media/{filename}"
    nuevo_video = models.Video(
        titulo=titulo,
        descripcion=descripcion,
        duracion=duracion,
        id_usuario=id_usuario,
        ruta=ruta,
    )
    crud.crear_video(db, nuevo_video)
    if etiqueta:
        crud.crear_etiqueta(db, etiqueta, nuevo_video.id_video)
    return {
        "message": "Video subido correctamente",
        "id_video": str(nuevo_video.id_video),
        "ruta": ruta,
        "duracion": duracion,
    }

@app.get("/videos", response_model=schemas.PaginacionVideos)
def listar_videos(page: int = 1, db: Session = Depends(get_db)):
    """
    Devuelve una lista paginada de videos, mostrando su autor,
    etiqueta, likes y duración.
    """
    limit = 3
    skip = (page - 1) * limit
    videos = crud.get_videos(db, skip=skip, limit=limit)
    total = crud.contar_videos(db)
    has_more = skip + limit < total
    result = []
    for v in videos:
        usuario = crud.get_usuario_by_id(db, v.id_usuario)
        etiqueta = crud.get_etiqueta_por_video(db, v.id_video)
        total_likes = crud.get_total_likes(db, v.id_video)
        result.append(
            {
                "id_video": str(v.id_video),
                "titulo": v.titulo,
                "descripcion": v.descripcion,
                "ruta": v.ruta,
                "usuario": usuario.nombre if usuario else "Desconocido",
                "etiqueta": etiqueta.nombre if etiqueta else "",
                "likes": total_likes or 0,
                "liked": False,
                "fecha_subida": v.fecha_subida,
                "duracion": str(v.duracion),
            }
        )
    return {"page": page, "videos": result, "has_more": has_more}

@app.delete("/videos/{id_video}")
def eliminar_video(id_video: UUID, id_usuario: int, db: Session = Depends(get_db)):
    """
    Elimina un video si pertenece al usuario autenticado.
    """
    video = crud.get_video_by_id(db, id_video)
    if not video:
        raise HTTPException(status_code=404, detail="Video no encontrado")
    if video.id_usuario != id_usuario:
        raise HTTPException(status_code=403, detail="No tienes permiso para eliminar este video")
    crud.eliminar_video(db, id_video)
    return {"message": "Video eliminado correctamente"}

# ===================================================== # ❤️ LIKES # =====================================================
@app.get("/videos/{id_video}/like", response_model=schemas.LikeResponse)
def obtener_estado_like(id_video: UUID, id_usuario: int, db: Session = Depends(get_db)):
    """
    Devuelve si el usuario actual ha dado 'like' a un video
    y el número total de 'likes' del mismo.
    """
    video = crud.get_video_by_id(db, id_video)
    if not video:
        raise HTTPException(status_code=404, detail="Video no encontrado")
    like = crud.get_like(db, id_usuario, id_video)
    liked = like.activo if like else False
    total_likes = crud.get_total_likes(db, id_video)
    return {"likes": total_likes, "liked": liked}

@app.post("/videos/{id_video}/like", response_model=schemas.LikeResponse)
def toggle_like(id_video: UUID, id_usuario: int, db: Session = Depends(get_db)):
    """
    Activa o desactiva el 'like' de un usuario sobre un video.
    Actualiza automáticamente el contador.
    """
    video = crud.get_video_by_id(db, id_video)
    if not video:
        raise HTTPException(status_code=404, detail="Video no encontrado")
    like = crud.get_like(db, id_usuario, id_video)
    if like:
        nuevo_estado = not like.activo
        crud.actualizar_estado_like(db, id_usuario, id_video, nuevo_estado)
        liked = nuevo_estado
    else:
        crud.create_like(db, id_usuario, id_video)
        liked = True
    total_likes = crud.get_total_likes(db, id_video)
    return {"likes": total_likes, "liked": liked}

# ===================================================== # 👀 INTERACCIONES (VISTAS Y PROGRESO) # =====================================================
@app.post("/videos/{id_video}/view")
def registrar_vista(id_video: UUID, db: Session = Depends(get_db)):
    """
    Incrementa el contador de vistas del video especificado.
    """
    video = crud.get_video_by_id(db, id_video)
    if not video:
        raise HTTPException(status_code=404, detail="Video no encontrado")
    interaccion = crud.registrar_vista(db, id_video)
    return {"views": interaccion.total_vistas}

@app.post("/videos/{id_video}/progress")
def registrar_progreso(
    id_video: UUID,
    segundos_vistos: float = Form(...),
    duracion_total: float = Form(...),
    db: Session = Depends(get_db),
):
    """
    Registra el tiempo total que el usuario ha visto de un video.
    Permite calcular promedios de visualización.
    """
    video = crud.get_video_by_id(db, id_video)
    if not video:
        raise HTTPException(status_code=404, detail="Video no encontrado")
    interaccion = crud.registrar_progreso(db, id_video, segundos_vistos, duracion_total)
    return {
        "message": "Progreso registrado",
        "vistas": interaccion.total_vistas,
        "promedio_tiempo_visto": str(interaccion.promedio_tiempo_visto),
    }

# ===================================================== # 🏷️ ETIQUETAS # =====================================================
@app.get("/etiquetas", response_model=list[schemas.EtiquetaResponse])
def listar_etiquetas(db: Session = Depends(get_db)):
    """Devuelve todas las etiquetas registradas."""
    return crud.listar_etiquetas(db)

@app.post("/etiquetas", response_model=schemas.EtiquetaResponse)
def crear_etiqueta(etiqueta: schemas.EtiquetaCreate, db: Session = Depends(get_db)):
    """Crea una nueva etiqueta asociada a un video existente."""
    nueva = crud.crear_etiqueta(db, etiqueta.nombre, etiqueta.id_video)
    return schemas.EtiquetaResponse.from_orm(nueva)

# ===================================================== # 🎲 VIDEOS ALEATORIOS # =====================================================
@app.get("/videos/random")
async def videos_random(
    id_usuario: int = Query(...),
    page: int = Query(1),
    page_size: int = Query(3),
    db: Session = Depends(get_db)
):
    """
    Devuelve una lista de videos aleatorios paginados (5 por página).
    Solo carga más cuando se solicita una nueva página.
    """
    # Obtener todos los videos
    todos_videos = crud.get_videos(db, skip=0, limit=crud.contar_videos(db))
    import random
    random.shuffle(todos_videos)
    total = len(todos_videos)
    start = (page - 1) * page_size
    end = start + page_size
    paged_videos = todos_videos[start:end]
    if not paged_videos:
        return {"videos": [], "has_more": False}
    result = []
    for v in paged_videos:
        usuario = crud.get_usuario_by_id(db, v.id_usuario)
        etiqueta = crud.get_etiqueta_por_video(db, v.id_video)
        total_likes = crud.get_total_likes(db, v.id_video)
        like = crud.get_like(db, id_usuario, v.id_video)
        liked = like.activo if like else False
        result.append(
            {
                "id_video": str(v.id_video),
                "titulo": v.titulo,
                "descripcion": v.descripcion,
                "ruta": v.ruta,
                "usuario": usuario.nombre if usuario else "Desconocido",
                "etiqueta": etiqueta.nombre if etiqueta else "",
                "likes": total_likes or 0,
                "liked": liked,
                "fecha_subida": v.fecha_subida,
                "duracion": str(v.duracion),
            }
        )
    has_more = end < total
    return {"videos": result, "has_more": has_more}
