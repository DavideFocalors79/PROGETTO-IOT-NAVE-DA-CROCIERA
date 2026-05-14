from pathlib import Path
import socket
import time
import sys
import json
import wifidc
import misurazione

# Perorso della cartella configurazione 
BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "configurazione"

#percorso dei file da.json e configurazionedc.json che si trovano nella cartella configurazione
DA_FILE = CONFIG_DIR / "da.json"
CONFIG_FILE = CONFIG_DIR / "configurazionedc.json"

def recv_line(sock) -> str:
    # Buffer dove accumulo i byte ricevuti
    data = bytearray()
    # Legge un byte alla volta fino a trovare il carattere newline
    while True:
        chunk = sock.recv(1)
        # Se non arriva nulla, la connessione è stata chiusa
        if not chunk:
            raise OSError("Connessione chiusa dal server")
        # Se trovo il terminatore di riga, esco dal ciclo
        if chunk == b"\n":
            break
        # Accumulo il byte ricevuto
        data.extend(chunk)
    # Converte i byte in stringa UTF-8 e rimuove spazi/newline finali
    return data.decode("utf-8", errors="replace").strip()

def connetti_socket(ip, porta, retry=5):
    # Tenta la connessione al server per 5 volte in caso di errori, con una pausa di 2 secondi tra i tentativi
    for i in range(retry):
        try:
            # Crea un socket TCP/IP IPv4
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Prova a connettersi all'indirizzo e porta del server
            s.connect((ip, porta))
            # Se la connessione riesce, restituisce il socket aperto
            return s
        except OSError as e:
            print("Connessione fallita (" + str(i+1) + "/" + str(retry) + "): " + str(e))
            
            # Se la connessione fallisce, chiude il socket se è stato creato
            try:
                s.close()
            except:
                pass
            # Attende 2 secondi prima di ritentare la connessione
            time.sleep(2)
            
    # Se dopo 5 tentativi la connessione non riesce, stampa un messaggio di errore 
    raise OSError("Impossibile connettersi al server")

def main():
    # Connessione del Raspberry Pico alla rete WiFi
    wlan = wifidc.connetti_wifi()
    time.sleep(1)
    
    # Stampa delle informazioni di rete ottenute
    wifidc.Info_WiFi(wlan)
    
    # Apertura del file da.json per ottenere l'indirizzo IP e la porta del server
    with open(DA_FILE, "r") as f:
        da = json.load(f)

    ip_server = da["IP"]
    porta_server = int(da["porta"])
    
    # Apertura del file configurazionedc.json per ottenere i parametri di configurazione del sensore
    with open(CONFIG_FILE, "r") as f:
        cfg = json.load(f)

    # Lettura del pin di segnale del sensore
    pin = int(cfg["cablaggio"]["segnale"])
    # Lettura dei limiti di temperatura e umidità del sensore
    tmin = cfg["sensore"]["tmin"]
    tmax = cfg["sensore"]["tmax"]
    umin = cfg["sensore"]["umin"]
    umax = cfg["sensore"]["umax"]
    # Connessione alla socket con ip e porta del server ottenuti da da.json
    sock = connetti_socket(ip_server, porta_server)
    
    # Ricezione della configurazione dal server
    init_str = recv_line(sock)
    init = json.loads(init_str)

    # Estrazione dei parametri di configurazione ricevuti dal server
    tempo_rilevazione = int(init["TEMPO_RILEVAZIONE"])
    n_decimali = int(init["N_DECIMALI"])

    seriale = 0
    
    # Ciclo infinito di acquisizione e invio dati
    while True:
        seriale += 1
        # Lettura della temperatura 
        temperatura = misurazione.on_temperatura(pin, n_decimali, tmin, tmax)
        # Lettura dell'umidità 
        umidita = misurazione.on_umidita(pin, n_decimali, umin, umax)
        # Timestamp corrente della rilevazione
        dataeora = int(time.time())
        dato_iot = {
            "camera": cfg["camera"],
            "ponte": cfg["ponte"],
            "sensore": cfg["sensore"],
            "identita": cfg["identita"],
            "osservazione": {
                "rilevazione": seriale,
                "dataeora": dataeora,
                "temperatura": temperatura,
                "umidita": umidita
            }
        }
        payload = json.dumps(dato_iot, separators=(",", ":"), ensure_ascii=False) + "\n"

        try:
            # Invio del payload al server
            sock.send(payload.encode("utf-8"))
        except OSError as e:
            # Se l'invio fallisce, stampa un messaggio di errore e tenta di riconnettersi al server
            print("Invio fallito: " + str(e) + ", riconnessione socket...")
            try:
                sock.close()
            except:
                pass
            sock = connetti_socket(ip_server, porta_server)
            continue
        # Stampa del payload inviato al server
        print(payload)
        
        # Attesa del tempo di rilevazione prima di acquisire e inviare il prossimo dato
        time.sleep(tempo_rilevazione)

if __name__ == "__main__":
    try:
        main()
    # Se si preme Ctrl+C, il programma si fermerà     
    except KeyboardInterrupt:
        print("\nSpegnimento del progamma.")
        sys.exit(0)