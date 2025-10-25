#!/bin/bash
set -e

echo ""
echo "================================================================"
echo "  Starting OtterWiki with Auto-Initialization"
echo "================================================================"
echo ""

# Run wiki initialization
/usr/local/bin/wiki-init.sh

# Start OtterWiki using supervisord (original startup method)
echo "Starting OtterWiki service with supervisord..."
echo ""

# Execute the original OtterWiki startup command
exec /usr/bin/supervisord -c /etc/supervisor/supervisord.conf
