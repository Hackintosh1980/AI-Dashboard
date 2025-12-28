import asyncio
import json
import os
from datetime import datetime, timezone

from bleak import BleakScanner, BleakClient

# TB2 SERVICE / CHAR
CHAR_COMMAND = "0000fff5-0000-1000-8000-00805f9b34fb"
CHAR_NOTIFY  = "0000fff3-0000-1000-8000-00805f9b34fb"

CMD_0D = bytearray([0x0D])

# Ausgabeziel
OUTFILE = "../data/ble_dump.json"

def extract_mac(addr: str) -> str:
    # Entfernt alle Nicht-Hex-Zeichen
    hex_only = "".join(c for c in addr if c in "0123456789ABCDEFabcdef").upper()

    # Nimmt die letzten 12 Stellen (= 6 Byte)
    return hex_only[-12:]


def build_tb2_pseudoadv(mac: str, notify_bytes: bytes, counter: int, rssi: int) -> str:
    # 1) MAC extrahieren + reverse
    mac_clean = extract_mac(mac)
    mac_rev = bytes.fromhex(mac_clean)[::-1].hex().upper()

    # 2) Counter (little endian)
    ctr = counter & 0xFFFF
    ctr_hex = f"{ctr:04x}".upper()
    ctr_le = ctr_hex[2:] + ctr_hex[:2]

    # 3) Payload (10 bytes nach 0x0D)
    payload = notify_bytes[1:11].hex().upper()

    # 4) Header 19 00
    return "19" + "00" + mac_rev + ctr_le + payload


async def run():
    print("Scanning…")
    devices = await BleakScanner.discover()

    target = None
    for d in devices:
        if "ThermoBeacon2" in (d.name or ""):
            target = d
            break

    if not target:
        print("❌ Kein TB2 gefunden.")
        return

    print(f"Connecting to {target.address}: {target.name}")

    counter = 0

    async with BleakClient(target.address, timeout=15.0) as client:
        print("Connected ✔")

        # Dump-Datei vorbereiten
        os.makedirs(os.path.dirname(OUTFILE), exist_ok=True)
        if not os.path.exists(OUTFILE):
            with open(OUTFILE, "w") as f:
                json.dump([], f)

        async def handle_notify(_, data: bytearray):
            nonlocal counter

            counter += 1
            rssi = client.rssi if hasattr(client, "rssi") else 0
            pseudo_raw = build_tb2_pseudoadv(target.address, data, counter, rssi)

            print(f"[NOTIFY] {data.hex('-')}")
            print(f"[RAW] {pseudo_raw}")

            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "name": target.name,
                "address": target.address,
                "rssi": rssi,
                "raw": pseudo_raw,
                "note": "gatt"
            }

            # Datei komplett überschreiben – nur letzter Eintrag bleibt
            arr = [entry]

            with open(OUTFILE, "w") as f:
                json.dump(arr, f, indent=2)

            # Direkt erneut triggern
            await client.write_gatt_char(CHAR_COMMAND, CMD_0D)

        print("Starting notify loop…")

        await client.start_notify(CHAR_NOTIFY, handle_notify)

        # Erster Kick
        await client.write_gatt_char(CHAR_COMMAND, CMD_0D)

        print("(Running… CTRL+C beendet)")
        while True:
            await asyncio.sleep(1)


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\nStopped.")
