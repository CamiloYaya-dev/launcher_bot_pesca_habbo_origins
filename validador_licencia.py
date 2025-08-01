import requests
import os
import time
import json
import tkinter as tk
from tkinter import ttk
from dotenv import load_dotenv
import urllib3
import tempfile
import sys

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Cargar variables de entorno
load_dotenv()
BASE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
dotenv_path = os.path.join(BASE_DIR, ".env")

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

API_URL = os.getenv("API_URL") or "http://144.91.110.153/validar"
API_KEY = os.getenv("API_KEY") or "LCklg5H2zMm0ULuMfvX9gqPKHXAiQg3bbA3dXURHk0M"
ARCHIVO_IMG = "3ZuxE7bre0kypSqM76n5dkak7zZBu0"
actualizador_mensajes = None
callback_descarga_completa = None

# Archivo oculto de control
NOMBRE_CONTROL = "50c7dbd9417e992d"
RUTA_CONTROL = os.path.join(tempfile.gettempdir(), NOMBRE_CONTROL)

# GUI temporal para progreso de descarga
descarga_root = None
descarga_label = None
descarga_barra = None
barra_progreso = None

CHUNK_SIZE = 16 * 1024 * 1024  # 16MB

LOG_PATH = os.path.join(os.getcwd(), "log_debug.txt")
def log_debug(msg):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{msg}\n")

def set_actualizador_mensajes(func):
    global actualizador_mensajes
    actualizador_mensajes = func

def set_callback_descarga_completa(func):
    global callback_descarga_completa
    callback_descarga_completa = func

def validar_licencia(key: str) -> dict:
    print("🔐 Validando licencia...")
    log_debug("🔐 Iniciando validación de licencia...")
    if not API_URL or not API_KEY:
        log_debug("❌ Configuración incompleta: falta API_URL o API_KEY.")
        return {
            "status": "error",
            "mensaje": "Configuración incompleta (falta API_URL o API_KEY en .env)"
        }

    try:
        log_debug(f"📤 Enviando solicitud a API: {API_URL}")
        response = requests.post(
            API_URL,
            headers={"x-api-key": API_KEY},
            json={"clave": key},
            timeout=5
        )
        log_debug("📥 Respuesta recibida.")
        data = response.json()
        log_debug(f"📄 Contenido respuesta: {data}")
        if data.get("status") == "valido":
            chequear_actualizacion()
        return data
    except Exception as e:
        log_debug(f"❌ Error de conexión al validar licencia: {e}")
        return {
            "status": "error",
            "mensaje": f"No se pudo conectar con el servidor: {str(e)}"
        }

def chequear_actualizacion():
    log_debug("🔄 Iniciando verificación de actualización...")
    path_archivo = os.path.join(os.getcwd(), ARCHIVO_IMG)
    log_debug(f"📁 Archivo esperado: {path_archivo}")
    try:
        log_debug("📤 Solicitando metadata de actualización...")
        resp = requests.get(
            API_URL.replace("/validar", "/actualizar"),
            headers={"x-api-key": API_KEY},
            timeout=5
        )

        log_debug(f"📥 Código de estado recibido: {resp.status_code}")
        if resp.status_code == 200:
            metadata = resp.json().get(ARCHIVO_IMG)
            log_debug(f"📄 Metadata recibida: {metadata}")
            if not metadata:
                log_debug("✅ No se requiere actualización.")
                _mensaje("✅ Archivo no requiere actualización.")
                if callback_descarga_completa:
                    callback_descarga_completa()
                return

            size_servidor = int(metadata.get("size", "0").replace(".", ""))
            timestamp_servidor = metadata.get("last_updated", "")

            if os.path.exists(path_archivo) and os.path.exists(RUTA_CONTROL):
                with open(RUTA_CONTROL, "r") as f:
                    datos_locales = json.load(f)
                log_debug(f"📄 Datos locales: {datos_locales}")
                if (str(datos_locales.get("last_updated")) == timestamp_servidor and
                        int(datos_locales.get("size", 0)) == os.path.getsize(path_archivo)):
                    log_debug("✅ Archivo local ya está actualizado.")
                    _mensaje("✅ Archivo ya actualizado previamente.")
                    if callback_descarga_completa:
                        callback_descarga_completa()
                    return

            log_debug("🔁 Se requiere actualización. Eliminando archivo existente...")
            if os.path.exists(path_archivo):
                os.remove(path_archivo)
                _esperar_eliminacion(path_archivo)

            mostrar_descarga_gui()
            descargar_archivo_img(size_servidor, timestamp_servidor)
            cerrar_descarga_gui()
            if callback_descarga_completa:
                callback_descarga_completa()

        elif resp.status_code == 205:
            log_debug("📦 No hay actualizaciones disponibles (205).")
            _mensaje("📦 No hay actualizaciones disponibles.")
            if callback_descarga_completa:
                callback_descarga_completa()
        else:
            log_debug(f"⚠️ Código inesperado en respuesta: {resp.status_code}")
            _mensaje(f"⚠️ Error verificando actualización. Código: {resp.status_code}")
    except Exception as e:
        log_debug(f"⚠️ Excepción durante verificación de actualización: {e}")
        _mensaje(f"⚠️ Excepción consultando actualización: {e}")

