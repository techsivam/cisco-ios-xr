from redfish.rest.v1 import RestClient, ServerDownOrUnreachableError

# Define iLO Credentials
ILO_HOST = "https://<ILO_IP_ADDRESS>"
ILO_USER = "<YOUR_USERNAME>"
ILO_PASSWORD = "<YOUR_PASSWORD>"

def get_ilo_firmware_version():
    try:
        # Initialize REST client
        client = RestClient(base_url=ILO_HOST, username=ILO_USER, password=ILO_PASSWORD)
        client.login()

        # Get iLO Manager Info (iLO Firmware)
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
