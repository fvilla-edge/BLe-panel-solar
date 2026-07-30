"""
Muestra por pantalla, en vivo, los datos del/los dispositivo(s) Victron
listados en config.py (leídos vía Bluetooth Instant Readout, sin emparejar).

Uso:
    .venv/bin/python leer_smartsolar.py
"""

import asyncio
import time
from datetime import datetime

from config import DEVICES
from victron_scanner import VictronScanner

# Cada cuántos segundos se muestra por pantalla un mismo dispositivo.
# El dispositivo sigue transmitiendo cada 1-3 segundos igual; esto solo
# frena la impresión, no la lectura.
INTERVALO_PANTALLA = 20

# Unidad de cada campo, según la documentación de victron-ble
# (victron_ble/devices/solar_charger.py). Lo que no está listado acá es
# texto sin unidad (charge_state, charger_error, model_name).
UNIDADES = {
    "battery_voltage": "V",
    "battery_charging_current": "A",
    "solar_power": "W",
    "yield_today": "Wh",
    "external_device_load": "A",
}

# Última vez que se mostró cada dirección, para el throttling.
_last_shown = {}


def mostrar(address, ble_device, advertisement, data):
    ahora = time.monotonic()
    if ahora - _last_shown.get(address, 0) < INTERVALO_PANTALLA:
        return
    _last_shown[address] = ahora

    hora = datetime.now().strftime("%H:%M:%S")
    print(f"\n[{hora}] {ble_device.name} ({ble_device.address})  RSSI: {advertisement.rssi} dBm")
    for clave, valor in data.items():
        unidad = UNIDADES.get(clave, "")
        print(f"    {clave}: {valor} {unidad}".rstrip())


async def main():
    print(f"Escuchando Bluetooth (una lectura por pantalla cada {INTERVALO_PANTALLA}s)... Ctrl+C para salir")
    scanner = VictronScanner(DEVICES, mostrar)
    await scanner.start()
    try:
        while True:
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
