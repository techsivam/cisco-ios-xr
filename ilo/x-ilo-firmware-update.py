# -*- coding: utf-8 -*-
import os
import sys
import json
from redfish import RedfishClient
from redfish.rest.v1 import ServerDownOrUnreachableError

# Import helper function (assuming get_resource_directory.py is available)
from get_resource_directory import get_resource_directory

# Configuration
SYSTEM_URL = "https://10.0.0.100"  # Replace with your iLO IP or hostname
LOGIN_ACCOUNT = "admin"            # Replace with your iLO username
LOGIN_PASSWORD = "password"        # Replace with your iLO password
FIRMWARE_PATH = "cp05199.exe"      # Firmware file in current directory
COMPSIG_PATH = "cp05199.compsig"   # Signature file in current directory
DISABLE_RESOURCE_DIR = False       # Set to True if resource directory is not supported

def upload_firmware(_redfishobj, firmware_loc, compsig_loc, update_repo=True, update_target=False):
    resource_instances = get_resource_directory(_redfishobj)

    if DISABLE_RESOURCE_DIR or not resource_instances:
        update_service_uri = _redfishobj.root.obj['UpdateService']['@odata.id']
    else:
        for instance in resource_instances:
            if '#UpdateService.' in instance['@odata.type']:
                update_service_uri = instance['@odata.id']
                break

    update_service_response = _redfishobj.get(update_service_uri)
    path = update_service_response.obj.HttpPushUri

    body = []
    json_data = {'UpdateRepository': update_repo, 'UpdateTarget': update_target, 'ETag': 'atag', 'Section': 0}
    session_key = _redfishobj.session_key

    filename = os.path.basename(firmware_loc)
    with open(firmware_loc, 'rb') as fle:
        output = fle.read()

    compsigname = os.path.basename(compsig_loc)
    with open(compsig_loc, 'rb') as cle:
        compsigoutput = cle.read()

    session_tuple = ('sessionKey', session_key)
    parameters_tuple = ('parameters', json.dumps(json_data))
    file_tuple = ('file', (filename, output, 'application/octet-stream'))
    compsig_tuple = ('compsig', (compsigname, compsigoutput, 'application/octet-stream'))

    body.append(session_tuple)
    body.append(parameters_tuple)
    body.append(compsig_tuple)
    body.append(file_tuple)

    header = {'Cookie': 'sessionKey=' + session_key}
    resp = _redfishobj.post(path, body, headers=header)

    if resp.status == 400:
        sys.stderr.write("Failed to upload firmware... Error: '%s'\n" % str(resp))
    elif resp.status not in [200, 201]:
        sys.stderr.write("An http response of '%s' was returned.\n" % resp.status)
    else:
        print("Firmware upload complete!\n")
    return update_service_uri

def update_firmware(_redfishobj, update_service_uri, fw_filename, tpm_flag=False):
    body = dict()
    update_uri = _redfishobj.get(update_service_uri).obj['Actions']['#UpdateService.SimpleUpdate']['target']
    
    # For Smart Array, the firmware is referenced by its filename in the repository
    body["ImageURI"] = fw_filename  # Use the filename as uploaded to the repository
    if tpm_flag:
        body["TPMOverrideFlag"] = tpm_flag

    resp = _redfishobj.post(update_uri, body)
    if resp.status == 400:
        try:
            print(json.dumps(resp.obj['error']['@Message.ExtendedInfo'], indent=4, sort_keys=True))
        except Exception:
            sys.stderr.write("A response error occurred, unable to access iLO Extended Message Info...\n")
    elif resp.status != 200:
        sys.stderr.write("An http response of '%s' was returned.\n" % resp.status)
    else:
        print("Firmware update initiated successfully!\n")
        print(json.dumps(resp.obj.get('@Message.ExtendedInfo', {}), indent=4, sort_keys=True))

if __name__ == "__main__":
    try:
        # Create a Redfish client object
        REDFISHOBJ = RedfishClient(base_url=SYSTEM_URL, username=LOGIN_ACCOUNT, password=LOGIN_PASSWORD)
        REDFISHOBJ.login()
    except ServerDownOrUnreachableError:
        sys.stderr.write("ERROR: Server not reachable or does not support Redfish.\n")
        sys.exit()

    # Step 1: Upload firmware and signature to iLO repository
    update_service_uri = upload_firmware(REDFISHOBJ, FIRMWARE_PATH, COMPSIG_PATH, update_repo=True, update_target=False)

    # Step 2: Update the Smart Array firmware
    if update_service_uri:
        update_firmware(REDFISHOBJ, update_service_uri, FIRMWARE_PATH)

    # Logout
    REDFISHOBJ.logout()