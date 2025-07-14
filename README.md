
[![GitHub contributors][contributors-pic]](contributors-url)
[![Issues][issues-pic]](issues-url)
[![Milestones][milestones-pic]](milestones-url)
[![Licence][license-pic]](https://github.com/Team26SWP/InnoAlias/blob/main/LICENSE)
[![Release][release-pic]](release-url)


<h1 align="center">Alias</h1>

<p align="center">
   The best web-application for learning terminology! </br>
   <a href="http://217.199.253.164/">Check this out!</a>
   <a href="https://drive.google.com/file/d/1oolvEd4Spec83L30ltrqCgKBHdhIibCs/view?usp=drive_link">View demo</a>
</p>

## About us

Memorizing new terminology can be tedious and boring, we are sure we've all faced this problem. And there are many tools that aim to fix it, take flashcards, for example. However, they can also fail to be engaging. That is where our solution comes in.
Alias is a game where players explain words to eachother, gaining points for each correct guess. Our app will help you learn new terminology, while also having fun with your friends, also improving the understanding of said terminology. With it, you can:
- Combine buisness with pleasure
- Actually understand new words, not simply memorize them
- Have a unique experience tailored specifically to your needs

## Project context diagram

![Context diagram](docs/images/context-diagram.svg)

## Feature roadmap
- [x] Single game master mode
- [x] Deck import 
- [x] Changeable game settings
- [x] Different game masters mode
- [x] User profiles support
- [x] Deck saveability & usability
- [x] Teams game mode
- [ ] Deck gallery
- [ ] Singleplayer

## Usage   

- Go to our website
- Create a new account
- Have fun with your friends!

## Installation

### 1. Hosted demo (fastest way)

| URL            | http://217.199.253.164/ |
|----------------|------------------------------|
| Test account   | email: demo@example.com<br>password: Demo1234! |

1. Open the link above.  
2. Sign in with the test credentials.  
3. Explore features.

### 2. Running locally (via Docker)

The **`docker-compose.yml`** in the repo is wired for our CI/CD pipeline, which normally **pulls** pre-built images from Docker Hub.  
If you want to **build and run everything from source on your own computer**, follow the steps below.

#### 2.1  Prerequisites

| Tool | Version | Check |
|------|---------|-------|
| Docker Engine | ≥ 24.0 | `docker --version` |
| Docker Compose | v2 (bundled with Docker Desktop) | `docker compose version` |

> **Tip:** On Windows use WSL 2; on macOS use Docker Desktop.

---

#### 2.2  Clone the repo

```bash
git clone https://github.com/Team26/InnoAlias.git
cd innoalias
```

#### 2.3 Add local environment variables
```bash
cp .env.example .env # Secret key you can generate via command "openssl rand -base64 32"
nano .env
```

The .env file already contains safe defaults (no production secrets). Adjust anything you need—e.g. SMTP creds—before starting the stack.

#### 2.4 Change docker-compose.yml

Just replace each `image:` line with a `build:` block that points at the directory containing the relevant Dockerfile:

```diff
 services:
   backend:
-    image: docker.io/${DOCKERHUB_USER}/innoalias-backend:latest
+    build:
+      context: ./backend
```

```diff
 services:
   frontend:
-    image: docker.io/${DOCKERHUB_USER}/innoalias-frontend:latest
+    build:
+      context: ./frontend
```

```diff
 services:
   nginx:
-    image: docker.io/${DOCKERHUB_USER}/innoalias-nginx:latest
+    build:
+      context: ./nginx
```

This step is necessary because right now docker-compose is configured for automatic deployment via CI/CD, but changing the strings will allow the project to be built locally.

#### 2.5 Launch the building!

```bash
docker-compose up -d --build
```

After build, you can use app on localhost.

## Documentation

- [Develompent](https://github.com/Team26SWP/InnoAlias/blob/main/CONTRIBUTING.md)
- [Quality attribute scenatios](https://github.com/Team26SWP/InnoAlias/blob/main/docs/quality-attributes/quality-attribute-scenarios.md)
- [Quality assurane](https://github.com/Team26SWP/InnoAlias/tree/main/docs/quality-assurance)
- [Build and deployment](https://github.com/Team26SWP/InnoAlias/tree/main/docs/automation)
- [Architecture](https://github.com/Team26SWP/InnoAlias/blob/main/docs/architecture/achitecture.md)


[contributors-pic]: https://img.shields.io/github/contributors/Team26SWP/InnoAlias
[contributors-url]: https://github.com/Team26SWP/InnoAlias/graphs/contributors
[issues-pic]: https://img.shields.io/github/issues/Team26SWP/InnoAlias
[issues-url]: https://github.com/Team26SWP/InnoAlias/issues
[milestones-pic]: https://img.shields.io/github/milestones/open/Team26SWP/InnoAlias
[milestones-url]: https://github.com/Team26SWP/InnoAlias/milestones
[license-pic]: https://img.shields.io/github/license/Team26SWP/InnoAlias
[license-url]: https://github.com/Team26SWP/InnoAlias/blob/main/LICENSE
[release-pic]: https://img.shields.io/github/v/release/Team26SWP/InnoAlias?include_prereleases
[release-url]: https://github.com/Team26SWP/InnoAlias/releases/tag/mvp_v2
