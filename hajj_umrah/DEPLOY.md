# Deployment

The site runs on [fly.io](https://fly.io) as a single machine in `ams`, with
SQLite, uploaded media and the rate-limit cache on a mounted volume, and static
files served by WhiteNoise from the image itself.

- `Dockerfile` — builds the image and runs `migrate` then `gunicorn`.
- `fly.toml` — the app config, the `[env]` block and the volume mount.
- `.env.example` — every variable the app reads.

## One-time setup

```bash
fly launch --no-deploy            # only if fly.toml does not exist yet
fly volumes create data_volume    # the mount that holds /data
fly secrets set DJANGO_SECRET_KEY="$(openssl rand -base64 48)"
fly secrets set GROQ_API_KEY=...
fly secrets set EMAIL_HOST_USER=... EMAIL_HOST_PASSWORD=...
fly deploy
```

Secrets set with `fly secrets set` are real environment variables, and
`load_dotenv(..., override=False)` in `config/settings.py` means they win over
anything in a `.env` file. Never commit a `.env`; `.env.example` is the
template and is safe to commit.

## What lives on the volume

`fly.toml` mounts a volume at `/data` and points three settings into it:

| Setting | Path | Contents |
| --- | --- | --- |
| `DJANGO_DB_PATH` | `/data/db.sqlite3` | The whole database |
| `DJANGO_MEDIA_ROOT` | `/data/media` | Uploaded images |
| `DJANGO_CACHE_ROOT` | `/data/cache` | Rate-limit counters |

This is the one thing to be careful about: **the database is a file on that
volume, not a managed service.** A single SQLite file is fine at this site's
scale and it is what keeps the deployment to one container with no external
services, but it means the volume is the only copy of the data. Back it up
before anything destructive.

```bash
fly ssh console -C 'cp /data/db.sqlite3 /data/db.sqlite3.$(date +%F)'
fly ssh console -C 'sqlite3 /data/db.sqlite3 ".backup /data/backup.sqlite3"'
```

The cache must be a **shared** backend, not Django's default `LocMemCache`.
The container runs `gunicorn --workers 2`, and a per-process cache would give
each worker its own rate-limit counters, doubling the effective caps. The
file-based cache on the volume is shared by every worker, which is why
`DJANGO_CACHE_ROOT` exists.

## Deploying an update

```bash
cd hajj_umrah && ../venv/bin/python manage.py test   # the chatbot tests are offline
cd .. && fly deploy
```

Migrations run automatically in the container's `CMD` before gunicorn starts.
A migration that takes a lock on the database is a problem here, since there is
only one writer: keep them small and backwards compatible for the seconds
between `migrate` finishing and the new workers accepting traffic.

## Before you rely on it

- `DJANGO_DEBUG=False` and a real `DJANGO_SECRET_KEY`. `DEBUG=True` on a public
  host leaks the settings and stack traces.
- `DJANGO_ALLOWED_HOSTS` must list the real host. The default
  (`127.0.0.1,localhost,testserver`) will reject every public request.
- `DJANGO_TRUST_X_FORWARDED_FOR` stays `True` **only** because Fly's proxy sits
  in front. If the app is ever exposed directly, set it to `False` so the chat
  rate limits key on the real client address instead of a forgeable header.
- The Gmail SMTP password must be an [app password](https://support.google.com/accounts/answer/185833),
  not the account password.

### `manage.py check --deploy`

Running it locally reports seven warnings. Most are simply the local
configuration (`DEBUG=True` and the `django-insecure-…` development key), and
they disappear once `DJANGO_DEBUG=False` and a real secret are set. Two are
not covered by `fly.toml` and are worth deciding on deliberately:

| Warning | Status |
| --- | --- |
| `security.W012` `SESSION_COOKIE_SECURE` | **Not set.** Add `SESSION_COOKIE_SECURE = True` in `settings.py` once the app is HTTPS-only. |
| `security.W016` `CSRF_COOKIE_SECURE` | **Not set.** Same: `CSRF_COOKIE_SECURE = True`. |
| `security.W004` / `W008` HSTS, SSL redirect | Fly's `force_https = true` handles the redirect at the proxy. `SECURE_HSTS_SECONDS` is still unset; enable it only once you are sure every subdomain is HTTPS. |
| `security.W019` `X_FRAME_OPTIONS` | **Intentional.** It is `SAMEORIGIN`, not `DENY`, because the dashboard preview embeds the public site in an iframe (`dashboard/views.py:preview`). |

They are left as they are because setting them unconditionally would break
local HTTP development, and because whether to add HSTS is a decision about the
rest of the estate, not this repository.


## Scaling past one machine

Stop here first — this layout is deliberately simple. If it ever needs to grow,
the two changes that matter, in order:

1. **Move the database off the volume.** A single SQLite file cannot be shared
   by two machines, and `auto_stop_machines`/`min_machines_running = 0` in
   `fly.toml` already means the machine count can go to zero and back.
   Postgres means also replacing the file-based cache with Redis, because the
   file cache only works while the files are on one machine.
2. **Only then consider more than one machine**, which also means the media
   directory has to move to object storage.

`config/asgi.py` exists so an async server can be introduced later without
touching a view, but nothing in the project needs ASGI today: the only slow
operation is the chatbot call, which already returns a cached or fallback reply
rather than holding a worker.

## Rolling back

```bash
fly releases                            # find the release to go back to
fly deploy --image <registry>/<image>:<version>
```

Because the database lives on the volume, a rollback restores the code but not
the data. If a migration is the thing being undone, restore the database backup
too.
