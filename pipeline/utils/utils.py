import os

def reemplazar(texto):
    """
    Reemplaza caracteres especiales y espacios en blanco por guiones bajos.
    Parametro: texto (str)
    Retorna: texto (str) con los caracteres reemplazados.
    """
    texto = texto.lower()
    texto = texto.replace("á", "a")
    texto = texto.replace("é", "e")
    texto = texto.replace("í", "i")
    texto = texto.replace("ó", "o")
    texto = texto.replace("ú", "u")
    texto = texto.replace("Á", "A")
    texto = texto.replace("É", "E")
    texto = texto.replace("Í", "I")
    texto = texto.replace("Ó", "O")
    texto = texto.replace("Ú", "U")
    texto = texto.replace("ñ", "n")
    texto = texto.replace("Ñ", "N")
    texto = texto.replace(" ", "_")
    texto = texto.replace("(", "")
    texto = texto.replace(")", "")
    return texto