# ✅ MV.py (modificado completo y funcional)
import os
import subprocess
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import sys
import ctypes
import platform
import tempfile
import traceback
from threading import Thread
import time
import win32gui
import win32con
import win32process
from validador_licencia import validar_licencia, set_actualizador_mensajes, set_callback_descarga_completa
from descifrador_img import descifrar_img, generar_fingerprint

QEMU_EXECUTABLE = r"C:\Program Files\qemu\qemu-system-x86_64.exe"
if getattr(sys, 'frozen', False):
    BASE_PATH = os.path.dirname(sys.executable)
else:
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))

ENC_FILE = os.path.join(BASE_PATH, "3ZuxE7bre0kypSqM76n5dkak7zZBu0")
estado_hypervisor_override = False
log_file = os.path.join(os.getcwd(), "log_debug.txt")

clave_usuario = ""

# Inicializar root oculto
root = tk.Tk()
root.withdraw()

def ejecutar_como_admin():
    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            script = os.path.abspath(sys.argv[0])
            params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
            root.destroy()
            sys.exit()
    except Exception as e:
        log_error("Error en ejecutar_como_admin: " + traceback.format_exc())
        sys.exit()

ejecutar_como_admin()

def log_error(msg):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def cuando_descarga_termine():
    root.deiconify()

set_callback_descarga_completa(cuando_descarga_termine)

def pedir_y_validar_clave():
    try:
        while True:
            key = simpledialog.askstring("🔑 Validación de licencia", "Ingresa tu clave de licencia:")
            if not key:
                messagebox.showwarning("⚠️ Cancelado", "No se ingresó ninguna clave.")
                return False
            resultado = validar_licencia(key.strip())
            if resultado["status"] == "valido":
                global clave_usuario
                clave_usuario = key.strip()
                messagebox.showinfo("✅ Acceso concedido", f"Bienvenido: {resultado['usuario']}")
                return True
            else:
                retry = messagebox.askretrycancel("❌ Acceso denegado", resultado["mensaje"] + "\n¿Deseas intentar de nuevo?")
                if not retry:
                    return False
    except Exception as e:
        log_error("Error en pedir_y_validar_clave: " + traceback.format_exc())
        return False

if not pedir_y_validar_clave():
    root.destroy()
    sys.exit()

# Mostrar GUI principal (solo cuando se llame cuando_descarga_termine)

root.title("Bot Fishing")
root.geometry("560x600")

frame_vm = tk.Frame(root, width=560, height=300, bg="black")
frame_vm.pack(pady=10)

tk.Label(root, text="Bot Fishing Habbo Origins - Entorno Seguro", font=("Arial", 14)).pack(pady=10)
etiqueta_estado = tk.Label(root, text="🔃 Cargando...", font=("Arial", 10))
etiqueta_estado.pack()

def actualizar_mensaje_seguro(msg):
    def tarea(): etiqueta_estado.config(text=msg)
    root.after(0, tarea)

set_actualizador_mensajes(actualizar_mensaje_seguro)

def verificar_qemu():
    try:
        return os.path.exists(QEMU_EXECUTABLE)
    except Exception as e:
        log_error("Error en verificar_qemu: " + traceback.format_exc())
        return False

def verificar_archivos():
    try:
        log_error(f"📂 Verificando existencia de archivo: {ENC_FILE}")
        return os.path.exists(ENC_FILE)
    except Exception as e:
        log_error("❌ Error en verificar_archivos: " + traceback.format_exc())
        return False

def verificar_hypervisor():
    global estado_hypervisor_override
    if estado_hypervisor_override:
        return True
    try:
        cmd = 'Get-WindowsOptionalFeature -Online | Where-Object {$_.FeatureName -eq "HypervisorPlatform"} | Select-Object -ExpandProperty State'
        result = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True)
        estado = result.stdout.strip().lower()
        return estado == "enabled" or estado == "habilitado"
    except Exception as e:
        log_error("Error en verificar_hypervisor: " + traceback.format_exc())
        return False

def actualizar_estado_botones(estado_qemu, estado_archivos, estado_hypervisor):
    boton_descargar_qemu.config(state=tk.DISABLED if estado_qemu else tk.NORMAL)
    boton_habilitar_hypervisor.config(state=tk.DISABLED if estado_hypervisor else tk.NORMAL)
    if estado_qemu and estado_archivos and estado_hypervisor:
        boton_iniciar.config(state=tk.NORMAL)
        actualizar_mensaje_seguro("✅ Todo listo para iniciar la máquina virtual.")
    else:
        boton_iniciar.config(state=tk.DISABLED)
        faltantes = []
        if not estado_qemu: faltantes.append("QEMU")
        if not estado_archivos: faltantes.append("archivo cifrado")
        if not estado_hypervisor: faltantes.append("Hypervisor")
        actualizar_mensaje_seguro("⚠️ Faltan requisitos: " + ", ".join(faltantes))

