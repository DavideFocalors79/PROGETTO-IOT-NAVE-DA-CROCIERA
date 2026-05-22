import json
import socket
import threading
from pathlib import Path

import paho.mqtt.client as mqtt
import cripto

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


def crea_dato_iotp(dato_dc, identita_giot, n_decimali):
    return {
        "cabina": dato_dc["camera"],
        "ponte": dato_dc["ponte"],
        "temperaturam": round(dato_dc["osservazione"]["temperatura"], n_decimali),
        "umiditam": round(dato_dc["osservazione"]["umidita"], n_decimali),
        "dataeora": dato_dc["osservazione"]["dataeora"],
        "invionumero": dato_dc["osservazione"]["rilevazione"],
        "identita": identita_giot
    }


def gestisci_client(conn, addr, parametri, client_mqtt):
    print(f"\n[+] Nuovo sensore connesso da: {addr}")

    tempo_rilevazione = int(parametri["TEMPO_RILEVAZIONE"])
    n_decimali = int(parametri["N_DECIMALI"])
    identita_giot = parametri["IDENTITA_GIOT"]
    topic_mqtt = parametri["TOPIC"]

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
                print(f"[{addr[1]}] DatoIoT ricevuto da dc.py:")
                print(json.dumps(dato_dc, indent=4, ensure_ascii=False))

                dato_iotp = crea_dato_iotp(dato_dc, identita_giot, n_decimali)

                payload_json = json.dumps(dato_iotp, ensure_ascii=False)
                payload_criptato = cripto.criptazione(payload_json)

                print(f"[{addr[1]}] DatoIoT elaborato dal gateway:")
                print(json.dumps(dato_iotp, indent=4, ensure_ascii=False))

                print(f"[{addr[1]}] Invio criptato su topic MQTT {topic_mqtt}")
                risultato = client_mqtt.publish(topic_mqtt, payload_criptato)

                if risultato.rc != mqtt.MQTT_ERR_SUCCESS:
                    print(f"[{addr[1]}] Errore publish MQTT: codice {risultato.rc}")
                else:
                    print(f"[{addr[1]}] Publish MQTT eseguito correttamente")

            except json.JSONDecodeError as e:
                print(f"[{addr[1]}] JSON non valido ricevuto dal client: {e}")
            except Exception as e:
                print(f"[{addr[1]}] Errore di comunicazione con il client: {e}")
                break

    print(f"[-] Sensore {addr} disconnesso")


def main():
    with open(PARAMETRI_FILE, "r", encoding="utf-8") as f:
        parametri = json.load(f)

    ip_server = parametri["IP_SERVER"]
    porta_server = int(parametri["PORTA_SERVER"])
    broker = parametri["BROKER"]
    porta_broker = int(parametri["PORTA_BROKER"])
    topic = parametri["TOPIC"]

    client = mqtt.Client()

    try:
        client.connect(broker, porta_broker, 60)
        client.loop_start()
        print(f"Connesso al broker MQTT {broker}:{porta_broker}")
        print(f"Topic di pubblicazione: {topic}")
    except Exception as e:
        print(f"Errore connessione al broker MQTT: {e}")
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