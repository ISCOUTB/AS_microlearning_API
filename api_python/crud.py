from sqlalchemy.orm import Session
from models import UsuarioApp

def get_usuario_by_correo(db: Session, correo: str):
    return db.query(UsuarioApp).filter(UsuarioApp.correo == correo).first()

def crear_usuario(db: Session, nombre: str, correo: str, contrasena: str):
    nuevo_usuario = UsuarioApp(nombre=nombre, correo=correo, contrasena=contrasena)
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return nuevo_usuario
