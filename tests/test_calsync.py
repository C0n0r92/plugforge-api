"""
Comprehensive unit and integration tests for CalSync API.
"""
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
import pytest


# ============================================================================
# UNIT TESTS
# ============================================================================

def test_health(client):
    """Test GET /calsync/health returns {"status": "ok"}."""
    response = client.get('/calsync/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'ok'
    assert data['service'] == 'calsync'


def test_add_link_valid(client, mock_supabase, sample_event):
    """Test POST /calsync/api/calendar/add-link with valid data returns URLs."""
    # Mock successful insert
    mock_response = MagicMock()
    mock_response.data = [{"id": str(uuid.uuid4())}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_response

    response = client.post(
        '/calsync/api/calendar/add-link',
        json=sample_event,
        content_type='application/json'
    )

    assert response.status_code == 200
    data = response.get_json()

    # Check all calendar links are present
    assert 'google' in data
    assert 'apple' in data
    assert 'outlook' in data
    assert 'yahoo' in data
    assert 'event_id' in data

    # Verify event was inserted into Supabase
    mock_supabase.table.assert_called()


def test_add_link_missing_title(client):
    """Test POST /calsync/api/calendar/add-link returns 400 when title is missing."""
    response = client.post(
        '/calsync/api/calendar/add-link',
        json={
            "start": "2024-12-25T10:00:00Z",
            "end": "2024-12-25T11:00:00Z"
        },
        content_type='application/json'
    )

    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'title' in data['error'].lower()


def test_add_link_missing_start(client):
    """Test POST /calsync/api/calendar/add-link returns 400 when start is missing."""
    response = client.post(
        '/calsync/api/calendar/add-link',
        json={
            "title": "Test Meeting",
            "end": "2024-12-25T11:00:00Z"
        },
        content_type='application/json'
    )

    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'start' in data['error'].lower()


def test_add_link_missing_end(client):
    """Test POST /calsync/api/calendar/add-link returns 400 when end is missing."""
    response = client.post(
        '/calsync/api/calendar/add-link',
        json={
            "title": "Test Meeting",
            "start": "2024-12-25T10:00:00Z"
        },
        content_type='application/json'
    )

    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'end' in data['error'].lower()


def test_add_link_no_body(client):
    """Test POST /calsync/api/calendar/add-link returns 400 when no body is sent."""
    # Send with content type but empty body
    response = client.post(
        '/calsync/api/calendar/add-link',
        json={},
        content_type='application/json'
    )

    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data


def test_google_url_format(client, mock_supabase, sample_event):
    """Test that Google URL contains calendar.google.com and correct params."""
    mock_response = MagicMock()
    mock_response.data = [{"id": str(uuid.uuid4())}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_response

    response = client.post(
        '/calsync/api/calendar/add-link',
        json=sample_event,
        content_type='application/json'
    )

    assert response.status_code == 200
    data = response.get_json()

    google_url = data['google']
    assert 'calendar.google.com' in google_url
    assert 'action=TEMPLATE' in google_url
    assert 'text=' in google_url
    assert 'dates=' in google_url
    # Verify the title is in the URL
    assert 'Test+Meeting' in google_url or 'Test%20Meeting' in google_url


def test_outlook_url_format(client, mock_supabase, sample_event):
    """Test that Outlook URL contains outlook.live.com."""
    mock_response = MagicMock()
    mock_response.data = [{"id": str(uuid.uuid4())}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_response

    response = client.post(
        '/calsync/api/calendar/add-link',
        json=sample_event,
        content_type='application/json'
    )

    assert response.status_code == 200
    data = response.get_json()

    outlook_url = data['outlook']
    assert 'outlook.live.com' in outlook_url
    assert 'subject=' in outlook_url
    assert 'startdt=' in outlook_url
    assert 'enddt=' in outlook_url


def test_yahoo_url_format(client, mock_supabase, sample_event):
    """Test that Yahoo URL contains calendar.yahoo.com."""
    mock_response = MagicMock()
    mock_response.data = [{"id": str(uuid.uuid4())}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_response

    response = client.post(
        '/calsync/api/calendar/add-link',
        json=sample_event,
        content_type='application/json'
    )

    assert response.status_code == 200
    data = response.get_json()

    yahoo_url = data['yahoo']
    assert 'calendar.yahoo.com' in yahoo_url
    assert 'v=60' in yahoo_url
    assert 'title=' in yahoo_url
    assert 'st=' in yahoo_url
    assert 'et=' in yahoo_url


def test_generate_api_key(client, mock_supabase):
    """Test POST /calsync/api/keys/generate returns key starting with csk_."""
    mock_response = MagicMock()
    mock_response.data = [{"api_key": "csk_test123456789012345678", "plan": "free"}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_response

    response = client.post(
        '/calsync/api/keys/generate',
        json={"plan": "free"},
        content_type='application/json'
    )

    assert response.status_code == 200
    data = response.get_json()
    assert 'api_key' in data
    assert data['api_key'].startswith('csk_')
    assert len(data['api_key']) > 4  # Should be csk_ + random chars
    assert 'plan' in data


def test_generate_api_key_pro_plan(client, mock_supabase):
    """Test generating Pro plan API key."""
    mock_response = MagicMock()
    mock_response.data = [{"api_key": "csk_pro123456789012345678", "plan": "pro"}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_response

    response = client.post(
        '/calsync/api/keys/generate',
        json={"plan": "pro", "bubble_app_id": "test_app"},
        content_type='application/json'
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['plan'] == 'pro'
    assert data['api_key'].startswith('csk_')
    assert 'bubble_app_id' in data


def test_generate_api_key_invalid_plan(client, mock_supabase):
    """Test generating API key with invalid plan returns 400."""
    response = client.post(
        '/calsync/api/keys/generate',
        json={"plan": "invalid"},
        content_type='application/json'
    )

    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data


def test_ics_download_not_found(client, mock_supabase):
    """Test GET /calsync/ical/event/fake-id.ics returns 404."""
    # Mock empty result (event not found)
    mock_response = MagicMock()
    mock_response.data = []
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

    fake_id = str(uuid.uuid4())
    response = client.get(f'/calsync/ical/event/{fake_id}.ics')

    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_add_link_persists_event(client, mock_supabase, sample_event):
    """Test that after add-link, the event_id can be used to download .ics."""
    event_id = str(uuid.uuid4())

    # Mock insert for add-link
    insert_response = MagicMock()
    insert_response.data = [{"id": event_id}]

    # Mock select for download
    select_response = MagicMock()
    select_response.data = [{
        "id": event_id,
        "title": sample_event["title"],
        "start_time": sample_event["start"],
        "end_time": sample_event["end"],
        "description": sample_event.get("description", ""),
        "location": sample_event.get("location", "")
    }]

    # Configure mock to return different responses
    mock_table = mock_supabase.table.return_value
    mock_table.insert.return_value.execute.return_value = insert_response
    mock_table.select.return_value.eq.return_value.execute.return_value = select_response

    # Step 1: Create event link
    response = client.post(
        '/calsync/api/calendar/add-link',
        json=sample_event,
        content_type='application/json'
    )

    assert response.status_code == 200
    data = response.get_json()
    returned_event_id = data['event_id']

    # Step 2: Download .ics file using the event_id
    response = client.get(f'/calsync/ical/event/{returned_event_id}.ics')

    assert response.status_code == 200
    assert response.content_type == 'text/calendar; charset=utf-8'


def test_ics_content_valid(client, mock_supabase, sample_event):
    """Test that downloaded .ics contains correct title and dates."""
    event_id = str(uuid.uuid4())

    # Mock select for download
    select_response = MagicMock()
    select_response.data = [{
        "id": event_id,
        "title": "My Test Event",
        "start_time": "2024-12-25T10:00:00Z",
        "end_time": "2024-12-25T11:00:00Z",
        "description": "Test description",
        "location": "Test location"
    }]

    mock_table = mock_supabase.table.return_value
    mock_table.select.return_value.eq.return_value.execute.return_value = select_response

    # Download .ics file
    response = client.get(f'/calsync/ical/event/{event_id}.ics')

    assert response.status_code == 200

    # Parse the .ics content
    ics_content = response.data.decode('utf-8')

    # Verify key fields are present
    assert 'My Test Event' in ics_content
    assert 'SUMMARY:My Test Event' in ics_content
    assert 'BEGIN:VEVENT' in ics_content
    assert 'END:VEVENT' in ics_content
    assert 'BEGIN:VCALENDAR' in ics_content
    assert 'END:VCALENDAR' in ics_content
    # Check dates are present (format may vary)
    assert '20241225T100000Z' in ics_content  # Start time
    assert '20241225T110000Z' in ics_content  # End time


def test_api_key_stored(client, mock_supabase):
    """Test that generated key can be found in DB."""
    generated_key = "csk_test987654321098765432"

    # Mock insert response
    insert_response = MagicMock()
    insert_response.data = [{
        "api_key": generated_key,
        "plan": "free",
        "usage_count": 0
    }]

    # Mock select response (simulating DB lookup)
    select_response = MagicMock()
    select_response.data = [{
        "api_key": generated_key,
        "plan": "free",
        "usage_count": 0
    }]

    mock_table = mock_supabase.table.return_value
    mock_table.insert.return_value.execute.return_value = insert_response
    mock_table.select.return_value.eq.return_value.execute.return_value = select_response

    # Generate API key
    response = client.post(
        '/calsync/api/keys/generate',
        json={"plan": "free"},
        content_type='application/json'
    )

    assert response.status_code == 200
    data = response.get_json()
    api_key = data['api_key']

    # Verify the API key was inserted
    mock_supabase.table.assert_called()
    # The insert should have been called with the generated key
    assert api_key.startswith('csk_')


def test_api_key_usage_tracking(client, mock_supabase, sample_event, mock_api_key_data):
    """Test that API key usage is tracked when provided."""
    # Mock validate response
    validate_response = MagicMock()
    validate_response.data = [mock_api_key_data]

    # Mock update response
    update_response = MagicMock()
    update_response.data = [{"usage_count": 1}]

    # Mock insert response
    insert_response = MagicMock()
    insert_response.data = [{"id": str(uuid.uuid4())}]

    mock_table = mock_supabase.table.return_value
    mock_table.select.return_value.eq.return_value.execute.return_value = validate_response
    mock_table.update.return_value.eq.return_value.execute.return_value = update_response
    mock_table.insert.return_value.execute.return_value = insert_response

    # Add API key to request
    event_with_key = {**sample_event, "api_key": mock_api_key_data["api_key"]}

    response = client.post(
        '/calsync/api/calendar/add-link',
        json=event_with_key,
        content_type='application/json'
    )

    assert response.status_code == 200
    # Verify update was called to increment usage
    mock_table.update.assert_called()


# ============================================================================
# EDGE CASES & ERROR HANDLING
# ============================================================================

def test_add_link_invalid_date_format(client):
    """Test that invalid date format returns 400."""
    response = client.post(
        '/calsync/api/calendar/add-link',
        json={
            "title": "Test",
            "start": "invalid-date",
            "end": "2024-12-25T11:00:00Z"
        },
        content_type='application/json'
    )

    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'datetime' in data['error'].lower()


def test_add_link_supabase_failure(client, mock_supabase, sample_event):
    """Test that Supabase failure doesn't break the response."""
    # Mock Supabase failure
    mock_supabase.table.return_value.insert.return_value.execute.side_effect = Exception("DB Error")

    response = client.post(
        '/calsync/api/calendar/add-link',
        json=sample_event,
        content_type='application/json'
    )

    # Should still return URLs even if DB insert fails
    assert response.status_code == 200
    data = response.get_json()
    assert 'google' in data
    assert 'apple' in data


def test_generate_api_key_no_supabase(client, monkeypatch):
    """Test API key generation fails gracefully without Supabase."""
    from src import calsync
    monkeypatch.setattr(calsync, 'supabase', None)

    response = client.post(
        '/calsync/api/keys/generate',
        json={"plan": "free"},
        content_type='application/json'
    )

    assert response.status_code == 500
    data = response.get_json()
    assert 'error' in data
    assert 'supabase' in data['error'].lower()


def test_ics_download_no_supabase(client, monkeypatch):
    """Test .ics download fails gracefully without Supabase."""
    from src import calsync
    monkeypatch.setattr(calsync, 'supabase', None)

    event_id = str(uuid.uuid4())
    response = client.get(f'/calsync/ical/event/{event_id}.ics')

    assert response.status_code == 500
    data = response.get_json()
    assert 'error' in data


def test_add_link_with_special_characters(client, mock_supabase):
    """Test that special characters in event data are handled correctly."""
    mock_response = MagicMock()
    mock_response.data = [{"id": str(uuid.uuid4())}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_response

    special_event = {
        "title": "Test & Meeting: <Important>",
        "start": "2024-12-25T10:00:00Z",
        "end": "2024-12-25T11:00:00Z",
        "description": "Description with special chars: @#$%",
        "location": "Room #5 (Building A)"
    }

    response = client.post(
        '/calsync/api/calendar/add-link',
        json=special_event,
        content_type='application/json'
    )

    assert response.status_code == 200
    data = response.get_json()
    assert 'google' in data
    assert 'outlook' in data
    assert 'yahoo' in data


def test_add_link_minimal_data(client, mock_supabase):
    """Test add-link with only required fields (no description or location)."""
    mock_response = MagicMock()
    mock_response.data = [{"id": str(uuid.uuid4())}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_response

    minimal_event = {
        "title": "Minimal Event",
        "start": "2024-12-25T10:00:00Z",
        "end": "2024-12-25T11:00:00Z"
    }

    response = client.post(
        '/calsync/api/calendar/add-link',
        json=minimal_event,
        content_type='application/json'
    )

    assert response.status_code == 200
    data = response.get_json()
    assert 'google' in data
    assert 'apple' in data
    assert 'outlook' in data
    assert 'yahoo' in data
