# الطوخي للحج والعمرة — Eltokhey Hajj & Umrah

Django site for a Hajj and Umrah travel agency: a public Arabic (RTL) brochure
site with a booking form and reviews, and a staff dashboard for trips, bookings,
reviews, site copy and the media library.

The site is deployed on [fly.io](https://fly.io) behind WhiteNoise, and runs on
SQLite on a mounted volume. See [DEPLOY.md](DEPLOY.md) for the deployment.

---

## Quick start

```bash
# from the repository root
python3 -m venv venv
venv/bin/pip install -r hajj_umrah/requirements.txt

cp .env.example .env          # then fill in the values
cd hajj_umrah
../venv/bin/python manage.py migrate
../venv/bin/python manage.py createsuperuser
../venv/bin/python manage.py runserver
```

`manage.py` lives in `hajj_umrah/`, so every command runs from that directory
and the interpreter is one level up at `../venv/bin/python`.

## Tests

```bash
cd hajj_umrah
../venv/bin/python manage.py test
```

The suite is entirely offline: no test makes a network request, so no API key
is needed and nothing is billed.

## Layout

```
.
├── hajj_umrah/                  the Django project
│   ├── manage.py
│   ├── config/                  settings, root URLconf, WSGI/ASGI
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py  asgi.py
│   ├── core/                    the public app
│   │   ├── models.py            Trip, Booking, Review, SiteSettings
│   │   ├── views.py             the public pages
│   │   ├── urls.py
│   │   ├── forms.py             review form
│   │   ├── whatsapp.py          WhatsApp deep links and messages
│   │   ├── context_processors.py  site_settings -> every template
│   │   ├── sitemaps.py
│   │   ├── admin.py
│   │   ├── migrations/
│   │   └── tests.py
│   ├── dashboard/               the staff app
│   │   ├── models.py            MediaFile (the image library)
│   │   ├── views.py  urls.py  forms.py
│   │   ├── permissions.py       staff_required / superuser_required
│   │   ├── templates/dashboard/
│   │   ├── static/dashboard/
│   │   ├── migrations/
│   │   └── tests.py
│   ├── templates/               public templates
│   ├── static/                  public CSS/JS/images, PWA files
│   ├── media/                   uploaded files (git-ignored)
│   └── requirements.txt
├── Dockerfile  fly.toml         deployment
├── .env.example                 every supported environment variable
└── venv/                        local virtualenv (git-ignored)
```

## The two apps

### `core` — everything a visitor sees

| URL | View | What it does |
| --- | --- | --- |
| `/` | `core.views.home` | Hero, featured trips, reviews strip |
| `/trips/` | `core.views.trips_list` | Full list with type/stock filters |
| `/trips/<slug>/` | `core.views.trip_detail` | One trip, with the booking CTA |
| `/about/` | `core.views.about` | Company details |
| `/booking/` | `core.views.booking` | Public booking request form (POST creates a `Booking`) |
| `/reviews/` | `core.views.reviews_list` | Paginated approved reviews |
| `/reviews/submit/` | `core.views.review_submit` | Review form; honeypot + per-IP rate limit |
| `/track/` | `core.views.track_booking` | Look a booking up by reference code or phone |
| `/offline/` | `core.views.offline` | PWA offline fallback |
| `/sw.js` | `core.views.service_worker` | Public service worker, served with no-cache |

URLs are namespaced under `core:` and always reversed by name, so a path
change never breaks a template.

### `dashboard` — everything staff sees

Mounted at `/dashboard/`. Access is enforced per view by the decorators in
`dashboard/permissions.py`:

- `staff_required` — any `is_staff` account. Used for trips, bookings, reviews,
  settings, sections, media and the preview.
- `superuser_required` — staff account management only. It stacks on top of
  `staff_required`, so the login check is never skipped.

A staff user who is not a superuser therefore sees the content menus but not
the users menu, and cannot reach the user-management views by URL.

## Models

- **`Trip`** — name, slug, type (`hajj` / `umrah` / `ramadan`), free-text
  `price` (it is usually marketing copy such as "ابتداءً من 37900"), duration,
  dates, transport, capacity/remaining, `is_active`, and a manual `order` that
  the public lists follow. `itinerary`, `includes` and `excludes` are JSON
  lists edited as one-item-per-line textareas by `dashboard.forms.TripForm`.
  Uploads are re-encoded and downscaled on save (1600px thumbnails, 400px
  review photos, EXIF stripped, transparency preserved).
- **`Booking`** — created from the public form or by hand in the dashboard.
  Gets a unique `reference_code` automatically, and moves through
  `pending → confirmed / rejected → completed`, notifying the customer by email
  and WhatsApp at each step.
- **`Review`** — customer reviews, `pending` until a staff member approves
  them. One submission per IP per 24 hours, plus a honeypot field.
- **`SiteSettings`** — a singleton row holding the company details and all the
  homepage copy. Injected into every template by
  `core.context_processors.site_settings`, and editable at
  `/dashboard/settings/`.
- **`MediaFile`** (dashboard) — the reusable image library.

There is no custom user model. Staff accounts are Django's own `auth.User`
rows with `is_staff` / `is_superuser`.

## Environment variables

Every one of these is optional locally; `.env.example` lists the defaults. The
full set is read in `config/settings.py`.

| Variable | Purpose |
| --- | --- |
| `DJANGO_SECRET_KEY` | **Required in production.** |
| `DJANGO_DEBUG` | `False` in production. |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated host list. |
| `DJANGO_DB_PATH` | SQLite file path. |
| `DJANGO_MEDIA_ROOT` | Writable path for uploads on the volume. |
| `DJANGO_TRUST_X_FORWARDED_FOR` | `False` when there is no proxy in front. |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | SMTP. Without credentials the console backend is used. |
| `DEFAULT_FROM_EMAIL`, `ADMIN_NOTIFICATION_EMAIL` | Who sends, who is notified. |

## Notes for contributors

- **Every Python file, class and function carries a docstring**, and every
  template and CSS/JS file starts with a comment naming the view that renders
  it. When you add a file, add the header too.
- **A `{# ... #}` header must come before `{% extends %}`**, never a
  `{% comment %}` block — Django rejects a `{% comment %}` before `{% extends %}`.
- **`.gitignore` rules for `media/` and `staticfiles/` are anchored
  with a leading slash on purpose.** An unanchored `media/` once silently
  excluded `dashboard/templates/dashboard/media/`, which cost the repository
  two templates.
- **Comments are in English, interface text is Arabic.** Keep it that way.
