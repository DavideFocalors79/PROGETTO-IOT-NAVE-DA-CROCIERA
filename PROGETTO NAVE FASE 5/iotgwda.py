import json
import socket
import paho.mqtt.client as mqtt
from pathlib import Path
import cripto
import threading

# Configurazione percorsi file
BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "configurazione"
PARAMETRI_FILE = CONFIG_DIR / "parametri.json"

# Funzione ausiliaria per ricevere una riga di testo dal socket
# Legge byte per byte fino a trovare il newline
def recv_line(sock):
    data = bytearray()
    while True:
        chunk = sock.recv(1)
        # Se non arriva nulla, significa che la connessione è stata chiusa
        if not chunk:
            return ""
        # Se trovo il newline, significa che ho ricevuto una riga completa
        if chunk == b"\n":
            break
        data.extend(chunk)
    # Converte i byte ricevuti in stringa 
    return data.decode("utf-8", errors="replace").strip()

# Funzione che gestisce la comunicazione con un singolo sensore
# Viene eseguita in un thread separato per gestire più sensori contemporaneamente
# Funzione che gestisce la comunicazione con un singolo sensore
# Viene eseguita in un thread separato per gestire più sensori contemporaneamente
def gestisci_client(conn, addr, parametri, client_mqtt):
    print(f"\n[+] Nuovo sensore connesso da: {addr}")
    
    # Estrazione dei parametri di configurazione dal file parametri.json
    TEMPO_RILEVAZIONE = parametri["TEMPO_RILEVAZIONE"]
    N_DECIMALI = parametri["N_DECIMALI"]
    IDENTITA_GIOT = parametri["IDENTITA_GIOT"]
    TOPIC = parametri["TOPIC"]

    with conn:
        # Invio configurazione iniziale al sensore 
        parametri_init = {
            "TEMPO_RILEVAZIONE": TEMPO_RILEVAZIONE,
            "N_DECIMALI": N_DECIMALI
        }
        try:
            conn.sendall((json.dumps(parametri_init) + "\n").encode("utf-8"))
        except:
            print(f" Errore nell'invio dei parametri a {addr}")
            return
        
        while True:
            try:
                # Ricezione dei dati client 
                line = recv_line(conn)
                if not line:
                    break  # Se il client chiude la connessione, esce dal loop
                
                # Conversione del dato json ricevuto in un dizionario Python
                dato_dc = json.loads(line)
                print(f"[{addr[1]}] DatoIoT ricevuto:", json.dumps(dato_dc))
                
                
                # Conversione del dato ricevuto in formato iotp 
                dato_iotp = {
                    "cabina": dato_dc["camera"],
                    "ponte": dato_dc["ponte"],
                    "temperaturam": round(dato_dc["osservazione"]["temperatura"], N_DECIMALI),
                    "umiditam": round(dato_dc["osservazione"]["umidita"], N_DECIMALI),
                    "dataeora": dato_dc["osservazione"]["dataeora"],
                    "invionumero": dato_dc["osservazione"]["rilevazione"],
                    "identita": IDENTITA_GIOT
                }
                
                # Criptazione del payload e lo stampa prima di inviarlo al broker MQTT
                payload_criptato = cripto.criptazione(json.dumps(dato_iotp))
                print(f"[{addr[1]}] Gateway in invio (MQTT):", payload_criptato)
                
                # Invio del payload criptato al broker MQTT 
                client_mqtt.publish(TOPIC, payload_criptato)
                
            except Exception as e:
                print(f"Errore di comunicazione con {addr}: {e}")
                break
                
    print(f"Sensore {addr} disconnesso.")

def main():
    # Lettura della configurazione dal file parametri.json
    with open(PARAMETRI_FILE, "r", encoding="utf-8") as f:
        parametri = json.load(f)

    # Estrazione parametri di connessione
    IP_SERVER = parametri["IP_SERVER"]
    PORTA_SERVER = int(parametri["PORTA_SERVER"])
    BROKER = parametri["BROKER"]
    PORTA_BROKER = int(parametri["PORTA_BROKER"])

    # Creazione del client MQTT e connessione al broker
    client = mqtt.Client()
    client.connect(BROKER, PORTA_BROKER, 60)
    client.loop_start()


    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        # Permette al socket di riutilizzare la porta se è ancora in TIME_WAIT
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Bind del server all'indirizzo e porta specificati
        server.bind((IP_SERVER, PORTA_SERVER))
        
        # Mette il server in ascolto per connessioni in ingresso
        server.listen()
        
        # Timeout di 1 secondo per permettere di interrompere con Ctrl+C
        server.settimeout(1.0)
        
        print(f"Gateway IoT in attesa di dati su {IP_SERVER}:{PORTA_SERVER}...")
        
        try:
            while True:
                try:
                    # Accetta una nuova connessione (timeout dopo 1 secondo)
                    conn, addr = server.accept()
                    
                    # Crea un nuovo thread per gestire questo sensore
                    # (così possiamo gestire più sensori contemporaneamente)
                    thread_client = threading.Thread(target=gestisci_client, args=(conn, addr, parametri, client))
                    
                    # Imposta il thread come daemon (si chiude quando il programma principale termina)
                    thread_client.daemon = True 
                    
                    # Avvia il thread
                    thread_client.start()
                    
                except socket.timeout:
                    pass 
                    
        except KeyboardInterrupt:
            print("\n Spegnimento manuale del Gateway in corso.")

if __name__ == "__main__":
    main()
