import pysftp
import os
from netmiko import ConnectHandler

# Datos de conexión SFTP
sftp_host = "192.168.228.130"
sftp_port = 2222
sftp_username = "user"
sftp_password = "password"
remote_backup_path = f"/upload/" #/ruta/a/tus/backups/" Reemplaza con la ruta real en el servidor SFTP
local_download_path = "D:/Documentos/Respaldos locales"  #"/ruta/donde/guardar/localmente/" Reemplaza con la ruta local deseada

# Datos de conexión del router Cisco
cisco_host = "192.168.228.129"  # Reemplaza con la IP de tu router Cisco
cisco_username = "cisco"  # Reemplaza con el usuario de tu router Cisco
cisco_password = "cisco"  # Reemplaza con la contraseña de tu router Cisco
cisco_device_type = "cisco_ios"  # Tipo de dispositivo para Netmiko

def listar_archivos_respaldo(sftp, ruta_remota, extensiones=(".cfg", ".backup", ".txt")):
    """Lista los archivos en la ruta remota del servidor SFTP con las extensiones especificadas."""
    try:
        archivos = sftp.listdir(ruta_remota)
        respaldos = [archivo for archivo in archivos if archivo.endswith(extensiones)]
        return respaldos
    except pysftp.exceptions.SFTPError as e:
        print(f"Error al listar archivos en {ruta_remota}: {e}")
        return []

def seleccionar_archivo(lista_archivos):
    """Permite al usuario seleccionar un archivo de la lista."""
    if not lista_archivos:
        print("No se encontraron archivos de respaldo.")
        return None

    print("\nArchivos de respaldo disponibles:")
    for i, archivo in enumerate(lista_archivos):
        print(f"{i + 1}. {archivo}")

    while True:
        try:
            seleccion = int(input("Seleccione el número del archivo a descargar y restaurar: "))
            if 1 <= seleccion <= len(lista_archivos):
                return lista_archivos[seleccion - 1]
            else:
                print("Selección inválida. Por favor, ingrese un número de la lista.")
        except ValueError:
            print("Entrada inválida. Por favor, ingrese un número.")

def descargar_archivo(sftp, archivo_remoto, ruta_local):
    """Descarga el archivo remoto al directorio local."""
    ruta_remota_completa = os.path.join(remote_backup_path, archivo_remoto)
    ruta_local_completa = os.path.join(ruta_local, archivo_remoto)
    try:
        print(f"Descargando {archivo_remoto} a {ruta_local_completa}...")
        sftp.get(ruta_remota_completa, ruta_local_completa)
        print(f"Descarga de {archivo_remoto} completada.")
        return ruta_local_completa
    except pysftp.exceptions.SFTPError as e:
        print(f"Error al descargar {archivo_remoto}: {e}")
        return None

def restaurar_configuracion_cisco(ruta_archivo_local):
    """Intenta restaurar la configuración en el router Cisco."""
    try:
        net_connect = ConnectHandler(
            device_type=cisco_device_type,
            host=cisco_host,
            username=cisco_username,
            password=cisco_password,
        )
        print(f"Conexión SSH exitosa a {cisco_host}")

        # *** AQUÍ DEBES IMPLEMENTAR LA LÓGICA DE RESTAURACIÓN ESPECÍFICA ***
        # Esto dependerá de cómo se aplican las configuraciones en tu entorno.
        # Algunas posibilidades:
        # 1. Copiar el archivo de configuración al router (TFTP, SCP).
        # 2. Pegar el contenido del archivo directamente en la configuración.
        # 3. Utilizar comandos específicos de Cisco para restaurar desde un archivo.

        # Ejemplo (MUY GENÉRICO y probablemente INCOMPLETO):
        # print("Iniciando proceso de restauración...")
        # # Si necesitas copiar el archivo al router primero (ej. usando TFTP):
        # # net_connect.send_command(f"copy tftp://TU_SERVIDOR_TFTP/{os.path.basename(ruta_archivo_local)} running-config")
        # # output = net_connect.send_command("reload") # ¡CUIDADO! Esto reiniciará el router.
        # print("Proceso de restauración (ejemplo) completado. ¡REVISA TU ROUTER!")

        print("\n*** IMPORTANTE: Debes implementar la lógica de restauración específica para tu entorno Cisco aquí. ***")
        print("Revisa la documentación de tu router sobre cómo restaurar la configuración desde un archivo.")

        net_connect.disconnect()
        print("Conexión SSH cerrada.")

    except Exception as e:
        print(f"Ocurrió un error al conectar o restaurar la configuración en el router: {e}")

def main():
    """Función principal del script."""
    try:
        with pysftp.Connection(sftp_host, username=sftp_username, password=sftp_password, port=sftp_port) as sftp:
            print(f"Conexión SFTP exitosa a {sftp_host}:{sftp_port}")

            archivos_respaldo = listar_archivos_respaldo(sftp, remote_backup_path)

            if archivos_respaldo:
                archivo_seleccionado = seleccionar_archivo(archivos_respaldo)

                if archivo_seleccionado:
                    ruta_archivo_local = descargar_archivo(sftp, archivo_seleccionado, local_download_path)
                    if ruta_archivo_local:
                        print(f"\nArchivo de respaldo descargado en: {ruta_archivo_local}")
                        restaurar_configuracion_cisco(ruta_archivo_local)
            else:
                print("No se encontraron archivos de respaldo en la ruta especificada.")

    except pysftp.exceptions.ConnectionException as e:
        print(f"Error de conexión SFTP: {e}")
    except pysftp.exceptions.CredentialException as e:
        print(f"Error de autenticación SFTP: {e}")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")

if __name__ == "__main__":
    main()