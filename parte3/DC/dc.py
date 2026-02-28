import socket
import json
import time
from machine import Pin
import wifidc
import misurazione

# Configurazione LED interno
led = Pin("LED", Pin.OUT)

def main():
    # 1. Connessione WiFi 
    wifidc.connetti_wifi()

    # 2. Carica parametri del Server DA 
    with open('da.json', 'r') as f:
        da_conf = json.load(f)

    # 3. Connessione Socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((da_conf['IP'], da_conf['porta']))

    # 4. Ricezione TEMPO_RILEVAZIONE dal server 
    data = s.recv(1024).decode('utf-8')
    params = json.loads(data)
    tempo_rif = params.get("TEMPO_RILEVAZIONE", 5)

    rilevazione_id = 1
    try:
        while True:
            led.on() # Accendi LED durante trasmissione 
            
            temp, umid, conf_dc = misurazione.leggi_dati_sensore()
            
            # Costruzione payload JSON richiesto 
            payload = {
                "camera": conf_dc["camera"],
                "ponte": conf_dc["ponte"],
                "sensore": conf_dc["sensore"],
                "identita": conf_dc["identita"],
                "osservazione": {
                    "rilevazione": rilevazione_id,
                    "temperatura": temp,
                    "umidita": umid
                }
            }
            
            s.send(json.dumps(payload).encode('utf-8'))
            print(f"Inviata rilevazione {rilevazione_id}")
            
            led.off()
            rilevazione_id += 1
            time.sleep(tempo_rif)
            
    except KeyboardInterrupt:
        s.close()

if __name__ == "__main__":
    main()
