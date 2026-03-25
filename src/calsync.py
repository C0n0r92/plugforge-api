"""CalSync — Add to Calendar API routes, mounted on /calsync/ prefix."""
import os
import uuid
import secrets
import json
import re
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode, quote
from functools import wraps

from flask import Blueprint, jsonify, request, Response, redirect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from icalendar import Calendar, Event, vText
from dateutil import parser as dateparser
from supabase import create_client, Client
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request as GoogleRequest

calsync_bp = Blueprint('calsync', __name__, url_prefix='/calsync')

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    storage_uri="memory://",
)

@limiter.request_filter
def rate_limit_exempt():
    """Exempt health check from rate limits."""
    return request.endpoint == 'calsync.health'

# Custom rate limit exceeded handler
def rate_limit_handler(e):
    """Return JSON error for rate limit exceeded."""
    return jsonify({
        "error": "Rate limit exceeded",
        "message": "Too many requests"
    }), 429

# Supabase client (using service role key for full access)
SUPABASE_URL = os.environ.get('PP_SUPABASE_URL', 'https://msicttgznftxzvnjawst.supabase.co')
SUPABASE_KEY = os.environ.get('PP_SUPABASE_SERVICE_ROLE_KEY', '')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_KEY else None

# Google OAuth config
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
GOOGLE_REDIRECT_URI = 'https://api.plugforge.dev/calsync/auth/google/callback'

BASE_URL = "https://api.plugforge.dev"


def parse_dt(s):
    """Parse ISO8601 datetime string."""
    return dateparser.parse(s)


def fmt_google(dt):
    """Format datetime for Google Calendar URL."""
    return dt.strftime('%Y%m%dT%H%M%SZ')


def fmt_yahoo(dt):
    """Format datetime for Yahoo Calendar URL."""
    return dt.strftime('%Y%m%dT%H%M%S')


