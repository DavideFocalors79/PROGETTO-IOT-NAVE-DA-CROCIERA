# Modulo di criptazione
# Script: cripto.py
# Algoritmo: da definire
# Simulazione con sostituzione della lettera 'a' con '*'
# Funzione di criptazione che sostituisce 'a' con '*'
def criptazione(payload):
    criptato = payload.replace("a","*")
    return criptato

# Funzione di decriptazione che sostituisce '*' con 'a'
def decriptazione(payload):
    decriptato = payload.replace("*","a")
    return decriptato
