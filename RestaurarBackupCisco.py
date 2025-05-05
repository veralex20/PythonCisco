import paramiko
import os
from netmiko import ConnectHandler

import logging

logging.basicConfig(filename='netmiko.log', level=logging.DEBUG)

# Datos de conexión SFTP
sftp_host = "192.168.228.130"
sftp_port = 2222
sftp_username = "user"
sftp_password = "password"
remote_backup_path = f"/upload/"  # Reemplaza con la ruta real en el servidor SFTP

# Datos de conexión del router Cisco
cisco_host = "192.168.228.129"  # Reemplaza con la IP de tu router Cisco
cisco_username = "cisco"  # Reemplaza con el usuario de tu router Cisco
cisco_password = "cisco"  # Reemplaza con la contraseña de tu router Cisco
cisco_device_type = "cisco_ios"  # Tipo de dispositivo para Netmiko

# Ruta local para guardar temporalmente el archivo
local_config_path = os.path.expanduser("~/backup_configs")  # Directorio para guardar los archivos descargados

def listar_archivos_respaldo_paramiko(sftp_client, ruta_remota, extensiones=(".txt",)):
    """Lista los archivos .txt en la ruta remota del servidor SFTP usando paramiko."""
    try:
        archivos = sftp_client.listdir(ruta_remota)
        respaldos = [archivo for archivo in archivos if archivo.endswith(extensiones)]
        return respaldos
    except Exception as e:
        print(f"Error al listar archivos en {ruta_remota}: {e}")
        return []

def seleccionar_archivo(lista_archivos):
    """Permite al usuario seleccionar un archivo de la lista."""
    if not lista_archivos:
        print("No se encontraron archivos de respaldo (.txt).")
        return None

    print("\nArchivos de respaldo disponibles:")
    for i, archivo in enumerate(lista_archivos):
        print(f"{i + 1}. {archivo}")

    while True:
        try:
            seleccion = int(input("Seleccione el número del archivo a restaurar: "))
            if 1 <= seleccion <= len(lista_archivos):
                return lista_archivos[seleccion - 1]
            else:
                print("Selección inválida. Por favor, ingrese un número de la lista.")
        except ValueError:
            print("Entrada inválida. Por favor, ingrese un número.")

def descargar_archivo_sftp(sftp_client, archivo_remoto, ruta_local):
    """Descarga el archivo desde el servidor SFTP a la ruta local."""
    ruta_remota_completa = os.path.join(remote_backup_path, archivo_remoto)
    ruta_local_completa = os.path.join(ruta_local, archivo_remoto)
    os.makedirs(ruta_local, exist_ok=True)  # Asegura que el directorio local exista
    try:
        print(f"[*] Descargando {archivo_remoto} desde {ruta_remota_completa} a {ruta_local_completa}...")
        sftp_client.get(ruta_remota_completa, ruta_local_completa)
        print("[+] Archivo descargado exitosamente.")
        return ruta_local_completa
    except Exception as e:
        print(f"Error al descargar {archivo_remoto}: {e}")
        return None

def aplicar_configuracion_directa(net_connect, ruta_archivo_local):
    """Lee el archivo de configuración local y lo aplica directamente al running-config del router."""
    try:
        with open(ruta_archivo_local, "r") as archivo_config:
            config_commands = archivo_config.read().splitlines()

        print("[*] Entrando al modo de configuración global...")
        net_connect.send_command("configure terminal")
        output_config_mode = net_connect.expect_exact("R1(config)#", timeout=20)  # Esperar el prompt de config correcto
        print(output_config_mode)

        print("[*] Aplicando configuración al router...")
        output = net_connect.send_config_set(config_commands, expect_string=r"R1(config)#|R1#", read_timeout=60)
        print(output)
        print("[+] Configuración aplicada exitosamente.")

        print("[*] Saliendo del modo de configuración global...")
        net_connect.send_command("end")
        output_end_mode = net_connect.expect_exact("R1(config)#|R1#", timeout=10)  # Esperar el prompt privilegiado correcto
        print(output_end_mode)

        return True
    except FileNotFoundError:
        print(f"[!] Error: El archivo no se encontró en {ruta_archivo_local}")
        return False
    except Exception as e:
        print(f"[!] Ocurrió un error al aplicar la configuración: {e}")
        return False

def main():
    """Función principal del script para descargar desde SFTP y aplicar configuración directa."""
    transport = None
    sftp_client = None
    net_connect = None
    try:
        print(f"[*] Conectando al servidor SFTP {sftp_host}:{sftp_port}...")
        transport = paramiko.Transport((sftp_host, sftp_port))
        transport.connect(username=sftp_username, password=sftp_password)
        sftp_client = paramiko.SFTPClient.from_transport(transport)
        print("[+] Conexión SFTP exitosa.")

        archivos_respaldo = listar_archivos_respaldo_paramiko(sftp_client, remote_backup_path)

        if archivos_respaldo:
            archivo_seleccionado = seleccionar_archivo(archivos_respaldo)

            if archivo_seleccionado:
                print(f"\n[*] Intentando restaurar la configuración desde: {archivo_seleccionado}")
                ruta_archivo_local = descargar_archivo_sftp(sftp_client, archivo_seleccionado, local_config_path)

                if ruta_archivo_local:
                    print(f"[*] Conectando al router Cisco {cisco_host}...")
                    net_connect = ConnectHandler(
                        device_type=cisco_device_type,
                        host=cisco_host,
                        username=cisco_username,
                        password=cisco_password,
                    )
                    print("[+] Conexión SSH exitosa al router.")

                    if aplicar_configuracion_directa(net_connect, ruta_archivo_local):
                        print("[+] Proceso de restauración completado.")

                        guardar_config = input("¿Desea guardar la configuración a la startup-config? (yes/no): ").lower()
                        if guardar_config == "yes":
                            output_guardar = net_connect.send_command("write memory", expect_string=r"#", strip_prompt=False, strip_command=False)
                            print(output_guardar)
                            print("Configuración guardada a la startup-config.")
                    else:
                        print("[!] Falló la aplicación directa de la configuración.")
                else:
                    print("[!] No se pudo descargar el archivo desde el servidor SFTP.")
        else:
            print("No se encontraron archivos de respaldo (.txt) en la ruta especificada.")

    except paramiko.AuthenticationException:
        print("[!] Error de autenticación SFTP. Verifica tu usuario y contraseña.")
    except paramiko.SSHException as e:
        print(f"[!] Error al establecer la conexión SSH al servidor SFTP o al router: {e}")
    except Exception as e:
        print(f"[!] Ocurrió un error inesperado: {e}")
    finally:
        if sftp_client:
            sftp_client.close()
        if transport:
            transport.close()
        if net_connect:
            net_connect.disconnect()
        print("[*] Conexiones cerradas.")

if __name__ == "__main__":
    main()