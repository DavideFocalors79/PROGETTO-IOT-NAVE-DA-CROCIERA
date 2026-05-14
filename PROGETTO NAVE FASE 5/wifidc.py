import rp2
import network
import ubinascii
import machine
import time
import json


def Parametri_WiFi():
    with open('wifipico.json', 'r') as file:
        credenziali = json.load(file)
        ssid = credenziali["ssid"]
        pasw = credenziali["pw"]
    return ssid, pasw


def Powersaving(wlan, scelta):
    if scelta == "SI":
        wlan.config(pm=0xa11140)
    return


def Connessione_WiFi(wlan, time_out, s, p, pausa):
    wlan.connect(s, p)
    print("Tentativi (attesa):", time_out)

    while time_out > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break

        time_out -= 1
        print("Tentativo connessione")
        time.sleep(pausa)

    if wlan.status() != 3:
        while True:
            Errore_con_blink_led(wlan.status())
    else:
        print("Connessione riuscita")
        status = wlan.ifconfig()
        print(status)
        print("IP Pico:", status[0])


def Errore_con_blink_led(num_blinks):
    led = machine.Pin("LED", machine.Pin.OUT)

    for i in range(num_blinks):
        led.on()
        time.sleep(0.2)
        led.off()
        time.sleep(0.2)


def Info_WiFi(wlan):

    mac = ubinascii.hexlify(network.WLAN().config('mac'),':').decode()
    print('mac = ' + mac)

    print('Canale: ', wlan.config('channel'))
    print('SSID: ', wlan.config('essid'))
    print('Segnale: ', wlan.config('txpower'))

    print()
    print("Scansione")
    print("(ssid, bssid, channel, RSSI, security, hidden)")
    print(wlan.scan())
    print()


def connetti_wifi():

    ATTESA = 10
    TEMPO_PAUSA = 1

    SSID, PASW = Parametri_WiFi()

    rp2.country('IT')

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    Powersaving(wlan, "NO")

    Connessione_WiFi(wlan, ATTESA, SSID, PASW, TEMPO_PAUSA)

    return wlan


