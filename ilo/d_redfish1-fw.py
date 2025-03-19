from redfish import RedfishClient

# Define the iLO connection details
ILO_HOST = "ilo-ip-address"
ILO_USER = "username"
ILO_PASSWORD = "password"

# Create a Redfish client object
SYSTEM_URL = "/redfish/v1/Systems/1/"
redfish_client = RedfishClient(base_url=ILO_HOST, username=ILO_USER, password=ILO_PASSWORD)

# Login to the iLO
redfish_client.login()

# Get the system information
system_info = redfish_client.get(SYSTEM_URL)

# Check if the request was successful
if system_info.status == 200:
    # Extract the firmware version
    firmware_version = system_info.dict['BiosVersion']
    print(f"Firmware Version: {firmware_version}")
else:
    print("Failed to retrieve system information.")

# Logout from the iLO
redfish_client.logout()