from redfish import RedfishClient
from redfish.rest.v1 import ServerDownOrUnreachableError

def get_ilo_firmware_version():
    # Define iLO connection details
    ilo_host = "https://<ilo-ip-address>"  # Replace with your iLO IP (e.g., https://192.168.1.100)
    ilo_username = "<your-username>"       # Replace with your iLO username
    ilo_password = "<your-password>"       # Replace with your iLO password

    # Create a Redfish client object
    try:
        redfish_obj = RedfishClient(base_url=ilo_host, username=ilo_username, password=ilo_password)
    except ServerDownOrUnreachableError:
        print("Unable to connect to the iLO server. Check the IP address and network connectivity.")
        return

    # Login to the iLO
    redfish_obj.login(auth="session")

    # Get the manager resource (iLO details)
    manager_uri = "/redfish/v1/Managers/1/"
    response = redfish_obj.get(manager_uri)

    # Check if the request was successful
    if response.status == 200:
        # Extract firmware version from the response
        firmware_version = response.dict.get("FirmwareVersion", "Unknown")
        print(f"iLO 5 Firmware Version: {firmware_version}")
    else:
        print(f"Failed to retrieve data. Status code: {response.status}")

    # Logout from the iLO session
    redfish_obj.logout()

if __name__ == "__main__":
    get_ilo_firmware_version()