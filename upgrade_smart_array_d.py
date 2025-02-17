import hpilo
import sys
import os

# Progress callback function
def print_progress(text):
    sys.stdout.write('\r\033[K' + text)  # Overwrite the previous message
    sys.stdout.flush()

# Connect to iLO
ilo = hpilo.Ilo(hostname='<iLO_IP>', login='<username>', password='<password>')

# Check current firmware version
current_fw_version = ilo.get_fw_version()
print(f"Current Firmware Version: {current_fw_version}")

# Path to the extracted .bin file
firmware_file = 'cp051996.bin'

# Verify the firmware file exists
if not os.path.exists(firmware_file):
    raise FileNotFoundError(f"Firmware file '{firmware_file}' not found.")

# Read the firmware file
with open(firmware_file, 'rb') as fw_file:
    firmware_data = fw_file.read()

# Upload the firmware to the iLO firmware server
print("Uploading firmware...")
ilo.upload_firmware(firmware_file, firmware_data)

# Flash the firmware with progress monitoring
print("Flashing firmware...")
ilo.update_rib_firmware(filename=firmware_file, progress=print_progress)

# Print a newline after progress messages
print("\nFirmware upgrade completed.")
