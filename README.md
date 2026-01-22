# Rooster Automation

Automatische download van maandrooster van ROI Online naar Apple Calendar via iPhone Shortcuts.

## Overzicht

Deze automatisering:

1. Monitort Gmail inbox (ahgautomations2@gmail.com) voor emails van `noreply@staff.nl`
2. Draait alleen op **woensdag tussen 12:00-17:00**
3. Download het maandrooster van ROI Online als .ics bestand
4. Slaat het op via één van de volgende methoden:
   - **File Storage**: Gedeelde map (iCloud Drive/OneDrive/Dropbox) + iPhone Shortcuts
   - **CalDAV**: Direct naar iCloud Calendar (automatische sync, geen Shortcuts nodig)

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
ROI_EMAIL=jouw_email_adres
ROI_PASSWORD=jouw_wachtwoord

GMAIL_ADDRESS=jouw_gmail_app_adres
GMAIL_APP_PASSWORD=jouw_gmail_app_wachtwoord

SHARED_FOLDER_PATH=C:/Users/JouwNaam/OneDrive/Rooster
# Of voor Mac: /Users/JouwNaam/Library/Mobile Documents/com~apple~CloudDocs/Rooster

TRIGGER_EMAIL_SENDER=noreply@staff.nl
```

### 3. Gmail API Setup (OAuth 2.0)

Voor Gmail monitoring gebruik je de **Gmail API** met OAuth 2.0 authenticatie:

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

### 4. Gedeelde Map

Kies een gedeelde map die toegankelijk is vanaf je iPhone:

**Windows:**

- OneDrive: `C:/Users/JouwNaam/OneDrive/Rooster`
- Dropbox: `C:/Users/JouwNaam/Dropbox/Rooster`

**Mac:**

- iCloud Drive: `/Users/JouwNaam/Library/Mobile Documents/com~apple~CloudDocs/Rooster`

Maak de map aan als deze nog niet bestaat.

### 5. CalDAV Setup (Optioneel - Alternatief voor File Storage)

In plaats van bestanden opslaan in een gedeelde map, kun je events direct uploaden naar iCloud Calendar via CalDAV.

**Voordelen:**

- ✅ Automatische sync naar alle Apple devices
- ✅ Geen iPhone Shortcuts nodig
- ✅ Events direct in je kalender

**Setup:**

1. **Genereer een App-Specific Password voor iCloud:**
   - Ga naar [appleid.apple.com](https://appleid.apple.com/account/manage)
   - Klik op "Sign-In and Security" → "App-Specific Passwords"
   - Klik op "Generate an app-specific password"
   - Geef het een naam (bijv. "Rooster Automation")
   - Kopieer het gegenereerde wachtwoord

2. **Update `.env` bestand:**

   ```env
   # Kies storage methode
   STORAGE_METHOD=caldav

   # CalDAV configuratie
   CALDAV_URL=https://caldav.icloud.com
   CALDAV_USERNAME=jouw_apple_id@icloud.com
   CALDAV_PASSWORD=xxxx-xxxx-xxxx-xxxx  # App-specific password
   CALDAV_CALENDAR_NAME=Rooster
   ```

3. **Maak een "Rooster" kalender aan in iCloud:**
   - Open Calendar app op je Mac/iPhone
   - Maak een nieuwe kalender aan met de naam "Rooster"
   - Zorg dat deze gesynchroniseerd is met iCloud

**Let op:** Als de kalender "Rooster" niet bestaat, worden events geüpload naar je eerste beschikbare kalender.

**Terug naar File Storage:**

```env
STORAGE_METHOD=file
```

## Gebruik

### Automatisering Starten

```bash
python main.py
```

De automatisering draait continu en checkt alleen op woensdag tussen 12:00-17:00 voor nieuwe emails.

### Handmatig Rooster Downloaden

```bash
python roi_scraper.py --output ./downloads
```

### Gmail Monitor Testen

```bash
python gmail_monitor.py
```

### Gedeelde Map Bekijken

```bash
python file_storage.py
```

## iPhone Shortcuts Setup

Om .ics bestanden automatisch te importeren in Apple Calendar:

1. Open **Shortcuts** app op iPhone
2. Maak een nieuwe **Automation**:
   - Trigger: "When file is added to folder"
   - Selecteer de gedeelde map (bijv. iCloud Drive/Rooster)
   - Filter: alleen .ics bestanden
3. Actie: "Add to Calendar"
   - Selecteer je gewenste kalender
4. Zet "Ask Before Running" uit voor volledige automatisering

## Project Structuur

```
rooster_automation/
├── main.py                 # Hoofdscript
├── roi_scraper.py         # ROI Online scraper
├── gmail_monitor.py       # Gmail monitoring
├── file_storage.py        # Bestandsbeheer
├── config.yaml            # Configuratie
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (niet in git)
├── .env.example          # Template voor .env
└── README.md             # Deze file
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

Als ROI Online hun website update, moeten mogelijk de element IDs in `config.yaml` worden aangepast:

```yaml
roi_online:
  month_radio_button_id: "ls_ch_i9gdcl_2"
  calendar_export_button_id: "ls_ch_ic0g"
  # etc.
```

Gebruik browser DevTools (F12) om de nieuwe IDs te vinden.

### Oude Bestanden Opruimen

Standaard worden .ics bestanden ouder dan 90 dagen automatisch verwijderd.
Wijzig dit in `main.py`:

```python
self.storage.cleanup_old_files(days_to_keep=90)  # Wijzig naar gewenste aantal dagen
```

## Support

Voor vragen of problemen, check de logs in `rooster_automation.log`.
