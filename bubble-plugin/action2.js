/**
 * CalSync Bubble Plugin — Action 2
 * Create Google Calendar Event (PRO)
 *
 * INPUTS:
 * - api_key (text): CalSync Pro API key (required)
 * - access_token (text): Google OAuth access token (from OAuth flow)
 * - title (text): Event title
 * - start (text): ISO8601 datetime string (e.g., "2026-03-25T10:00:00Z")
 * - end (text): ISO8601 datetime string
 * - description (text, optional): Event description
 * - location (text, optional): Event location
 *
 * OUTPUTS (exposed as action result):
 * - success (boolean): Whether the event was created successfully
 * - event_id (text): Google Calendar event ID
 * - html_link (text): Link to view event in Google Calendar
 * - expired (boolean): Whether the access token has expired (requires re-auth)
 */

function(properties, context) {
    const API_URL = 'https://api.plugforge.dev/calsync/api/gcal/create';

    // Validate required inputs
    if (!properties.api_key) {
        throw new Error('api_key is required (Pro feature)');
    }

    if (!properties.access_token) {
        throw new Error('access_token is required (complete OAuth flow first)');
    }

    if (!properties.title || !properties.start || !properties.end) {
        throw new Error('Missing required fields: title, start, and end are required');
    }

    // Build request payload
    const payload = {
        api_key: properties.api_key,
        access_token: properties.access_token,
        title: properties.title,
        start: properties.start,
        end: properties.end,
        description: properties.description || '',
        location: properties.location || ''
    };

    // Make API request
    return context.request({
        url: API_URL,
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CalSync-Key': properties.api_key
        },
        body: JSON.stringify(payload)
    }).then(response => {
        const data = JSON.parse(response.body);

        if (response.statusCode === 401 && data.expired) {
            // Token expired - user needs to re-authenticate
            return {
                success: false,
                expired: true,
                event_id: null,
                html_link: null,
                error: 'Access token expired. Please re-authenticate with Google.'
            };
        }

        if (response.statusCode !== 200) {
            throw new Error(`API Error: ${data.error || 'Unknown error'}`);
        }

        return {
            success: data.success,
            event_id: data.event_id,
            html_link: data.html_link,
            expired: false
        };
    });
}
