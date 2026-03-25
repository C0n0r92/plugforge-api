/**
 * CalSync Bubble Plugin — Action 4
 * Generate iCal Feed URL (FREE with API key)
 *
 * Creates a subscribable iCal feed that users can add to their calendar app.
 * The feed URL remains constant and can be updated with new events.
 *
 * INPUTS:
 * - api_key (text): CalSync API key (required)
 * - events (list): Array of events, each with:
 *   - title (text): Event title
 *   - start (text): ISO8601 datetime string
 *   - end (text): ISO8601 datetime string
 *   - description (text, optional): Event description
 *   - location (text, optional): Event location
 *
 * OUTPUTS (exposed as action result):
 * - feed_id (text): Unique feed identifier
 * - feed_url (text): Subscribable iCal feed URL (add to any calendar app)
 *
 * USAGE:
 * Users can subscribe to the feed_url in:
 * - Apple Calendar: File → New Calendar Subscription
 * - Google Calendar: Other calendars → From URL
 * - Outlook: Add calendar → From internet
 */

function(properties, context) {
    const API_URL = 'https://api.plugforge.dev/calsync/api/feed/create';

    // Validate required inputs
    if (!properties.api_key) {
        throw new Error('api_key is required');
    }

    if (!properties.events || !Array.isArray(properties.events) || properties.events.length === 0) {
        throw new Error('events array is required and must contain at least one event');
    }

    // Validate each event has required fields
    properties.events.forEach((event, index) => {
        if (!event.title || !event.start || !event.end) {
            throw new Error(`Event at index ${index} is missing required fields (title, start, end)`);
        }
    });

    // Build request payload
    const payload = {
        api_key: properties.api_key,
        events: properties.events.map(event => ({
            title: event.title,
            start: event.start,
            end: event.end,
            description: event.description || '',
            location: event.location || ''
        }))
    };

    // Make API request
    return context.request({
        url: API_URL,
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    }).then(response => {
        if (response.statusCode !== 200) {
            const data = JSON.parse(response.body);
            throw new Error(`API Error: ${data.error || 'Unknown error'}`);
        }

        const data = JSON.parse(response.body);

        return {
            feed_id: data.feed_id,
            feed_url: data.feed_url
        };
    });
}
