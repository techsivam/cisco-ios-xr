import os
import sys
import time
import requests
import hpilo
from dotenv import load_dotenv
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Disable insecure HTTPS warnings (adjust based on your security requirements)
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Load iLO credentials from .env file
load_dotenv()
hostname = os.getenv("ILO_HOSTNAME")
username = os.getenv("ILO_USERNAME")
password = os.getenv("ILO_PASSWORD")

if not hostname or not username or not password:
    print("Missing iLO credentials in .env file!")
    sys.exit(1)

# Create an hpilo instance (optional – here we just print the current firmware version)
ilo = hpilo.Ilo(hostname, login=username, password=password)
print("Current iLO firmware version:", ilo.get_fw_version())

# Define the endpoints for the Redfish API (adjust these URLs as needed for your environment)
upload_url = f"https://{hostname}/redfish/v1/UpdateService/Oem/Hpe/ComponentRepository"
task_url   = f"https://{hostname}/redfish/v1/UpdateService/Oem/Hpe/UpdateTaskQueue"

# Ensure firmware and companion signature files exist
firmware_file = "cp051996.exe"
compsig_file  = "cp051996.compsig"

if not os.path.exists(firmware_file) or not os.path.exists(compsig_file):
    print("Firmware or signature file not found in the current directory!")
    sys.exit(1)

# Create a requests session and use basic authentication.
session = requests.Session()
session.verify = False  # Disable certificate verification; enable in production if possible.
session.auth = (username, password)

# Upload firmware files to the iLO repository
print("Uploading firmware files...")
with open(firmware_file, 'rb') as exe_fd, open(compsig_file, 'rb') as compsig_fd:
    files = {
        'file':    (firmware_file, exe_fd, 'application/octet-stream'),
        'compsig': (compsig_file,  compsig_fd,  'application/octet-stream')
    }
    response = session.post(upload_url, files=files)
    if response.status_code == 200:
        print("Firmware files uploaded successfully.")
    else:
        print("Failed to upload firmware files:", response.status_code, response.text)
        sys.exit(1)

# Create an update task so that the Smart Array update is applied.
# The 'Targets' field here should reference the proper system component.
task_data = {
    "Name": "SmartArrayUpdate",
    "Targets": ["/redfish/v1/Systems/1/Storage"]
}

print("Creating update task...")
response = session.post(task_url, json=task_data)
if response.status_code == 201:
    print("Update task created successfully.")
    task_id = response.json().get("Id")
    if not task_id:
        print("No task ID found in the response.")
        sys.exit(1)
    print("Task ID:", task_id)
else:
    print("Failed to create update task:", response.status_code, response.text)
    sys.exit(1)

# Monitor the update task status periodically until it completes or fails.
status_url = f"{task_url}/{task_id}"
print("Monitoring update task status...")
while True:
    status_response = session.get(status_url)
    if status_response.status_code != 200:
        print("Failed to retrieve task status:", status_response.status_code, status_response.text)
        break
    task_status = status_response.json().get("TaskState")
    print("Task status:", task_status)
    if task_status in ["Completed", "Failed"]:
        break
    time.sleep(30)  # Wait 30 seconds before checking again

print("Update process finished with status:", task_status)
