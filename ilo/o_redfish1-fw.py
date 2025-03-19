from redfish import redfish_client
from redfish.rest.v1 import ServerDownOrUnreachableError

# iLO 5 Credentials and IP Address
ILO_HOST = "https://<ILO_IP_ADDRESS>"
ILO_USER = "<YOUR_USERNAME>"
ILO_PASSWORD = "<YOUR_PASSWORD>"

def get_ilo_firmware_version():
    try:
        # Create Redfish Client
        client = redfish_client(base_url=ILO_HOST, username=ILO_USER, password=ILO_PASSWORD)
        client.login()

        # Retrieve iLO Firmware Information
        response = client.get("/redfish/v1/Managers/1/")
        
        if response.status == 200:
            firmware_version = response.dict.get("FirmwareVersion")
            print(f"iLO Firmware Version: {firmware_version}")
        else:
            print(f"Failed to retrieve firmware version. Status code: {response.status}")

        client.logout()
    except ServerDownOrUnreachableError:
        print("iLO is unreachable. Please check your connection.")
    except Exception as e:
        print(f"Error: {e}")

# Run the function
get_ilo_firmware_version()