def verificar_todo():
    actualizar_mensaje_seguro("🔎 Verificando requisitos del sistema...")
    root.update()
    estado_qemu = verificar_qemu()
    estado_archivos = verificar_archivos()
    estado_hypervisor = verificar_hypervisor()
    actualizar_estado_botones(estado_qemu, estado_archivos, estado_hypervisor)

def simular_hypervisor():
    global estado_hypervisor_override
    estado_hypervisor_override = True
    messagebox.showinfo("🔧 Modo Prueba", "Ahora se simula que Hypervisor está habilitado.")
    verificar_todo()

def embebir_ventana_qemu(pid, hwnd_contenedor):
    def callback(hwnd, pid_target):
        _, pid_hwnd = win32process.GetWindowThreadProcessId(hwnd)
        if pid_hwnd == pid_target:
            win32gui.SetParent(hwnd, hwnd_contenedor)
            win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE,
                                   win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE) & ~win32con.WS_OVERLAPPEDWINDOW)
            win32gui.SetWindowPos(hwnd, None, 0, 0, 560, 300, win32con.SWP_NOZORDER)
            return False
        return True
    for _ in range(20):
        win32gui.EnumWindows(lambda hwnd, _: callback(hwnd, pid), None)
        time.sleep(0.5)

def iniciar_maquina_virtual():
    barra_progreso.set(0)
    barra_widget.pack()
    actualizar_mensaje_seguro("🔓 Descifrando la imagen, espera un momento...")
    boton_iniciar.config(state=tk.DISABLED)

    def actualizar_barra(valor):
        root.after(0, barra_progreso.set, valor)

    def tarea():
        try:
            output_img, lock_file, temp_dir, fingerprint = descifrar_img(ENC_FILE, clave_usuario, progreso_callback=actualizar_barra)
            if not os.path.exists(lock_file):
                raise Exception("❌ No se encontró archivo de validación.")
            with open(lock_file, 'r') as f:
                token = f.read().strip()
            if token != fingerprint:
                raise Exception("❌ Entorno no autorizado.")
            actualizar_mensaje_seguro("✅ Imagen descifrada. Iniciando VM...")
            cmd = [
                QEMU_EXECUTABLE,
                "-m", "2048",
                "-smp", "2",
                "-hda", output_img,
                "-net", "nic",
                "-net", "user",
                "-accel", "whpx",
                "-display", "sdl",
                "-drive", f"file=fat:rw:{temp_dir},format=raw,media=disk"
            ]
            proc = subprocess.Popen(cmd)
            time.sleep(1)
            embebir_ventana_qemu(proc.pid, frame_vm.winfo_id())
        except Exception as e:
            log_error("Error en iniciar_maquina_virtual: " + traceback.format_exc())
            messagebox.showerror("❌ Error", f"No se pudo descifrar correctamente:\n{str(e)}")
        finally:
            barra_widget.pack_forget()
            verificar_todo()

    Thread(target=tarea).start()

def limpiar_archivos_temporales():
    try:
        archivo_lista = os.path.join(tempfile.gettempdir(), "rAZCuQEwYjKxV1yCc89cqMBu0keveY.tmp")
        if os.path.exists(archivo_lista):
            with open(archivo_lista, "r") as f:
                rutas = f.read().splitlines()
            for ruta in rutas:
                if os.path.exists(ruta):
                    os.remove(ruta)
            os.remove(archivo_lista)
    except Exception as e:
        print(f"Error al limpiar archivos temporales: {e}")

root.protocol("WM_DELETE_WINDOW", lambda: (limpiar_archivos_temporales(), root.destroy()))

frame_botones = tk.Frame(root)
frame_botones.pack(pady=10)

tk.Button(frame_botones, text="Reverificar requisitos", command=verificar_todo).grid(row=0, column=0, padx=5)
arquitectura = platform.architecture()[0]
url_qemu = "https://qemu.weilnetz.de/w64/" if arquitectura == "64bit" else "https://qemu.weilnetz.de/w32/"
boton_descargar_qemu = tk.Button(frame_botones, text=f"Descargar QEMU {arquitectura}", command=lambda: os.system(f'start {url_qemu}'))
boton_descargar_qemu.grid(row=1, column=0, padx=5)

boton_habilitar_hypervisor = tk.Button(
    frame_botones,
    text="Habilitar Hypervisor (admin)",
    command=lambda: os.system(
        "start powershell -Command \"Start-Process powershell -ArgumentList 'Enable-WindowsOptionalFeature -Online -FeatureName HypervisorPlatform -All' -Verb runAs\""
    )
)
boton_habilitar_hypervisor.grid(row=2, column=0, padx=5)

boton_iniciar = tk.Button(root, text="Iniciar Máquina Virtual", font=("Arial", 12), command=iniciar_maquina_virtual, state=tk.DISABLED)
boton_iniciar.pack(pady=10)

barra_progreso = tk.IntVar()
barra_widget = ttk.Progressbar(root, orient='horizontal', length=300, mode='determinate', variable=barra_progreso)
barra_widget.pack(pady=10)
barra_widget.pack_forget()

root.after(1000, verificar_todo)
root.mainloop()
