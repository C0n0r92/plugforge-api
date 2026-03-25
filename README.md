# PlugForge API

A centralized Flask API backend for all PlugForge plugins (Bubble.io, Webflow, etc.).

## Architecture

PlugForge API is a modular Flask application where each plugin is implemented as a Blueprint. This allows:
- Clean separation of concerns
- Independent plugin development
- Shared infrastructure and deployment
- Single domain for all plugins: `api.plugforge.dev`

## Current Plugins

### CalSync (`/calsync`)
Add-to-calendar functionality with support for Google Calendar, Apple Calendar, Outlook, and Yahoo Calendar.

**Features:**
- Generate add-to-calendar links (free tier)
- Create/update/delete Google Calendar events (Pro tier)
- iCal feed management
- API key authentication with usage tracking

**Endpoints:**
- `POST /calsync/api/calendar/add-link` - Generate calendar links
- `POST /calsync/api/gcal/create` - Create Google Calendar event (Pro)
- `POST /calsync/api/gcal/update` - Update Google Calendar event (Pro)
- `POST /calsync/api/gcal/delete` - Delete Google Calendar event (Pro)
- `POST /calsync/api/feed/create` - Create iCal feed
- `GET /calsync/feed/{feed_id}.ics` - Download iCal feed

## Local Development

```bash
# Clone the repository
git clone https://github.com/C0n0r92/plugforge-api.git
cd plugforge-api

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your credentials

# Run the application
python app.py
```

The API will be available at `http://localhost:8080`

## Adding a New Plugin

1. **Create a new blueprint** in `src/your_plugin.py`:

```python
from flask import Blueprint, jsonify

your_plugin_bp = Blueprint('your_plugin', __name__, url_prefix='/your-plugin')

@your_plugin_bp.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "your-plugin"})

# Add your plugin endpoints here...
```

2. **Register the blueprint** in `app.py`:

```python
from src.your_plugin import your_plugin_bp
app.register_blueprint(your_plugin_bp, url_prefix='/your-plugin')
```

3. **Update the root endpoint** to list your plugin:

```python
@app.route('/', methods=['GET'])
def root():
    return jsonify({
        "status": "ok",
        "service": "plugforge-api",
        "version": "1.0.0",
        "plugins": ["calsync", "your-plugin"]  # Add your plugin here
    })
```

4. **Add any new dependencies** to `requirements.txt`

5. **Test locally**, then commit and push to deploy

## Deployment

The API is deployed on DigitalOcean App Platform and automatically deploys when code is pushed to the `main` branch.

**Production URL:** `https://api.plugforge.dev`

### Environment Variables

Set these in the DigitalOcean dashboard (Settings → App-Level Environment Variables):

- `PP_SUPABASE_URL` - Supabase project URL
- `PP_SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
- `GOOGLE_CLIENT_ID` - Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Google OAuth client secret

## Project Structure

```
plugforge-api/
├── app.py              # Main Flask app
├── requirements.txt    # Python dependencies
├── Procfile           # Deployment configuration
├── .env.example       # Environment template
├── .gitignore
├── README.md
├── .do/
│   └── app.yaml       # DigitalOcean App Platform spec
├── bubble-plugin/     # Bubble.io plugin code
└── src/
    ├── __init__.py
    └── calsync.py     # CalSync blueprint
```

## Health Checks

- Root: `GET /health` → `{"status": "ok", "service": "plugforge-api"}`
- CalSync: `GET /calsync/health` → `{"status": "ok", "service": "calsync"}`

## License

Private - All Rights Reserved
