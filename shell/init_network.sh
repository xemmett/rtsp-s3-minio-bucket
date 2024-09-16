#!/bin/bash

# Prompt for network credentials
read -p "Enter the SSID of the network: " SSID
read -sp "Enter the password for the network: " PASSWORD
echo

# Backup the current wpa_supplicant.conf file
cp /etc/wpa_supplicant/wpa_supplicant.conf /etc/wpa_supplicant/wpa_supplicant.conf.backup

# Write new network configuration to wpa_supplicant.conf
cat <<EOF > /etc/wpa_supplicant/wpa_supplicant.conf
country=IE
update_config=1
ctrl_interface=/var/run/wpa_supplicant

network={
    ssid="$SSID"
    psk="$PASSWORD"
    key_mgmt=WPA-PSK
}
EOF

# Restart the networking service to apply changes
sudo systemctl restart dhcpcd

echo "Network configuration updated. Please reconnect to the Raspberry Pi if needed."
