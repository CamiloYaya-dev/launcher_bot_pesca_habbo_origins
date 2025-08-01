from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad
from tqdm import tqdm
import os

clave = b'3n%QezhSAGk7$w!sdj29vn3v8zjNmc4q'  # 32 bytes
input_file = 'tiny10.img'
output_file = '3ZuxE7bre0kypSqM76n5dkak7zZBu0'
block_size = 64 * 1024  # 64 KB

iv = get_random_bytes(16)
cipher = AES.new(clave, AES.MODE_CBC, iv)

file_size = os.path.getsize(input_file)

with open(input_file, 'rb') as f_in, open(output_file, 'wb') as f_out:
    f_out.write(iv)
    with tqdm(total=file_size, unit='B', unit_scale=True, desc="Cifrando") as pbar:
        prev_block = f_in.read(block_size)
        while True:
            curr_block = f_in.read(block_size)
            if not curr_block:
                # Último bloque → pad
                padded = pad(prev_block, AES.block_size)
                f_out.write(cipher.encrypt(padded))
                break
            f_out.write(cipher.encrypt(prev_block))
            pbar.update(len(prev_block))
            prev_block = curr_block

print("✅ Cifrado completado:", output_file)
