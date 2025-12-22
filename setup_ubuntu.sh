#!/bin/bash
set -e

# Configuration
APP_DIR="/opt/rechnungs-tool"
DOMAIN="rechnung.printbrigata.ch"
EMAIL="info@printbrigata.ch" # Change this!

echo ">>> Updating System..."
apt-get update

echo ">>> Installing System Dependencies..."
# minimal python, pip, venv + libraries for cairosvg (important!) + nginx + certbot
apt-get install -y python3-pip python3-venv python3-dev \
    libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info \
    nginx certbot python3-certbot-nginx

echo ">>> Setting up Application Directory..."
# Assuming you upload the files to this folder, or clone git here.
# For this script, we assume files are in current directory and we copy them to /opt
mkdir -p $APP_DIR
cp -r . $APP_DIR
cd $APP_DIR

echo ">>> Setting up Virtual Environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ">>> Configuring Systemd..."
cp printbrigata.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable printbrigata
systemctl restart printbrigata

echo ">>> Configuring Nginx..."
cp nginx_printbrigata.conf /etc/nginx/sites-available/printbrigata
rm -f /etc/nginx/sites-enabled/printbrigata
ln -s /etc/nginx/sites-available/printbrigata /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default  # Disable default site if needed
systemctl start nginx

echo ">>> Setting up SSL (Let's Encrypt)..."
# Using --non-interactive mode requires agreeing to terms and valid email
certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m $EMAIL --redirect

echo ">>> Deployment Complete!"
echo "Your app should be live at https://$DOMAIN"
