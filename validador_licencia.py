# validador_licencia.py

def validar_licencia(key: str) -> dict:
    """
    Simula una validación de licencia contra un servidor remoto.

    Devuelve un dict con:
    - status: "valido" o "invalido"
    - mensaje: descripción
    """
    # MOCK: lista de llaves válidas para pruebas
    llaves_validas = {
        "1": "Usuario de prueba",
        "KEY-DE-PRUEBA-VALIDA-1234": "Usuario QA",
        "MI-LLAVE-SECRETA-9999": "Admin Local"
    }

    if key in llaves_validas:
        return {
            "status": "valido",
            "usuario": llaves_validas[key]
        }
    else:
        return {
            "status": "invalido",
            "mensaje": "Llave no autorizada o expirada"
        }

# Ejemplo de uso (puedes borrar esto si solo lo importas)
if __name__ == "__main__":
    key = input("🔑 Ingrese su licencia: ").strip()
    resultado = validar_licencia(key)
    if resultado["status"] != "valido":
        print("❌ Acceso denegado:", resultado["mensaje"])
