#!/bin/bash
set -e

# Wait for database if needed (for future use with external databases)
# Example: wait-for-it.sh db:5432 -t 30

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting application..."
exec "$@"
