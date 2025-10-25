#!/bin/bash
set -e

# Run initialization script
/app/init_employees.sh

# Start the FastAPI application
echo "Starting Employee Directory API..."
exec uvicorn main:app --host 0.0.0.0 --port 8100 --reload
