import asyncio
import time
from fastapi import FastAPI, UploadFile, File, HTTPException
import uvicorn

app = FastAPI(title="Hackathon Eterno Backend - Benchmark")

# Simulación de un Broker de Mensajería (ej. Redis/RabbitMQ) en memoria
class MockBroker:
    def __init__(self):
        self.queue = []
    
    async def enqueue_async(self, data):
        # Simula la latencia de red/I/O de escribir en el broker (10ms)
        await asyncio.sleep(0.01)
        self.queue.append(data)

    def enqueue_sync(self, data):
        # Simula el bloqueo síncrono al escribir en el broker
        time.sleep(0.01)
        self.queue.append(data)

broker = MockBroker()

# --- ARQUITECTURA A: ASÍNCRONA (Nuestra propuesta para producción) ---
@app.post("/submit-async")
async def submit_async(file: UploadFile = File(...)):
    try:
        # Lee el archivo de forma asíncrona (I/O)
        content = await file.read()
        payload = {"filename": file.filename, "size": len(content), "timestamp": time.time()}
        
        # Encola en el broker sin bloquear el bucle de eventos
        await broker.enqueue_async(payload)
        return {"status": "accepted", "message": "Subida encolada para testeo"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ARQUITECTURA B: SÍNCRONA (Alternativa tradicional) ---
# Nota: FastAPI ejecuta los endpoints 'def' normales en un threadpool subyacente
@app.post("/submit-sync")
def submit_sync(file: UploadFile = File(...)):
    try:
        # Bloqueo síncrono de lectura e inserción
        content = file.file.read()
        payload = {"filename": file.filename, "size": len(content), "timestamp": time.time()}
        
        broker.enqueue_sync(payload)
        return {"status": "accepted", "message": "Subida encolada para testeo"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Arranca el servidor uvicorn con un único proceso para la demostración
    uvicorn.run("app.py:app", host="127.0.0.1", port=8000, workers=1)