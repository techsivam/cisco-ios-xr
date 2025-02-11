import pexpect

# Define the device connection (modify accordingly)
device_ip = "your_device_ip"
username = "your_username"
password = "your_password"

# SSH into the device
child = pexpect.spawn(f"ssh {username}@{device_ip}")

# Expect the password prompt and send the password
child.expect("password:")
child.sendline(password)

# Expect the device prompt (modify as per your device prompt)
child.expect("#")

# Send the ONIE update command
child.sendline("hw-module location all bootmedia onie-update reload")

# Wait for the confirmation prompt and respond with "yes"
child.expect(r"Reload hardware module \? \[no,yes\]")
child.sendline("yes")

# Wait for a few seconds to allow the command to execute
child.expect("#", timeout=60)

# Print the output
print(child.before.decode())

# Close the connection
child.sendline("exit")
child.close()
