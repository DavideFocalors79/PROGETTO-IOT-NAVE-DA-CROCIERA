from pathlib import Path
import socket
import time
import sys
import json
import misurazione

BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "configurazione"

DA_FILE = CONFIG_DIR / "da.json"
CONFIG_FILE = CONFIG_DIR / "configurazionedc.json"

def recv_line(sock) -> str:
    data = bytearray()
    while True:
        chunk = sock.recv(1)
        if not chunk:
            raise OSError("Connessione chiusa dal server")
        if chunk == b"\n":
            break
        data.extend(chunk)
    return data.decode("utf-8", errors="replace").strip()

def connetti_socket(ip, porta, retry=5):
    for i in range(retry):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, porta))
            return s
        except OSError as e:
            print(f"Connessione fallita ({i+1}/{retry}): {e}")
            try:
                s.close()
            except:
                pass
            time.sleep(2)
    raise OSError("Impossibile connettersi al server")

def main():
    with open(DA_FILE, "r", encoding="utf-8") as f:
        da = json.load(f)

    ip_server = da["IP"]
    porta_server = int(da["porta"])

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    sock = connetti_socket(ip_server, porta_server)

    init_str = recv_line(sock)
    init = json.loads(init_str)

    tempo_rilevazione = int(init["TEMPO_RILEVAZIONE"])
    n_decimali = int(init["N_DECIMALI"])

    seriale = 0

    while True:
        seriale += 1

        temperatura = misurazione.on_temperatura(n_decimali)
        umidita = misurazione.on_umidita(n_decimali)
        dataeora = int(time.time())

        dato_iot = {
            "camera": cfg["camera"],
            "ponte": cfg["ponte"],
            "sensore": cfg["sensore"],
            "identita": cfg["identita"],
            "osservazione": {
                "rilevazione": seriale,
                "dataeora": dataeora,
                "temperatura": temperatura,
                "umidita": umidita
            }
        }

        payload = json.dumps(dato_iot, separators=(",", ":"), ensure_ascii=False) + "\n"

        try:
            sock.sendall(payload.encode("utf-8"))
        except OSError as e:
            print(f"Invio fallito: {e}, riconnessione socket...")
            try:
                sock.close()
            except:
                pass
            sock = connetti_socket(ip_server, porta_server)
            continue

        print("Dato inviato a iotgwda.py:")
        print(json.dumps(dato_iot, indent=4, ensure_ascii=False))

        time.sleep(tempo_rilevazione)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSpegnimento del programma.")
        sys.exit(0)