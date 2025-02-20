import requests
import json
import os
import sys
import time
import logging
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration from .env
ILO_HOSTNAME = os.getenv("ILO_HOSTNAME")
ILO_USERNAME = os.getenv("ILO_USERNAME")
ILO_PASSWORD = os.getenv("ILO_PASSWORD")
BASE_URL = f"https://{ILO_HOSTNAME}/redfish/v1"

# Possible paths for firmware files
FIRMWARE_FILE_NAME = "cp051996.exe"
COMPSIG_FILE_NAME = "cp051996.compsig"
CURRENT_DIR = os.getcwd()
FILES_DIR = os.path.join(CURRENT_DIR, "files")
FIRMWARE_PATHS = [
    os.path.join(CURRENT_DIR, FIRMWARE_FILE_NAME),
    os.path.join(FILES_DIR, FIRMWARE_FILE_NAME)
]
COMPSIG_PATHS = [
    os.path.join(CURRENT_DIR, COMPSIG_FILE_NAME),
    os.path.join(FILES_DIR, COMPSIG_FILE_NAME)
]

# Configure logging
LOGS_DIR = os.path.join(CURRENT_DIR, "logs")
LOG_FILE = os.path.join(LOGS_DIR, "smart_array_firmware_update.log")

# Create logs directory if it doesn't exist
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)
    print(f"Created logs directory: {LOGS_DIR}")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),  # Save logs to file in logs/ directory
        logging.StreamHandler()         # Also print to console
    ]
)
logger = logging.getLogger(__name__)

# Suppress SSL warnings (optional, for self-signed certificates)
requests.packages.urllib3.disable_warnings()

# Check if firmware files exist and return their paths
def check_files():
    firmware_path = None
    compsig_path = None
    
    for path in FIRMWARE_PATHS:
        if os.path.exists(path):
            firmware_path = path
            break
    for path in COMPSIG_PATHS:
        if os.path.exists(path):
            compsig_path = path
            break
    
    if not firmware_path:
        logger.error(f"Firmware file {FIRMWARE_FILE_NAME} not found in current directory or files/ subdirectory.")
        sys.exit(1)
    if not compsig_path:
        logger.error(f"Companion signature file {COMPSIG_FILE_NAME} not found in current directory or files/ subdirectory.")
        sys.exit(1)
    
    logger.info(f"Firmware file found at: {firmware_path}")
    logger.info(f"Compsig file found at: {compsig_path}")
    return firmware_path, compsig_path

# Get a session token for authenticated requests
def get_session_token():
    url = f"{BASE_URL}/SessionService/Sessions/"
    headers = {
        "Content-Type": "application/json",
        "OData-Version": "4.0"
    }
    payload = {
        "UserName": ILO_USERNAME,
        "Password": ILO_PASSWORD
    }
    try:
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(payload),
            verify=False
        )
        response.raise_for_status()
        session_id = response.json().get("Id")
        session_token = response.headers.get("X-Auth-Token")
        logger.info(f"Session created successfully. Session ID: {session_id}")
        return session_token
    except requests.RequestException as e:
        logger.error(f"Failed to create session: {e}")
        sys.exit(1)

# Upload firmware to iLO Repository
def upload_firmware_to_repository(session_token, firmware_path):
    url = f"{BASE_URL}/UpdateService/FirmwareInventory/"
    headers = {
        "X-Auth-Token": session_token,
        "OData-Version": "4.0"
    }
    files = {
        "file": (FIRMWARE_FILE_NAME, open(firmware_path, "rb"), "application/octet-stream")
    }
    try:
        logger.info(f"Uploading {firmware_path} to iLO Repository...")
        response = requests.post(
            url,
            headers=headers,
            files=files,
            verify=False
        )
        response.raise_for_status()
        firmware_uri = response.headers.get("Location")
        logger.info(f"Firmware uploaded successfully. URI: {firmware_uri}")
        return firmware_uri
    except requests.RequestException as e:
        logger.error(f"Failed to upload firmware: {e}")
        sys.exit(1)

# Install firmware from the iLO Repository
def install_firmware(session_token, firmware_uri):
    url = f"{BASE_URL}/UpdateService/Actions/UpdateService.SimpleUpdate/"
    headers = {
        "X-Auth-Token": session_token,
        "Content-Type": "application/json",
        "OData-Version": "4.0"
    }
    payload = {
        "ImageURI": firmware_uri,
        "UpdateTarget": True,
        "Section": "Firmware"
    }
    try:
        logger.info("Initiating firmware installation...")
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(payload),
            verify=False
        )
        response.raise_for_status()
        task_uri = response.headers.get("Location")
        logger.info(f"Firmware installation queued. Task URI: {task_uri}")
        return task_uri
    except requests.RequestException as e:
        logger.error(f"Failed to initiate firmware installation: {e}")
        sys.exit(1)

# Monitor installation task status
def monitor_task(session_token, task_uri):
    url = f"{BASE_URL}{task_uri}"
    headers = {
        "X-Auth-Token": session_token,
        "OData-Version": "4.0"
    }
    while True:
        try:
            response = requests.get(url, headers=headers, verify=False)
            response.raise_for_status()
            task_data = response.json()
            task_state = task_data.get("TaskState")
            logger.info(f"Task State: {task_state}")
            if task_state in ["Completed", "Exception", "Cancelled"]:
                logger.info(f"Task completed with state: {task_state}")
                if task_state != "Completed":
                    logger.error("Task failed or was cancelled. Check iLO for details.")
                    sys.exit(1)
                break
            time.sleep(10)
        except requests.RequestException as e:
            logger.error(f"Error monitoring task: {e}")
            sys.exit(1)

# Perform a cold boot (reboot the server)
def cold_boot(session_token):
    url = f"{BASE_URL}/Systems/1/Actions/ComputerSystem.Reset/"
    headers = {
        "X-Auth-Token": session_token,
        "Content-Type": "application/json",
        "OData-Version": "4.0"
    }
    payload = {
        "ResetType": "ForceRestart"
    }
    try:
        logger.info("Initiating cold boot...")
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(payload),
            verify=False
        )
        response.raise_for_status()
        logger.info("Cold boot command sent. Waiting for server to reboot...")
        time.sleep(60)
    except requests.RequestException as e:
        logger.error(f"Error during cold boot: {e}")
        sys.exit(1)

# Main execution
def main():
    logger.info("Starting Smart Array firmware update process...")
    
    # Step 1: Verify firmware files and get their paths
    firmware_path, compsig_path = check_files()

    # Step 2: Authenticate and get session token
    session_token = get_session_token()

    # Step 3: Upload firmware to iLO Repository
    firmware_uri = upload_firmware_to_repository(session_token, firmware_path)

    # Step 4: Install firmware
    task_uri = install_firmware(session_token, firmware_uri)

    # Step 5: Monitor installation state
    monitor_task(session_token, task_uri)

    # Step 6: Perform cold boot
    cold_boot(session_token)

    logger.info("Firmware upgrade process completed. Verify status in iLO interface.")

if __name__ == "__main__":
    main()
