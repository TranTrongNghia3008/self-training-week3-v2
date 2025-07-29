#!/bin/sh

# Dừng script nếu có lỗi
set -e

echo ">> Applying migrations..."
python manage.py migrate --noinput

echo ">> Creating superuser..."
python manage.py shell << END
from django.contrib.auth import get_user_model
import os
User = get_user_model()
username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "adminpassword")
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
END

echo ">> Collecting static files..."
python manage.py collectstatic --noinput

# Chạy Gunicorn server
echo ">> Starting server..."
exec "$@"
