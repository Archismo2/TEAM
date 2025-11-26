#pip install bleak
import asyncio
from bleak import BleakScanner, BleakClient



devAddy = input("Enter the device address (XX:XX:XX:XX:XX:XX): ")

async def get_ble_battery_level(device_address):
    async with BleakClient(device_address) as client:
        # Find the battery service and characteristic (replace with actual UUIDs)
        battery_service_uuid = "0000180f-0000-1000-8000-00805f9b34fb"  # Generic Battery Service UUID
        battery_level_char_uuid = "00002a19-0000-1000-8000-00805f9b34fb" # Battery Level Characteristic UUID

        battery_level = await client.read_gatt_char(battery_level_char_uuid)
        return int(battery_level[0]) # Battery level is typically a single byte


device_address = devAddy
battery_percentage = asyncio.run(get_ble_battery_level(device_address))
print(f"Battery level: {battery_percentage}%")
