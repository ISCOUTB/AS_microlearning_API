from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql+pg8000://postgres:cNFtPnwvOAUwtaEmxpxLFgJkxBSwzlxK@interchange.proxy.rlwy.net:20795/railway"

# Crear el motor
engine = create_engine(DATABASE_URL, echo=True)

# Sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Test de conexión
if __name__ == "__main__":
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("Conexión exitosa:", result.scalar())
