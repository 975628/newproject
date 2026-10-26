# ConnectSphere

ConnectSphere is a Django social platform starter with profiles, a post feed,
comments, likes, follows, friend requests, notifications, privacy controls, and
a REST API.

## Features

- Django authentication, registration, profile editing, profile pictures, and
  visibility settings.
- Image/text posts with public, followers, friends, or private audiences.
- Comments, likes, follow/unfollow, friend requests, blocking, and reporting.
- In-app notifications delivered live over authenticated WebSockets.
- Search over posts and public profiles.
- Django REST Framework endpoints under `/api/`.
- Django admin moderation for posts and reports.
- Responsive Bootstrap-based pages and automated tests.

## Run locally

Python 3.10+ is recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py runserver
```

The default local configuration uses SQLite and an in-memory WebSocket
channel layer. If you run the server using the `.env` PostgreSQL/Redis values,
start the included services with Docker Compose instead. Django does not read
`.env` files automatically; set the values in your shell or use Compose's
`env_file`.

Open <http://127.0.0.1:8000/>. Create an account, then use
`/admin/` for moderation (create an administrator with
`python manage.py createsuperuser`).

## Main routes

| Route | Description |
| --- | --- |
| `/` | Feed, search, and post composer |
| `/accounts/login/`, `/register/` | Authentication |
| `/profile/<username>/` | Profile, posts, and social actions |
| `/friends/` | Friend requests and connections |
| `/notifications/` | Notification inbox |
| `/api/posts/` | Paginated post API |
| `/api/comments/` | Paginated comment API |
| `/api/follows/` | Authenticated follow API |
| `/api/friend-requests/` | Authenticated friend request API |
| `/api/notifications/` | Authenticated notification API |
| `/api/profiles/<username>/` | Profile API |
| `/ws/notifications/` | Authenticated notification WebSocket |

The API uses session or HTTP Basic authentication. Mutating operations require
authentication; browser session requests are protected by Django CSRF.

## Tests and checks

```powershell
python manage.py check
python manage.py test
```

## Docker Compose

Docker Compose starts the Django ASGI server, PostgreSQL, and Redis:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

For anything internet-facing, replace all example passwords and the secret
key, set `DEBUG=False`, set `ALLOWED_HOSTS` to the deployment hostname, and
configure HTTPS/CSRF trusted origins at the hosting provider. Uploaded media
needs persistent storage and backups; the Compose media volume is local to the
Docker host, not a cloud object store.

## Deployment

The application is ASGI-ready and can be deployed to a container host such as
Railway. Configure `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS`, a PostgreSQL
`DATABASE_URL`, and a Redis `REDIS_URL`; use the provided Dockerfile. Run
migrations during release and configure persistent/object storage for uploaded
media. A real production rollout should also configure HTTPS, backups,
monitoring, rate limits, and a moderation/privacy policy.

## Design notes

- Django's ORM maps the relations to validated, composable queries and keeps
  ownership, unique likes/follows, and cascading deletion in the data layer.
- Privacy checks are applied in feed/profile queries and API access; blocks
  prevent access and interactions between the two accounts.
- Scale the feed with PostgreSQL indexes, pagination, Redis-backed Channels,
  object storage/CDN for media, caching, and background jobs as traffic grows.
- Notifications, follows, likes, and friend activity encourage return visits;
  user controls, clear privacy settings, and moderation are important for trust.
- Reports are queued in Django admin. A production community needs documented
  rules, staff review, escalation, and abuse/rate-limiting workflows.

## Current scope

This is a functional learning project, not a production-certified social
network. Real-time chat, groups, events, automated moderation, deployment
credentials, and cloud media storage are not included.