def sanitize_input(text, max_length):
    """
    Sanitize user input by:
    - Stripping HTML tags
    - Removing null bytes and control characters
    - Truncating to max_length
    """
    if not text:
        return ""

    # Convert to string if not already
    text = str(text)

    # Remove null bytes
    text = text.replace('\x00', '')

    # Remove other control characters (except newlines, tabs, carriage returns)
    text = re.sub(r'[\x01-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)

    # Strip HTML tags (simple regex - removes anything between < and >)
    text = re.sub(r'<[^>]*>', '', text)

    # Truncate to max length
    if len(text) > max_length:
        text = text[:max_length]

    return text


def validate_iso_datetime(dt_string):
    """
    Validate that a string is a valid ISO8601 datetime.
    Returns (is_valid: bool, error_message: str|None)
    """
    if not dt_string:
        return False, "Datetime string is required"

    try:
        # Try parsing with dateutil parser
        parsed = dateparser.parse(dt_string)
        if parsed is None:
            return False, "Invalid datetime format"
        return True, None
    except (ValueError, TypeError) as e:
        return False, f"Invalid datetime format: {str(e)}"


def generate_api_key():
    """Generate a CalSync API key: csk_<24 random chars>."""
    random_part = secrets.token_urlsafe(18)[:24]  # URL-safe base64, truncated to 24 chars
    return f"csk_{random_part}"


def get_api_key_from_request():
    """Extract API key from request body or X-CalSync-Key header."""
    # Try header first
    header_key = request.headers.get('X-CalSync-Key')
    if header_key:
        return header_key

    # Try body
    data = request.get_json(silent=True)
    if data and 'api_key' in data:
        return data['api_key']

    return None


def validate_api_key(api_key: str, require_pro: bool = False):
    """
    Validate API key and optionally check for pro plan.
    Returns (valid: bool, key_data: dict|None, error_msg: str|None)
    """
    if not supabase:
        return False, None, "Supabase not configured"

    try:
        result = supabase.table('calsync_api_keys').select('*').eq('api_key', api_key).execute()
        if not result.data:
            return False, None, "Invalid API key"

        key_data = result.data[0]

        if require_pro and key_data['plan'] != 'pro':
            return False, key_data, "This endpoint requires a Pro plan"

        return True, key_data, None
    except Exception as e:
        return False, None, f"API key validation error: {str(e)}"


def require_pro_plan(f):
    """Decorator to require Pro plan API key."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = get_api_key_from_request()
        if not api_key:
            return jsonify({"error": "API key required (provide in X-CalSync-Key header or api_key field)"}), 401

        valid, key_data, error = validate_api_key(api_key, require_pro=True)
        if not valid:
            return jsonify({"error": error}), 403

        # Increment usage count
        try:
            supabase.table('calsync_api_keys').update({
                'usage_count': key_data['usage_count'] + 1
            }).eq('api_key', api_key).execute()
        except:
            pass  # Non-critical

        # Pass key_data to the endpoint
        request.calsync_key_data = key_data
        return f(*args, **kwargs)

    return decorated_function


def refresh_google_token(refresh_token: str) -> dict:
    """Refresh Google OAuth access token."""
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET
    )
    creds.refresh(GoogleRequest())

    return {
        'access_token': creds.token,
        'expires_at': datetime.now(timezone.utc) + timedelta(seconds=3600)
    }


@calsync_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "service": "calsync"})


@calsync_bp.route('/api/keys/generate', methods=['POST'])
@limiter.limit("10 per hour")
def generate_key():
    """
    Generate a new CalSync API key.
    Body: { bubble_app_id?: string, plan?: "free"|"pro" }
    Returns: { api_key: string, plan: string }
    """
    if not supabase:
        return jsonify({"error": "Supabase not configured"}), 500

    data = request.get_json() or {}
    bubble_app_id = data.get('bubble_app_id')
    plan = data.get('plan', 'free')

    if plan not in ['free', 'pro']:
        return jsonify({"error": "Invalid plan (must be 'free' or 'pro')"}), 400

    try:
        api_key = generate_api_key()

        result = supabase.table('calsync_api_keys').insert({
            'api_key': api_key,
            'plan': plan,
            'bubble_app_id': bubble_app_id,
            'usage_count': 0
        }).execute()

        return jsonify({
            "api_key": api_key,
            "plan": plan,
            "bubble_app_id": bubble_app_id
        })
    except Exception as e:
        return jsonify({"error": f"Failed to generate API key: {str(e)}"}), 500


@calsync_bp.route('/api/calendar/add-link', methods=['POST'])
@limiter.limit("60 per minute;1000 per day")
def add_link():
    """
    Generate add-to-calendar links for all major calendar providers.
    Free tier endpoint (no API key required, but logs usage if provided).

    Body: {
        title: string,
        start: ISO8601 string,
        end: ISO8601 string,
        description?: string,
        location?: string,
        api_key?: string (optional for usage tracking)
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400
    if not data.get('title'):
        return jsonify({"error": "Missing required field: title"}), 400
    if not data.get('start'):
        return jsonify({"error": "Missing required field: start"}), 400
    if not data.get('end'):
        return jsonify({"error": "Missing required field: end"}), 400

    # Validate datetime formats before sanitization
    start_valid, start_error = validate_iso_datetime(data['start'])
    if not start_valid:
        return jsonify({"error": f"Invalid start datetime: {start_error}"}), 400

    end_valid, end_error = validate_iso_datetime(data['end'])
    if not end_valid:
        return jsonify({"error": f"Invalid end datetime: {end_error}"}), 400

    # Sanitize inputs
    title = sanitize_input(data['title'], 200)
    description = sanitize_input(data.get('description', ''), 2000)
    location = sanitize_input(data.get('location', ''), 500)
    start = data['start']
    end = data['end']

    try:
        start_dt = parse_dt(start)
        end_dt = parse_dt(end)
    except Exception as e:
        return jsonify({"error": f"Invalid datetime format: {str(e)}"}), 400

    # Optional: track usage if API key provided
    api_key = data.get('api_key')
    if api_key and supabase:
        try:
            valid, key_data, _ = validate_api_key(api_key)
            if valid:
                supabase.table('calsync_api_keys').update({
                    'usage_count': key_data['usage_count'] + 1
                }).eq('api_key', api_key).execute()
        except:
            pass  # Non-critical

    # Google Calendar link
    google_url = "https://calendar.google.com/calendar/render?" + urlencode({
        'action': 'TEMPLATE',
        'text': title,
        'dates': f"{fmt_google(start_dt)}/{fmt_google(end_dt)}",
        'details': description,
        'location': location,
    })

    # Outlook link
    outlook_url = "https://outlook.live.com/calendar/0/deeplink/compose?" + urlencode({
        'subject': title,
        'startdt': start,
        'enddt': end,
        'body': description,
        'location': location,
        'path': '/calendar/action/compose',
        'rru': 'addevent',
    })

    # Yahoo Calendar link
    yahoo_url = "https://calendar.yahoo.com/?" + urlencode({
        'v': '60',
        'title': title,
        'st': fmt_yahoo(start_dt),
        'et': fmt_yahoo(end_dt),
        'desc': description,
        'in_loc': location,
    })

    # Apple Calendar (.ics file) — persist to Supabase
    event_id = str(uuid.uuid4())
    if supabase:
        try:
            supabase.table('calsync_events').insert({
                'id': event_id,
                'title': title,
                'start_time': start,
                'end_time': end,
                'description': description,
                'location': location,
            }).execute()
        except Exception as e:
            # Fallback: continue without Apple link
            pass

    apple_url = f"{BASE_URL}/calsync/ical/event/{event_id}.ics"

    return jsonify({
        "google": google_url,
        "apple": apple_url,
        "outlook": outlook_url,
        "yahoo": yahoo_url,
        "event_id": event_id,
    })


@calsync_bp.route('/ical/event/<event_id>.ics', methods=['GET'])
@limiter.limit("120 per minute")
def download_ics(event_id):
    """
    Download .ics file for a single event (Apple Calendar).
    This endpoint supports the Apple Calendar link from add-link.
    """
    if not supabase:
        return jsonify({"error": "Supabase not configured"}), 500

    try:
        result = supabase.table('calsync_events').select('*').eq('id', event_id).execute()
        if not result.data:
            return jsonify({"error": "Event not found"}), 404

        e = result.data[0]

        cal = Calendar()
        cal.add('prodid', '-//CalSync//plugforge.dev//')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'PUBLISH')

        ev = Event()
        ev.add('summary', e['title'])
        ev.add('dtstart', parse_dt(e['start_time']))
        ev.add('dtend', parse_dt(e['end_time']))
        if e.get('description'):
            ev.add('description', e['description'])
        if e.get('location'):
            ev['location'] = vText(e['location'])
        ev.add('uid', f"{e['id']}@plugforge.dev")
        ev.add('dtstamp', datetime.now(timezone.utc))
        cal.add_component(ev)

        return Response(
            cal.to_ical(),
            mimetype='text/calendar',
            headers={
                'Content-Type': 'text/calendar; charset=utf-8',
                'Content-Disposition': f'attachment; filename="{e["title"]}.ics"',
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# Google Calendar OAuth + Event Management (Pro Feature)
# ============================================================================

@calsync_bp.route('/auth/google', methods=['GET'])
def google_auth():
    """
    Initiate Google OAuth flow.
    Query params: api_key (required), bubble_app_id (optional)
    Redirects to Google consent screen.
    """
    api_key = request.args.get('api_key')
    bubble_app_id = request.args.get('bubble_app_id', '')

    if not api_key:
        return jsonify({"error": "api_key required in query params"}), 400

    # Validate API key
    valid, key_data, error = validate_api_key(api_key, require_pro=True)
    if not valid:
        return jsonify({"error": error}), 403

    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return jsonify({"error": "Google OAuth not configured (missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET)"}), 500

    try:
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=['https://www.googleapis.com/auth/calendar.events'],
            redirect_uri=GOOGLE_REDIRECT_URI
        )

        # Encode state param with api_key and bubble_app_id
        state = json.dumps({'api_key': api_key, 'bubble_app_id': bubble_app_id})
        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',
            state=state
        )

        return redirect(authorization_url)
    except Exception as e:
        return jsonify({"error": f"OAuth init failed: {str(e)}"}), 500


@calsync_bp.route('/auth/google/callback', methods=['GET'])
def google_callback():
    """
    Google OAuth callback handler.
    Exchanges authorization code for tokens and stores in Supabase.
    """
    code = request.args.get('code')
    state = request.args.get('state')

    if not code:
        return "Error: No authorization code received", 400

    try:
        # Decode state
        state_data = json.loads(state) if state else {}
        api_key = state_data.get('api_key')
        bubble_app_id = state_data.get('bubble_app_id', '')

        if not api_key:
            return "Error: Invalid state (missing api_key)", 400

        # Exchange code for tokens
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=['https://www.googleapis.com/auth/calendar.events'],
            redirect_uri=GOOGLE_REDIRECT_URI
        )
        flow.fetch_token(code=code)

        credentials = flow.credentials
        access_token = credentials.token
        refresh_token = credentials.refresh_token
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=3600)

        # Store tokens in Supabase
        if supabase:
            # Delete existing tokens for this api_key
            supabase.table('calsync_google_tokens').delete().eq('api_key', api_key).execute()

            # Insert new tokens
            supabase.table('calsync_google_tokens').insert({
                'api_key': api_key,
                'access_token': access_token,
                'refresh_token': refresh_token,
                'expires_at': expires_at.isoformat(),
                'bubble_app_id': bubble_app_id
            }).execute()

        # Return success page with access token (Bubble captures this)
        return f"""
        <html>
        <head><title>Google Calendar Connected</title></head>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
            <h1 style="color: #4CAF50;">✓ Google Calendar Connected</h1>
            <p>Your CalSync account is now connected to Google Calendar.</p>
            <p style="font-size: 12px; color: #666;">You can close this window.</p>
            <script>
                // Pass access token to parent window (for Bubble)
                if (window.opener) {{
                    window.opener.postMessage({{
                        type: 'calsync_oauth_success',
                        access_token: '{access_token}'
                    }}, '*');
                }}
            </script>
        </body>
        </html>
        """
    except Exception as e:
        return f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>", 500


