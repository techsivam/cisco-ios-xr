import requests
import json
from urllib3.exceptions import InsecureRequestWarning

# Disable SSL warnings (not recommended for production)
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

class ILOSecureBootPKManager:
    def __init__(self, ilo_ip, username, password):
        self.base_url = f"https://{ilo_ip}/redfish/v1"
        self.auth = (username, password)
        self.headers = {'Content-Type': 'application/json'}
        
    def get_request(self, url):
        """Helper function for GET requests"""
        try:
            response = requests.get(
                url,
                auth=self.auth,
                headers=self.headers,
                verify=False
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"GET request failed: {e}")
            return None

    def post_request(self, url, payload):
        """Helper function for POST requests"""
        try:
            response = requests.post(
                url,
                auth=self.auth,
                headers=self.headers,
                data=json.dumps(payload),
                verify=False
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"POST request failed: {e}")
            return None

    def get_system_resource(self):
        """Get the first system resource from the collection"""
        systems_url = f"{self.base_url}/Systems/"
        systems_data = self.get_request(systems_url)
        if systems_data and 'Members' in systems_data and systems_data['Members']:
            return systems_data['Members'][0]['@odata.id']
        return None

    def delete_platform_key(self):
        """Delete only the Platform Key (PK) from Secure Boot"""
        system_url = self.get_system_resource()
        if not system_url:
            print("Failed to get system resource")
            return False
            
        # First check Secure Boot status
        secureboot_url = f"{self.base_url}{system_url}/SecureBoot"
        secureboot_data = self.get_request(secureboot_url)
        if not secureboot_data:
            print("Failed to get Secure Boot status")
            return False
            
        print("\nCurrent Secure Boot Status:")
        print(f"Enabled: {secureboot_data.get('SecureBootEnable', 'Unknown')}")
        print(f"Current Boot State: {secureboot_data.get('SecureBootCurrentBoot', 'Unknown')}")
        print(f"Mode: {secureboot_data.get('SecureBootMode', 'Unknown')}")
        
        # Get Secure Boot databases collection
        databases_url = secureboot_data.get('SecureBootDatabases', {}).get('@odata.id')
        if not databases_url:
            print("No Secure Boot databases found")
            return False
            
        databases_data = self.get_request(f"{self.base_url}{databases_url}")
        if not databases_data or 'Members' not in databases_data:
            print("Failed to get Secure Boot databases")
            return False
            
        # Find PK database
        pk_url = None
        for db in databases_data['Members']:
            db_url = db['@odata.id']
            if db_url.endswith('PK'):
                pk_url = db_url
                break
                
        if not pk_url:
            print("Platform Key (PK) database not found")
            return False
            
        # Perform the PK deletion
        reset_url = f"{self.base_url}{system_url}/SecureBoot/Actions/SecureBoot.ResetKeys"
        payload = {
            "ResetKeysType": "DeletePK"  # Specifically delete only PK
        }
        
        print("\nAttempting to delete Platform Key...")
        response = self.post_request(reset_url, payload)
        
        if response and response.status_code in [200, 204]:
            print("Successfully deleted Platform Key")
            print("System will now be in Setup Mode")
            return True
        else:
            print("Failed to delete Platform Key")
            return False

# Example usage
if __name__ == "__main__":
    # Replace with your iLO details
    ILO_IP = "your_ilo_ip"
    USERNAME = "your_username"
    PASSWORD = "your_password"
    
    # Create PK manager instance
    pk_manager = ILOSecureBootPKManager(ILO_IP, USERNAME, PASSWORD)
    
    # Delete the Platform Key
    success = pk_manager.delete_platform_key()
    
    if not success:
        print("\nPlatform Key deletion failed. Possible reasons:")
        print("- Insufficient privileges")
        print("- Secure Boot is not enabled")
        print("- Platform Key doesn't exist")
        print("- iLO version doesn't support this operation")
