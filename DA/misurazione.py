import random

def rileva_temperatura(min=10, max=40, decimali=2):
    return round(random.uniform(min, max), decimali)

def rileva_umidita(min=20, max=90, decimali=2):
    return round(random.uniform(min, max), decimali)
