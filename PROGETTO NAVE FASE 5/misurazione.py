import random


def on_temperatura(N):
    """Genera una simulazione della temperatura.
    Il dato generato è casuale e in un range tra 10-40.
    """
    temperatura = round(random.uniform(0, 40), N)
    return temperatura


def on_umidita(N):
    """Genera una simulazione dell'umidità.
    Il dato generato è casuale e in un range tra 20-90.
    """
    umidita = round(random.uniform(20, 90), N)
    return umidita
