# Pulse

A lightweight uptime monitor that watches your URLs and tells you when things go wrong.

Pulse runs background checks on a configurable interval, records response times and status codes, and exposes a clean API for your frontend to consume. Built with FastAPI and PostgreSQL to modern SQLAlchemy 2.0 standards.

---

## How It Works

You register a URL as a monitor. A background worker wakes up every few seconds, checks which monitors are due, probes each one concurrently, and records the result as a probe. Your dashboard reads those probes to show uptime percentage, average response time, and historical status.

Authentication is JWT-based with access and refresh tokens. Google OAuth is supported alongside email/password. New accounts go through email verification before accessing protected routes.

---

## Stack

- **FastAPI** — API framework
- **PostgreSQL** — primary database
- **SQLAlchemy 2.0** — async ORM
- **Alembic** — database migrations
- **Redis** — token blacklist for logout and token rotation
- **httpx** — async HTTP client for probing URLs
- **authlib** — Google OAuth
- **FastAPI-Mail** — transactional email
- **Docker** — containerised development and deployment

---

## Features

- URL monitoring with configurable check intervals
- Background worker with automatic crash recovery
- JWT authentication with refresh token rotation and blacklisting
- Google OAuth with automatic account linking
- Email verification and password reset
- User-scoped monitor and probe data
- Admin endpoints for platform-wide stats and user management
- Public quick-check endpoint — probe any URL without an account
- Role-based access control — user and admin roles

---
