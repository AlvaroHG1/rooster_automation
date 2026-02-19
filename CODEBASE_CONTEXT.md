# Rooster Automation — Codebase Context

## Doel

**Rooster Automation** is een Python-applicatie die automatisch werkroosters downloadt van het **ROI Online** personeelsportaal en synchroniseert naar een **iCloud Calendar** via CalDAV. De applicatie draait als een long-running service (lokaal of in Docker) en monitort een Gmail-inbox op trigger-e-mails. Zodra een trigger-e-mail binnenkomt (bijv. "Nieuw rooster beschikbaar"), wordt het rooster van de betreffende week automatisch gedownload en naar de agenda geüpload.

---

## Tech Stack

| Onderdeel         | Technologie                                              |
| ----------------- | -------------------------------------------------------- |
| Taal              | Python 3                                                 |
| Web scraping      | Playwright (headless Chromium)                           |
| E-mail monitoring | IMAP (Gmail)                                             |
| Agenda-sync       | CalDAV (iCloud) via `caldav` + `icalendar`               |
| Configuratie      | Pydantic Settings + YAML (`config/config.yaml`) + `.env` |
| Scheduling        | `schedule` library                                       |
| Deployment        | Docker + Docker Compose                                  |

---

## Projectstructuur

```
rooster_automation/
├── main.py                          # Root entry point (importeert app.main)
├── requirements.txt                 # Python dependencies
├── Dockerfile                       # Playwright-based Docker image
├── docker-compose.yml               # Service definitie met volumes & env
├── .env.example                     # Voorbeeld environment variables
├── config/
│   └── config.yaml                  # Niet-geheime configuratie (URLs, UI element IDs, schedule)
├── app/
│   ├── __init__.py
│   ├── main.py                      # Hoofd-orchestratie: RoosterAutomation klasse
│   ├── core/
│   │   ├── __init__.py
│   │   ├── settings.py              # Pydantic Settings: merged YAML + env vars
│   │   ├── logging_config.py        # Centralized logging setup
│   │   └── utils.py                 # Gedeelde utilities (retry_on_failure decorator)
│   └── services/
│       ├── __init__.py
│       ├── gmail_monitor.py         # Gmail inbox monitoring via IMAP
│       ├── roi_scraper.py           # Playwright scraper voor ROI Online portal
│       └── calendar_service.py      # CalDAV upload naar iCloud Calendar
├── scripts/                         # Hulpscripts (investigate, verify)
├── tests/                           # Test bestanden
└── temp_downloads/                  # Tijdelijke opslag voor gedownloade .ics bestanden
```

---

## Modules in detail

### `app/main.py` — RoosterAutomation (Orchestrator)

De centrale klasse die alle componenten aanstuurt:

- **`RoosterAutomation.__init__`**: Initialiseert `ROIScraper`, `GmailMonitor` en `CalendarService`.
- **`is_active_time()`**: Controleert of huidige dag/uur binnen het actieve schema valt (configureerbaar).
- **`check_email_and_download()`**: Checkt Gmail op trigger-e-mails; start download als er een wordt gevonden.
- **`download_and_save_roster(target_week)`**: Downloadt het rooster via de scraper, uploadt events naar CalDAV, en ruimt oude events op (>90 dagen).
- **`run()`**: Start de main loop met `schedule` (standaard elke 10 minuten een e-mail check).

### `app/services/gmail_monitor.py` — GmailMonitor

- Verbindt via **IMAP4_SSL** met Gmail.
- Zoekt naar e-mails van een configureerbare trigger-afzender (`noreply@staff.nl` of `rooster@roi-online.nl`).
- Houdt de laatste verwerkte UID bij om duplicaten te voorkomen. Bij de eerste run wordt de huidige UID opgeslagen zonder actie.
- Extraheert het **weeknummer** uit de e-mail body via regex (`week \d+`).
- Retourneert een dict: `{"found": bool, "week": int|None, "uid": bytes}`.

### `app/services/roi_scraper.py` — ROIScraper

- Gebruikt **Playwright** (headless Chromium) om de ROI Online website te scrapen.
- **Login flow**: Vult credentials in en logt in op het portaal.
- **Week-navigatie**: Als een `target_week` is opgegeven, navigeert de scraper naar die week door prev/next knoppen te klikken. Gebruikt ISO weeknummer-berekening om de juiste richting en aantal clicks te bepalen.
- **Download**: Selecteert de maandweergave, klikt op de kalender-export knop, en slaat het `.ics` bestand op als `rooster_{year}_week_{week}.ics`.
- Alle UI element IDs zijn configureerbaar via `config.yaml`.

### `app/services/calendar_service.py` — CalendarService

