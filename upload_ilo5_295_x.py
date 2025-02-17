import hpilo
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve server details from environment variables
hostname = os.getenv('DCC0-ILO-IP-ADDRESS')
username = os.getenv('DCC0-ILO-USERNAME')
password = os.getenv('DCC0-ILO-PASSWORD')

# Check if all required environment variables are set
if not all([hostname, username, password]):
    raise ValueError("Missing one or more environment variables. Check your .env file.")

# Connect to the iLO
ilo = hpilo.Ilo(hostname, username, password)

# Check current firmware version
current_version = ilo.get_fw_version()
print(f"Current iLO firmware version: {current_version}")

# Define the path to the firmware file in the current directory
firmware_path = os.path.join(os.getcwd(), 'ilo5_295.bin')

# Function to show progress of firmware update
def print_progress(text):
    sys.stdout.write('\r\033[K' + text)
    sys.stdout.flush()

# Update firmware
try:
    ilo.update_rib_firmware(filename=firmware_path, progress=print_progress)
    print("\nFirmware update completed.")
except Exception as e:
    print(f"An error occurred during firmware update: {e}")

# Verify the firmware version after update
updated_version = ilo.get_fw_version()
print(f"Updated iLO firmware version: {updated_version}")
