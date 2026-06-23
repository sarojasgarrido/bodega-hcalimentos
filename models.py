import os
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# ==========================================
# 1. CONFIGURACIÓN DE LA CONEXIÓN
# ==========================================

# Buscamos la URL de la nube. Si no la encuentra (porque estás en tu notebook),
# usa por defecto un archivo local llamado "bodega_local.db"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bodega_local.db")

# Parche de seguridad para Neon.tech/Render (exigen postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# ==========================================
# 2. MOTOR DE BASE DE DATOS (ENGINE)
# ==========================================

# SQLite requiere un parámetro extra para evitar errores de hilos en FastAPI
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # Configuración limpia para PostgreSQL (Neon.tech)
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==========================================
# 3. DEFINICIÓN DE TABLAS (MODELOS)
# ==========================================

class Ubicacion(Base):
    __tablename__ = "ubicaciones"

    id = Column(Integer, primary_key=True, index=True)
    codigo_qr = Column(String, unique=True, index=True)  # Ej: UBI-ZONA-A1
    estado = Column(String, default="Libre")             # "Libre" u "Ocupado"

    # Relación bidireccional
    pallets = relationship("Pallet", back_populates="ubicacion")


class Pallet(Base):
    __tablename__ = "pallets"

    id = Column(Integer, primary_key=True, index=True)
    codigo_qr = Column(String, unique=True, index=True)  # Ej: PAL-20260622...
    sku = Column(String, index=True)
    cantidad = Column(Integer)
    fecha_ingreso = Column(String)
    estado = Column(String, default="En Recepción")      # "En Recepción" o "Almacenado"
    
    # Llave foránea que lo conecta a una ubicación específica
    id_ubicacion = Column(Integer, ForeignKey("ubicaciones.id"), nullable=True)

    # Relación bidireccional
    ubicacion = relationship("Ubicacion", back_populates="pallets")

# ==========================================
# 4. CREACIÓN AUTOMÁTICA DE TABLAS
# ==========================================
# ¡Muy importante! Esta línea hace que la primera vez que Render se conecte a Neon,
# cree las tablas vacías automáticamente para que el sistema funcione de inmediato.
Base.metadata.create_all(bind=engine)