@calsync_bp.route('/api/gcal/create', methods=['POST'])
@require_pro_plan
def gcal_create():
    """
    Create event in user's Google Calendar (Pro feature).
    Body: {
        api_key: string,
        access_token: string,
        title: string,
        start: ISO8601 string,
        end: ISO8601 string,
        description?: string,
        location?: string
    }
    Returns: { event_id: string, success: bool, html_link: string }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    access_token = data.get('access_token')
    if not all([access_token, data.get('title'), data.get('start'), data.get('end')]):
        return jsonify({"error": "Missing required fields: access_token, title, start, end"}), 400

    # Validate datetime formats
    start_valid, start_error = validate_iso_datetime(data['start'])
    if not start_valid:
        return jsonify({"error": f"Invalid start datetime: {start_error}"}), 400

    end_valid, end_error = validate_iso_datetime(data['end'])
    if not end_valid:
        return jsonify({"error": f"Invalid end datetime: {end_error}"}), 400

    # Sanitize inputs
    title = sanitize_input(data['title'], 200)
    description = sanitize_input(data.get('description', ''), 2000)
    location = sanitize_input(data.get('location', ''), 500)
    start = data['start']
    end = data['end']

    try:
        # Build Google Calendar API client
        creds = Credentials(token=access_token)
        service = build('calendar', 'v3', credentials=creds)

        # Create event
        event_body = {
            'summary': title,
            'start': {'dateTime': start, 'timeZone': 'UTC'},
            'end': {'dateTime': end, 'timeZone': 'UTC'},
            'description': description,
            'location': location,
        }

        event = service.events().insert(calendarId='primary', body=event_body).execute()

        return jsonify({
            "success": True,
            "event_id": event['id'],
            "html_link": event.get('htmlLink', '')
        })
    except Exception as e:
        # If token expired, try to refresh
        if 'invalid_grant' in str(e) or 'expired' in str(e).lower():
            return jsonify({"error": "Access token expired. Please re-authenticate.", "expired": True}), 401
        return jsonify({"error": f"Failed to create event: {str(e)}"}), 500


@calsync_bp.route('/api/gcal/update', methods=['POST'])
@require_pro_plan
def gcal_update():
    """
    Update existing Google Calendar event (Pro feature).
    Body: {
        api_key: string,
        access_token: string,
        event_id: string,
        title?: string,
        start?: ISO8601 string,
        end?: ISO8601 string,
        description?: string,
        location?: string
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    access_token = data.get('access_token')
    event_id = data.get('event_id')

    if not access_token or not event_id:
        return jsonify({"error": "Missing required fields: access_token, event_id"}), 400

    # Validate datetime formats if provided
    if 'start' in data:
        start_valid, start_error = validate_iso_datetime(data['start'])
        if not start_valid:
            return jsonify({"error": f"Invalid start datetime: {start_error}"}), 400

    if 'end' in data:
        end_valid, end_error = validate_iso_datetime(data['end'])
        if not end_valid:
            return jsonify({"error": f"Invalid end datetime: {end_error}"}), 400

    try:
        creds = Credentials(token=access_token)
        service = build('calendar', 'v3', credentials=creds)

        # Get existing event
        event = service.events().get(calendarId='primary', eventId=event_id).execute()

        # Update fields with sanitization
        if 'title' in data:
            event['summary'] = sanitize_input(data['title'], 200)
        if 'start' in data:
            event['start'] = {'dateTime': data['start'], 'timeZone': 'UTC'}
        if 'end' in data:
            event['end'] = {'dateTime': data['end'], 'timeZone': 'UTC'}
        if 'description' in data:
            event['description'] = sanitize_input(data['description'], 2000)
        if 'location' in data:
            event['location'] = sanitize_input(data['location'], 500)

        updated_event = service.events().update(
            calendarId='primary',
            eventId=event_id,
            body=event
        ).execute()

        return jsonify({
            "success": True,
            "event_id": updated_event['id'],
            "html_link": updated_event.get('htmlLink', '')
        })
    except Exception as e:
        if 'invalid_grant' in str(e) or 'expired' in str(e).lower():
            return jsonify({"error": "Access token expired. Please re-authenticate.", "expired": True}), 401
        return jsonify({"error": f"Failed to update event: {str(e)}"}), 500


@calsync_bp.route('/api/gcal/delete', methods=['POST'])
@require_pro_plan
def gcal_delete():
    """
    Delete Google Calendar event (Pro feature).
    Body: { api_key: string, access_token: string, event_id: string }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    access_token = data.get('access_token')
    event_id = data.get('event_id')

    if not access_token or not event_id:
        return jsonify({"error": "Missing required fields: access_token, event_id"}), 400

    try:
        creds = Credentials(token=access_token)
        service = build('calendar', 'v3', credentials=creds)

        service.events().delete(calendarId='primary', eventId=event_id).execute()

        return jsonify({"success": True, "message": "Event deleted"})
    except Exception as e:
        if 'invalid_grant' in str(e) or 'expired' in str(e).lower():
            return jsonify({"error": "Access token expired. Please re-authenticate.", "expired": True}), 401
        return jsonify({"error": f"Failed to delete event: {str(e)}"}), 500


# ============================================================================
# iCal Feed Management (Subscribable Calendar URLs)
# ============================================================================

@calsync_bp.route('/api/feed/create', methods=['POST'])
@limiter.limit("30 per minute")
def feed_create():
    """
    Create a persistent iCal feed with multiple events.
    Free tier with API key.

    Body: {
        api_key: string,
        events: [{ title, start, end, description?, location? }]
    }
    Returns: { feed_id: string, feed_url: string }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    api_key = data.get('api_key')
    events = data.get('events', [])

    if not api_key:
        return jsonify({"error": "api_key required"}), 400

    if not events or not isinstance(events, list):
        return jsonify({"error": "events array required"}), 400

    # Validate API key
    valid, key_data, error = validate_api_key(api_key)
    if not valid:
        return jsonify({"error": error}), 403

    if not supabase:
        return jsonify({"error": "Supabase not configured"}), 500

    try:
        # Validate events structure and sanitize inputs
        sanitized_events = []
        for event in events:
            if not all(k in event for k in ['title', 'start', 'end']):
                return jsonify({"error": "Each event must have title, start, and end"}), 400

            # Validate datetime formats
            start_valid, start_error = validate_iso_datetime(event['start'])
            if not start_valid:
                return jsonify({"error": f"Invalid start datetime in event: {start_error}"}), 400

            end_valid, end_error = validate_iso_datetime(event['end'])
            if not end_valid:
                return jsonify({"error": f"Invalid end datetime in event: {end_error}"}), 400

            # Sanitize event data
            sanitized_event = {
                'title': sanitize_input(event['title'], 200),
                'start': event['start'],
                'end': event['end'],
                'description': sanitize_input(event.get('description', ''), 2000),
                'location': sanitize_input(event.get('location', ''), 500)
            }
            sanitized_events.append(sanitized_event)

        feed_id = str(uuid.uuid4())

        supabase.table('calsync_feeds').insert({
            'feed_id': feed_id,
            'api_key': api_key,
            'events': json.dumps(sanitized_events)
        }).execute()

        # Increment usage
        supabase.table('calsync_api_keys').update({
            'usage_count': key_data['usage_count'] + 1
        }).eq('api_key', api_key).execute()

        feed_url = f"https://api.plugforge.dev/calsync/feed/{feed_id}.ics"

        return jsonify({
            "feed_id": feed_id,
            "feed_url": feed_url
        })
    except Exception as e:
        return jsonify({"error": f"Failed to create feed: {str(e)}"}), 500


@calsync_bp.route('/feed/<feed_id>.ics', methods=['GET'])
@limiter.limit("120 per minute")
def feed_download(feed_id):
    """
    Download full iCal feed (subscribable URL).
    This URL can be subscribed to in any calendar app.
    """
    if not supabase:
        return jsonify({"error": "Supabase not configured"}), 500

    try:
        result = supabase.table('calsync_feeds').select('*').eq('feed_id', feed_id).execute()
        if not result.data:
            return jsonify({"error": "Feed not found"}), 404

        feed_data = result.data[0]
        events = json.loads(feed_data['events']) if isinstance(feed_data['events'], str) else feed_data['events']

        # Build iCal
        cal = Calendar()
        cal.add('prodid', '-//CalSync Feed//plugforge.dev//')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'PUBLISH')
        cal.add('X-WR-CALNAME', 'CalSync Feed')
        cal.add('X-WR-TIMEZONE', 'UTC')

        for event_data in events:
            ev = Event()
            ev.add('summary', event_data['title'])
            ev.add('dtstart', parse_dt(event_data['start']))
            ev.add('dtend', parse_dt(event_data['end']))
            if event_data.get('description'):
                ev.add('description', event_data['description'])
            if event_data.get('location'):
                ev['location'] = vText(event_data['location'])

            # Generate unique UID for each event
            event_uid = str(uuid.uuid5(uuid.UUID(feed_id), event_data['title'] + event_data['start']))
            ev.add('uid', f"{event_uid}@plugforge.dev")
            ev.add('dtstamp', datetime.now(timezone.utc))

            cal.add_component(ev)

        return Response(
            cal.to_ical(),
            mimetype='text/calendar',
            headers={
                'Content-Type': 'text/calendar; charset=utf-8',
                'Content-Disposition': f'attachment; filename="calsync-feed-{feed_id}.ics"',
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@calsync_bp.route('/api/feed/<feed_id>', methods=['PUT'])
@require_pro_plan
def feed_update(feed_id):
    """
    Update events in an existing feed (Pro feature).
    Body: { api_key: string, events: [...] }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    events = data.get('events', [])

    if not events or not isinstance(events, list):
        return jsonify({"error": "events array required"}), 400

    if not supabase:
        return jsonify({"error": "Supabase not configured"}), 500

    try:
        # Validate events structure and sanitize inputs
        sanitized_events = []
        for event in events:
            if not all(k in event for k in ['title', 'start', 'end']):
                return jsonify({"error": "Each event must have title, start, and end"}), 400

            # Validate datetime formats
            start_valid, start_error = validate_iso_datetime(event['start'])
            if not start_valid:
                return jsonify({"error": f"Invalid start datetime in event: {start_error}"}), 400

            end_valid, end_error = validate_iso_datetime(event['end'])
            if not end_valid:
                return jsonify({"error": f"Invalid end datetime in event: {end_error}"}), 400

            # Sanitize event data
            sanitized_event = {
                'title': sanitize_input(event['title'], 200),
                'start': event['start'],
                'end': event['end'],
                'description': sanitize_input(event.get('description', ''), 2000),
                'location': sanitize_input(event.get('location', ''), 500)
            }
            sanitized_events.append(sanitized_event)

        # Update feed
        result = supabase.table('calsync_feeds').update({
            'events': json.dumps(sanitized_events),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }).eq('feed_id', feed_id).execute()

        if not result.data:
            return jsonify({"error": "Feed not found"}), 404

        return jsonify({
            "success": True,
            "feed_id": feed_id,
            "feed_url": f"https://api.plugforge.dev/calsync/feed/{feed_id}.ics"
        })
    except Exception as e:
        return jsonify({"error": f"Failed to update feed: {str(e)}"}), 500
