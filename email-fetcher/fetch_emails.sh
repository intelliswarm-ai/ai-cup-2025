#!/bin/bash
set -e

echo "=========================================="
echo "Email Fetcher - Auto-fetch on Startup"
echo "=========================================="

BACKEND_HOST=${BACKEND_HOST:-backend}
BACKEND_PORT=${BACKEND_PORT:-8000}
POSTGRES_HOST=${POSTGRES_HOST:-postgres}
POSTGRES_DB=${POSTGRES_DB:-mailbox_db}
POSTGRES_USER=${POSTGRES_USER:-mailbox_user}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-mailbox_pass}
FETCH_LIMIT=${FETCH_LIMIT:-10000}
MAX_WAIT_TIME=${MAX_WAIT_TIME:-120}

echo "Configuration:"
echo "  Backend: http://${BACKEND_HOST}:${BACKEND_PORT}"
echo "  Database: ${POSTGRES_HOST}/${POSTGRES_DB}"
echo "  Fetch Limit: ${FETCH_LIMIT}"
echo "  Max Wait Time: ${MAX_WAIT_TIME}s"
echo ""

# Wait for backend to be ready
echo "→ Waiting for backend API to be ready..."
waited=0
while [ $waited -lt $MAX_WAIT_TIME ]; do
    if curl -s -f "http://${BACKEND_HOST}:${BACKEND_PORT}/api/emails?limit=1" > /dev/null 2>&1; then
        echo "✓ Backend API is ready!"
        break
    fi
    echo "  Waiting... (${waited}s/${MAX_WAIT_TIME}s)"
    sleep 5
    waited=$((waited + 5))
done

if [ $waited -ge $MAX_WAIT_TIME ]; then
    echo "✗ Backend API not available after ${MAX_WAIT_TIME}s"
    echo "✗ Skipping email fetch"
    exit 1
fi

# Clear the database
echo "→ Clearing database tables..."
export PGPASSWORD="${POSTGRES_PASSWORD}"

# Delete all data from tables (keeping schema intact)
echo "  Deleting workflow_results..."
psql -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "DELETE FROM workflow_results;" > /dev/null 2>&1 || true

echo "  Deleting emails..."
psql -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "DELETE FROM emails;" > /dev/null 2>&1 || true

# Reset sequences to start IDs from 1
echo "  Resetting ID sequences..."
psql -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "ALTER SEQUENCE emails_id_seq RESTART WITH 1;" > /dev/null 2>&1 || true
psql -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "ALTER SEQUENCE workflow_results_id_seq RESTART WITH 1;" > /dev/null 2>&1 || true

# Verify deletion
email_count=$(psql -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -t -A -c "SELECT COUNT(*) FROM emails;")
echo "✓ Database cleared and sequences reset (emails: ${email_count})"

# Wait for email-seeder to finish by checking MailPit message count
echo "→ Waiting for email-seeder to populate MailPit..."
MAILPIT_HOST=${MAILPIT_HOST:-mailpit}
MAILPIT_PORT=${MAILPIT_PORT:-8025}
MIN_MESSAGES=${MIN_MESSAGES:-1000}

waited=0
max_seeder_wait=300  # 5 minutes max wait for seeder

while [ $waited -lt $max_seeder_wait ]; do
    message_count=$(curl -s "http://${MAILPIT_HOST}:${MAILPIT_PORT}/api/v1/messages" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('total', 0))" 2>/dev/null || echo "0")

    if [ "$message_count" -ge "$MIN_MESSAGES" ]; then
        echo "✓ MailPit has ${message_count} messages, ready to fetch!"
        break
    fi

    echo "  MailPit has ${message_count} messages, waiting for at least ${MIN_MESSAGES}... (${waited}s/${max_seeder_wait}s)"
    sleep 10
    waited=$((waited + 10))
done

if [ $waited -ge $max_seeder_wait ]; then
    echo "⚠ Timeout waiting for email-seeder, fetching anyway..."
fi

# Fetch emails from MailPit
echo "→ Fetching emails from MailPit..."
response=$(curl -s -X POST "http://${BACKEND_HOST}:${BACKEND_PORT}/api/emails/fetch?limit=${FETCH_LIMIT}")

# Parse and display results
echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print('')
    print('✓ Fetch completed successfully!')
    print(f\"  Status: {data.get('status', 'unknown')}\")
    print(f\"  Fetched: {data.get('fetched', 0)} emails\")
    print(f\"  Total in MailPit: {data.get('total_in_mailpit', 0)}\")
    print('')
except Exception as e:
    print(f'✗ Error parsing response: {e}')
    print(f'Response: {sys.stdin.read()}')
    sys.exit(1)
"

echo "=========================================="
echo "Email Fetcher - Completed"
echo "=========================================="
