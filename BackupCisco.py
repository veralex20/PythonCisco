from netmiko import ConnectHandler
import datetime
import paramiko
import os

# 1. Datos del router
router = {
    'device_type': 'cisco_ios',
    'host': '192.168.228.129',
    'username': 'cisco',
    'password': 'cisco'
}

# 2. Fecha y nombre del archivo
fecha = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
nombre_archivo = f"R1-backup-{fecha}.txt"

# 3. Conectarse al router y obtener la config
print("[*] Conectando al router...")
conexion = ConnectHandler(**router)
print("[*] Obteniendo configuración...")
config = conexion.send_command("show running-config")
conexion.disconnect()

# 4. Guardar localmente
with open(nombre_archivo, "w") as f:
    f.write(config)
print(f"[+] Backup guardado localmente como {nombre_archivo}")

# 5. Datos del servidor SFTP
sftp_host = "192.168.228.130"
sftp_port = 2222                    # puerto del servidor sftp
sftp_user = "user"                  # tu usuario SFTP
sftp_pass = "password"              # contraseña SFTP
ruta_remota = f"/upload/{nombre_archivo}" # ruta donde se almacenaran los backup

# 6. Subir al servidor SFTP
try:
    print("[*] Conectando al servidor SFTP...")
    transport = paramiko.Transport((sftp_host, sftp_port))
    transport.connect(username=sftp_user, password=sftp_pass)
    sftp = paramiko.SFTPClient.from_transport(transport)
    print(f"[*] Subiendo backup a {ruta_remota}...")
    sftp.put(nombre_archivo, ruta_remota)
    sftp.close()
    transport.close()
    print("[+] Backup subido correctamente al servidor SFTP.")

# 7. Borrar archivo local
    os.remove(nombre_archivo)
    print(f"[+] Archivo local {nombre_archivo} eliminado.")

except Exception as e:
    print(f"[!] Error al subir el archivo: {e}")
