FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY hajj_umrah/requirements.txt /app/hajj_umrah/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/hajj_umrah/requirements.txt

COPY hajj_umrah /app/hajj_umrah

WORKDIR /app/hajj_umrah
RUN python manage.py collectstatic --noinput

EXPOSE 8080

CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:8080 --workers 2"]