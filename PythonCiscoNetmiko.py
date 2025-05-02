from netmiko import ConnectHandler

# Datos del router
R1 = {
    'device_type': 'cisco_ios',    # Ajustar según dispositivo
    'host': '192.168.228.129',     # IP del router en GNS3
    'username': 'cisco',
    'password': 'cisco',
#    'secret': 'admin',            # Si usamos clave para enable
}

# Conexión al dispositivo
net_connect = ConnectHandler(**R1)
#net_connect.enable()  # Entra al modo enable

# Enviar un comando
output = net_connect.send_command('show run')
print(output)

# Cerrar conexión
net_connect.disconnect()
