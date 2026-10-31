import os
import json
import hashlib
import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from web3 import Web3
from supabase import create_client, Client
from fastapi.responses import HTMLResponse

load_dotenv()

app = FastAPI(
    title="VERTEX AXIOMA - Motor de Petrificación API",
    version="1.0.0",
    description="Sello de Inmutabilidad Transfronteriza - Auditoría 4.0"
)

# Habilitar CORS para que tu interfaz web (HTML) pueda conectarse sin problemas
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
RPC_URL = os.getenv("RPC_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")

class AxiomaCloudPetrification:
    """
    Motor en la nube de Indexación, Anclaje en Blockchain (Polygon Amoy) 
    y Sincronización con Supabase - VERTEX AXIOMA®
    """
    def __init__(self, file_bytes, filename, metadata=None):
        self.file_bytes = file_bytes
        self.filename = filename
        self.chunk_size = 1024
        self.metadata = metadata or {}
        self.timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.indexed_chunks = []
        self.chunk_hashes = []
        self.root_hash = None
        
        # Inicializar Web3 (Polygon Amoy)
        if RPC_URL:
            self.w3 = Web3(Web3.HTTPProvider(RPC_URL))
        else:
            self.w3 = None
        
        # Inicializar Supabase
        if SUPABASE_URL and SUPABASE_KEY and "tu-proyecto" not in SUPABASE_URL:
            try:
                self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            except Exception:
                self.supabase = None
        else:
            self.supabase = None

    def process_binary(self):
        """Indexa los bytes del archivo recibido en memoria por bloques SHA-256."""
        index = 0
        for i in range(0, len(self.file_bytes), self.chunk_size):
            chunk_data = self.file_bytes[i:i + self.chunk_size]
            chunk_hash = hashlib.sha256(chunk_data).hexdigest()
            self.indexed_chunks.append({
                "index": index,
                "offset": i,
                "size_bytes": len(chunk_data),
                "chunk_hash": chunk_hash
            })
            self.chunk_hashes.append(chunk_hash)
            index += 1

    def generate_root_hash(self):
        """Genera el Hash Raíz (Prueba Petrificada)."""
        combined_payload = "".join(self.chunk_hashes) + json.dumps(self.metadata, sort_keys=True) + self.timestamp
        self.root_hash = hashlib.sha256(combined_payload.encode('utf-8')).hexdigest()
        return self.root_hash

    def anchor_on_polygon(self):
        """Ancla el Root Hash en Polygon Amoy usando Gas Legacy."""
        if not PRIVATE_KEY or not self.w3:
            return "SIMULATED_TX_HASH_0X..."

        try:
            account = self.w3.eth.account.from_key(PRIVATE_KEY)
            nonce = self.w3.eth.get_transaction_count(account.address)
            
            current_gas_price = self.w3.eth.gas_price
            adjusted_gas_price = int(current_gas_price * 1.2)

            tx = {
                'nonce': nonce,
                'to': account.address, 
                'value': 0,
                'gas': 100000,
                'gasPrice': adjusted_gas_price,
                'chainId': 80002, 
                'data': self.w3.to_hex(text=self.root_hash)
            }

            signed_tx = self.w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            return self.w3.to_hex(tx_hash)
        
        except Exception as e:
            return f"ERROR_TX_SIMULATED_FALLBACK: {str(e)}"

    def save_to_supabase(self, manifest, tx_hash):
        """Registra el manifiesto en Supabase."""
        if not self.supabase:
            return

        try:
            data_to_insert = {
                "root_hash": manifest["root_hash"],
                "target_file": manifest["target_file"],
                "timestamp_utc": manifest["timestamp_utc"],
                "tx_hash": tx_hash,
                "metadata_caso": manifest["metadata_caso"],
                "compliance_seal": manifest["compliance_seal"]
            }
            self.supabase.table("axioma_evidencias").insert(db_payload).execute()
        except Exception as e:
            print(f"Error Supabase: {e}")

    def execute(self):
        self.process_binary()
        root = self.generate_root_hash()
        tx_hash = self.anchor_on_polygon()

        manifest = {
            "ecosystem": "VERTEX AXIOMA",
            "protocol": "Protocolo AXIOMA®",
            "compliance_seal": "Sello de Inmutabilidad Transfronteriza",
            "timestamp_utc": self.timestamp,
            "target_file": self.filename,
            "total_chunks_indexed": len(self.indexed_chunks),
            "root_hash": root,
            "blockchain_tx": tx_hash,
            "metadata_caso": self.metadata
        }

        self.save_to_supabase(manifest, tx_hash)
        return manifest

@app.get("/", response_class=HTMLResponse)
def serve_home():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return """
    <html>
        <head><title>VERTEX AXIOMA</title></head>
        <body style="background: #0f172a; color: #38bdf8; font-family: monospace; text-align: center; padding-top: 50px;">
            <h1>Sello de Inmutabilidad Transfronteriza</h1>
            <p>API Operativa - Falta adjuntar el archivo index.html en el repositorio.</p>
        </body>
    </html>
    """

@app.post("/petrify/")
async def petrify_file(
    file: UploadFile = File(...), 
    expediente: str = "EXP-2026-CFI-INNOVA", 
    jurisdiccion: str = "Laboratorio Autónomo VERTEX AXIOMA"
):
    try:
        content = await file.read()
        metadata = {
            "expediente_ref": expediente,
            "jurisdiccion": jurisdiccion,
            "auditor": "Verónica Arapian"
        }
        motor = AxiomaCloudPetrification(content, file.filename, metadata)
        resultado = motor.execute()
        return {"status": "success", "manifiesto": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
if supabase:
        try:
            db_payload = {
                "root_hash": root_hash,
                "target_file": file.filename,
                "timestamp_utc": timestamp_str,
                "tx_hash": tx_hash,
                "metadata_caso": manifiesto["metadata_caso"],
                "compliance_seal": "Sello de Inmutabilidad Transfronteriza"
            }
            print(f"[DEBUG AXIOMA] Enviando a Supabase: {db_payload}")
            
            # Ejecutamos la inserción capturando la respuesta completa
            response = supabase.table("axioma_evidencias").insert(db_payload).execute()
            
            print(f"[SUPABASE ÉXITO]: Respuesta recibida correctamente -> {response}")
            
        except Exception as db_err:
            print(f"[ERROR CRÍTICO SUPABASE]: {type(db_err).__name__} -> {str(db_err)}")
