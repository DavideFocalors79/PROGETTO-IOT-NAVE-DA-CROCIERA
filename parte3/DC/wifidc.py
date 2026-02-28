import network
import json
import time

def connetti_wifi():
    # Carica credenziali da wifipico.json 
    with open('wifipico.json', 'r') as f:
        config = json.load(f)
    
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print(f"Connessione a {config['ssid']}...")
        wlan.connect(config['ssid'], config['pw'])
        while not wlan.isconnected():
            time.sleep(1)
    
    print("Connesso! IP:", wlan.ifconfig()[0])
    return wlan.ifconfig()[0]