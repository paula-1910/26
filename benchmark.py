import asyncio
import httpx
import time

URL_ASYNC = "http://127.0.0.1:8000/submit-async"
URL_SYNC = "http://127.0.0.1:8000/submit-sync"
NUM_PETICIONES = 200  # Simulación de ráfaga concurrente alta

async def enviar_subida(client, url):
    # Simula un archivo de 200KB en memoria
    files = {'file': ('solution.py', b'X' * 200 * 1024, 'text/plain')}
    try:
        start = time.perf_counter()
        response = await client.post(url, files=files)
        end = time.perf_counter()
        return end - start, response.status_code
    except Exception:
        return 0, 500

async def run_benchmark(url, nombre_arq):
    print(f"\nIniciando test de carga sobre: {nombre_arq}...")
    # Límites altos para forzar la concurrencia real
    limits = httpx.Limits(max_keepalive_connections=NUM_PETICIONES, max_connections=NUM_PETICIONES)
    
    async with httpx.AsyncClient(limits=limits, timeout=10.0) as client:
        start_time = time.perf_counter()
        
        # Dispara todas las peticiones en paralelo
        tasks = [enviar_subida(client, url) for _ in range(NUM_PETICIONES)]
        resultados = await asyncio.gather(*tasks)
        
        total_time = time.perf_counter() - start_time
        
        tiempos = [r[0] for r in resultados if r[1] == 200]
        errores = sum(1 for r in resultados if r[1] != 200)
        
        avg_time = sum(tiempos) / len(tiempos) if tiempos else 0
        print(f"--- Resultados {nombre_arq} ---")
        print(f"Tiempo total para resolver la ráfaga: {total_time:.4f} segundos")
        print(f"Tiempo de respuesta promedio por petición: {avg_time:.4f} segundos")
        print(f"Peticiones fallidas/bloqueadas: {errores}")

if __name__ == "__main__":
    print("Asegúrate de que 'app.py' se está ejecutando en otra terminal.")
    # Ejecuta ambos benchmarks de manera secuencial
    asyncio.run(run_benchmark(URL_SYNC, "Arquitectura Síncrona (Threadpool / Bloqueante)"))
    asyncio.run(run_benchmark(URL_ASYNC, "Arquitectura Asíncrona (Asyncio / Event Loop)"))