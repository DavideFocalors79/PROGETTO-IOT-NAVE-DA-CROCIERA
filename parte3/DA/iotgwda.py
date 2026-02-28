import socket
import json
import time
import os
from datetime import datetime
import cripta # Modulo locale 

# Carica parametri 
with open('configurazione/parametri.json', 'r') as f:
    config = json.load(f)

def calcola_media(lista):
    return round(sum(lista) / len(lista), config["N_DECIMALI"])

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((config["IP_SERVER"], config["PORTA_SERVER"]))
    server.listen(1)
    
    print(f"DA in ascolto su {config['IP_SERVER']}...")
    
    conn, addr = server.accept()
    # Invia tempo rilevazione al DC 
    conn.send(json.dumps({"TEMPO_RILEVAZIONE": config["TEMPO_RILEVAZIONE"]}).encode('utf-8'))

    rilevazioni_temp = []
    rilevazioni_umid = []
    invio_numero = 1
    totale_ricevuti = 0

    try:
        while True:
            data = conn.recv(4096).decode('utf-8')
            if not data: break
            
            dato_dc = json.loads(data)
            totale_ricevuti += 1
            obs = dato_dc["osservazione"]
            rilevazioni_temp.append(obs["temperatura"])
            rilevazioni_umid.append(obs["umidita"])

            # Ogni TEMPO_INVIO (numero di rilevazioni), invia alla piattaforma
            if len(rilevazioni_temp) >= config["TEMPO_INVIO"]:
                payload_da = {
                    "camera": dato_dc["camera"],
                    "ponte": dato_dc["ponte"],
                    "temperaturam": calcola_media(rilevazioni_temp),
                    "umiditam": calcola_media(rilevazioni_umid),
                    "dataeora": int(time.time()),
                    "invionumero": invio_numero,
                    "identita": config["IDENTITA_GIOT"]
                }
                
                # Criptazione (simulata) 
                dato_criptato = cripta.criptazione(json.dumps(payload_da))
                print(f"Invio alla piattaforma: {dato_criptato}")

                # Salva su db.json 
                with open('iotp/db.json', 'a') as f:
                    f.write(json.dumps(payload_da) + "\n")
                
                # Reset per prossima media
                rilevazioni_temp = []
                rilevazioni_umid = []
                invio_numero += 1

    except KeyboardInterrupt:
        print(f"\nFine. Rilevazioni totali inviate: {invio_numero - 1}") 
        conn.close()

if __name__ == "__main__":
    main()
