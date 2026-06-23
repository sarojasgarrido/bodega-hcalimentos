from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
from io import BytesIO
import qrcode
import models

# Iniciamos la aplicación
app = FastAPI(title="Gestión de Bodega HC Alimentos - Tesis", version="1.1")

# Configuramos la carpeta de plantillas
templates = Jinja2Templates(directory="templates")

# Función para conectarse a la base de datos
def get_db():
    db = models.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def leer_raiz():
    return {"mensaje": "¡Sistema de Almacenamiento Caótico en línea!"}

@app.get("/ubicaciones/")
def obtener_ubicaciones(db: Session = Depends(get_db)):
    return db.query(models.Ubicacion).all()

# --- FUNCIONALIDADES DE ALMACENAMIENTO CAÓTICO ---

@app.post("/recepcion/pallet/")
def registrar_nuevo_pallet(sku: str, cantidad: int, db: Session = Depends(get_db)):
    fecha_actual = datetime.now()
    qr_unico = f"PAL-{fecha_actual.strftime('%Y%m%d%H%M%S')}"
    
    nuevo_pallet = models.Pallet(
        codigo_qr=qr_unico,
        sku=sku,
        cantidad=cantidad,
        fecha_ingreso=fecha_actual.strftime("%Y-%m-%d %H:%M:%S")
    )
    
    db.add(nuevo_pallet)
    db.commit()
    db.refresh(nuevo_pallet)
    
    return {"mensaje": "Pallet registrado exitosamente", "pallet": nuevo_pallet}

@app.put("/asignacion_caotica/{pallet_id}")
def asignar_ubicacion_caotica(pallet_id: int, db: Session = Depends(get_db)):
    pallet = db.query(models.Pallet).filter(models.Pallet.id == pallet_id).first()
    if not pallet:
        raise HTTPException(status_code=404, detail="Pallet no encontrado")
        
    if pallet.estado == "Almacenado":
        raise HTTPException(status_code=400, detail="El pallet ya está almacenado")

    ubicacion_libre = db.query(models.Ubicacion).filter(models.Ubicacion.estado == "Libre").first()
    
    if not ubicacion_libre:
        raise HTTPException(status_code=400, detail="¡Bodega llena! No hay ubicaciones libres.")

    pallet.id_ubicacion = ubicacion_libre.id
    pallet.estado = "Almacenado"
    ubicacion_libre.estado = "Ocupado"
    
    db.commit()
    db.refresh(pallet)
    db.refresh(ubicacion_libre)
    
    return {
        "mensaje": "Ubicación asignada por almacenamiento caótico",
        "qr_pallet": pallet.codigo_qr,
        "sku": pallet.sku,
        "coordenada_asignada": ubicacion_libre.codigo_qr
    }

# --- ENDPOINT DE GENERACIÓN DE IMAGEN QR ---

@app.get("/generar-qr/{codigo_qr}")
def generar_imagen_qr(codigo_qr: str):
    img_qr = qrcode.make(codigo_qr)
    buffer = BytesIO()
    img_qr.save(buffer, format="PNG")
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="image/png")

# --- NUEVA INTERFAZ VISUAL (CORREGIDA) ---

@app.get("/escaner/")
def abrir_escaner(request: Request):
    """
    Ruta corregida para renderizar la plantilla HTML sin causar errores de contexto.
    """
    return templates.TemplateResponse(
        request=request, 
        name="scanner.html", 
        context={"request": request}
    )
