# index.py
import subprocess
import os
import tempfile
import time
import psutil
import signal
import sys
import ctypes
from datetime import datetime

# Detectar ruta base, ya sea desde .py o .exe compilado
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS  # Carpeta temporal donde PyInstaller descomprime
else:
    base_path = os.path.dirname(__file__)

log_file = os.path.join(base_path, "log_debug.txt")

def log(msg):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n")

def ejecutar_mv():
    ruta_mv = os.path.join(base_path, "mv.exe")
    log(f"🧪 Intentando ejecutar mv.exe como administrador desde: {ruta_mv}")

    try:
        # Usa ShellExecuteEx para obtener el handle del proceso lanzado
        from ctypes import wintypes, byref

        SEE_MASK_NOCLOSEPROCESS = 0x00000040

        class SHELLEXECUTEINFO(ctypes.Structure):
            _fields_ = [
                ('cbSize', ctypes.c_ulong),
                ('fMask', ctypes.c_ulong),
                ('hwnd', wintypes.HWND),
                ('lpVerb', wintypes.LPCWSTR),
                ('lpFile', wintypes.LPCWSTR),
                ('lpParameters', wintypes.LPCWSTR),
                ('lpDirectory', wintypes.LPCWSTR),
                ('nShow', ctypes.c_int),
                ('hInstApp', wintypes.HINSTANCE),
                ('lpIDList', ctypes.c_void_p),
                ('lpClass', wintypes.LPCWSTR),
                ('hkeyClass', wintypes.HKEY),
                ('dwHotKey', ctypes.c_ulong),
                ('hIcon', wintypes.HANDLE),
                ('hProcess', wintypes.HANDLE)
            ]

        sei = SHELLEXECUTEINFO()
        sei.cbSize = ctypes.sizeof(sei)
        sei.fMask = SEE_MASK_NOCLOSEPROCESS
        sei.lpVerb = "runas"
        sei.lpFile = ruta_mv
        sei.nShow = 1

        if not ctypes.windll.shell32.ShellExecuteExW(byref(sei)):
            raise ctypes.WinError()

        log("✅ mv.exe ejecutado correctamente como administrador.")

        # Esperar a que el proceso hijo termine
        ctypes.windll.kernel32.WaitForSingleObject(sei.hProcess, -1)
        return None

    except Exception as e:
        log(f"❌ Error ejecutando mv.exe como admin: {e}")
        return None


def cerrar_qemu():
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if "qemu-system-x86_64.exe" in proc.info['name']:
                os.kill(proc.info['pid'], signal.SIGTERM)
                log(f"🔴 QEMU cerrado: PID {proc.info['pid']}")
        except Exception as e:
            log(f"⚠️ No se pudo cerrar QEMU: {e}")

def limpiar_archivos_temporales():
    try:
        archivo_lista = os.path.join(tempfile.gettempdir(), "rAZCuQEwYjKxV1yCc89cqMBu0keveY.tmp")
        if os.path.exists(archivo_lista):
            with open(archivo_lista, "r") as f:
                rutas = f.read().splitlines()
            for ruta in rutas:
                if os.path.exists(ruta):
                    os.remove(ruta)
                    log(f"🧹 Eliminado: {ruta}")
            os.remove(archivo_lista)
            log("✅ Archivos temporales eliminados correctamente.")
        else:
            log("ℹ️ No se encontraron archivos temporales que limpiar.")
    except Exception as e:
        log(f"❌ Error al limpiar archivos: {e}")

if __name__ == "__main__":
    proceso_mv = ejecutar_mv()
    try:
        proceso_mv.wait()
    except KeyboardInterrupt:
        log("⛔ Interrupción manual detectada.")
    finally:
        log("🧹 MV cerrado, iniciando limpieza...")
        cerrar_qemu()
        limpiar_archivos_temporales()
        log("✅ Proceso finalizado con éxito.")
