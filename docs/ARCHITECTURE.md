# Architecture

## Django apps

- `users`: authentication forms, profiles, search/feed and privacy access rules.
- `posts`: posts, comments, likes, and moderation reports.
- `friends`: follow edges, friend requests, and blocks.
- `notifications`: persisted notification inbox and authenticated Channels consumer.
- `api`: Django REST Framework serializers, viewsets, and profile endpoint.

The built-in Django `User` remains the authentication identity; `users.Profile`
adds the social profile through a one-to-one relation. Friend requests are
directional rows whose `accepted` status represents a mutual friendship.
Following is independent from friendship.

## Request/data flow

Templates and APIs both use the same post visibility helpers. A post is visible
to its owner, to everyone when public, to followers when configured for
followers, or to accepted friends when configured for friends. Profile
visibility and blocking are checked before serving profile content. Writes use
authenticated endpoints and ownership checks.

Notification creation persists an inbox row, then publishes a small event to
the recipient's Channels group. The WebSocket consumer only joins the group for
the authenticated session user. Local development uses an in-memory channel
layer; multi-process deployments should configure Redis.

## Data model

```text
User 1—1 Profile
User 1—N Post 1—N Comment
User N—N Post (Like through unique Like)
User N—N User (Follow)
User N—N User (directional FriendRequest; accepted = friends)
User N—N User (directional Block)
User 1—N Notification (recipient and actor)
```

## Operational considerations

Use PostgreSQL and Redis in a multi-instance deployment, durable storage for
uploaded media, TLS, secret management, and scheduled database/media backups.
Review report queues regularly. Add rate limits, automated abuse detection,
audit trails, and retention policies before opening the service publicly.
