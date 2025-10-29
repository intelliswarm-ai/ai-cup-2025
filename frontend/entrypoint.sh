#!/bin/sh
set -e

# Create SSL directory if it doesn't exist
mkdir -p /etc/nginx/ssl

# Generate self-signed SSL certificate if it doesn't exist
if [ ! -f /etc/nginx/ssl/localhost.crt ] || [ ! -f /etc/nginx/ssl/localhost.key ]; then
    echo "Generating self-signed SSL certificate for localhost..."
    apk add --no-cache openssl
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/nginx/ssl/localhost.key \
        -out /etc/nginx/ssl/localhost.crt \
        -subj "/C=US/ST=State/L=City/O=AI-Cup-2025/CN=localhost" \
        -addext "subjectAltName=DNS:localhost,IP:127.0.0.1" 2>/dev/null
    echo "✓ SSL certificate generated successfully"
else
    echo "✓ SSL certificate already exists"
fi

# Start nginx
echo "Starting nginx..."
exec nginx -g "daemon off;"
