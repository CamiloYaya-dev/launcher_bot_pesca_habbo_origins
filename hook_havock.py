import threading
import pyautogui
import pygetwindow as gw
import cv2
import numpy as np
import time

# Colores únicos en RGB
COLOR_PUNTA = (0, 255, 255)     # Azul total
COLOR_ZONA = (255, 191, 0)      # Amarillo de la zona
TOLERANCIA_PIXELES = 3

# Estado global
minijuego_activo = False

def enfocar_ventana(titulo="Habbo Hotel: Origins"):
    ventanas = gw.getWindowsWithTitle(titulo)
    if not ventanas:
        print("❌ No se encontró la ventana del juego.")
        return None
    ventana = ventanas[0]
    if not ventana.isActive:
        ventana.activate()
        time.sleep(0.1)
        pyautogui.click(ventana.left + 50, ventana.top + 50)  # clic para asegurar foco
    return ventana

def buscar_color(color_bgr, region=None):
    if region:
        screenshot = pyautogui.screenshot(region=region)
    else:
        screenshot = pyautogui.screenshot()
    img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    mask = cv2.inRange(img, color_bgr, color_bgr)
    puntos = cv2.findNonZero(mask)
    if puntos is not None:
        return [tuple(pt[0]) for pt in puntos]
    return []

def hook_loop(region=None):
    global minijuego_activo
    print("🎮 Hook Havoc iniciado...")

    while True:
        puntos_zona = buscar_color(COLOR_ZONA[::-1], region)
        puntos_punta = buscar_color(COLOR_PUNTA[::-1], region)

        if puntos_zona and puntos_punta:
            if not minijuego_activo:
                print("🎯 Minijuego detectado.")
                enfocar_ventana()  # Enfoca al detectarlo
            minijuego_activo = True

            x_punta, y_punta = puntos_punta[0]
            x_zona, y_zona = puntos_zona[0]

            dx = x_punta - x_zona
            dy = y_punta - y_zona

            # Distancia euclidiana para saber si está dentro del área segura
            distancia = np.sqrt(dx**2 + dy**2)

            if distancia <= TOLERANCIA_PIXELES:
                print("✅ En zona segura.")
            elif dx > 0:
                print("⬅️ Q (derecha)")
                pyautogui.keyDown('q')
                pyautogui.keyUp('q')
            else:
                print("➡️ E (izquierda)")
                pyautogui.keyDown('e')
                pyautogui.keyUp('e')
        else:
            if puntos_zona and not puntos_punta:
                print("🟡 Zona visible pero sin marcador azul (punta).")
            elif puntos_punta and not puntos_zona:
                print("🔵 Punta visible pero sin zona amarilla.")

            minijuego_activo = False


def iniciar_hook(region=None):
    t = threading.Thread(target=hook_loop, args=(region,), daemon=True)
    t.start()
