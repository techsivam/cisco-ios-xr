import requests
from requests.auth import HTTPBasicAuth

# Replace these values with your iLO server details
ILO_IP = "{ILO_IP}"
USERNAME = "{USERNAME}"
PASSWORD = "{PASSWORD}"
SECUREBOOT_PK_URL = f"https://{ILO_IP}/redfish/v1/Systems/1/SecureBoot/SecureBootDatabases/PK/"

# Disable SSL warnings (Not recommended for production)
requests.packages.urllib3.disable_warnings()

def get_platform_key():
    try:
        response = requests.get(
            SECUREBOOT_PK_URL,
            auth=HTTPBasicAuth(USERNAME, PASSWORD),
            verify=False
        )
        
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"Failed to retrieve Platform Key. Status Code: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    platform_key_data = get_platform_key()
    if platform_key_data:
        print("Platform Key Data:", platform_key_data)
