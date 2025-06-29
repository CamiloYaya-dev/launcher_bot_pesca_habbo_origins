import pyautogui
import cv2
import numpy as np
import time
import hook_havock
import sys
from detectar_sala import detectar_sala
import math

# Colores clave
COLOR_PEZ = (255, 0, 255)
COLOR_ICONO = (102, 102, 153)
COLOR_SALA_PARQUE = (255, 255, 204)
COLOR_SALA_FLOTANTE = (249, 206, 83)

# Parámetros
ESPERA_ICONO = 15
MAX_REINTENTOS = 3
ANCHO_CASILLA = 34
ALTO_CASILLA = 17
TIEMPO_POR_CASILLA = 0.90

ultima_casilla_click = None

def buscar_color_direccion(color_bgr, region, orientacion):
    screenshot = pyautogui.screenshot(region=region)
    img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    mask = cv2.inRange(img, color_bgr, color_bgr)
    puntos = []

    if orientacion == "horizontal":
        for y in range(mask.shape[0]):
            for x in range(mask.shape[1]):
                if mask[y, x] == 255:
                    puntos.append((x, y))
    elif orientacion == "vertical":
        for x in range(mask.shape[1]):
            for y in range(mask.shape[0]):
                if mask[y, x] == 255:
                    puntos.append((x, y))
    return puntos

def buscar_color_especifico(color_bgr, region):
    screenshot = pyautogui.screenshot(region=region)
    img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    mask = cv2.inRange(img, color_bgr, color_bgr)
    puntos = cv2.findNonZero(mask)
    if puntos is not None:
        return [tuple(pt[0]) for pt in puntos]
    return []

def buscar_casilla_mas_cercana(color, bbox, objetivo_pez):
    puntos = buscar_color_especifico(color[::-1], bbox)
    if not puntos:
        return None
    pez_x = objetivo_pez[0] + bbox[0]
    pez_y = objetivo_pez[1] + bbox[1]
    casilla_mas_cercana = min(
        puntos,
        key=lambda pt: np.hypot((pt[0] + bbox[0]) - pez_x, (pt[1] + bbox[1]) - pez_y)
    )
    return bbox[0] + casilla_mas_cercana[0], bbox[1] + casilla_mas_cercana[1]

def calcular_tiempo_espera(previo, nuevo):
    if previo is None:
        return 10
    dx = nuevo[0] - previo[0]
    dy = nuevo[1] - previo[1]
    casillas_x = abs(dx) / ANCHO_CASILLA
    casillas_y = abs(dy) / ALTO_CASILLA
    num_casillas = math.sqrt(casillas_x ** 2 + casillas_y ** 2)
    return round(num_casillas * TIEMPO_POR_CASILLA, 2)

def main():
    global ultima_casilla_click
    sala, orientacion = detectar_sala()
    if not sala:
        print("❌ No se pudo detectar la sala. Abortando.")
        return

    print("⏳ Buscando ventana...")
    ventana = pyautogui.getWindowsWithTitle("Habbo Hotel: Origins")
    if not ventana:
        print("❌ No se encontró la ventana.")
        return
    habbo = ventana[0]
    if not habbo.isActive:
        habbo.activate()

    bbox = (habbo.left, habbo.top, habbo.width, habbo.height)
    print(f"✅ Ventana encontrada: Pos=({bbox[0]},{bbox[1]}) Tamaño=({bbox[2]}x{bbox[3]})")

    hook_havock.iniciar_hook(bbox)

    while True:
        if hook_havock.minijuego_activo:
            print("⏸️ Pausando pesca: minijuego en curso...")
            time.sleep(0.5)
            continue

        puntos_pez = buscar_color_direccion(COLOR_PEZ[::-1], bbox, orientacion)
        if puntos_pez:
            # Buscar el pez más cercano a la última casilla clickeada
            if ultima_casilla_click:
                objetivo = min(
                    puntos_pez,
                    key=lambda pt: np.hypot((bbox[0] + pt[0]) - ultima_casilla_click[0], (bbox[1] + pt[1]) - ultima_casilla_click[1])
                )
            else:
                objetivo = puntos_pez[0]

            click_x = bbox[0] + objetivo[0]
            click_y = bbox[1] + objetivo[1]

            if sala in ["sala_parque", "sala_flotante"]:
                color = COLOR_SALA_PARQUE if sala == "sala_parque" else COLOR_SALA_FLOTANTE
                label = "parque" if sala == "sala_parque" else "flotante"
                resultado = buscar_casilla_mas_cercana(color, bbox, objetivo)
                if resultado:
                    cx, cy = resultado
                    print(f"✨ Casilla {label} más cercana en: ({cx},{cy}) — click previo...")
                    pyautogui.click(cx, cy)
                    tiempo_espera = calcular_tiempo_espera(ultima_casilla_click, (cx, cy))
                    ultima_casilla_click = (cx, cy)
                    print(f"⏳ Esperando {tiempo_espera} segundos...")
                    time.sleep(tiempo_espera)
                else:
                    print(f"⚠️ No se encontró casilla especial {label}.")

            print(f"🎯 Pez detectado en: ({click_x},{click_y})")
            pyautogui.click(click_x, click_y)
            pyautogui.click(click_x, click_y)
            ultima_casilla_click = (click_x, click_y)
            time.sleep(ESPERA_ICONO)

            for intento in range(MAX_REINTENTOS + 1):
                puntos_icono = buscar_color_direccion(COLOR_ICONO[::-1], bbox, orientacion)
                if puntos_icono:
                    print("🎣 Icono de pesca detectado. Esperando a que desaparezca...")
                    while buscar_color_direccion(COLOR_ICONO[::-1], bbox, orientacion):
                        time.sleep(1)
                    print("✅ Icono desapareció.")
                    break
                else:
                    if intento < MAX_REINTENTOS:
                        pez_actual = buscar_color_direccion(COLOR_PEZ[::-1], bbox, orientacion)
                        pez_en_rango = next(
                            ((x, y) for (x, y) in pez_actual
                            if abs((bbox[0] + x) - click_x) <= 10 or abs((bbox[1] + y) - click_y) <= 10),
                            None
                        )
                        if pez_en_rango:
                            nuevo_click_x = bbox[0] + pez_en_rango[0]
                            nuevo_click_y = bbox[1] + pez_en_rango[1]
                            print(f"🔁 Reintento #{intento + 1} — pez en cruz detectado en ({nuevo_click_x},{nuevo_click_y})")
                            pyautogui.click(nuevo_click_x, nuevo_click_y)
                            ultima_casilla_click = (nuevo_click_x, nuevo_click_y)
                            time.sleep(ESPERA_ICONO)
                        else:
                            print("❌ No se encontró pez en cruz. Cancelando reintentos.")
                            break
                    else:
                        print("❌ No apareció icono. Buscando nuevo pez...")
        else:
            print("🔎 No se encontró ningun pez")
        time.sleep(0.3)

if __name__ == "__main__":
    main()
