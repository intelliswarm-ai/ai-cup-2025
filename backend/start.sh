#!/bin/bash
set -e

echo "Waiting for PostgreSQL to be ready..."
until pg_isready -h postgres -p 5432 -U mailbox_user; do
  echo "Waiting for database connection..."
  sleep 2
done

echo "Running Liquibase migrations..."
cd /app
liquibase \
  --changelog-file=db/changelog/db.changelog-master.xml \
  --url=jdbc:postgresql://postgres:5432/mailbox_db \
  --username=mailbox_user \
  --password=mailbox_pass \
  --driver=org.postgresql.Driver \
  --classpath=/liquibase/postgresql-42.6.0.jar \
  update

echo "Migrations completed successfully!"

# Temporarily disabled to preserve data during development
# echo "Clearing existing email data for fresh start..."
# PGPASSWORD=mailbox_pass psql -h postgres -U mailbox_user -d mailbox_db <<EOF
# TRUNCATE TABLE workflow_results CASCADE;
# TRUNCATE TABLE emails RESTART IDENTITY CASCADE;
# EOF
# echo "Database cleared! Starting with fresh system..."

echo "Starting FastAPI application..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
