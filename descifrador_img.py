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

def escribir_serial_en_img(temp_dir, serial):
    archivo_serial = os.path.join(temp_dir, "clave_licencia.txt")
    with open(archivo_serial, "w") as f:
        f.write(serial)
    print(f"✅ Serial escrito en: {archivo_serial}")

def descifrar_img(input_file, serial, progreso_callback=None):
    temp_dir = tempfile.mkdtemp()
    vfat_dir = tempfile.mkdtemp()  # <-- Nueva carpeta solo para montar

    fingerprint = generar_fingerprint()
    nombre_aleatorio = uuid.uuid4().hex[:16]
    output_img = os.path.join(temp_dir, f"{nombre_aleatorio}.img")
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

    # ✅ Inyectar el serial en la carpeta VFAT (diferente a la del .img)
    escribir_serial_en_img(vfat_dir, serial)

    # Guardar rutas para limpieza posterior
    with open(os.path.join(temp_dir, "rAZCuQEwYjKxV1yCc89cqMBu0keveY.tmp"), "w") as f:
        f.write(f"{output_img}\n{lock_file}\n{vfat_dir}")

    return output_img, lock_file, vfat_dir, fingerprint
