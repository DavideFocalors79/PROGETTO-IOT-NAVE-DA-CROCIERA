from machine import Pin
import dht

def on_temperatura(pin, N, tmin, tmax):
    """
    Metodo per la misurazione della temperatura su 
    scheda con mycropython
    """

    sensor = dht.DHT11(Pin(pin))
    sensor.measure()
    return sensor.temperature()


def on_umidita(pin, N, umin, umax):
    """
    Metodo per la misurazione dell'umidità su 
    scheda con mycropython
    """
    sensor = dht.DHT11(Pin(pin))
    sensor.measure()
    return sensor.humidity()