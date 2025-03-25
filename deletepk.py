import requests
import json
from getpass import getpass

def get_ilo_session(base_url, username, password):
    """
    Create a session with iLO and return session object with auth headers
    """
    requests.packages.urllib3.disable_warnings()
    session = requests.Session()
    
    login_payload = {
        "UserName": username,
        "Password": password
    }
    
    login_url = f"{base_url}/redfish/v1/SessionService/Sessions/"
    
    try:
        response = session.post(login_url, json=login_payload, verify=False)
        response.raise_for_status()
        session.headers.update({"X-Auth-Token": response.headers["X-Auth-Token"]})
        return session
    except requests.exceptions.RequestException as e:
        print(f"Failed to create session: {e}")
        return None

def delete_platform_key(base_url, session):
    """
    Delete the Platform Key (PK) using the ResetKeys action with DeletePK
    """
    action_url = f"{base_url}/redfish/v1/Systems/1/SecureBoot/Actions/SecureBoot.ResetKeys"
    
    # Action payload to delete only the PK
    payload = {
        "ResetKeysType": "DeletePK"
    }
    
    try:
        # Perform the POST request to execute the ResetKeys action
        response = session.post(action_url, json=payload, verify=False)
        response.raise_for_status()
        
        print("Platform Key (PK) deletion request successful.")
        print("System is now in Setup Mode.")
        print(f"Response: {response.text}")
        
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error deleting Platform Key: {e}")
        if e.response is not None:
            print(f"Response details: {e.response.text}")
        return False

def get_secure_boot_status(base_url, session):
    """
    Retrieve Secure Boot status to confirm the change (optional)
    """
    secure_boot_url = f"{base_url}/redfish/v1/Systems/1/SecureBoot/"
    
    try:
        response = session.get(secure_boot_url, verify=False)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving Secure Boot status: {e}")
        return None

def main():
    # iLO server details
    base_url = input("Enter iLO base URL (e.g., https://ilo-ip): ")
    username = input("Enter iLO username: ")
    password = getpass("Enter iLO password: ")
    
    # Create session
    session = get_ilo_session(base_url, username, password)
    if not session:
        return
    
    # Optional: Check current Secure Boot status before deletion
    print("\nSecure Boot Status Before Deletion:")
    status_before = get_secure_boot_status(base_url, session)
    if status_before:
        print(f"SecureBootEnable: {status_before.get('SecureBootEnable', 'N/A')}")
        print(f"SecureBootCurrentBoot: {status_before.get('SecureBootCurrentBoot', 'N/A')}")
        print(f"SecureBootMode: {status_before.get('SecureBootMode', 'N/A')}")
    
    # Delete Platform Key
    if delete_platform_key(base_url, session):
        # Optional: Check status after deletion to confirm
        print("\nSecure Boot Status After Deletion:")
        status_after = get_secure_boot_status(base_url, session)
        if status_after:
            print(f"SecureBootEnable: {status_after.get('SecureBootEnable', 'N/A')}")
            print(f"SecureBootCurrentBoot: {status_after.get('SecureBootCurrentBoot', 'N/A')}")
            print(f"SecureBootMode: {status_after.get('SecureBootMode', 'N/A')}")
    
    # Logout
    session.close()

if __name__ == "__main__":
    main()
