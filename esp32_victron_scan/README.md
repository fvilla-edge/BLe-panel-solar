# esp32_victron_scan

Sketch de prueba para el ESP32-C3 Super Mini: escanea BLE, filtra los
advertisements del SmartSolar (Company ID `0x02E1`, record type `0x10`) y
tira la manufacturer data cruda por USB serial. Es el paso previo a portar
el desencriptado a C — ver la memoria `esp32_victron_scan` del proyecto
para el contexto completo.

## Una sola vez: instalar el toolchain

Ya está instalado en esta máquina (`arduino-cli` en `~/.local/bin`, en el
PATH). Si hay que repetirlo en otra:

```bash
mkdir -p ~/.local/bin
curl -fsSL -o /tmp/arduino-cli.tar.gz https://downloads.arduino.cc/arduino-cli/arduino-cli_latest_Linux_64bit.tar.gz
tar -xzf /tmp/arduino-cli.tar.gz -C ~/.local/bin arduino-cli

arduino-cli config init
arduino-cli config set board_manager.additional_urls https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
arduino-cli core update-index
arduino-cli core install esp32:esp32
arduino-cli lib install "NimBLE-Arduino"
```

## Compilar

Desde la carpeta del proyecto (`BLe panel solar /`, la que tiene este
`README.md` adentro de `esp32_victron_scan/`):

```bash
arduino-cli compile --fqbn esp32:esp32:nologo_esp32c3_super_mini esp32_victron_scan
```

`nologo_esp32c3_super_mini` es el board definido para el "ESP32-C3 Super
Mini" (la placa genérica sin marca). Si compila mal por esto, buscar el
FQBN correcto con `arduino-cli board listall | grep -i c3`.

## Flashear

Con la placa conectada por USB (aparece como `/dev/ttyACM0`):

```bash
arduino-cli upload -p /dev/ttyACM0 --fqbn esp32:esp32:nologo_esp32c3_super_mini esp32_victron_scan
```

Si el puerto es otro, confirmarlo con `ls /dev/ttyACM*` o `ls /dev/ttyUSB*`.

## Ver los datos por terminal

```bash
arduino-cli monitor -p /dev/ttyACM0 -c baudrate=115200
```

Al conectar, la placa se resetea sola (mensajes de boot del ROM) y después
tira líneas del tipo:

```
Iniciando escaneo BLE (Victron, Company ID 0x02E1)...
MAC=cb:ea:5b:96:33:6c RSSI=-95 LEN=22 DATA=E102100275A0012C393A21AE2614AF458B466539DA40
```

Salir con `Ctrl+C`.

Si por lo que sea `arduino-cli monitor` no anda, alternativa con `screen`
(instalado en esta máquina):

```bash
screen /dev/ttyACM0 115200
```

Salir de `screen`: `Ctrl+A` seguido de `k`, después confirmar con `y`.

## Notas

- El RSSI suele verse débil (-90 a -100) porque el SmartSolar está lejos
  o hay obstáculos — no es un problema del sketch. Si no aparece ninguna
  línea en ~15-20s, primero confirmar que el SmartSolar está encendido y
  anunciando (con `victron_scanner.py`/`leer_smartsolar.py` desde esta PC).
- Solo filtra el tipo de paquete que importa (`0x10`, Instant Readout
  cifrado). Victron manda otros advertisements con el mismo Company ID que
  se descartan a propósito (ver la memoria del proyecto para el detalle).
