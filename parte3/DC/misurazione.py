import random
import json

def leggi_dati_sensore():
    # Carica configurazione cablaggio e limiti 
    with open('configurazionedc.json', 'r') as f:
        conf = json.load(f)
    
    # Simulazione lettura basata sui limiti del sensore nel JSON
    s = conf['sensore']
    t = round(random.uniform(s['tmin'], s['tmax']), 2)
    u = round(random.uniform(s['umin'], s['umax']), 2)
    
    return t, u, conf
