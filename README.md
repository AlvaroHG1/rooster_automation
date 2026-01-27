# Rooster Automation

Automatische download van maandrooster van ROI Online naar Apple Calendar via iPhone Shortcuts.

## Overzicht

Deze automatisering:

1. Monitort Gmail inbox voor emails van `noreply@staff.nl`
2. Draait alleen op **donderdag tussen 11:00-24:00** (configureerbaar in `config.yaml`)
3. Download het rooster van ROI Online als .ics bestand
4. Upload events automatisch naar iCloud Calendar via CalDAV
5. Sync automatisch naar alle Apple devices

**Voordelen:**

- ✅ Automatische sync naar alle Apple devices
- ✅ Geen handmatige stappen vereist
- ✅ Events direct in je kalender
- ✅ Week-specifieke roosters worden ondersteund

## Installatie (Lokaal - zonder Docker)

> **💡 Tip**: Voor VM deployment, gebruik de Docker methode hierboven.

### 1. Python Dependencies

```bash
# Installeer dependencies
pip install -r requirements.txt

# Installeer Playwright browsers
playwright install chromium
```

### 2. Environment Variables

Kopieer `.env.example` naar `.env` en vul de waarden in:

```bash
cp .env.example .env
```

Bewerk `.env`:

```env
# ROI Online Credentials
ROI_EMAIL=jouw_email_adres
ROI_PASSWORD=jouw_wachtwoord

# Gmail Settings
GMAIL_ADDRESS=jouw_gmail_app_adres
GMAIL_APP_PASSWORD=jouw_gmail_app_wachtwoord

# Trigger Email
TRIGGER_EMAIL_SENDER=noreply@staff.nl

# CalDAV Configuratie (iCloud Calendar)
CALDAV_URL=https://caldav.icloud.com
CALDAV_USERNAME=jouw_apple_id@icloud.com
CALDAV_PASSWORD=xxxx-xxxx-xxxx-xxxx  # App-specific password
CALDAV_CALENDAR_NAME=Rooster
```

### 3. CalDAV Setup (iCloud Calendar)

Deze applicatie gebruikt CalDAV om events direct naar je iCloud Calendar te uploaden.

**Setup:**

