import socket
import json
import sys
import os
import errno
from datetime import datetime

# Importa il modulo di criptazione
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'DC'))
import crypto

# Percorsi
CONFIG_PATH = "DA/configurazione/parametri.conf"
DATA_PATH = "DA/dati/iotdata.dbt"

# Lettura parametri
try:
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
except Exception as e:
    print("Errore lettura parametri:", e)
    exit(1)

TEMPO_RILEVAZIONE = config["TEMPO_RILEVAZIONE"]
N_DECIMALI = config["N_DECIMALI"]
IDENTITA_GIOT = config["IDENTITA_GIOT"]
TEMPO_INVIO = config["TEMPO_INVIO"]
IP_SERVER = config["IP_SERVER"]
PORTA_SERVER = config["PORTA_SERVER"]

def crea_server():
    """Crea e avvia il server socket TCP/IPv4"""
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            server_socket.bind((IP_SERVER, PORTA_SERVER))
        except OSError as e:
            if getattr(e, 'errno', None) == errno.EADDRNOTAVAIL or 'Cannot assign requested address' in str(e):
                print(f"[DA] Indirizzo {IP_SERVER} non disponibile: {e}. Provo 0.0.0.0 come fallback.")
                server_socket.bind(('0.0.0.0', PORTA_SERVER))
            else:
                raise
        server_socket.listen(1)
        print(f"[DA] Server in ascolto su {IP_SERVER}:{PORTA_SERVER}\n")
        return server_socket
    except Exception as e:
        print(f"[DA] Errore nella creazione del server: {e}")
        sys.exit(1)

def accetta_client(server_socket):
    """Accetta connessione da un client DC e riceve i dati"""
    try:
        client_socket, address = server_socket.accept()
        print(f"[DA] Client connesso da {address}\n")
        
        # Invia TEMPO_RILEVAZIONE al client
        parametri = {"TEMPO_RILEVAZIONE": TEMPO_RILEVAZIONE}
        client_socket.sendall(json.dumps(parametri).encode('utf-8'))
        
        # Ricevi dati dal client
        while True:
            data = client_socket.recv(4096).decode('utf-8')
            if not data:
                break
            
            try:
                dato_iot = json.loads(data)
                identita = dato_iot['identita']
                
                # Mostra il dato ricevuto a schermo
                print(f"\n{'='*60}")
                print(f"[DA] DATO RICEVUTO DA {identita}")
                print(f"{'='*60}")
                print(json.dumps(dato_iot, indent=2))
                print(f"{'='*60}\n")
                
                # Salva il dato ricevuto in archivio
                with open(DATA_PATH, 'a') as f:
                    f.write(json.dumps(dato_iot) + '\n')
                
            except json.JSONDecodeError:
                print(f"[DA] Errore nel parsing JSON")
        
        client_socket.close()
        print(f"[DA] Client {address} disconnesso")
    except Exception as e:
        print(f"[DA] Errore nella ricezione: {e}")

def main():
    """Funzione principale"""
    server_socket = crea_server()
    print("DA avviato (CTRL+C per terminare)\n")
    
    try:
        while True:
            accetta_client(server_socket)
    except KeyboardInterrupt:
        print(f"\n[DA] Terminazione...")
        server_socket.close()

if __name__ == "__main__":
    main()