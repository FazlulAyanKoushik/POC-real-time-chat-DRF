# Realtime Thread-Based Chat App

A **fully asynchronous** Django REST Framework project with **JWT authentication**, **thread-based chat**, **real-time messaging** via WebSockets, and a **friendship system** with message limits for non-friends. The project is **Dockerized** for easy deployment and development.

---

## Features

- **User Authentication**
  - JWT-based authentication using `djangorestframework-simplejwt`
  - User registration and login endpoints

- **Friendship System**
  - Send, accept, reject friend requests
  - List friends and pending friend requests
  - Enforce “20-message limit for non-friends” rule

- **Thread-Based Chat**
  - 1-on-1 chat threads between users
  - Persistent message storage in SQLite
  - Async message sending and receiving

- **Real-Time Messaging**
  - WebSocket support via Django Channels
  - Uvicorn ASGI server for async handling
  - Future-ready for Redis channel layer

- **Dockerized**
  - Easy setup with Docker and `docker-compose`
  - Automatic static file collection
  - Hot-reload support during development

---

## Technology Stack

- **Backend:** Django 4.x, Django REST Framework, Django Channels  
- **Authentication:** JWT (SimpleJWT)  
- **Database:** SQLite (default, file-based)  
- **Realtime:** WebSockets via Channels  
- **ASGI Server:** Uvicorn  
- **Containerization:** Docker, Docker Compose  
- **Optional Redis:** For production-ready Channels layer

---
## Create .env file

```aiignore
DEBUG=True
SECRET_KEY=django-insecure-dev-key
ALLOWED_HOSTS=*
```

## Build and start containers
```aiignore
docker compose up --build
```
