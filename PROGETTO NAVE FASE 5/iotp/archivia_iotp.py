import json
from pathlib import Path
import paho.mqtt.client as mqtt
import cripto

# Percorso del file iotp.json per la configurazione del gateway
BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "iotp.json"

#Lettura del file iotp.json
with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = json.load(f)

# Estrazione dei parametri dal file iotp.json
TOPIC = config["topic"]
BROKER = config["broker"]["host"]
PORTA = int(config["broker"]["porta"])
DBFILE = BASE_DIR / config["dbfile"]["file"]
MODO = config["dbfile"]["modo"]

# Funzione 
def on_connect(client, userdata, flags, rc):
    # Se la connessione è riuscita, rc sarà 0 e 
    if rc == 0:
        print("Connesso al broker MQTT")
        print(f"Sottoscritto al topic: {TOPIC}")
        # Sottoscrizione al topic specificato nel file di configurazione
        client.subscribe(TOPIC)
    # Se la connessione fallisce, rc sarà diverso da 0 e stampiamo un messaggio di errore    
    else:
        print(f"Errore connessione MQTT, codice: {rc}")


def on_message(client, userdata, msg):
    try:
        # Prende il payload del messaggio ricevuto e lo traduce in stringa
        payload_criptato = msg.payload.decode("utf-8")
        # Decriptazione del payload ricevuto con salvataggio del file 
        payload_decriptato = cripto.decriptazione(payload_criptato)
        dato = json.loads(payload_decriptato)

        print("Dato ricevuto da iotgwda.py e decriptato:")
        
        # Stampa il contenuto del payload 
        print(json.dumps(dato, indent=4, ensure_ascii=False))

        # Apre il file dbplatform.json in modalità append e salva il dato ricevuto, tutto questo è presente in iotp.json
        with open(DBFILE, MODO, encoding="utf-8") as f:
            f.write(json.dumps(dato, ensure_ascii=False) + "\n")

    except Exception as e:
        print("Errore nella ricezione o archiviazione:", e)


def main():
    
    # Creazione del client MQTT 
    client = mqtt.Client()
    
    # Assegna le funzioni di callback per la connessione e la ricezione dei messaggi
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"Connessione a broker {BROKER}:{PORTA} ...")
    client.connect(BROKER, PORTA, 60)
    # Avvia il loop del client MQTT per gestire la connessione e la ricezione dei messaggi
    client.loop_forever()


if __name__ == "__main__":
    try:
        main()
        # Se si preme Ctrl+C, il programma si fermerà e stamperà un messaggio 
    except KeyboardInterrupt:
        print("\nSpegnimento manuale del Gateway in corso.")