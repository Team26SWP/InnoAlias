
[![GitHub contributors][contributors-pic]](contributors-url)
[![Issues][issues-pic]](issues-url)
[![Milestones][milestones-pic]](milestones-url)
[![Licence][license-pic]](https://github.com/Team26SWP/InnoAlias/blob/main/LICENSE)
[![Release][release-pic]](release-url)


<h1 align="center">Alias</h1>

<p align="center">
   The best web-application for learning terminology! </br>
   <a href="http://innoalias.duckdns.org/">Check this out!</a>
   <a href="https://drive.google.com/file/d/1oolvEd4Spec83L30ltrqCgKBHdhIibCs/view?usp=drive_link">View demo</a>
</p>

## About the project

Alias is a game that helps you memorize terms. Players divide into teams, and in each team a player called the "game master" explains a word to their teammates, while they guess. The goal is to guess as many words as possible.

The problem with regular memorization methods is that they are often boring and too shallow. Our product solves this problem by making learning fun and efficient. Moreover, it makes playing with your friends convenient, as it introduces savable decks, flexible game settings and a deck gallery to share decks with others! 

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
- [x] Deck gallery
- [x] Singleplayer
- [ ] Additional game modes
- [ ] Innopolis SSO support

## Usage   

| URL            | http://innoalias.duckdns.org/ |
|----------------|------------------------------|

### Creating an account
1. Click "Log in"
2. "Sign in"
3. Enter your credentials and click "Create"

### Hosting a game
1. Click "Create lobby"
2. Enter words by hand, via a txt file or from a saved deck
3. Change settings to your preferences (optional)
4. Click "Create Game"
5. Whenever you are ready, click "Start game"

### Joining game
1. Click "Join game"
2. Enter code shared by the host
3. Click "Join"

OR

Go to the link shared by the host

OR

Scan the QR code shared by the host

### Saving a deck (after a played game)
1. Click "Save deck"
2. Provide name, tags and select privacy option
3. Click "Save"

### Creating a deck
1. Click "Profile"
2. Click "Create deck"
3. Fill in deck name, words and pick privacy option
4. Click "Create"

### Browsing gallery
1. Scroll down on the main page
2. Select the deck you are interested in
3. Click "Save to profile" to save to profile
4. Click "Use this deck" to start creating a game with words from this deck

### Playing with AI
1. Click "Singleplayer"
2. Add words, similarly to regular game
3. Change settings to your preferences (optional)
4. Click "Create game"

## Installation

### Running locally (via Docker)

If you want to **build and run everything from source on your own computer**, follow the steps below.

#### 1  Prerequisites

| Tool | Version | Check |
|------|---------|-------|
| Docker Engine | ≥ 24.0 | `docker --version` |
| Docker Compose | v2 (bundled with Docker Desktop) | `docker compose version` |

> **Tip:** On Windows use WSL 2; on macOS use Docker Desktop.

---

#### 2  Clone the repo

```bash
git clone https://github.com/Team26/InnoAlias.git
cd innoalias
```

#### 3 Add local environment variables
```bash
cp .env.example .env # Secret key you can generate via command "openssl rand -base64 32"
nano .env
```

The .env file already contains safe defaults (no production secrets). Adjust anything you need.

#### 4 Launch the building!

```bash
docker-compose -f docker-compose-dev.yml up -d --build
```

After build, you can use app on localhost.

## Documentation

- [Development](https://github.com/Team26SWP/InnoAlias/blob/main/CONTRIBUTING.md)
- [Quality attribute scenarios](https://github.com/Team26SWP/InnoAlias/blob/main/docs/quality-attributes/quality-attribute-scenarios.md)
- [Quality assurance](https://github.com/Team26SWP/InnoAlias/tree/main/docs/quality-assurance)
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
