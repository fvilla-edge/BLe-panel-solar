"""
Muestra por pantalla, en vivo, los datos del/los dispositivo(s) Victron
listados en config.py (leídos vía Bluetooth Instant Readout, sin emparejar).

Uso:
    .venv/bin/python leer_smartsolar.py
"""

import asyncio
import inspect
import time
from datetime import datetime
from enum import Enum

from victron_ble.scanner import BaseScanner
from victron_ble.devices import DeviceData, detect_device_type
from victron_ble.exceptions import AdvertisementKeyMissingError, UnknownDeviceError

from config import DEVICES

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


def parsed_to_dict(parsed: DeviceData) -> dict:
    """
    Cada anuncio trae métodos get_xxx() (get_battery_voltage, get_solar_power,
    etc.), distintos según el modelo detectado. Esta función los recorre
    todos automáticamente en vez de listarlos a mano uno por uno.
    """
    data = {}
    for name, method in inspect.getmembers(parsed, predicate=inspect.ismethod):
        if name.startswith("get_"):
            value = method()
            if isinstance(value, Enum):
                value = value.name.lower()
            if value is not None:
                data[name[4:]] = value
    return data


class PrettyScanner(BaseScanner):
    """
    BaseScanner escucha todos los anuncios Bluetooth del aire y se queda
    solo con los que traen el Company ID 0x02E1 (asignado a Victron Energy
    por Bluetooth SIG, es un dato público). Ese filtro ya viene hecho:
    a este scanner solo llegan anuncios de equipos Victron.
    """

    def __init__(self, device_keys: dict):
        super().__init__()
        # Direcciones MAC en minúscula -> clave de encriptación (config.py).
        self._device_keys = {k.lower(): v for k, v in device_keys.items()}
        # Una vez identificado el modelo de un dispositivo, queda guardado el
        # decodificador ya armado con su clave, para no rearmarlo en cada
        # anuncio (el modelo no cambia).
        self._known_devices = {}
        # Última vez que se mostró cada dirección, para el throttling.
        self._last_shown = {}

    def callback(self, ble_device, raw_data, advertisement):
        address = ble_device.address.lower()

        # Se ignora cualquier equipo Victron que no sea el buscado (por si
        # hay más de uno cerca y no está en config.py).
        if address not in self._device_keys:
            return

        if address not in self._known_devices:
            # El paquete cifrado trae, sin descifrar, un byte que indica el
            # tipo de producto (MPPT, BMV, shunt, etc.). detect_device_type
            # lee ese byte y elige la clase Python que sabe interpretar los
            # campos de ESE modelo (un SmartSolar no reporta los mismos
            # datos que una batería con shunt, por ejemplo).
            device_klass = detect_device_type(raw_data)
            if not device_klass:
                return
            # Acá entra la clave de encriptación: queda guardada junto con
            # la clase detectada, lista para descifrar el próximo anuncio
            # de esta misma dirección.
            self._known_devices[address] = device_klass(self._device_keys[address])

        try:
            # parse() desencripta el payload (AES-CTR con la clave de 16
            # bytes) y separa los campos (voltaje, corriente, etc.)
            parsed = self._known_devices[address].parse(raw_data)
        except AdvertisementKeyMissingError:
            # La clave en config.py no es la correcta para este dispositivo.
            return
        except UnknownDeviceError:
            # Se descifró pero el modelo no tiene parser conocido en esta
            # versión de victron-ble.
            return

        # Throttling: solo se muestra si pasaron >= INTERVALO_PANTALLA
        # segundos desde la última vez que se mostró esta dirección.
        ahora = time.monotonic()
        ultima_vez = self._last_shown.get(address, 0)
        if ahora - ultima_vez < INTERVALO_PANTALLA:
            return
        self._last_shown[address] = ahora

        data = parsed_to_dict(parsed)
        hora = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{hora}] {ble_device.name} ({ble_device.address})  RSSI: {advertisement.rssi} dBm")
        for clave, valor in data.items():
            unidad = UNIDADES.get(clave, "")
            print(f"    {clave}: {valor} {unidad}".rstrip())


async def main():
    print(f"Escuchando Bluetooth (una lectura por pantalla cada {INTERVALO_PANTALLA}s)... Ctrl+C para salir")
    scanner = PrettyScanner(DEVICES)
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
