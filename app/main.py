import json
import threading
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db import get_db, engine, Base
from app.models import RegistroCarga
from app.producer_queues import enviar_mensaje_cola
from app.consumer_queues import activar_consumer
from app.utils import get_fecha_actual

# Crear las tablas en la base de datos
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Servicio de Carga con Colas y DB")
app.state.consumer_thread = None  # Para trackear el hilo del consumer

@app.post("/enviar")
async def enviar_carga(db: Session = Depends(get_db)):
    try:
        estado = "PENDIENTE"
        # Guardar registro en la base de datos
        nuevo_registro = RegistroCarga(
            estado=estado,
            fecha_de_publicacion=get_fecha_actual()
        )
        db.add(nuevo_registro)
        db.commit()
        db.refresh(nuevo_registro)
        
        detalle = json.dumps({
            "id": nuevo_registro.id, 
            "estado": estado
        })
        respuesta_cola = enviar_mensaje_cola(detalle)

        return {
            "mensaje": "Mensaje enviado a la cola y registro guardado en la base de datos",
            "respuesta_cola": respuesta_cola,
            "registro": {
                "id": nuevo_registro.id,
                "estado": nuevo_registro.estado,
                "fecha_carga": nuevo_registro.fecha_de_publicacion
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/registros")
async def obtener_registros(db: Session = Depends(get_db)):
    registros = db.query(RegistroCarga).all()
    return {
        "numero_registros": len(registros),
        "registros": registros
    }

@app.delete("/registros")
async def limpiar_registros(db: Session = Depends(get_db)):
    db.query(RegistroCarga).delete()
    db.commit()
    return {"mensaje": "Registros eliminados"}

@app.get("/activa_consumer")
async def activar_consumidor():
    if app.state.consumer_thread and app.state.consumer_thread.is_alive():
        return {"mensaje": "El consumer ya está activo"}
    
    # Crear y arrancar el hilo
    app.state.consumer_thread = threading.Thread(target=activar_consumer, daemon=True)
    app.state.consumer_thread.start()
    return {"mensaje": "Consumer activado en segundo plano"}

@app.get("/estado_consumer")
async def estado_consumer():
    if app.state.consumer_thread and app.state.consumer_thread.is_alive():
        return {"estado": "activo", "hilos_activos": threading.active_count()}
    return {"estado": "inactivo", "hilos_activos": threading.active_count()}