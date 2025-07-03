# Hubstaff API Service

This document describes the Hubstaff API service that provides internal API calls to Hubstaff for retrieving activity data and other information.

## Overview

The `HubstaffAPIService` class provides a clean interface for making authenticated API calls to Hubstaff's internal API endpoints. It handles authentication, error handling, and data formatting.

## Features

- **Activity Retrieval**: Get activities for organizations within specified time ranges
- **Organization Management**: List organizations the user has access to
- **User Information**: Get current user details
- **Project Management**: List projects for organizations
- **Error Handling**: Comprehensive error handling with meaningful messages
- **Data Formatting**: Built-in formatting for activity summaries

## Usage

### Basic Setup

```python
from bot_controller.services.hubstaff_api import create_hubstaff_api_service

# Create API service with user's access token
api_service = create_hubstaff_api_service(user.hubstaff_access_token)
```

### Get Organizations

```python
# Get list of organizations
organizations = api_service.get_organizations()
for org in organizations:
    print(f"Organization: {org['name']} (ID: {org['id']})")
```

### Get Activities

```python
from datetime import datetime, timedelta

# Get activities for last 24 hours
organization_id = 123
activities = api_service.get_last_day_activities(organization_id)

# Or get activities for custom time range
end_time = datetime.now()
start_time = end_time - timedelta(days=7)
activities = api_service.get_activities(organization_id, start_time, end_time)
```

### Format Activity Summary

```python
from bot_controller.services.hubstaff_api import format_activities_summary

# Format activities into readable summary
summary = format_activities_summary(activities)
print(summary)
```

## API Endpoints

The service uses the following Hubstaff API endpoints:

- `GET /v2/organizations` - List organizations
- `GET /v2/organizations/{id}/activities` - Get activities
- `GET /v2/user` - Get current user info
- `GET /v2/organizations/{id}/projects` - List projects
- `GET /v2/organizations/{id}/users` - List users

## Data Models

### ActivityData

```python
@dataclass
class ActivityData:
    user_id: int
    user_name: str
    project_id: Optional[int]
    project_name: Optional[str]
    task_id: Optional[int]
    task_name: Optional[str]
    start_time: datetime
    end_time: Optional[datetime]
    duration: int  # in seconds
    timezone: str
    note: Optional[str]
```

## Error Handling

The service provides comprehensive error handling:

- **401 Unauthorized**: Authentication failed - user needs to reconnect
- **403 Forbidden**: Access denied - insufficient permissions
- **404 Not Found**: Resource not available
- **5xx Server Errors**: Hubstaff server issues

## Bot Integration

The service is integrated into the Telegram bot with the following commands:

- `/my_activity` - Show user's personal activity for last 24 hours
- Admin menu "📊 Show All Activity" - Show all team activity for last 24 hours

## Example Bot Response

```
📊 **Last 24 Hours Activity Summary**

⏰ **Total Time Tracked:** 45.2 hours
👥 **Active Users:** 8
📝 **Total Activities:** 23

**User Activity Breakdown:**
• 👤 **John Doe:** 8.5 hours
• 👤 **Jane Smith:** 7.2 hours
• 👤 **Mike Johnson:** 6.8 hours

**Recent Activities:**
• 🕐 **14:30** - John Doe (Project Alpha): 2.1h
• 🕐 **13:15** - Jane Smith (Project Beta): 1.8h
• 🕐 **12:00** - Mike Johnson (Project Gamma): 1.5h
```

## Configuration

The service uses the following configuration from `settings.py`:

- `HUBSTAFF_CLIENT_ID` - Hubstaff application client ID
- `HUBSTAFF_CLIENT_SECRET` - Hubstaff application client secret
- `HUBSTAFF_REDIRECT_URI` - OAuth redirect URI

## Security

- All API calls are authenticated using Bearer tokens
- Tokens are stored securely in the user database
- Automatic error handling for expired/invalid tokens
- User-specific access control

## Troubleshooting

### Common Issues

#### 1. "Access denied" Error
**Cause**: Insufficient OAuth scopes or user permissions
**Solution**: 
- Ensure OAuth scope includes `hubstaff:read`
- Check user's role in the organization
- Verify the user has access to the specific organization

#### 2. "No Organizations Found"
**Cause**: User not associated with any organizations
**Solution**: 
- Verify user account is properly set up in Hubstaff
- Check if user needs to be invited to an organization

#### 3. "Authentication failed"
**Cause**: Expired or invalid access token
**Solution**: 
- Reconnect using `/hubstaff_login`
- Check if token refresh is needed

### Debug Commands

Use `/debug_permissions` to check your current access levels and identify specific issues.

### Testing API Access

Use the test script to debug API calls:
```bash
python test_hubstaff_api.py <your_access_token>
```

## Future Enhancements

- Support for multiple organizations
- Activity filtering by project/task
- Export functionality (CSV, JSON)
- Real-time activity monitoring
- Custom time range selection 