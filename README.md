# Rooster Automation

Automatische download van maandrooster van ROI Online naar Apple Calendar via iPhone Shortcuts.

## Overzicht

Deze automatisering:

1. Monitort Gmail inbox (ahgautomations2@gmail.com) voor emails van `noreply@staff.nl`
2. Draait alleen op **woensdag tussen 12:00-17:00**
3. Download het maandrooster van ROI Online als .ics bestand
4. Slaat het op in een gedeelde map (iCloud Drive/OneDrive/Dropbox)
5. iPhone Shortcuts detecteert het bestand en importeert het automatisch in Apple Calendar

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
ROI_EMAIL=alvarogroenewegen@gmail.com
ROI_PASSWORD=jouw_wachtwoord

GMAIL_ADDRESS=ahgautomations2@gmail.com
GMAIL_APP_PASSWORD=jouw_gmail_app_wachtwoord

SHARED_FOLDER_PATH=C:/Users/JouwNaam/OneDrive/Rooster
# Of voor Mac: /Users/JouwNaam/Library/Mobile Documents/com~apple~CloudDocs/Rooster

TRIGGER_EMAIL_SENDER=noreply@staff.nl
```

### 3. Gmail App Password

Voor Gmail monitoring heb je een **App Password** nodig:

1. Ga naar [Google Account Security](https://myaccount.google.com/security)
2. Zet 2-Step Verification aan (als nog niet gedaan)
3. Ga naar "App passwords"
4. Genereer een nieuw app password voor "Mail"
5. Kopieer het wachtwoord naar `GMAIL_APP_PASSWORD` in `.env`

### 4. Gedeelde Map

Kies een gedeelde map die toegankelijk is vanaf je iPhone:

**Windows:**

- OneDrive: `C:/Users/JouwNaam/OneDrive/Rooster`
- Dropbox: `C:/Users/JouwNaam/Dropbox/Rooster`

**Mac:**

- iCloud Drive: `/Users/JouwNaam/Library/Mobile Documents/com~apple~CloudDocs/Rooster`

Maak de map aan als deze nog niet bestaat.

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
