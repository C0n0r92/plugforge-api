/**
 * CalSync Bubble Plugin — Action 3
 * Delete Google Calendar Event (PRO)
 *
 * INPUTS:
 * - api_key (text): CalSync Pro API key (required)
 * - access_token (text): Google OAuth access token (from OAuth flow)
 * - event_id (text): Google Calendar event ID to delete
 *
 * OUTPUTS (exposed as action result):
 * - success (boolean): Whether the event was deleted successfully
 * - expired (boolean): Whether the access token has expired (requires re-auth)
 * - message (text): Success or error message
 */

function(properties, context) {
    const API_URL = 'https://api.plugforge.dev/calsync/api/gcal/delete';

    // Validate required inputs
    if (!properties.api_key) {
        throw new Error('api_key is required (Pro feature)');
    }

    if (!properties.access_token) {
        throw new Error('access_token is required (complete OAuth flow first)');
    }

    if (!properties.event_id) {
        throw new Error('event_id is required');
    }

    // Build request payload
    const payload = {
        api_key: properties.api_key,
        access_token: properties.access_token,
        event_id: properties.event_id
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
                message: 'Access token expired. Please re-authenticate with Google.'
            };
        }

        if (response.statusCode !== 200) {
            throw new Error(`API Error: ${data.error || 'Unknown error'}`);
        }

        return {
            success: data.success,
            expired: false,
            message: data.message
        };
    });
}
