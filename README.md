# Eltokhey Hajj & Umrah

Django site for a Hajj and Umrah travel agency: a public Arabic (RTL) brochure
site with an AI booking assistant, and a staff dashboard for trips, bookings,
reviews, site copy and the media library.

```
Dockerfile  fly.toml      deployment (fly.io + WhiteNoise + SQLite on a volume)
hajj_umrah/               the Django project — start at hajj_umrah/README.md
venv/                     local virtualenv
```

**Read [`hajj_umrah/README.md`](hajj_umrah/README.md) for the architecture** —
the two apps and their URL maps, the models, the environment variables, and why
the AI chatbot's `core/chatbot.py` is shaped the way it is. Deployment is in
[`hajj_umrah/DEPLOY.md`](hajj_umrah/DEPLOY.md).

## Quick start

```bash
python3 -m venv venv
venv/bin/pip install -r hajj_umrah/requirements.txt
cp .env.example .env          # then fill in the values
cd hajj_umrah
../venv/bin/python manage.py migrate
../venv/bin/python manage.py createsuperuser
../venv/bin/python manage.py runserver
```

Run every command from `hajj_umrah/` with `../venv/bin/python`. The test suite
is offline — no API key, no billed requests:

```bash
cd hajj_umrah && ../venv/bin/python manage.py test
```
