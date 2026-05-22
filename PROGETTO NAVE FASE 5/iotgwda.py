import json
import socket
import threading
from pathlib import Path
import paho.mqtt.client as mqtt
import cripto  # Importiamo il modulo di criptazione per HiveMQ

BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "configurazione"
PARAMETRI_FILE = CONFIG_DIR / "parametri.json"

def recv_line(sock):
    data = bytearray()
    while True:
        try:
            chunk = sock.recv(1)
            if not chunk:
                return ""
            if chunk == b"\n":
                break
            data.extend(chunk)
        except OSError:
            return ""
    return data.decode("utf-8", errors="replace").strip()

def build_telemetry(dato_dc, identita_giot, n_decimali):
    osservazione = dato_dc["osservazione"]
    sensore = dato_dc.get("sensore", {})
    return {
        "temperature": round(osservazione["temperatura"], n_decimali),
        "humidity": round(osservazione["umidita"], n_decimali),
        "cabin": dato_dc["camera"],
        "deck": dato_dc["ponte"],
        "ship": identita_giot,
        "deviceId": dato_dc["identita"],
        "sensorName": sensore.get("nome", "DHT11"),
        "tMin": sensore.get("tmin", 0),
        "tMax": sensore.get("tmax", 40)
    }

def gestisci_client(conn, addr, parametri, client_tb, client_hive):
    print(f"[SOCKET] Connessione accettata da {addr}")
    n_decimali = int(parametri["N_DECIMALI"])
    identita_giot = parametri["IDENTITA_GIOT"]
    
    # Invio dei parametri iniziali al DC (Client)
    init_payload = {
        "TEMPO_RILEVAZIONE": parametri["TEMPO_RILEVAZIONE"],
        "N_DECIMALI": n_decimali
    }
    try:
        conn.sendall((json.dumps(init_payload) + "\n").encode("utf-8"))
    except OSError:
        conn.close()
        return

    while True:
        line = recv_line(conn)
        if not line:
            print(f"[SOCKET] Connessione chiusa da {addr}")
            break
        
        try:
            dato_dc = json.loads(line)
            osservazione = dato_dc["osservazione"]
            
            # --- 1. INVIO A THINGSBOARD (In chiaro) ---
            telemetria_tb = build_telemetry(dato_dc, identita_giot, n_decimali)
            payload_tb = json.dumps(telemetria_tb)
            res_tb = client_tb.publish(parametri["TOPIC_TB"], payload_tb)
            if res_tb.rc != 0:
                print(f"[TB ERROR] Errore publish ThingsBoard: codice {res_tb.rc}")
            else:
                print("[TB SUCCESS] Dati inviati alla Dashboard di ThingsBoard")

            # --- 2. INVIO A HIVEMQ / ARCHIVIA (Criptato) ---
            dati_archivia = {
                "cabina": dato_dc["camera"],
                "ponte": dato_dc["ponte"],
                "temperaturam": round(osservazione["temperatura"], n_decimali),
                "umiditam": round(osservazione["umidita"], n_decimali),
                "dataeora": osservazione["dataeora"],
                "invionumero": osservazione["rilevazione"],
                "identita": identita_giot
            }
            payload_json = json.dumps(dati_archivia, ensure_ascii=False)
            payload_criptato = cripto.criptazione(payload_json)
            
            res_hive = client_hive.publish(parametri["TOPIC_HIVEMQ"], payload_criptato)
            if res_hive.rc != 0:
                print(f"[HIVEMQ ERROR] Errore publish HiveMQ: codice {res_hive.rc}")
            else:
                print("[HIVEMQ SUCCESS] Dati criptati inviati a HiveMQ per l'archiviazione")

        except Exception as e:
            print(f"Errore elaborazione dati: {e}")
            break

    conn.close()

def main():
    with open(PARAMETRI_FILE, "r", encoding="utf-8") as f:
        parametri = json.load(f)

    ip_server = parametri["IP_SERVER"]
    porta_server = int(parametri["PORTA_SERVER"])
    porta_broker = int(parametri["PORTA_BROKER"])

    # Configurazione Client 1: ThingsBoard
    client_tb = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    client_tb.username_pw_set(parametri["TOKEN_TB"])
    
    # Configurazione Client 2: HiveMQ
    client_hive = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)

    try:
        print("Connessione ai Broker MQTT...")
        client_tb.connect(parametri["BROKER_TB"], porta_broker, 60)
        client_tb.loop_start()
        print(f"-> Connesso a ThingsBoard ({parametri['BROKER_TB']})")

        client_hive.connect(parametri["BROKER_HIVEMQ"], porta_broker, 60)
        client_hive.loop_start()
        print(f"-> Connesso a HiveMQ ({parametri['BROKER_HIVEMQ']})")
    except Exception as e:
        print(f"Errore critico durante la connessione MQTT: {e}")
        return

    # Avvio del Server Socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((ip_server, porta_server))
        server.listen()
        server.settimeout(1.0)

        print(f"\nGateway IoT attivo! In attesa di connessioni socket su {ip_server}:{porta_server}...\n")

        try:
            while True:
                try:
                    conn, addr = server.accept()
                    thread_client = threading.Thread(
                        target=gestisci_client,
                        args=(conn, addr, parametri, client_tb, client_hive),
                        daemon=True
                    )
                    thread_client.start()
                except socket.timeout:
                    pass
        except KeyboardInterrupt:
            print("\nSpegnimento del Gateway in corso...")
        finally:
            client_tb.loop_stop()
            client_tb.disconnect()
            client_hive.loop_stop()
            client_hive.disconnect()

if __name__ == "__main__":
    main()