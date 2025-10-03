# LMArena Bridge Dashboard System

A comprehensive dashboard system for managing API tokens, tracking usage statistics, and monitoring your LMArena Bridge deployment.

## Features

### 1. **Active Token Display**
- Real-time count of active API tokens
- Dynamic token status monitoring

### 2. **Admin Panel** (`/admin`)
- Secure authentication with username/password from `.env`
- Complete token management:
  - Create new tokens with optional user information
  - Revoke/activate tokens
  - Delete tokens permanently
  - View detailed token statistics
- Analytics dashboard with charts:
  - Request volume over time
  - Geographic distribution of users
  - Model usage breakdown

### 3. **User Dashboard** (Main Page `/`)
- Public statistics overview
- Token validation and information lookup
- Usage timeline charts (last 7 days)
- Recent activity feed showing:
  - Model usage
  - Country of origin
  - Token consumption

### 4. **Modern Dark Red/Purple Galactic UI**
- Professional dark theme with red-purple gradient accents
- Animated starfield background
- No emojis (clean, professional design)
- Fully responsive for mobile devices
- Interactive charts using Chart.js

### 5. **Security Features**
- Admin panel not linked from main page (direct URL access only)
- Session-based authentication with 24-hour timeout
- Environment variable configuration for credentials
- Token-based API access control
- IP address tracking and geolocation

### 6. **Usage Analytics**
- Request count tracking
- Token usage estimation
- Model usage breakdown
- Geographic distribution (country-level)
- IP address history (last 100 per token)
- Timeline charts for trend analysis

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements_dashboard.txt
```

### 2. Configure Environment Variables

Edit the `.env` file in the project root:

```env
# Admin Credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password_here

# Dashboard Configuration
DASHBOARD_PORT=5103
SECRET_KEY=your-secret-key-here

# Database
DB_FILE=dashboard_data.json
```

**Important:** Change the default password before deploying!

### 3. Start the Dashboard Server

```bash
python dashboard_server.py
```

The dashboard will be available at:
- Main Dashboard: `http://127.0.0.1:5103/`
- Admin Panel: `http://127.0.0.1:5103/admin`

## Usage

### For Administrators

1. **Access Admin Panel**
   - Navigate to `http://127.0.0.1:5103/admin`
   - Login with credentials from `.env`

2. **Create API Tokens**
   - Click "Generate Token" in the admin panel
   - Optionally add user name and email
   - Copy the generated token (shown only once!)
   - Distribute to users

3. **Manage Tokens**
   - View all tokens and their statistics
   - Revoke tokens to disable access
   - Activate previously revoked tokens
   - Delete tokens permanently
   - View detailed usage per token

4. **Monitor Usage**
   - View charts showing request trends
   - Check geographic distribution
   - Monitor model usage patterns

### For Users

1. **Check Token Status**
   - Visit `http://127.0.0.1:5103/`
   - Enter your API token in the "Check Your Token" section
   - View your usage statistics:
     - Total requests made
     - Total tokens consumed
     - Last used timestamp
     - Number of unique IPs

2. **Use Your Token**
   - Add token to API requests as Bearer token:
   ```bash
   curl http://127.0.0.1:5102/v1/chat/completions \
     -H "Authorization: Bearer YOUR_TOKEN_HERE" \
     -H "Content-Type: application/json" \
     -d '{...}'
   ```

## Integration with api_server.py

The dashboard automatically integrates with the existing `api_server.py`:

1. **Token Validation**: All API requests are validated against active tokens
2. **Usage Logging**: Each request logs:
   - Model used
   - Estimated token count
   - Client IP address
   - Country (via IP geolocation)
   - Timestamp

3. **Backward Compatibility**: If dashboard is not available, the system falls back to the old `api_key` configuration in `config.jsonc`

## Database Structure

The system uses a JSON-based database (`dashboard_data.json`) with the following structure:

```json
{
  "tokens": {
    "token_id": {
      "key": "lma_...",
      "created_at": "2025-01-01T00:00:00",
      "last_used": "2025-01-01T12:00:00",
      "is_active": true,
      "user_info": {"name": "...", "email": "..."},
      "usage_stats": {
        "total_requests": 100,
        "total_tokens": 50000,
        "models_used": {"model-name": 50},
        "ip_addresses": ["1.2.3.4"],
        "countries": {"United States": 100}
      }
    }
  },
  "usage_logs": [...],
  "stats": {
    "total_requests": 100,
    "total_tokens": 50000,
    "active_tokens": 5
  }
}
```

## API Endpoints

### Public Endpoints

- `GET /` - Main dashboard page
- `GET /api/stats` - Global statistics (JSON)
- `GET /api/token/{token}/info` - Token information (JSON)
- `GET /api/usage/timeline?days=7&token=...` - Usage timeline data

### Admin Endpoints (Authentication Required)

- `GET /admin` - Admin panel page
- `GET /admin/login` - Login page
- `POST /admin/login` - Handle login
- `GET /admin/logout` - Logout
- `POST /admin/token/create` - Create new token
- `POST /admin/token/{token_id}/revoke` - Revoke token
- `POST /admin/token/{token_id}/activate` - Activate token
- `POST /admin/token/{token_id}/delete` - Delete token
- `GET /api/admin/tokens` - Get all tokens (JSON)
- `GET /api/admin/recent-usage` - Recent usage logs (JSON)

## Mobile Responsiveness

The dashboard is fully responsive with breakpoints at:
- **Desktop**: 1024px and above
- **Tablet**: 768px - 1023px
- **Mobile**: 320px - 767px

Features on mobile:
- Stacked layout for better readability
- Touch-friendly buttons and controls
- Responsive charts that adapt to screen size
- Collapsible sections for better navigation

## Security Considerations

1. **Change Default Credentials**: Always change the default admin password in `.env`
2. **HTTPS**: Use HTTPS in production (configure reverse proxy)
3. **Firewall**: Restrict dashboard access to trusted networks
4. **Token Security**: Treat API tokens like passwords
5. **Session Management**: Sessions expire after 24 hours
6. **No Public Links**: Admin panel is not linked from public pages

## Troubleshooting

### Dashboard not loading
- Check if `dashboard_server.py` is running
- Verify port 5103 is not in use
- Check console for error messages

### Token validation failing
- Ensure `database.py` is in the same directory
- Check `dashboard_data.json` exists and is readable
- Verify token is active in admin panel

### Charts not displaying
- Check browser console for JavaScript errors
- Ensure Chart.js CDN is accessible
- Verify API endpoints are returning data

### Geolocation not working
- Check internet connectivity (uses ip-api.com)
- Local IPs (127.0.0.1) will show as "Local"
- API rate limits may apply for high-volume usage

## License

This dashboard system is part of the LMArena Bridge project.
