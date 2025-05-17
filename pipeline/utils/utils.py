import os

def replace(text):
    """
    Reemplaza caracteres especiales y espacios en blanco por guiones bajos.
    Parametro: text (str)
    Retorna: text (str) con los caracteres reemplazados.
    """
    text = text.lower()
    text = text.replace("á", "a")
    text = text.replace("é", "e")
    text = text.replace("í", "i")
    text = text.replace("ó", "o")
    text = text.replace("ú", "u")
    text = text.replace("Á", "A")
    text = text.replace("É", "E")
    text = text.replace("Í", "I")
    text = text.replace("Ó", "O")
    text = text.replace("Ú", "U")
    text = text.replace("ñ", "n")
    text = text.replace("Ñ", "N")
    text = text.replace(" ", "_")
    text = text.replace("(", "")
    text = text.replace(")", "")
    return text