def descargar_archivo_img(size_servidor, timestamp_servidor):
    log_debug("📥 Iniciando descarga de imagen cifrada...")
    _mensaje("⬇️ Descargando desde API protegida...")
    URL = API_URL.replace("/validar", "/descargar/img")
    try:
        with requests.get(URL, headers={"x-api-key": API_KEY}, stream=True, timeout=300, verify=False) as r:
            r.raise_for_status()
            total = int(r.headers.get('content-length', 0))
            log_debug(f"📦 Tamaño total a descargar: {total} bytes")
            descargado = 0
            inicio = time.time()
            ultima = inicio

            with open(ARCHIVO_IMG, "wb") as f:
                for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
                        descargado += len(chunk)
                        porcentaje = int((descargado / total) * 100) if total else 0
                        ahora = time.time()
                        velocidad = descargado / max((ahora - inicio), 0.1) / (1024 * 1024)

                        if ahora - ultima >= 1:
                            msg = f"📦 {porcentaje}% - Vel: {velocidad:.2f} MB/s"
                            log_debug(msg)
                            _mensaje(msg)
                            if descarga_label:
                                descarga_label.config(text=msg)
                            if barra_progreso:
                                barra_progreso.set(porcentaje)
                            descarga_root.update()
                            ultima = ahora

        log_debug("✅ Descarga completada correctamente.")
        _mensaje(f"✅ Descarga completada en: {ARCHIVO_IMG}")
        with open(RUTA_CONTROL, "w") as f:
            json.dump({"last_updated": timestamp_servidor, "size": size_servidor}, f)
        log_debug("🧾 Archivo de control actualizado.")
    except Exception as e:
        log_debug(f"❌ Error durante descarga: {e}")
        _mensaje(f"❌ Error en descarga protegida: {e}")

def mostrar_descarga_gui():
    global descarga_root, descarga_label, descarga_barra, barra_progreso
    descarga_root = tk.Toplevel()
    descarga_root.title("Descargando actualización")
    descarga_root.geometry("400x100")
    descarga_label = tk.Label(descarga_root, text="Iniciando descarga...")
    descarga_label.pack(pady=10)
    barra_progreso = tk.DoubleVar()
    descarga_barra = ttk.Progressbar(descarga_root, length=300, variable=barra_progreso, maximum=100)
    descarga_barra.pack()
    descarga_root.update()

def cerrar_descarga_gui():
    global descarga_root
    if descarga_root:
        descarga_root.destroy()
        descarga_root = None

def _esperar_eliminacion(ruta, intentos=10, delay=1):
    for intento in range(intentos):
        if not os.path.exists(ruta):
            log_debug(f"✅ Archivo eliminado exitosamente: {ruta}")
            return
        log_debug(f"⌛ Esperando eliminación del archivo (intento {intento+1}/{intentos})...")
        _mensaje(f"⌛ Esperando que se libere el archivo... ({intento + 1}/{intentos})")
        time.sleep(delay)
    raise Exception("⏱️ Timeout: El archivo no se pudo eliminar tras múltiples intentos.")

def _mensaje(texto):
    print(texto)
    if actualizador_mensajes:
        actualizador_mensajes(texto)

# Test manual
if __name__ == "__main__":
    key = input("🔑 Ingrese su licencia: ").strip()
    resultado = validar_licencia(key)
    if resultado["status"] != "valido":
        print("❌ Acceso denegado:", resultado.get("mensaje", "Error desconocido"))
    else:
        print("✅ Licencia válida:", resultado["usuario"])
