#!/usr/bin/env bash
# Build script used by Render and by manual VPS deploys.
set -o errexit
set -o pipefail
set -o nounset

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate --noinput

if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] \
  && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ] \
  && [ -n "${DJANGO_SUPERUSER_EMAIL:-}" ]; then
  python manage.py createsuperuser --noinput || true
fi
