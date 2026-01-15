# Simulazione
# Sensore di temperatura e umidità
#
# Script misurazione.py
# Parametro ingresso da main: N numero di decimali arrotondamento
#
# Simulazione sensore temperatura, da 10 a 40 gradi
# cifre decimali pari a N
#
import random   # Generazione numeri casuali
#
# Funzioni
#
def on_temperatura(N):
    TEMP = round(random.uniform(10,40), N)
    return TEMP
# Simulazione sensore umidità, da 20 a 90 gradi
# cifre decimali pari a N
def on_umidita(N):
    UMID = round(random.uniform(20,90), N)
    return UMID
#
