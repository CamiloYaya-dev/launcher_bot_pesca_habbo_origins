from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import os
import tempfile
import uuid
import hashlib
import platform

clave = b'3n%QezhSAGk7$w!sdj29vn3v8zjNmc4q'
block_size = 64 * 1024  # 64 KB

def generar_fingerprint():
    datos = platform.node() + platform.version() + str(uuid.getnode())
    return hashlib.sha256(datos.encode()).hexdigest()

def descifrar_img(input_file, progreso_callback=None):
    temp_dir = tempfile.gettempdir()
    os.makedirs(temp_dir, exist_ok=True)

    fingerprint = generar_fingerprint()
    nombre_aleatorio = uuid.uuid4().hex[:16]
    nombre_aleatorio_bat = uuid.uuid4().hex[:16]
    output_img = os.path.join(temp_dir, f"{nombre_aleatorio}")  # sin extensión
    output_bat = os.path.join(temp_dir, f"{nombre_aleatorio_bat}.bat")
    lock_file = os.path.join(temp_dir, '.lock')

    with open(lock_file, 'w') as lock:
        lock.write(fingerprint)

    with open(input_file, 'rb') as f_in:
        iv = f_in.read(16)
        cipher = AES.new(clave, AES.MODE_CBC, iv)
        file_size = os.path.getsize(input_file) - 16

        total_read = 0
        with open(output_img, 'wb') as f_out:
            while True:
                chunk = f_in.read(block_size)
                if not chunk:
                    break
                decrypted = cipher.decrypt(chunk)
                if f_in.tell() == os.path.getsize(input_file):
                    decrypted = unpad(decrypted, AES.block_size)
                f_out.write(decrypted)
                total_read += len(chunk)

                if progreso_callback:
                    progreso_callback(int(total_read / file_size * 100))

    bat_content = f"""@echo off
cd /d "{temp_dir}"
if not exist ".lock" (
    echo ❌ No se encontró archivo de validación. Saliendo...
    pause
    exit /b
)
for /f %%i in ('type ".lock"') do set "token=%%i"
set "current={fingerprint}"
if not "%token%"=="%current%" (
    echo ❌ Entorno no autorizado. Abortando ejecución.
    pause
    exit /b
)
start "" /b "C:\\Program Files\\qemu\\qemu-system-x86_64.exe" ^
 -m 4096 ^
 -smp 2 ^
 -hda "{output_img}" ^
 -net nic ^
 -net user ^
 -display sdl ^
 -accel whpx
"""

    with open(output_bat, 'w', encoding="utf-8") as f:
        f.write(bat_content)

    with open(os.path.join(temp_dir, "rAZCuQEwYjKxV1yCc89cqMBu0keveY.tmp"), "w") as f:
        f.write(f"{output_img}\n{output_bat}\n{lock_file}")

    return output_bat
