import json
import socket
import paho.mqtt.client as mqtt
from pathlib import Path
import cripto
import threading

# Configurazione percorsi file
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

def gestisci_client(conn, addr, parametri, client_mqtt):
    print(f"\n[+] Nuovo sensore connesso da: {addr}")

    TEMPO_RILEVAZIONE = parametri["TEMPO_RILEVAZIONE"]
    N_DECIMALI        = parametri["N_DECIMALI"]
    IDENTITA_GIOT     = parametri["IDENTITA_GIOT"]
    TOPIC_HIVEMQ      = parametri["TOPIC"]
    TOPIC_THINGSBOARD = "v1/devices/me/telemetry"

    with conn:
        parametri_init = {
            "TEMPO_RILEVAZIONE": TEMPO_RILEVAZIONE,
            "N_DECIMALI": N_DECIMALI
        }
        try:
            conn.sendall((json.dumps(parametri_init) + "\n").encode("utf-8"))
        except:
            print(f"Errore nell'invio dei parametri a {addr}")
            return

        while True:
            try:
                line = recv_line(conn)
                if not line:
                    break

                dato_dc = json.loads(line)
                print(f"[{addr[1]}] DatoIoT ricevuto:", json.dumps(dato_dc))

                # Costruzione dato formato IOTP
                dato_iotp = {
                    "cabina":       dato_dc["camera"],
                    "ponte":        dato_dc["ponte"],
                    "temperaturam": round(dato_dc["osservazione"]["temperatura"], N_DECIMALI),
                    "umiditam":     round(dato_dc["osservazione"]["umidita"],     N_DECIMALI),
                    "dataeora":     dato_dc["osservazione"]["dataeora"],
                    "invionumero":  dato_dc["osservazione"]["rilevazione"],
                    "identita":     IDENTITA_GIOT
                }

                # Invio criptato a HiveMQ (archivia_iotp.py)
                payload_criptato = cripto.criptazione(json.dumps(dato_iotp))
                print(f"[{addr[1]}] Invio criptato a HiveMQ:", payload_criptato)
                client_mqtt.publish(TOPIC_HIVEMQ, payload_criptato)

                # Invio telemetria a ThingsBoard (temperatura e umidità)
                telemetria_tb = {
                    "temperature": dato_iotp["temperaturam"],
                    "humidity":    dato_iotp["umiditam"],
                    "cabin":       dato_iotp["cabina"],
                    "deck":        dato_iotp["ponte"]
                }
                print(f"[{addr[1]}] Invio a ThingsBoard:", telemetria_tb)
                client_mqtt.publish(TOPIC_THINGSBOARD, json.dumps(telemetria_tb), qos=1)

            except Exception as e:
                print(f"Errore di comunicazione con {addr}: {e}")
                break

    print(f"Sensore {addr} disconnesso.")

def main():
    with open(PARAMETRI_FILE, "r", encoding="utf-8") as f:
        parametri = json.load(f)

    IP_SERVER    = parametri["IP_SERVER"]
    PORTA_SERVER = int(parametri["PORTA_SERVER"])
    BROKER       = parametri["BROKER"]
    PORTA_BROKER = int(parametri["PORTA_BROKER"])
    TOKEN_TB     = parametri["TOKEN_TB"]

    # Client MQTT unico con credenziali ThingsBoard
    # username = token ThingsBoard, questo permette di inviare sia a HiveMQ che a ThingsBoard
    client = mqtt.Client()
    client.username_pw_set(TOKEN_TB)

    try:
        client.connect(BROKER, PORTA_BROKER, 60)
        client.loop_start()
        print(f"Connesso al broker MQTT: {BROKER}:{PORTA_BROKER}")
        print(f"Connesso a ThingsBoard con token: {TOKEN_TB}")
    except Exception as e:
        print(f"Errore connessione MQTT: {e}")
        return

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((IP_SERVER, PORTA_SERVER))
        server.listen()
        server.settimeout(1.0)

        print(f"Gateway IoT in attesa di dati su {IP_SERVER}:{PORTA_SERVER}...")

        try:
            while True:
                try:
                    conn, addr = server.accept()
                    thread_client = threading.Thread(
                        target=gestisci_client,
                        args=(conn, addr, parametri, client)
                    )
                    thread_client.daemon = True
                    thread_client.start()
                except socket.timeout:
                    pass

        except KeyboardInterrupt:
            print("\nSpegnimento manuale del Gateway in corso.")
        finally:
            client.loop_stop()

if __name__ == "__main__":
    main()
