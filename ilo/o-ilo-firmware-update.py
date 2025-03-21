import os
import sys
import json
from dotenv import load_dotenv  # Load environment variables
from redfish import RedfishClient
from redfish.rest.v1 import ServerDownOrUnreachableError
from get_resource_directory import get_resource_directory

# Load environment variables from .env file
load_dotenv()

# Retrieve credentials from the .env file
SYSTEM_URL = os.getenv("ILO_HOST")
LOGIN_ACCOUNT = os.getenv("ILO_USER")
LOGIN_PASSWORD = os.getenv("ILO_PASS")
FIRMWARE_PATH = os.getenv("FIRMWARE_PATH")
COMPSIG_PATH = os.getenv("COMPSIG_PATH")

DISABLE_RESOURCE_DIR = False  # Enable resource directory
UPDATE_REPO = True  # Upload firmware to iLO Repository
UPDATE_TARGET = True  # Apply the update immediately


def upload_firmware(_redfishobj, firmware_loc, compsig_loc, update_repo=True, update_target=False):
    """Upload firmware with compsig verification to iLO repository"""
    resource_instances = get_resource_directory(_redfishobj)

    if DISABLE_RESOURCE_DIR or not resource_instances:
        update_service_uri = _redfishobj.root.obj['UpdateService']['@odata.id']
    else:
        for instance in resource_instances:
            if '#UpdateService.' in instance['@odata.type']:
                update_service_uri = instance['@odata.id']

    update_service_response = _redfishobj.get(update_service_uri)
    path = update_service_response.obj.HttpPushUri

    session_key = _redfishobj.session_key

    with open(firmware_loc, 'rb') as fle:
        firmware_data = fle.read()
    with open(compsig_loc, 'rb') as cle:
        compsig_data = cle.read()

    json_data = {'UpdateRepository': update_repo, 'UpdateTarget': update_target, 'ETag': 'atag', 'Section': 0}
    body = [
        ('sessionKey', session_key),
        ('parameters', json.dumps(json_data)),
        ('compsig', (os.path.basename(compsig_loc), compsig_data, 'application/octet-stream')),
        ('file', (os.path.basename(firmware_loc), firmware_data, 'application/octet-stream'))
    ]

    headers = {'Cookie': 'sessionKey=' + session_key}
    resp = _redfishobj.post(path, body, headers=headers)

    if resp.status == 400:
        sys.stderr.write(f"Firmware upload failed: {resp}\n")
    elif resp.status not in [200, 201]:
        sys.stderr.write(f"HTTP Response: {resp.status}\n")
    else:
        print("Firmware uploaded successfully!\n")


def update_ilo_firmware(_redfishobj, fw_url, tpm_flag=False):
    """Update iLO firmware from uploaded repository"""
    body = dict()
    update_service_uri = None

    resource_instances = get_resource_directory(_redfishobj)
    if DISABLE_RESOURCE_DIR or not resource_instances:
        update_service_uri = _redfishobj.root.obj['UpdateService']['@odata.id']
    else:
        for instance in resource_instances:
            if '#UpdateService.' in instance['@odata.type']:
                update_service_uri = instance['@odata.id']
                break

    if update_service_uri:
        update_uri = _redfishobj.get(update_service_uri).obj['Actions']['#UpdateService.SimpleUpdate']['target']
        body["ImageURI"] = fw_url
        if tpm_flag:
            body["TPMOverrideFlag"] = tpm_flag

        resp = _redfishobj.post(update_uri, body)
        if resp.status == 400:
            sys.stderr.write("Firmware update failed: {}\n".format(json.dumps(resp.obj['error']['@Message.ExtendedInfo'], indent=4)))
        elif resp.status != 200:
            sys.stderr.write("HTTP Response: {}\n".format(resp.status))
        else:
            print("Firmware update success!\n")


if __name__ == "__main__":
    try:
        # Create a Redfish client object
        REDFISHOBJ = RedfishClient(base_url=SYSTEM_URL, username=LOGIN_ACCOUNT, password=LOGIN_PASSWORD)
        REDFISHOBJ.login()
    except ServerDownOrUnreachableError:
        sys.stderr.write("ERROR: iLO server not reachable!\n")
        sys.exit()

    # Upload firmware and compsig
    upload_firmware(REDFISHOBJ, FIRMWARE_PATH, COMPSIG_PATH, UPDATE_REPO, UPDATE_TARGET)

    # Update iLO firmware after upload (if needed)
    FIRMWARE_URL = f"http://{SYSTEM_URL}/firmware/{os.path.basename(FIRMWARE_PATH)}"
    update_ilo_firmware(REDFISHOBJ, FIRMWARE_URL)

    REDFISHOBJ.logout()
