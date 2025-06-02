import tinytuya
import time

# Configura las credenciales del dispositivo
DEVICE_ID = "eba3f1c2eaca6f424bujr8"  # Device ID de la sirena
IP_ADDRESS = "192.168.1.12"           # IP de la sirena
LOCAL_KEY = "Lc.eV;q?b[4'_?5'"       # Local Key de la sirena
DEVICE_VERSION = "3.5"   

# Conectar al dispositivo
device = tinytuya.Device(DEVICE_ID, IP_ADDRESS, LOCAL_KEY, version=DEVICE_VERSION)

try:
    # Obtener el estado actual del dispositivo (para depuración)
    status = device.status()
    print("Estado del dispositivo:", status)

    # Activar la sirena (DPS '104' parece ser el interruptor ON/OFF)
    print("Activando la sirena...")
    device.set_value(104, True)  # Enciende la sirena
    time.sleep(2)                # Mantén encendida por 5 segundos
    print("Desactivando la sirena...")
    device.set_value(104, False)  # Apaga la sirena

except Exception as e:
    print("Error:", e)

finally:
    print("Operación completada")