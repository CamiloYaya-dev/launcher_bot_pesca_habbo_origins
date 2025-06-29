import cv2
import numpy as np
import pyautogui
import os

UMBRAL = 0.1  # umbral ajustado según tus pruebas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TITULO_VENTANA = "Habbo Hotel: Origins"

SALAS = {
    "sala_parque": {
        "fondo": os.path.join(BASE_DIR, "niveles", "park_bg.png"),
        "orientacion": "horizontal"
    },
    "sala_muelle": {
        "fondo": os.path.join(BASE_DIR, "niveles", "Pier_BG.png"),
        "orientacion": "horizontal"
    },
    "sala_flotante": {
        "fondo": os.path.join(BASE_DIR, "niveles", "float_backgnd.png"),
        "orientacion": "vertical"
    }
}

def capturar_ventana(titulo=TITULO_VENTANA):
    ventanas = pyautogui.getWindowsWithTitle(titulo)
    if not ventanas:
        print("❌ No se encontró la ventana del juego.")
        return None
    ventana = ventanas[0]
    if not ventana.isActive:
        ventana.activate()
    bbox = (ventana.left, ventana.top, ventana.width, ventana.height)
    screenshot = pyautogui.screenshot(region=bbox)
    return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

def comparar(imagen_a_buscar, fondo, metodo):
    fondo_gray = cv2.cvtColor(fondo, cv2.COLOR_BGR2GRAY)
    imagen_gray = cv2.cvtColor(imagen_a_buscar, cv2.COLOR_BGR2GRAY)

    if fondo_gray.shape[0] > imagen_gray.shape[0] or fondo_gray.shape[1] > imagen_gray.shape[1]:
        print(f"⚠️ Saltando comparación {metodo}: fondo más grande que imagen.")
        return 0.0

    res = cv2.matchTemplate(imagen_gray, fondo_gray, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(res)
    print(f"🧪 Coincidencia ({metodo}): {max_val:.2f}")
    return max_val

def detectar_sala():
    imagen_actual = capturar_ventana()
    if imagen_actual is None:
        return

    redimensionada = cv2.resize(imagen_actual, (960, 490))
    cv2.imwrite("redimensionada.png", redimensionada)

    for nombre_sala, datos in SALAS.items():
        fondo = cv2.imread(datos["fondo"])
        if fondo is None:
            print(f"❌ No se pudo cargar la imagen de fondo para {nombre_sala}")
            continue

        score = comparar(redimensionada, fondo, metodo=nombre_sala)
        if score >= UMBRAL:
            print(f"✅ Sala detectada: {nombre_sala} (coincidencia {score:.2f})")
            return nombre_sala, datos["orientacion"]

    print("❌ No coincide suficientemente con ninguna sala.")
    return None, None

if __name__ == "__main__":
    detectar_sala()