- **Lazy connection**: Maakt pas verbinding met de CalDAV server als er daadwerkelijk een operatie nodig is.
- **`save_ics_file(path)`**: Leest een `.ics` bestand, parst het met `icalendar`, en uploadt elk `VEVENT` afzonderlijk naar de CalDAV server. Behoudt VTIMEZONE componenten per event.
- **`delete_old_events(days_to_keep=90)`**: Verwijdert events ouder dan 90 dagen via server-side `date_search` (efficiënt, voorkomt O(N) client-side iteratie).
- **Retry-logica**: Alle CalDAV-operaties gebruiken de `@retry_on_failure` decorator met automatische reconnect bij ConnectionError/AuthorizationError.
- Ondersteunt context manager (`with CalendarService() as cs:`).

### `app/core/settings.py` — Settings

- Gebruikt **Pydantic Settings** (`BaseSettings`) met geneste modellen:
  - `RoiOnlineSettings`: URL, veld-IDs, credentials (uit env).
  - `GmailSettings`: Check interval, max emails, credentials (uit env).
  - `ScheduleSettings`: Actieve dagen, start/eind uur. Ondersteunt `active_day` (enkelvoud) en `active_days` (meervoud) in YAML.
  - `CalDavSettings`: URL, username, password, calendar name (allemaal uit env).
  - `LoggingSettings`: Level, format, file path.
- **Merge-strategie**: YAML-waarden voor niet-geheime config, env vars voor secrets. Env vars hebben voorrang.
- Globale `settings` singleton wordt bij import-time geladen.
- Backwards-compatible proxy properties voor directe toegang (bijv. `settings.roi_url`).

### `app/core/utils.py` — Utilities

- **`retry_on_failure(retries, delay, backoff, exceptions)`**: Decorator die functies automatisch herprobeert bij falen, met exponentiële backoff.

### `app/core/logging_config.py` — Logging

- Configureert `logging.basicConfig` met zowel file- als stdout-handlers.
- Onderdrukt third-party loggers (`urllib3`, `googleapiclient`).

---

## Configuratie

### Environment Variables (`.env`)

| Variable               | Beschrijving                                               |
| ---------------------- | ---------------------------------------------------------- |
| `ROI_EMAIL`            | ROI Online inloggegevens                                   |
| `ROI_PASSWORD`         | ROI Online wachtwoord                                      |
| `GMAIL_ADDRESS`        | Gmail adres voor monitoring                                |
| `GMAIL_APP_PASSWORD`   | Gmail app-specifiek wachtwoord                             |
| `TRIGGER_EMAIL_SENDER` | Afzender van trigger e-mails (default: `noreply@staff.nl`) |
| `CALDAV_URL`           | CalDAV server URL (default: `https://caldav.icloud.com`)   |
| `CALDAV_USERNAME`      | Apple ID e-mail                                            |
| `CALDAV_PASSWORD`      | App-specifiek wachtwoord voor iCloud                       |
| `CALDAV_CALENDAR_NAME` | Naam van de doelkalender (default: `Rooster`)              |

### YAML Config (`config/config.yaml`)

Bevat niet-geheime configuratie:

- **`roi_online`**: Portal URL en alle HTML element IDs voor de scraper.
- **`gmail`**: Check interval (10 min), max emails om te controleren.
- **`schedule`**: Actieve dag(en) en uren.
- **`logging`**: Log level, format, en bestandspad.

---

## Deployment

- **Dockerfile**: Gebaseerd op `mcr.microsoft.com/playwright/python:v1.49.0-jammy`. Draait als non-root user `automation`.
- **Docker Compose**: Configureert volumes voor `.env`, `config/`, `shared/`, en `logs/`. Timezone ingesteld op `Europe/Amsterdam`. Auto-restart policy.

---

## Data Flow

```
Gmail Inbox
    │
    ▼
GmailMonitor (IMAP check elke 10 min)
    │ trigger e-mail gevonden + weeknummer geëxtraheerd
    ▼
ROIScraper (Playwright)
    │ login → navigeer naar week → download .ics
    ▼
temp_downloads/rooster_{year}_week_{week}.ics
    │
    ▼
CalendarService (CalDAV)
    │ parse .ics → upload events individueel → cleanup oude events
    ▼
iCloud Calendar ("Rooster")
```

---

## Dependencies (`requirements.txt`)

- `playwright==1.41.0` — Headless browser automation
- `google-auth`, `google-auth-oauthlib`, `google-api-python-client` — Google API libs (voor toekomstige Gmail API migratie)
- `pyyaml==6.0.1` — YAML config parsing
- `python-dotenv==1.0.1` — `.env` bestand laden
- `schedule==1.2.1` — Taak scheduling
- `caldav==1.3.9` — CalDAV protocol client
- `icalendar==5.0.11` — iCalendar (`.ics`) parsing
- `pydantic>=2.0.0`, `pydantic-settings>=2.0.0` — Configuratie validatie
