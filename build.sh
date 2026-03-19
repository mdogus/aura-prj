#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

if [ "${RUN_SEED_ON_DEPLOY:-false}" = "true" ]; then
  python manage.py seed_demo_users --dataset "${SEED_DATASET:-demo}" --reset
fi
