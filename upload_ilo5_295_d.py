import hpilo
import sys
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Progress callback function to monitor firmware update progress
def print_progress(text):
    sys.stdout.write('\r\033[K' + text)  # Overwrite the previous message
    sys.stdout.flush()

# Connect to iLO using environment variables
hostname = os.getenv('HOSTNAME')
username = os.getenv('USERNAME')
password = os.getenv('PASSWORD')

if not all([hostname, username, password]):
    raise ValueError("Missing environment variables. Please check your .env file.")

ilo = hpilo.Ilo(hostname=hostname, login=username, password=password)

# Check current firmware version
current_fw_version = ilo.get_fw_version()
print(f"Current Firmware Version: {current_fw_version}")

# Read the firmware file from the current directory
firmware_file = 'ilo5_295.bin'
with open(firmware_file, 'rb') as fw_file:
    firmware_data = fw_file.read()

# Upload the firmware to the iLO firmware server
print("Uploading firmware...")
ilo.upload_firmware(firmware_file, firmware_data)

# Flash the firmware
print("Flashing firmware...")
ilo.update_rib_firmware(filename=firmware_file, progress=print_progress)

# Print a newline after progress messages
print("\nFirmware upgrade completed.")
