import json
import time
import random
import os
from misurazione import rileva_temperatura, rileva_umidita

# Percorsi
CONFIG_PATH = "configurazione/parametri.conf"
DATA_PATH = "dati/iotdata.dbt"

# Lettura parametri
try:
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
except Exception as e:
    print("Errore lettura parametri:", e)
    exit(1)

TEMPO_RILEVAZIONE = config["TEMPO_RILEVAZIONE"]
N_DECIMALI = config["N_DECIMALI"]
N_CABINE = config["N_CABINE"]
N_PONTI = config["N_PONTI"]

rilevazioni = 0
somma_temp = 0
somma_umid = 0

print("Simulazione avviata (CTRL+C per terminare)\n")

try:
    while True:
        rilevazioni += 1

        cabina = random.randint(1, N_CABINE)
        ponte = random.randint(1, N_PONTI)

        temperatura = rileva_temperatura(decimali=N_DECIMALI)
        umidita = rileva_umidita(decimali=N_DECIMALI)

        timestamp = time.time()

        dato_iot = {
            "cabina": cabina,
            "ponte": ponte,
            "rilevazione": rilevazioni,
            "dataeora": timestamp,
            "temperatura": temperatura,
            "umidita": umidita
        }

        # Statistiche
        somma_temp += temperatura
        somma_umid += umidita

        # Visualizzazione
        print(json.dumps(dato_iot, indent=4))

        # Scrittura su file
        with open(DATA_PATH, "a") as f:
            f.write(json.dumps(dato_iot, indent=4))
            f.write("\n\n")

        time.sleep(TEMPO_RILEVAZIONE)

except KeyboardInterrupt:
    print("\n--- TERMINAZIONE ---")
    print("Numero rilevazioni:", rilevazioni)
    print(
        "Temperatura media:",
        round(somma_temp / rilevazioni, N_DECIMALI)
    )
    print(
        "Umidità media:",
        round(somma_umid / rilevazioni, N_DECIMALI)
    )
