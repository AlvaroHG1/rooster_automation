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
ROI_EMAIL=alvarogroenewegen@gmail.com
ROI_PASSWORD=jouw_wachtwoord

GMAIL_ADDRESS=ahgautomations2@gmail.com
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

## Shared Folder Setup voor iPhone

De container schrijft .ics bestanden naar de `./shared` folder op je host. Voor iPhone toegang heb je verschillende opties:

### Optie 1: SMB Share (Aanbevolen voor Linux VM)

**Op de VM:**

```bash
# Installeer Samba
sudo apt-get update
sudo apt-get install samba

# Maak shared folder
mkdir -p ~/rooster_automation/shared

# Configureer Samba
sudo nano /etc/samba/smb.conf
```

Voeg toe aan `/etc/samba/smb.conf`:

```ini
[Rooster]
    path = /home/jouw-user/rooster_automation/shared
    browseable = yes
    read only = no
    valid users = jouw-user
    create mask = 0644
    directory mask = 0755
```

```bash
# Maak Samba wachtwoord
sudo smbpasswd -a jouw-user

# Herstart Samba
sudo systemctl restart smbd
sudo systemctl enable smbd

# Open firewall (indien nodig)
sudo ufw allow samba
```

**Op iPhone:**

1. Open **Files** app
2. Tap op **...** (drie puntjes)
3. Kies **Connect to Server**
4. Vul in: `smb://vm-ip-adres/Rooster`
5. Login met je credentials

### Optie 2: Cloud Storage Sync

Mount een cloud storage folder in de container:

**Voor OneDrive:**

```yaml
# In docker-compose.yml
volumes:
  - ~/OneDrive/Rooster:/app/shared
```

**Voor Dropbox:**

```yaml
volumes:
  - ~/Dropbox/Rooster:/app/shared
```

### Optie 3: WebDAV Server

Voeg een WebDAV server toe aan `docker-compose.yml`:

```yaml
services:
  rooster-automation:
    # ... existing config ...

  webdav:
    image: bytemark/webdav
    restart: always
    ports:
      - "8080:80"
    environment:
      - AUTH_TYPE=Basic
      - USERNAME=rooster
      - PASSWORD=jouw-wachtwoord
    volumes:
      - ./shared:/var/lib/dav
```

Op iPhone: Files app > Connect to Server > `http://vm-ip:8080`

## Docker Commands

### Basis Commands

```bash
# Start container
docker-compose up -d

# Stop container
docker-compose down

# Herstart container
docker-compose restart

# Bekijk logs (live)
docker-compose logs -f

# Bekijk logs (laatste 100 regels)
docker-compose logs --tail=100

# Container status
docker-compose ps
```

### Updates Deployen

```bash
# Pull laatste code
git pull

# Rebuild container
docker-compose build

# Start met nieuwe versie
docker-compose up -d
```

### Troubleshooting

```bash
# Bekijk container logs
docker-compose logs rooster-automation

# Ga de container in
docker-compose exec rooster-automation /bin/bash

# Verwijder alles en start opnieuw
docker-compose down -v
docker-compose up -d --build
```

## Monitoring

### Logs Locatie

Logs worden opgeslagen in `./logs/rooster_automation.log` op de host.

```bash
# Bekijk logs
tail -f logs/rooster_automation.log

# Zoek naar errors
grep ERROR logs/rooster_automation.log
```

### Health Check

Voeg toe aan `docker-compose.yml` voor health monitoring:

```yaml
services:
  rooster-automation:
    # ... existing config ...
    healthcheck:
      test:
        [
          "CMD",
          "python",
          "-c",
          "import os; exit(0 if os.path.exists('/app/.env') else 1)",
        ]
      interval: 1m
      timeout: 10s
      retries: 3
```

## Security Best Practices

1. **Gebruik sterke wachtwoorden** in `.env`
2. **Limiteer network toegang** met firewall rules
3. **Update regelmatig** met `git pull && docker-compose up -d --build`
4. **Backup `.env` file** (maar niet in git!)
5. **Monitor logs** voor verdachte activiteit

## Automatisch Starten bij Boot

Docker Compose containers met `restart: always` starten automatisch bij system boot.

Verifieer:

```bash
docker-compose ps
```

## Resource Limits

Voeg toe aan `docker-compose.yml` om resource gebruik te limiteren:

```yaml
services:
  rooster-automation:
    # ... existing config ...
    deploy:
      resources:
        limits:
          cpus: "0.5"
          memory: 512M
        reservations:
          cpus: "0.25"
          memory: 256M
```
