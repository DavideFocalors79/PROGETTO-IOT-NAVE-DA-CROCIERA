import json
import socket
import threading
from pathlib import Path

import paho.mqtt.client as mqtt

BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "configurazione"
PARAMETRI_FILE = CONFIG_DIR / "parametri.json"


def recv_line(sock):
    data = bytearray()
    while True:
        chunk = sock.recv(1)
        if not chunk:
            return ""
        if chunk == b"\n":
            break
        data.extend(chunk)
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
        "tMax": sensore.get("tmax", 50),
        "uMin": sensore.get("umin", 0),
        "uMax": sensore.get("umax", 100),
        "serialNumber": osservazione["rilevazione"]
    }


def publish_telemetry(client, telemetry, ts=None):
    if ts is None:
        payload = telemetry
    else:
        payload = {
            "ts": ts * 1000,
            "values": telemetry
        }

    result = client.publish(
        "v1/devices/me/telemetry",
        json.dumps(payload, ensure_ascii=False),
        qos=1
    )
    return result


def gestisci_client(conn, addr, parametri, client_mqtt):
    print(f"\n[+] Nuovo dispositivo connesso da: {addr}")

    tempo_rilevazione = int(parametri["TEMPO_RILEVAZIONE"])
    n_decimali = int(parametri["N_DECIMALI"])
    identita_giot = parametri["IDENTITA_GIOT"]

    with conn:
        parametri_init = {
            "TEMPO_RILEVAZIONE": tempo_rilevazione,
            "N_DECIMALI": n_decimali
        }

        try:
            conn.sendall((json.dumps(parametri_init) + "\n").encode("utf-8"))
        except OSError as e:
            print(f"Errore nell'invio dei parametri iniziali a {addr}: {e}")
            return

        while True:
            try:
                line = recv_line(conn)
                if not line:
                    break

                dato_dc = json.loads(line)

                print(f"[{addr[1]}] Dato ricevuto da dc.py:")
                print(json.dumps(dato_dc, indent=4, ensure_ascii=False))

                timestamp = int(dato_dc["osservazione"]["dataeora"])
                telemetry = build_telemetry(dato_dc, identita_giot, n_decimali)

                print(f"[{addr[1]}] Telemetria inviata a ThingsBoard:")
                print(json.dumps(telemetry, indent=4, ensure_ascii=False))

                result = publish_telemetry(client_mqtt, telemetry, timestamp)

                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    print(f"[{addr[1]}] Invio MQTT a ThingsBoard completato")
                else:
                    print(f"[{addr[1]}] Errore publish MQTT: codice {result.rc}")

            except json.JSONDecodeError as e:
                print(f"[{addr[1]}] JSON non valido ricevuto dal client: {e}")
            except Exception as e:
                print(f"[{addr[1]}] Errore di comunicazione con il client: {e}")
                break

    print(f"[-] Dispositivo {addr} disconnesso")


def main():
    with open(PARAMETRI_FILE, "r", encoding="utf-8") as f:
        parametri = json.load(f)

    ip_server = parametri["IP_SERVER"]
    porta_server = int(parametri["PORTA_SERVER"])
    broker = parametri["BROKER"]
    porta_broker = int(parametri["PORTA_BROKER"])
    token_tb = parametri["TOKEN_TB"]

    client = mqtt.Client()
    client.username_pw_set(token_tb)

    try:
        client.connect(broker, porta_broker, 60)
        client.loop_start()
        print(f"Connesso a ThingsBoard MQTT su {broker}:{porta_broker}")
    except Exception as e:
        print(f"Errore connessione MQTT a ThingsBoard: {e}")
        return

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((ip_server, porta_server))
        server.listen()
        server.settimeout(1.0)

        print(f"Gateway IoT in attesa di dati su {ip_server}:{porta_server}...")

        try:
            while True:
                try:
                    conn, addr = server.accept()
                    thread_client = threading.Thread(
                        target=gestisci_client,
                        args=(conn, addr, parametri, client),
                        daemon=True
                    )
                    thread_client.start()
                except socket.timeout:
                    pass

        except KeyboardInterrupt:
            print("\nSpegnimento manuale del Gateway in corso.")
        finally:
            client.loop_stop()
            client.disconnect()


if __name__ == "__main__":
    main()