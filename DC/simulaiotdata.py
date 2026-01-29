import socket
import json
import time
import sys
import os
from collections import defaultdict
from datetime import datetime
import socket
import json
import time
import sys
import os
import random
from datetime import datetime

# Importa moduli locali
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'DA'))
import misurazione

# Percorso configurazione DA (contiene parametri condivisi)
CONFIG_PATH = "DA/configurazione/parametri.conf"

# Lettura parametri
try:
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
except Exception as e:
    print("Errore lettura parametri:", e)
    exit(1)

N_DECIMALI = config.get("N_DECIMALI", 2)
IDENTITA_GIOT = config.get("IDENTITA_GIOT", "GIOT-001")
IP_SERVER = config.get("IP_SERVER", "127.0.0.1")
PORTA_SERVER = config.get("PORTA_SERVER", 9999)
N_CABINE = config.get("N_CABINE", 1)
N_PONTI = config.get("N_PONTI", 1)

def crea_client():
    """Crea un client TCP e si connette al DA server"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((IP_SERVER, PORTA_SERVER))
        print(f"[DC] Connesso a {IP_SERVER}:{PORTA_SERVER}")
        return s
    except Exception as e:
        print(f"[DC] Errore nella connessione a {IP_SERVER}:{PORTA_SERVER}: {e}. Provo 127.0.0.1 come fallback.")
        try:
            s.connect(('127.0.0.1', PORTA_SERVER))
            print(f"[DC] Connesso a 127.0.0.1:{PORTA_SERVER}")
            return s
        except Exception as e2:
            print(f"[DC] Errore anche con 127.0.0.1: {e2}")
            s.close()
            raise

def ricevi_parametri(sock):
    """Riceve parametri iniziali inviati dal DA (es. TEMPO_RILEVAZIONE)"""
    try:
        data = sock.recv(4096).decode('utf-8')
        if not data:
            raise RuntimeError("Nessun dato ricevuto dal server")
        params = json.loads(data)
        return params
    except Exception as e:
        print(f"[DC] Errore ricezione parametri: {e}")
        raise

def genera_dato(rilevazione_num):
    """Genera un DatoIoT conforme alle specifiche del progetto"""
    cabina = random.randint(1, max(1, N_CABINE))
    ponte = random.randint(1, max(1, N_PONTI))

    sensore = {
        "nome": "DHT11",
        "tmin": 0,
        "tmax": 40,
        "umin": 20,
        "umax": 90,
        "erroret": 2,
        "erroreu": 4
    }

    temperatura = misurazione.rileva_temperatura(decimali=N_DECIMALI)
    umidita = misurazione.rileva_umidita(decimali=N_DECIMALI)

    dato = {
        "cabina": cabina,
        "ponte": ponte,
        "sensore": sensore,
        "identita": socket.gethostname(),
        "osservazione": {
            "rilevazione": rilevazione_num,
            "temperatura": temperatura,
            "umidita": umidita
        }
    }

    return dato

def main():
    """Loop principale: connessione, ricezione parametri e invio dati periodici"""
    try:
        sock = crea_client()
    except Exception:
        return

    try:
        params = ricevi_parametri(sock)
        tempo_rilevazione = params.get("TEMPO_RILEVAZIONE", 5)
        print(f"[DC] TEMPO_RILEVAZIONE ricevuto: {tempo_rilevazione} s")

        contatore = 1
        print("[DC] Avvio invio dati (CTRL+C per terminare)")
        while True:
            dato = genera_dato(contatore)
            payload = json.dumps(dato)
            try:
                sock.sendall(payload.encode('utf-8'))
                print(f"[DC] Inviato rilevazione #{contatore}: cabina {dato['cabina']} ponte {dato['ponte']}")
            except Exception as e:
                print(f"[DC] Errore invio dato: {e}")
                break

            contatore += 1
            time.sleep(tempo_rilevazione)

    except KeyboardInterrupt:
        print("\n[DC] Terminazione richiesta dall'utente")
    except Exception as e:
        print(f"[DC] Errore: {e}")
    finally:
        try:
            sock.close()
        except Exception:
            pass

if __name__ == "__main__":
    main()
