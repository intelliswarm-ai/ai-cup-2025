#!/bin/bash
set -e

echo "=========================================="
echo "Employee Directory Initialization"
echo "=========================================="

# Ensure data directory exists
mkdir -p /app/data

EMPLOYEES_FILE="/app/data/employees.json"

# Check if employees.json already exists
if [ -f "$EMPLOYEES_FILE" ]; then
    EMPLOYEE_COUNT=$(python3 -c "import json; print(len(json.load(open('$EMPLOYEES_FILE'))))")
    echo "✓ Found existing employees.json with $EMPLOYEE_COUNT employees"
    echo "✓ Skipping initialization (data already exists)"
else
    echo "✗ No employees.json found"
    echo "→ Generating employee directory from backend database..."

    # Wait for backend to be ready
    echo "→ Waiting for backend API to be ready..."
    max_attempts=30
    attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f http://backend:8000/api/emails?limit=1 > /dev/null 2>&1; then
            echo "✓ Backend API is ready"
            break
        fi
        attempt=$((attempt + 1))
        echo "  Attempt $attempt/$max_attempts..."
        sleep 2
    done

    if [ $attempt -eq $max_attempts ]; then
        echo "⚠ Backend API not available after $max_attempts attempts"
        echo "⚠ Creating empty employee directory"
        echo "[]" > "$EMPLOYEES_FILE"
    else
        # Run the generation script
        echo "→ Running employee generation script..."
        python3 /app/generate_employees_from_db.py

        if [ -f "$EMPLOYEES_FILE" ]; then
            EMPLOYEE_COUNT=$(python3 -c "import json; print(len(json.load(open('$EMPLOYEES_FILE'))))")
            echo "✓ Generated $EMPLOYEE_COUNT employees"
        else
            echo "✗ Failed to generate employees.json"
            echo "[]" > "$EMPLOYEES_FILE"
        fi
    fi
fi

echo "=========================================="
echo "Employee Directory Ready"
echo "=========================================="
