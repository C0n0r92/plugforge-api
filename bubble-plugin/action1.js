/**
 * CalSync Bubble Plugin — Action 1
 * Generate Add-to-Calendar Links (FREE)
 *
 * INPUTS:
 * - title (text): Event title
 * - start (text): ISO8601 datetime string (e.g., "2026-03-25T10:00:00Z")
 * - end (text): ISO8601 datetime string
 * - description (text, optional): Event description
 * - location (text, optional): Event location
 *
 * OUTPUTS:
 * - google_url (text): Google Calendar add link
 * - apple_url (text): Apple Calendar .ics download link
 * - outlook_url (text): Outlook Calendar add link
 * - yahoo_url (text): Yahoo Calendar add link
 * - event_id (text): Event ID for reference
 */

function(properties, context) {
    const API_URL = 'https://api.plugforge.dev/calsync/api/calendar/add-link';

    if (!properties.title || !properties.start || !properties.end) {
        throw new Error('Missing required fields: title, start, and end are required');
    }

    const payload = {
        title: properties.title,
        start: properties.start,
        end: properties.end,
        description: properties.description || '',
        location: properties.location || ''
    };

    return fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(function(response) { return response.json(); })
    .then(function(data) {
        if (data.error) throw new Error(data.error);
        return {
            google_url: data.google,
            apple_url: data.apple,
            outlook_url: data.outlook,
            yahoo_url: data.yahoo,
            event_id: data.event_id
        };
    });
}
