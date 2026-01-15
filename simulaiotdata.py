# Simulazione DA / GIOT
# Raccolta dati IoT da sensori simulati
#
# Script: simulaiotdata.py

import json
import time
import random
import os
import misurazione

# Percorsi
PATH_CONFIG = "configurazione/parametri.conf"
PATH_DATI = "dati/iotdata.dbt"

# Lettura parametri di configurazione
with open(PATH_CONFIG, "r") as file:
    parametri = json.load(file)

TEMPO_RILEVAZIONE = parametri["TEMPO_RILEVAZIONE"]
N_DECIMALI = parametri["N_DECIMALI"]
N_CABINE = parametri["N_CABINE"]
N_PONTI = parametri["N_PONTI"]

# Inizializzazione
contatore = 0
somma_temp = 0.0
somma_umid = 0.0

os.makedirs("dati", exist_ok=True)

try:
    while True:
        contatore += 1

        cabina = random.randint(1, N_CABINE)
        ponte = random.randint(1, N_PONTI)

        temperatura = misurazione.on_temperatura(N_DECIMALI)
        umidita = misurazione.on_umidita(N_DECIMALI)

        timestamp = time.time()

        dato_iot = {
            "cabina": cabina,
            "ponte": ponte,
            "rilevazione": contatore,
            "dataeora": timestamp,
            "temperatura": temperatura,
            "umidita": umidita
        }

        print(json.dumps(dato_iot, indent=4))

        with open(PATH_DATI, "a") as archivio:
            archivio.write(json.dumps(dato_iot, indent=4))
            archivio.write("\n\n")

        somma_temp += temperatura
        somma_umid += umidita

        time.sleep(TEMPO_RILEVAZIONE)

except KeyboardInterrupt:
    if contatore > 0:
        media_temp = round(somma_temp / contatore, N_DECIMALI)
        media_umid = round(somma_umid / contatore, N_DECIMALI)
    else:
        media_temp = 0
        media_umid = 0

    print("\n--- FINE RILEVAZIONE ---")
    print("Numero rilevazioni:", contatore)
    print("Temperatura media:", media_temp)
    print("Umidità media:", media_umid)
