/**
 * CalSync Bubble Plugin — Action 1
 * Generate Add-to-Calendar Links (FREE)
 *
 * INPUTS:
 * - title (text): Event title
 * - event_date (text): Date e.g. "2026-04-01" or "April 1, 2026"
 * - start_time (text): Start time e.g. "10:00 AM" or "10:00"
 * - end_time (text): End time e.g. "11:00 AM" or "11:00"
 * - timezone (text, optional): e.g. "Europe/London", "America/New_York" (defaults to "UTC")
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

    if (!properties.title || !properties.event_date || !properties.start_time || !properties.end_time) {
        throw new Error('Missing required fields: title, event_date, start_time, and end_time are required');
    }

    const payload = {
        title: properties.title,
        event_date: properties.event_date,
        start_time: properties.start_time,
        end_time: properties.end_time,
        timezone: properties.timezone || 'UTC',
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
