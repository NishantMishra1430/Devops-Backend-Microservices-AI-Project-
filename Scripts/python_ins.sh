#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "==================================================="
echo "🚀 Starting Python 3.11 Installation for Ubuntu LTS"
echo "==================================================="

# 1. Update and Upgrade system packages
echo -e "\n📦 Step 1: Updating system package index..."
sudo apt update -y
sudo apt upgrade -y

# 2. Install prerequisites
echo -e "\n🛠️ Step 2: Installing prerequisite software..."
sudo apt install -y software-properties-common wget curl build-essential

# 3. Add DeadSnakes PPA (To ensure we get exact Python versions easily on older LTS)
echo -e "\n🐍 Step 3: Adding DeadSnakes PPA repository..."
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update -y

# 4. Install Python 3.11, PIP, and VENV
echo -e "\n⚙️ Step 4: Installing Python 3.11, PIP, and VENV..."
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# 5. Set Python 3.11 as the default 'python3' command
echo -e "\n🔗 Step 5: Configuring default python3 version..."
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# 6. Verify Installation
echo -e "\n✅ Step 6: Verifying Installation..."
echo "Python Version: $(python3 --version)"
echo "PIP Version: $(pip3 --version)"

echo "==================================================="
echo "🎉 Python setup completed successfully on your VPS!"
echo "==================================================="