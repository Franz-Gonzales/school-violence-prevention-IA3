import tinytuya
import time

# Configura las credenciales del dispositivo
TUYA_DEVICE_ID="ebdec829afd5c0e395bmjo"
TUYA_IP_ADDRESS="192.168.1.16"
TUYA_LOCAL_KEY="`?6TnKAIXb=4h)4*"
TUYA_DEVICE_VERSION="3.5"   

# Conectar al dispositivo
device = tinytuya.Device(TUYA_DEVICE_ID, TUYA_IP_ADDRESS, TUYA_LOCAL_KEY, version=TUYA_DEVICE_VERSION)

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