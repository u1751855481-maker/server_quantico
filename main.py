import os
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

app = FastAPI()

# CORS: necesario para builds web (itch.io)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # en cuanto puedas, cambia a tu dominio de itch.io
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.environ.get("API_KEY", "")  # configura en el hosting

class Instruccion(BaseModel):
    puerta: str
    params: Optional[List[float]] = None

class DatosCircuito(BaseModel):
    instrucciones: List[Instruccion]

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/ejecutar_circuito")
async def ejecutar_circuito(
    datos: DatosCircuito,
    x_api_key: Optional[str] = Header(default=None)
):
    # Seguridad mínima (opcional pero recomendado)
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if len(datos.instrucciones) > 200:
        raise HTTPException(status_code=400, detail="Demasiadas instrucciones")

    qc = QuantumCircuit(1)

    for inst in datos.instrucciones:
        p = inst.puerta.lower()
        if p == "h":
            qc.h(0)
        elif p == "x":
            qc.x(0)
        elif p == "y":
            qc.y(0)
        elif p == "z":
            qc.z(0)
        elif p in ("rx", "ry", "rz"):
            if not inst.params:
                raise HTTPException(status_code=400, detail=f"Falta parámetro para {p}")
            angulo = float(inst.params[0])
            if p == "rx":
                qc.rx(angulo, 0)
            elif p == "ry":
                qc.ry(angulo, 0)
            else:
                qc.rz(angulo, 0)
        else:
            raise HTTPException(status_code=400, detail=f"Puerta desconocida: {inst.puerta}")

    qc.measure_all()

    sim = AerSimulator()
    job = sim.run(qc, shots=1)
    counts = job.result().get_counts()
    bit_medido = int(next(iter(counts.keys())))

    return {"estado": "Exito", "medicion": bit_medido, "counts": counts}
