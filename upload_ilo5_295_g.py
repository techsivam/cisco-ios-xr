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

# ... (rest of the code remains the same)

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

    # ... (rest of the firmware update code as before)

except FileNotFoundError as e:
    print(f"Error: {e}")
except hpilo.HPIloError as e:
    print(f"iLO Error: {e}")
except ValueError as e: # Catch the new ValueError
    print(f"Error: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    if 'ilo' in locals() and ilo is not None:
        ilo.close()
