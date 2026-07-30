# Lectura del SmartSolar por Bluetooth

Dispositivo: **SmartSolar Charger MPPT 75/15 rev2** (HQ2248DRUEV)
MAC: `CB:EA:5B:96:33:6C`

## Cómo funciona

Este cargador transmite sus datos (voltaje, corriente, potencia solar, etc.)
como "Instant Readout": un anuncio Bluetooth LE cifrado que cualquier equipo
cercano puede escuchar **sin emparejar**. Para leerlo hace falta la clave de
encriptación de 16 bytes (32 caracteres hex) propia de ese dispositivo.

Esto es distinto del "Connect" completo que hace la app VictronConnect por
Bluetooth (ese usa un servicio GATT propietario tipo VE.Direct y pide un PIN
de emparejamiento, normalmente `000000`). Ese otro camino se intentó primero
acá y falló por timeout de emparejamiento — no hace falta para leer los datos
en vivo, así que no vale la pena insistir con él.

## Cómo conseguir/renovar la clave de encriptación

1. Abrir VictronConnect en el celular y conectarse al dispositivo (PIN `000000`
   la primera vez).
2. Tocar el ícono de ajustes ⚙ del dispositivo (dentro de su pantalla, no el
   menú general de la app).
3. Ir a **"Product info"**.
4. Buscar **"Instant readout via Bluetooth"** y tocar **"Show"** al lado de la
   clave de encriptación.
5. Copiar esa clave (32 caracteres hex) y la MAC del dispositivo.

Esta clave puede cambiar si se resetea el dispositivo o se regenera desde la
app. Si el script deja de mostrar datos, revisar acá primero.

## Dónde está guardado

- `config.py` — MAC + clave de encriptación del dispositivo.
- `leer_smartsolar.py` — script que escucha Bluetooth y muestra los datos por
  pantalla en vivo (no guarda nada en disco).
- `.venv/` — entorno virtual de Python con las dependencias (`bleak`,
  `victron-ble`). No se instaló nada a nivel de sistema salvo `python3-pip`.

## Requisitos del sistema

- Adaptador Bluetooth funcionando (`bluetoothctl` y `rfkill` sin bloqueos).
- `python3-pip` y `python3-venv` instalados (vía `apt`).
- El SmartSolar tiene que tener habilitado "Instant readout via Bluetooth"
  en VictronConnect (viene activado por defecto).

## Cómo correrlo

```
cd "BLe panel solar"
.venv/bin/python leer_smartsolar.py
```

Ctrl+C para cortar.

## Agregar otro dispositivo Victron

Sumar una línea en `config.py` con su MAC y su clave (mismo procedimiento de
arriba), y agregarlo también en `DEVICES` dentro de `leer_smartsolar.py` si
hace falta filtrar por más de uno (ya soporta varios automáticamente, el
diccionario `DEVICES` de `config.py` es compartido).

## Publicar en Losant por MQTT

`publicar_losant.py` toma los mismos datos de `leer_smartsolar.py` (reusa
`victron_scanner.py`) y los publica como estado del dispositivo en Losant,
usando la librería `losantmqtt`.

```
.venv/bin/python publicar_losant.py
```

Publica cada 30s por dispositivo (`INTERVALO_PUBLICACION` en el script),
para no gastar de golpe la cuota mensual de mensajes de Losant.

### Credenciales

Van en `losant_config.py` (no se sube a git, está en `.gitignore`):

```python
DEVICE_ID = "..."
ACCESS_KEY = "..."
ACCESS_SECRET = "..."
```

