# Docker Deployment Guide

## Voordelen van Docker

- ✅ **Portable**: Werkt op elke VM (Linux/Windows/Mac)
- ✅ **Geïsoleerd**: Geen conflicten met andere software
- ✅ **Auto-restart**: Container herstart automatisch na crash/reboot
- ✅ **Reproducible**: Altijd dezelfde environment
- ✅ **Easy updates**: `docker-compose pull && docker-compose up -d`

## Quick Start

### 1. Installeer Docker

**Linux (Ubuntu/Debian):**

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

**Windows/Mac:**
Download Docker Desktop van https://www.docker.com/products/docker-desktop

### 2. Clone Repository

```bash
git clone <repository-url>
cd rooster_automation
```

### 3. Configureer Environment

```bash
cp .env.example .env
nano .env  # Of gebruik je favoriete editor
```

Vul in:

```env
ROI_EMAIL=jouw_email
ROI_PASSWORD=jouw_wachtwoord

GMAIL_ADDRESS=jouw_email
# Gmail API uses OAuth - see step 3b for credential setup

# Wordt automatisch /app/shared in container
SHARED_FOLDER_PATH=/app/shared

TRIGGER_EMAIL_SENDER=noreply@staff.nl
```

### 3b. Gmail API Credentials

Voor Gmail API authenticatie heb je `credentials.json` en `token.json` nodig:

1. Plaats `credentials.json` (van Google Cloud Console) in de `config/` folder
2. Voer lokaal éénmalig uit om `token.json` te genereren:
   ```bash
   python main.py
   ```
3. Kopieer de gegenereerde `token.json` naar de `config/` folder
4. De container mount automatisch `./config:/app/config`

### 4. Start Container

```bash
docker-compose up -d
```

### 5. Bekijk Logs

```bash
docker-compose logs -f
```

