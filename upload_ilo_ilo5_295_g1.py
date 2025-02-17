import hpilo
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# iLO Credentials from .env
ilo_ip = os.getenv("DCC0-ILO-IP-ADDRESS")
ilo_username = os.getenv("DCC0-ILO-USERNAME")
ilo_password = os.getenv("DCC0-ILO-PASSWORD")

# Firmware File Path (Assumes it's in the same directory as the script)
firmware_file = "ilo5_295.bin"

def print_progress(text):
    sys.stdout.write('\r\033[K' + text)
    sys.stdout.flush()

try:
    # Check if required environment variables are set
    if not all([ilo_ip, ilo_username, ilo_password]):
        raise ValueError("Missing required iLO credentials in .env file.")

    # Establish iLO Connection
    ilo = hpilo.Ilo(ilo_ip, username=ilo_username, password=ilo_password)

    # Get Current Firmware Version
    current_firmware = ilo.get_firmware_version()
    print(f"Current iLO Firmware: {current_firmware}")

    # Check if the firmware file exists
    if not os.path.exists(firmware_file):
        raise FileNotFoundError(f"Firmware file not found: {firmware_file}")

    # Upload and Flash Firmware
    print(f"Uploading and flashing firmware: {firmware_file}")
    with open(firmware_file, "rb") as f:
        ilo.update_firmware(f)

    # Monitor Firmware Update Progress
    while True:
        update_status = ilo.get_firmware_update_status()
        print_progress(f"Firmware Update Status: {update_status}")
        if "Complete" in update_status:
            print_progress("Firmware update completed successfully!\n")
            break
        elif "Failed" in update_status or "Error" in update_status:
            print_progress(f"Firmware update failed: {update_status}\n")
            break
        import time
        time.sleep(10)  # Adjust sleep time as needed

    # Verify New Firmware Version
    new_firmware = ilo.get_firmware_version()
    print(f"New iLO Firmware: {new_firmware}")

    ilo.close()

except FileNotFoundError as e:
    print(f"Error: {e}")
except hpilo.HPIloError as e:
    print(f"iLO Error: {e}")
except ValueError as e:
    print(f"Error: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    if 'ilo' in locals() and ilo is not None:
        ilo.close()