1. **Genereer een App-Specific Password voor iCloud:**
   - Ga naar [appleid.apple.com](https://appleid.apple.com/account/manage)
   - Klik op "Sign-In and Security" → "App-Specific Passwords"
   - Klik op "Generate an app-specific password"
   - Geef het een naam (bijv. "Rooster Automation")
   - Kopieer het gegenereerde wachtwoord

2. **Maak een "Rooster" kalender aan in iCloud:**
   - Open Calendar app op je Mac/iPhone
   - Maak een nieuwe kalender aan met de naam "Rooster"
   - Zorg dat deze gesynchroniseerd is met iCloud

3. **De CalDAV credentials zijn al in je `.env` bestand gezet** (zie stap 2)

**Let op:** Als de kalender "Rooster" niet bestaat, worden events geüpload naar je eerste beschikbare kalender.

### 4. Gmail API Setup (OAuth 2.0)

Voor Gmail monitoring gebruikt de applicatie IMAP met een app-specific password (al ingesteld in `.env`).

**Alternatief: Gmail API (Optioneel)**

Als je de Gmail API wilt gebruiken in plaats van IMAP:

#### Stap 1: Google Cloud Project Aanmaken

1. Ga naar [Google Cloud Console](https://console.cloud.google.com)
2. Klik op "Select a project" → "New Project"
3. Geef het project een naam (bijv. "Rooster Automation")
4. Klik op "Create"

#### Stap 2: Gmail API Inschakelen

1. Selecteer je nieuwe project
2. Ga naar "APIs & Services" → "Library"
3. Zoek naar "Gmail API"
4. Klik op "Enable"

#### Stap 3: OAuth 2.0 Credentials Aanmaken

1. Ga naar "APIs & Services" → "Credentials"
2. Klik op "Configure Consent Screen"
   - Kies "External" (tenzij je een Google Workspace account hebt)
   - Vul app naam in: "Rooster Automation"
   - Vul je email adres in bij "User support email" en "Developer contact"
   - Klik op "Save and Continue"
   - Skip "Scopes" (klik "Save and Continue")
   - Bij "Test users": voeg `ahgautomations2@gmail.com` toe
   - Klik op "Save and Continue"
3. Ga terug naar "Credentials"
4. Klik op "+ CREATE CREDENTIALS" → "OAuth client ID"
5. Application type: **Desktop app**
6. Name: "Rooster Automation Desktop"
7. Klik op "Create"
8. **Download** het credentials bestand
9. Hernoem het naar `credentials.json`
10. Plaats het in de project folder: `c:\Users\Alvaro\vscode\rooster_automation\`

#### Stap 4: Eerste Authenticatie

Bij de eerste keer dat je de applicatie start:

1. Een browser venster opent automatisch
2. Login met `ahgautomations2@gmail.com`
3. Klik op "Advanced" → "Go to Rooster Automation (unsafe)"
4. Klik op "Allow" om toegang te geven
5. Een `token.json` bestand wordt automatisch aangemaakt
6. Vanaf nu werkt het automatisch (geen re-authenticatie nodig)

**Let op:** De `token.json` vernieuwt zichzelf automatisch. Je hoeft nooit opnieuw te authenticeren, tenzij je de token handmatig verwijdert.

## Gebruik

### Automatisering Starten

```bash
python main.py
```

De automatisering draait continu en checkt alleen op de geconfigureerde dag/tijd voor nieuwe emails.

### Configuratie Aanpassen

Pas `config/config.yaml` aan om het schedule te wijzigen:

```yaml
schedule:
  active_day: "thursday" # dag van de week
  start_hour: 11 # start uur
  end_hour: 24 # eind uur
```

## Project Structuur

```
rooster_automation/
├── main.py                           # Entry point
├── app/
│   ├── main.py                       # Hoofd orchestrator
│   ├── core/
│   │   ├── settings.py               # Configuratie management
│   │   └── utils.py                  # Utilities (retry decorator)
│   └── services/
│       ├── calendar_service.py       # CalDAV integratie
│       ├── gmail_monitor.py          # Gmail IMAP monitoring
│       └── roi_scraper.py            # Playwright scraper
├── config/
│   └── config.yaml                   # Configuratie
├── tests/
│   ├── test_caldav_connection.py     # CalDAV test
│   └── test_file_storage_connection.py
├── scripts/
│   ├── investigate_site.py           # Site inspector
│   ├── verify_navigation.py          # Navigation test
│   └── verify_refactor.py            # Component test
├── requirements.txt                  # Dependencies
├── Dockerfile                        # Container setup
├── docker-compose.yml                # Orchestration
├── .env                              # Environment vars (niet in git)
├── .env.example                      # Template
└── README.md                         # Deze file
```

## Logging

Logs worden opgeslagen in `rooster_automation.log` en getoond in de console.

Log levels:

- **INFO**: Normale operaties
- **DEBUG**: Gedetailleerde informatie (wijzig in config.yaml)
- **ERROR**: Fouten en exceptions

## Troubleshooting

### "ROI_EMAIL and ROI_PASSWORD must be set"

- Controleer of `.env` bestand bestaat
- Controleer of alle waarden zijn ingevuld

### "GMAIL_APP_PASSWORD must be set"

- Genereer een Gmail App Password (zie installatie stap 3)
- Gebruik het app password, NIET je normale Gmail wachtwoord

### "Failed to search emails"

- Controleer Gmail App Password
- Controleer internetverbinding
- Controleer of IMAP is ingeschakeld in Gmail settings

### Playwright browser errors

- Run: `playwright install chromium`

### .ics bestand wordt niet gedownload

- Test handmatig: `python roi_scraper.py --output ./test`
- Controleer ROI Online credentials
- Controleer of de website nog steeds dezelfde element IDs gebruikt

### iPhone Shortcuts importeert niet automatisch

- Controleer of de gedeelde map correct is ingesteld
- Controleer of de Shortcuts automation actief is
- Test handmatig door een .ics bestand in de map te plaatsen

## Onderhoud

### Element IDs Updaten

Als ROI Online hun website update, moeten mogelijk de element IDs in `config/config.yaml` worden aangepast:

```yaml
roi_online:
  month_radio_button_id: "ls_ch_i9gdcl_2"
  calendar_export_button_id: "ls_ch_ic0g"
  week_display_id: "ls_ch_i45lDL"
  prev_week_button_id: "ls_ch_i45lP"
  next_week_button_id: "ls_ch_i45lN"
  # etc.
```

Gebruik browser DevTools (F12) om de nieuwe IDs te vinden, of gebruik het helper script:

```bash
python scripts/investigate_site.py
```

### Week Navigation Testen

Test de week navigation functionaliteit met:

```bash
python scripts/verify_navigation.py
```

### Oude Events Opruimen

Standaard worden oude events niet automatisch verwijderd. Om events ouder dan X dagen te verwijderen, gebruik je de `delete_old_events` methode van `CalendarService`:

```python
# In app/main.py na het uploaden van events:
self.storage.delete_old_events(days_to_keep=90)  # Wijzig naar gewenste aantal dagen
```

## Support

Voor vragen of problemen, check de logs in `rooster_automation.log`.

