import os
import sys
import hpilo
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve iLO credentials from .env
ILO_IP = os.getenv("ILO_HOSTNAME")
ILO_USER = os.getenv("ILO_USERNAME")
ILO_PASSWORD = os.getenv("ILO_PASSWORD")
FIRMWARE_FILE = "ilo5_295.bin"

def print_progress(text):
    sys.stdout.write("\r\033[K" + text)
    sys.stdout.flush()

try:
    # Validate if environment variables are loaded
    if not all([ILO_IP, ILO_USER, ILO_PASSWORD]):
        print("Error: Missing iLO credentials in .env file.")
        sys.exit(1)

    # Connect to iLO
    ilo = hpilo.Ilo(hostname=ILO_IP, login=ILO_USER, password=ILO_PASSWORD)

    # Get and print the current firmware version
    firmware_info = ilo.get_fw_version()
    print(f"Current iLO Firmware Version: {firmware_info}")

    # Check if firmware file exists
    if not os.path.exists(FIRMWARE_FILE):
        print(f"Error: Firmware file {FIRMWARE_FILE} not found in the current directory.")
        sys.exit(1)

    # Upload and flash the new firmware
    print("Uploading and flashing new firmware...")
    ilo.update_rib_firmware(filename=FIRMWARE_FILE, progress=print_progress)

    print("\nFirmware update initiated successfully. Please wait for completion.")
    
except hpilo.IloError as e:
    print(f"Failed to update firmware: {e}")
