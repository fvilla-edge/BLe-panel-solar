"""
Publica por MQTT en Losant los datos leídos por Bluetooth del SmartSolar
(mismo Instant Readout que usa leer_smartsolar.py).

Uso:
    .venv/bin/python publicar_losant.py
"""

import asyncio
import time

from losantmqtt import Device

from config import DEVICES
from losant_config import ACCESS_KEY, ACCESS_SECRET, DEVICE_ID
from victron_scanner import VictronScanner

# Atributos que interesa mandar a Losant. Hay que crear cada uno como
# "Attribute" del dispositivo en Losant, con este mismo nombre.
ATRIBUTOS = {
    "battery_voltage",
    "battery_charging_current",
    "solar_power",
    "yield_today",
    "external_device_load",
    "charge_state",
    "charger_error",
    "model_name",
}

# Cada cuántos segundos se publica un estado por MQTT. El dispositivo
# transmite por BLE cada 1-3s; publicar tan seguido no aporta y consume
# rápido la cuota mensual de mensajes de Losant.
INTERVALO_PUBLICACION = 30

device = Device(DEVICE_ID, ACCESS_KEY, ACCESS_SECRET)

# Última vez que se publicó cada dirección, para el throttling.
_last_sent = {}


def publicar(address, ble_device, advertisement, data):
    ahora = time.monotonic()
    if ahora - _last_sent.get(address, 0) < INTERVALO_PUBLICACION:
        return

    estado = {clave: valor for clave, valor in data.items() if clave in ATRIBUTOS}
    if estado and device.is_connected():
        estado["rssi"] = advertisement.rssi
        device.send_state(estado)
        _last_sent[address] = ahora
        print(f"Publicado: {estado}")


async def main():
    print("Conectando a Losant...")
    device.connect(blocking=False)
    scanner = VictronScanner(DEVICES, publicar)
    await scanner.start()
    try:
        while True:
            device.loop()
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        await scanner.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCortado por el usuario.")
