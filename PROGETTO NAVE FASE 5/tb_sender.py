import socket
import json
import paho.mqtt.client as mqtt
import time
import cripto  # Assicurati che cripto.py sia nella stessa cartella

# --- CONFIGURAZIONE THINGSBOARD (MQTT) ---
TOKEN = "Wq6DY3KiyIqMaOizBil7"
THINGSBOARD_HOST = "thingsboard.cloud"
MQTT_PORT = 1883
MQTT_TOPIC = "v1/devices/me/telemetry"

# --- CONFIGURAZIONE SERVER DA (SOCKET TCP) ---
IP_DA = "0.0.0.0" # Ascolta su tutte le interfacce
PORTA_DA = 9090   # La stessa porta che usa il DC per connettersi

def main():
    # 1. Inizializzazione Client MQTT per ThingsBoard
    client_mqtt = mqtt.Client()
    client_mqtt.username_pw_set(TOKEN)
    
    try:
        client_mqtt.connect(THINGSBOARD_HOST, MQTT_PORT, 60)
        client_mqtt.loop_start()
        print(f"Connesso a ThingsBoard via MQTT.")
    except Exception as e:
        print(f"Errore connessione ThingsBoard: {e}")
        return

    # 2. Inizializzazione Server Socket TCP per ricevere dai DC
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((IP_DA, PORTA_DA))
    server_socket.listen(5)
    
    print(f"DA in ascolto per i dati dai DC su porta {PORTA_DA}...")

    try:
        while True:
            conn, addr = server_socket.accept()
            print(f"\nRicevuta connessione da DC: {addr}")
            
            with conn:
                data = conn.recv(1024).decode('utf-8')
                if data:
                    print(f"Dato criptato ricevuto: {data}")
                    
                    # 3. Decriptazione e parsing
                    try:
                        # Se il DC manda dati criptati (es. con asterischi come nel tuo file cripto.py)
                        data_decriptata = cripto.decriptazione(data)
                        payload = json.loads(data_decriptata)
                        
                        print(f"Dato decriptato: {payload}")

                        # 4. Inoltro a ThingsBoard via MQTT
                        # Inviamo solo i valori di telemetria
                        telemetria = {
                            "temperature": payload.get("temperatura"),
                            "humidity": payload.get("umidita"),
                            "cabin": payload.get("cabina"),
                            "deck": payload.get("ponte")
                        }
                        
                        client_mqtt.publish(MQTT_TOPIC, json.dumps(telemetria), qos=1)
                        print(f"Inviato a ThingsBoard: {telemetria}")

                    except Exception as e:
                        print(f"Errore processamento dati: {e}")
                        
    except KeyboardInterrupt:
        print("\nChiusura DA...")
    finally:
        client_mqtt.loop_stop()
        server_socket.close()

if __name__ == "__main__":
    main()
    