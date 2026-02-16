#!/bin/bash
# Deploy script — pulls latest code and restarts the bot
set -e

cd ~/Discord_bot
git pull origin main
pip3 install -r requirements.txt
sudo systemctl restart monsterbot
echo "Deploy complete. Status:"
sudo systemctl status monsterbot --no-pager
