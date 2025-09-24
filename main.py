from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import and_
import models, schemas, crud
from database import SessionLocal, engine
from typing import List
from models import UsuarioApp, Video, Interaccion, Etiqueta, Like
from sqlalchemy import Column, Integer, UUID
import os

# Crear tablas si no existen
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Videos", version="1.0")

# Montar archivos estáticos (asegúrate de tener carpeta "static" con index.html)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/images", StaticFiles(directory="images"), name="images")

VIDEO_DIR = os.path.join(os.path.dirname(__file__), "videos")
os.makedirs(VIDEO_DIR, exist_ok=True)

# Dependencia DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    # Sirve el index.html
    return FileResponse("static/index.html")

# ---------------- USUARIOS ----------------
@app.get("/usuarios", response_model=List[schemas.UsuarioResponse])
def get_usuarios(db: Session = Depends(get_db)):
    return db.query(UsuarioApp).all()

@app.post("/usuarios")
def crear_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    nuevo_usuario = UsuarioApp(
        nombre=usuario.nombre,
        correo=usuario.correo,
        contrasena=usuario.contrasena
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return schemas.UsuarioResponse.from_orm(nuevo_usuario)

# ---------------- LOGIN ----------------
@app.post("/login")
def login(request: schemas.LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(UsuarioApp).filter(UsuarioApp.correo == request.correo).first()
    if not usuario or usuario.contrasena != request.contrasena:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    return {"message": "Login exitoso", "id_usuario": usuario.id_usuario, "nombre": usuario.nombre}

# ---------------- VIDEOS  ----------------
@app.get("/videos", response_model=List[schemas.VideoResponse])
def listar_videos(db: Session = Depends(get_db)):
    return db.query(Video).all()

@app.post("/videos", response_model=schemas.VideoResponse)
def crear_video(video: schemas.VideoCreate, db: Session = Depends(get_db)):
    nuevo_video = Video(
        titulo=video.titulo,
        descripcion=video.descripcion,
        id_usuario=video.id_usuario
    )
    db.add(nuevo_video)
    db.commit()
    db.refresh(nuevo_video)
    return schemas.VideoResponse.from_orm(nuevo_video)

@app.post("/upload_video")
def upload_video(titulo: str = Form(...), descripcion: str = Form(""), etiqueta: str = Form(""), id_usuario: int = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Solo permitir subir videos si el usuario existe
    usuario = db.query(UsuarioApp).filter(UsuarioApp.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    filename = file.filename
    save_path = os.path.join(VIDEO_DIR, filename)
    with open(save_path, "wb") as buffer:
        buffer.write(file.file.read())
    ruta = f"videos/{filename}"
    nuevo_video = Video(titulo=titulo, descripcion=descripcion, id_usuario=id_usuario, ruta=ruta)
    db.add(nuevo_video)
    db.commit()
    db.refresh(nuevo_video)
    if etiqueta:
        nueva_etiqueta = Etiqueta(nombre=etiqueta, id_video=nuevo_video.id_video)
        db.add(nueva_etiqueta)
        db.commit()
    return {"message": "Video subido", "id_video": str(nuevo_video.id_video), "ruta": ruta}

@app.get("/videos/{filename}")
def serve_video(filename: str):
    file_path = os.path.join(VIDEO_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="video/mp4")
    return Response(status_code=404)

@app.get("/feed_videos/{id_usuario}")
def feed_videos(id_usuario: int, db: Session = Depends(get_db)):
    videos = db.query(Video).order_by(Video.fecha_subida.asc()).all()
    feed = []
    for v in videos:
        usuario = db.query(UsuarioApp).filter(UsuarioApp.id_usuario == v.id_usuario).first()
        etiqueta = db.query(Etiqueta).filter(Etiqueta.id_video == v.id_video).first()
        
        # Contar likes
        total_likes = db.query(Like).filter(Like.id_video == v.id_video).count()
        # Verificar si este usuario ya dio like
        liked = db.query(Like).filter(
            Like.id_video == v.id_video, Like.id_usuario == id_usuario
        ).first() is not None

        feed.append({
            "id_video": str(v.id_video),
            "titulo": v.titulo,
            "descripcion": v.descripcion,
            "ruta": v.ruta,
            "usuario": usuario.nombre if usuario else "Desconocido",
            "etiqueta": etiqueta.nombre if etiqueta else "",
            "likes": total_likes or 0,
            "liked": liked
        })
    return feed


@app.delete("/videos/{id_video}")
def eliminar_video(id_video: str, id_usuario: int, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id_video == id_video).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video no encontrado")
    if video.id_usuario != id_usuario:
        raise HTTPException(status_code=403, detail="No tienes permiso para eliminar este video")
    # Eliminar interacciones
    db.query(Interaccion).filter(Interaccion.id_video == id_video).delete()
    # Eliminar etiquetas
    db.query(Etiqueta).filter(Etiqueta.id_video == id_video).delete()
    # Eliminar likes
    db.query(Like).filter(Like.id_video == id_video).delete()
    # Eliminar el video
    db.delete(video)
    db.commit()
    return {"ok": True, "message": "Video eliminado"}

# ---------------- INTERACCIONES ----------------
@app.get("/interacciones", response_model=List[schemas.InteraccionResponse])
def listar_interacciones(db: Session = Depends(get_db)):
    return db.query(Interaccion).all()

@app.post("/interacciones", response_model=schemas.InteraccionResponse)
def crear_interaccion(interaccion: schemas.InteraccionCreate, db: Session = Depends(get_db)):
    nueva_interaccion = Interaccion(
        id_video=interaccion.id_video,
        total_vistas=interaccion.total_vistas,
        total_likes=interaccion.total_likes
    )
    db.add(nueva_interaccion)
    db.commit()
    db.refresh(nueva_interaccion)
    return schemas.InteraccionResponse.from_orm(nueva_interaccion)

# ---------------- ETIQUETAS ----------------
@app.get("/etiquetas", response_model=List[schemas.EtiquetaResponse])
def listar_etiquetas(db: Session = Depends(get_db)):
    return db.query(Etiqueta).all()

@app.post("/etiquetas", response_model=schemas.EtiquetaResponse)
def crear_etiqueta(etiqueta: schemas.EtiquetaCreate, db: Session = Depends(get_db)):
    nueva_etiqueta = Etiqueta(
        nombre=etiqueta.nombre,
        id_video=etiqueta.id_video
    )
    db.add(nueva_etiqueta)
    db.commit()
    db.refresh(nueva_etiqueta)
    return schemas.EtiquetaResponse.from_orm(nueva_etiqueta)


@app.post("/videos/{id_video}/like")
def toggle_like(id_video: str, id_usuario: int, db: Session = Depends(get_db)):
    like = db.query(Like).filter_by(id_usuario=id_usuario, id_video=id_video).first()
    
    if like:
        db.delete(like)
        db.commit()
        liked = False
    else:
        nuevo_like = Like(id_usuario=id_usuario, id_video=id_video)
        db.add(nuevo_like)
        db.commit()
        liked = True

    total_likes = db.query(Like).filter_by(id_video=id_video).count() or 0

    return {"likes": total_likes, "liked": liked}

