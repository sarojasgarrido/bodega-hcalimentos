from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
from io import BytesIO
import qrcode
import models

app = FastAPI(title="Gestión de Bodega HC Alimentos - Tesis", version="1.2")
templates = Jinja2Templates(directory="templates")

def get_db():
    db = models.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def menu_principal(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/escaner/")
def abrir_escaner(request: Request, modo: str = "entrada"):
    return templates.TemplateResponse("scanner.html", {"request": request, "modo": modo})

# --- ENTRADA ---
@app.post("/recepcion/pallet/")
def registrar_nuevo_pallet(sku: str, cantidad: int, db: Session = Depends(get_db)):
    fecha_actual = datetime.now()
    qr_unico = f"PAL-{fecha_actual.strftime('%Y%m%d%H%M%S')}"
    
    nuevo_pallet = models.Pallet(
        codigo_qr=qr_unico, sku=sku, cantidad=cantidad, 
        fecha_ingreso=fecha_actual.strftime("%Y-%m-%d %H:%M:%S"),
        estado="En Recepción"
    )
    db.add(nuevo_pallet)
    db.commit()
    db.refresh(nuevo_pallet)
    
    # Asignación automática inmediata
    ubicacion_libre = db.query(models.Ubicacion).filter(models.Ubicacion.estado == "Libre").first()
    if ubicacion_libre:
        nuevo_pallet.id_ubicacion = ubicacion_libre.id
        nuevo_pallet.estado = "Almacenado"
        ubicacion_libre.estado = "Ocupado"
        db.commit()
    
    return {"mensaje": "Pallet registrado y almacenado", "qr": qr_unico}

# --- SALIDA ---
@app.post("/despacho/pallet/")
def procesar_salida(codigo_qr: str, db: Session = Depends(get_db)):
    pallet = db.query(models.Pallet).filter(models.Pallet.codigo_qr == codigo_qr).first()
    if not pallet:
        raise HTTPException(status_code=404, detail="Pallet no encontrado")
    
    ubicacion = db.query(models.Ubicacion).filter(models.Ubicacion.id == pallet.id_ubicacion).first()
    if ubicacion:
        ubicacion.estado = "Libre"
    
    pallet.estado = "Despachado"
    pallet.id_ubicacion = None
    db.commit()
    return {"mensaje": "Pallet despachado correctamente"}

@app.get("/generar-qr/{codigo_qr}")
def generar_imagen_qr(codigo_qr: str):
    img_qr = qrcode.make(codigo_qr)
    buffer = BytesIO()
    img_qr.save(buffer, format="PNG")
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="image/png")