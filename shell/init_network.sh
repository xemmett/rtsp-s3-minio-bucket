#!/bin/bash

# Prompt user for network settings
echo "Enter your wireless network name:"
read -r NETWORK_NAME

echo "Enter your wireless network password:"
read -r NETWORK_PASSWORD

# Configure wireless interface
sudo nano /etc/network/interfaces

# Add or edit the following lines to enable wireless networking on wlan0
cat <<EOF >>/etc/network/interfaces
auto wlan0
iface wlan0 inet dhcp
wpa-ssid "$NETWORK_NAME"
wpa-psk "$NETWORK_PASSWORD"
EOF

# Save and apply changes
echo "Press Enter to save changes..."
read -r

sudo service networking restart

echo "Wireless interface configured. Please verify connection."