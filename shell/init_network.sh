#!/bin/bash

# Prompt for network credentials
read -p "Enter the SSID of the network: " SSID
read -sp "Enter the password for the network: " PASSWORD
echo

# Backup the current wpa_supplicant.conf file
sudo cp /etc/wpa_supplicant/wpa_supplicant.conf /etc/wpa_supplicant/wpa_supplicant.conf.backup

# Write new network configuration to wpa_supplicant.conf
echo "Updating wpa_supplicant configuration..."
echo -e "country=IE\nupdate_config=1\nctrl_interface=/var/run/wpa_supplicant\n\nnetwork={\n    ssid=\"$SSID\"\n    psk=\"$PASSWORD\"\n    key_mgmt=WPA-PSK\n}\n" | sudo tee /etc/wpa_supplicant/wpa_supplicant.conf > /dev/null

# Restart the networking service to apply changes
if sudo systemctl restart dhcpcd; then
    echo "Network configuration updated. Please reconnect to the Raspberry Pi if needed."
else
    echo "Failed to restart dhcpcd.service. Please manually restart the networking service."
fi
