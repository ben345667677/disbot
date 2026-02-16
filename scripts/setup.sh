#!/bin/bash
# One-time EC2 setup for Monster Bot
# Run as: bash scripts/setup.sh
set -e

echo "=== Installing system dependencies ==="
sudo yum update -y
sudo yum install -y python3.11 python3.11-pip git

echo "=== Cloning repository ==="
cd ~
if [ ! -d "Discord_bot" ]; then
  git clone https://github.com/YOUR_USERNAME/Discord_bot.git
fi
cd Discord_bot

echo "=== Installing Python dependencies ==="
pip3 install -r requirements.txt

echo "=== Creating .env placeholder ==="
if [ ! -f .env ]; then
  cat > .env <<'EOF'
DISCORD_TOKEN=your_token_here
OPENAI_API_KEY=your_key_here
EOF
  echo ">>> Edit .env with your real values, or let GitHub Actions manage it."
fi

echo "=== Creating systemd service ==="
sudo tee /etc/systemd/system/monsterbot.service > /dev/null <<EOF
[Unit]
Description=Monster Bot Discord Bot
After=network.target

[Service]
User=$(whoami)
WorkingDirectory=$HOME/Discord_bot
ExecStart=/usr/bin/python3 bot.py
Restart=always
RestartSec=5
EnvironmentFile=$HOME/Discord_bot/.env

[Install]
WantedBy=multi-user.target
EOF

echo "=== Enabling and starting service ==="
sudo systemctl daemon-reload
sudo systemctl enable monsterbot
sudo systemctl start monsterbot

echo "=== Done! Check status with: sudo systemctl status monsterbot ==="
