#!/bin/bash
set -e

echo "=== BottleCRM — Render Entrypoint ==="

# Wait for PostgreSQL
echo "Waiting for PostgreSQL at ${DBHOST}:${DBPORT}..."
retries=0
max_retries=60
while ! python -c "
import socket, os
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(3)
s.connect((os.environ['DBHOST'], int(os.environ['DBPORT'])))
s.close()
" 2>/dev/null; do
    retries=$((retries + 1))
    if [ "$retries" -ge "$max_retries" ]; then
        echo "ERROR: Could not connect to PostgreSQL after $max_retries attempts."
        exit 1
    fi
    echo "  PostgreSQL not ready yet (attempt $retries/$max_retries)..."
    sleep 2
done
echo "PostgreSQL is ready."

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Create default admin user
echo "Creating default admin user (if needed)..."
python manage.py create_default_admin

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start with gunicorn
echo "Starting server on 0.0.0.0:8000..."
exec gunicorn crm.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 120 --access-logfile - --error-logfile -