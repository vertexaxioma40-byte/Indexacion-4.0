import os
import json
import hashlib
import datetime
from dotenv import load_dotenv
from web3 import Web3
from supabase import create_client, Client

# Cargar variables del entorno desde el archivo .env
load_dotenv()

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
RPC_URL = os.getenv("RPC_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")

class AxiomaNetworkPetrification:
    """
    Motor Avanzado de Indexación, Anclaje en Blockchain (Polygon Amoy) 
    y Sincronización con Supabase - VERTEX AXIOMA®
    """
    def __init__(self, file_path, chunk_size=1024, metadata=None):
        self.file_path = file_path
        self.chunk_size = chunk_size
        self.metadata = metadata or {}
        # Timestamp moderno UTC
        self.timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.indexed_chunks = []
        self.chunk_hashes = []
        self.root_hash = None
        
        # Inicializar conexión Web3 (Polygon Amoy)
        if RPC_URL:
            self.w3 = Web3(Web3.HTTPProvider(RPC_URL))
        else:
            self.w3 = None
        
        # Inicializar cliente Supabase (Valida que la URL no sea un placeholder)
        if SUPABASE_URL and SUPABASE_KEY and "tu-proyecto" not in SUPABASE_URL:
            try:
                self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
                print("[Supabase] Cliente inicializado correctamente.")
            except Exception as e:
                self.supabase = None
                print(f"[Aviso Supabase] No se pudo conectar: {e}")
        else:
            self.supabase = None
            print("[Aviso] Supabase no configurado o URL pendiente en el .env.")

    def index_and_hash_binary(self):
        """Lee cualquier archivo binario por bloques, generando un SHA-256 por bloque."""
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"El archivo '{self.file_path}' no fue encontrado.")

        with open(self.file_path, "rb") as f:
            index = 0
            while True:
                chunk_data = f.read(self.chunk_size)
                if not chunk_data:
                    break
                
                chunk_hash = hashlib.sha256(chunk_data).hexdigest()
                self.indexed_chunks.append({
                    "index": index,
                    "offset": index * self.chunk_size,
                    "size_bytes": len(chunk_data),
                    "chunk_hash": chunk_hash
                })
                self.chunk_hashes.append(chunk_hash)
                index += 1
        return self.indexed_chunks

    def generate_root_hash(self):
        """Genera el Hash Raíz (Prueba Petrificada)."""
        combined_payload = "".join(self.chunk_hashes) + json.dumps(self.metadata, sort_keys=True) + self.timestamp
        self.root_hash = hashlib.sha256(combined_payload.encode('utf-8')).hexdigest()
        return self.root_hash

    def anchor_on_polygon(self):
        """Ancla el Root Hash en Polygon Amoy usando Gas Legacy para evitar rechazos por gas mínimo."""
        if not PRIVATE_KEY or not self.w3:
            print("[Advertencia] Faltan credenciales de Blockchain o RPC en el .env. Saltando anclaje on-chain.")
            return "SIMULATED_TX_HASH_0X..."

        try:
            account = self.w3.eth.account.from_key(PRIVATE_KEY)
            nonce = self.w3.eth.get_transaction_count(account.address)
            
            # Obtener el gas price actual de la red y sumarle un 20% de margen
            current_gas_price = self.w3.eth.gas_price
            adjusted_gas_price = int(current_gas_price * 1.2)

            tx = {
                'nonce': nonce,
                'to': account.address, 
                'value': 0,
                'gas': 100000,
                'gasPrice': adjusted_gas_price,
                'chainId': 80002, # Chain ID de Polygon Amoy
                'data': self.w3.to_hex(text=self.root_hash)
            }

            signed_tx = self.w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            return self.w3.to_hex(tx_hash)
        
        except Exception as e:
            print(f"[Error de Red Blockchain / Fondos insuficientes]: {e}")
            return "ERROR_TX_SIMULATED_FALLBACK"

    def save_to_supabase(self, manifest, tx_hash):
        """Registra el manifiesto y el hash de la transacción en Supabase."""
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
            response = self.supabase.table("axioma_evidencias").insert(data_to_insert).execute()
            print("[Supabase] Registro guardado exitosamente en la base de datos.")
            return response
        except Exception as e:
            print(f"[Error en Supabase (Verificá que la tabla 'axioma_evidencias' exista)]: {e}")

    def petrify_and_sync(self):
        """Ejecuta todo el pipeline: Indexación -> Hash -> Blockchain -> Supabase -> JSON."""
        self.index_and_hash_binary()
        root = self.generate_root_hash()
        
        print(f"[*] Root Hash generado: {root}")
        print("[*] Conectando y anclando en Polygon Amoy...")
        tx_hash = self.anchor_on_polygon()
        print(f"[*] Transacción Blockchain TX: {tx_hash}")

        manifest = {
            "ecosystem": "VERTEX AXIOMA",
            "protocol": "Protocolo AXIOMA®",
            "compliance_seal": "Sello de Inmutabilidad Transfronteriza",
            "timestamp_utc": self.timestamp,
            "target_file": os.path.basename(self.file_path),
            "total_chunks_indexed": len(self.indexed_chunks),
            "root_hash": root,
            "blockchain_tx": tx_hash,
            "metadata_caso": self.metadata
        }

        # Sincronizar con Supabase
        self.save_to_supabase(manifest, tx_hash)

        # Guardar manifiesto local en JSON
        output_filename = f"manifiesto_{os.path.basename(self.file_path)}.json"
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=4, ensure_ascii=False)
        
        print(f"[Éxito] Manifiesto exportado localmente a '{output_filename}'")
        return manifest

# ==========================================
# Bloque de Prueba y Ejecución Local
# ==========================================
if __name__ == "__main__":
    test_filename = "evidencia_forense_prueba.bin"
    
    with open(test_filename, "wb") as f:
        f.write(b"VERTEX AXIOMA - Protocolo de Prueba Petrificada con .env y Polygon Amoy" * 15)

    metadata_pericial = {
        "expediente_ref": "EXP-2026-AXIOMA-TEST-001",
        "jurisdiccion": "Laboratorio Forense Autónomo",
        "auditor": "Verónica Arapian"
    }

    try:
        print("--- INICIANDO MOTOR DE PETRIFICACIÓN AXIOMA ---")
        motor = AxiomaNetworkPetrification(test_filename, chunk_size=128, metadata=metadata_pericial)
        resultado = motor.petrify_and_sync()
        
        print("\n--- RESUMEN DEL MANIFIESTO EMITIDO ---")
        print(json.dumps(resultado, indent=4))

    finally:
        if os.path.exists(test_filename):
            os.remove(test_filename)