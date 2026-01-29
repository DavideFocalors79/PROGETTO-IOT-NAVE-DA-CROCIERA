# Modulo di criptazione
# Script: cripto.py
# Algoritmo: da definire
# Simulazione con sostituzione della lettera 'a' con '*'
def criptazione(payload):
    criptato = payload.replace("a","*")
    return criptato
#
def decriptazione(payload):
    decriptato = payload.replace("*","a")
    return decriptato
