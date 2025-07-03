import requests
import urllib3
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import urllib.parse


@dataclass
class ActivityData:
    """Data class for daily activity information"""
    # Basic identification
    id: Optional[int]
    user_id: int
    user_name: str
    project_id: Optional[int]
    project_name: Optional[str]
    task_id: Optional[int]
    task_name: Optional[str]
    
    # Time information
    date: Optional[str]
    start_time: datetime
    end_time: Optional[datetime]
    
    # Duration tracking (all in seconds)
    tracked: int  # Total time worked
    keyboard: Optional[int]  # Keyboard active time
    mouse: Optional[int]  # Mouse active time
    overall: Optional[int]  # Keyboard or mouse active time
    input_tracked: Optional[int]  # Time with input tracking enabled
    manual: Optional[int]  # Manual time
    idle: Optional[int]  # Idle time
    resumed: Optional[int]  # Resumed time
    billable: Optional[int]  # Billable time
    work_break: Optional[int]  # Work break time
    
    # Metadata
    timezone: str
    note: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    
    @property
    def duration(self) -> int:
        """Backward compatibility: return tracked time as duration"""
        return self.tracked
    
    @property
    def active_time(self) -> int:
        """Get active time (keyboard or mouse)"""
        return self.overall or 0
    
    @property
    def productivity_ratio(self) -> float:
        """Calculate productivity ratio (active time / tracked time)"""
        if self.tracked == 0:
            return 0.0
        return (self.active_time / self.tracked) * 100


class HubstaffAPIError(Exception):
    """Custom exception for Hubstaff API errors"""
    pass


class HubstaffAPIService:
    """Service for making internal API calls to Hubstaff"""
    
    BASE_URL = "https://api.hubstaff.com"
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'User-Agent': 'HubstaffBot/1.0'
        })

    def _make_request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make HTTP request to Hubstaff API without encoding query parameters"""
        url = f"{self.BASE_URL}{endpoint}"
        
   
        try:
            # Build URL manually with unencoded parameters
            if params:
                query_parts = []
                for key, value in params.items():
                    if isinstance(value, list):
                        for v in value:
                            query_parts.append(f"{key}={v}")
                    else:
                        query_parts.append(f"{key}={value}")
                query_string = "&".join(query_parts)
                full_url = f"{url}?{query_string}"
            else:
                full_url = url
                
          
          
            
            # Use urllib3 pool manager to bypass requests' encoding
            http = urllib3.PoolManager()
            response = http.request(
                method=method.upper(),
                url=full_url,
                headers=dict(self.session.headers),
                timeout=30
            )
            

            # Handle status codes
            response_body = response.data.decode('utf-8')
            
            if response.status == 401:
                raise HubstaffAPIError("Authentication failed. Please reconnect to Hubstaff.")
            elif response.status == 403:
                try:
                    error_data = json.loads(response_body)
                    error_message = error_data.get('error', {}).get('message', 'Access denied')
                    raise HubstaffAPIError(f"Access denied: {error_message}")
                except Exception:
                    raise HubstaffAPIError("Access denied. You don't have permission to access this resource.")
            elif response.status == 404:
                raise HubstaffAPIError("Resource not found. The requested data is not available.")
            elif response.status >= 500:
                raise HubstaffAPIError("Hubstaff server error. Please try again later.")
            
            if response.status >= 400:
                # Include the full response body in the error message
                try:
                    error_data = json.loads(response_body)
                    error_message = f"HTTP {response.status} error: {json.dumps(error_data, indent=2)}"
                except Exception:
                    error_message = f"HTTP {response.status} error. Response: {response_body}"
                raise HubstaffAPIError(error_message)
                
            return json.loads(response.data.decode('utf-8'))

        except Exception as e:
            if isinstance(e, HubstaffAPIError):
                raise
            raise HubstaffAPIError(f"API request failed: {e}")

    def get_organizations(self) -> List[Dict[str, Any]]:
        """Get list of organizations the user has access to"""
        # Debug: Show access token being used
        print(f"🔑 **Access Token Debug (Organizations):**")
        print(f"Token length: {len(self.access_token)} characters")
        print(f"Token starts with: {self.access_token[:20]}...")
        print(f"Token ends with: ...{self.access_token[-10:]}")
        print(f"Full token: {self.access_token}")
        print("-" * 50)
        
        response = self._make_request('GET', '/v2/organizations')
        return response.get('organizations', [])
    
    def get_activities(self, organization_id: int, start_time: datetime, end_time: datetime) -> List[ActivityData]:
        """
        Get activities for a specific organization within a time range
        
        Args:
            organization_id: The organization ID
            start_time: Start time for the query
            end_time: End time for the query
            
        Returns:
            List of ActivityData objects
        """
        # Debug: Show access token being used
        print(f"🔑 **Access Token Debug:**")
        print(f"Token length: {len(self.access_token)} characters")
        print(f"Token starts with: {self.access_token[:20]}...")
        print(f"Token ends with: ...{self.access_token[-10:]}")
        print(f"Full token: {self.access_token}")
        print(f"Organization ID: {organization_id}")
        print(f"Time range: {start_time} to {end_time}")
        print("-" * 50)
        
        # Format times for API
        start_str = start_time.strftime('%Y-%m-%dT%H:%M:%S')
        end_str = end_time.strftime('%Y-%m-%dT%H:%M:%S')
        
        params = {
            'date[start]': start_str,
            'date[stop]': end_str
        }
        
        response = self._make_request(
            'GET', 
            f'/v2/organizations/{organization_id}/activities/daily',
            params=params
        )
        
        # Get users cache for proper user names
        users_cache = self.get_users_cache(organization_id)
        
        activities = []
        for activity in response.get('daily_activities', []):
            # Parse date if available
            date_str = activity.get('date')
            
            # Parse start time (use date if no specific start time)
            start_time = None
            if activity.get('starts_at'):
                start_time = datetime.fromisoformat(activity['starts_at'].replace('Z', '+00:00'))
            elif date_str:
                # Use date as start time if no specific start time
                start_time = datetime.fromisoformat(f"{date_str}T00:00:00")
            else:
                start_time = datetime.now()
            
            # Parse end time if available
            end_time = None
            if activity.get('stops_at'):
                end_time = datetime.fromisoformat(activity['stops_at'].replace('Z', '+00:00'))
            
            # Get proper user name from cache or API
            user_id = activity.get('user_id')
            user_name = 'Unknown User'
            
            if user_id:
                if user_id in users_cache:
                    user_name = users_cache[user_id].get('name', 'Unknown User')
                else:
                    # Fallback: try to get user directly
                    user_info = self.get_user_by_id(user_id)
                    if user_info:
                        user_name = user_info.get('name', 'Unknown User')
            
            activity_data = ActivityData(
                # Basic identification
                id=activity.get('id'),
                user_id=user_id,
                user_name=user_name,
                project_id=activity.get('project_id'),
                project_name=activity.get('project_name'),
                task_id=activity.get('task_id'),
                task_name=activity.get('task_name'),
                
                # Time information
                date=date_str,
                start_time=start_time,
                end_time=end_time,
                
                # Duration tracking
                tracked=activity.get('tracked', 0),
                keyboard=activity.get('keyboard'),
                mouse=activity.get('mouse'),
                overall=activity.get('overall'),
                input_tracked=activity.get('input_tracked'),
                manual=activity.get('manual'),
                idle=activity.get('idle'),
                resumed=activity.get('resumed'),
                billable=activity.get('billable'),
                work_break=activity.get('work_break'),
                
                # Metadata
                timezone=activity.get('timezone', 'UTC'),
                note=activity.get('note'),
                created_at=activity.get('created_at'),
                updated_at=activity.get('updated_at')
            )
            activities.append(activity_data)
        
        return activities
    
    def get_last_day_activities(self, organization_id: int) -> List[ActivityData]:
        """
        Get activities for the last 24 hours
        
        Args:
            organization_id: The organization ID
            
        Returns:
            List of ActivityData objects for the last 24 hours
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(days=1)
        
        return self.get_activities(organization_id, start_time, end_time)
    
    def get_user_info(self) -> Dict[str, Any]:
        """Get current user information"""
        response = self._make_request('GET', '/v2/users/me')
        return response.get('user', {})
    
    def get_projects(self, organization_id: int) -> List[Dict[str, Any]]:
        """Get projects for an organization"""
        response = self._make_request('GET', f'/v2/organizations/{organization_id}/projects')
        return response.get('projects', [])
    
    def get_users(self, organization_id: int) -> List[Dict[str, Any]]:
        """Get users for an organization"""
        response = self._make_request('GET', f'/v2/organizations/{organization_id}/members')
        return response.get('users', [])
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user details by user ID"""
        try:
            response = self._make_request('GET', f'/v2/users/{user_id}')
            return response.get('user', {})
        except Exception as e:
            print(f"⚠️ **Error getting user {user_id}:** {e}")
            return None
    
    def get_users_cache(self, organization_id: int) -> Dict[int, Dict[str, Any]]:
        """Get users for an organization and cache them by ID for quick lookup"""
        users = self.get_users(organization_id)
        return {user['id']: user for user in users}
    
    def test_permissions(self) -> Dict[str, Any]:
        """Test user permissions and return available endpoints"""
        permissions = {
            'organizations': False,
            'user_info': False,
            'activities': False,
            'projects': False,
            'users': False
        }
        
        # Test organizations endpoint
        try:
            orgs = self.get_organizations()
            permissions['organizations'] = True
            permissions['organizations_count'] = len(orgs)
        except Exception as e:
            permissions['organizations_error'] = str(e)
        
        # Test user info endpoint
        try:
            user_info = self.get_user_info()
            permissions['user_info'] = True
            permissions['user_data'] = user_info
        except Exception as e:
            permissions['user_info_error'] = str(e)
        
        # Test activities endpoint if we have organizations
        if permissions['organizations'] and permissions.get('organizations_count', 0) > 0:
            try:
                orgs = self.get_organizations()
                first_org = orgs[0]
                activities = self.get_last_day_activities(first_org['id'])
                permissions['activities'] = True
                permissions['activities_count'] = len(activities)
            except Exception as e:
                permissions['activities_error'] = str(e)
        
        return permissions


def format_activities_summary(activities: List[ActivityData]) -> str:
    """
    Format activities data into a readable summary with productivity metrics
    
    Args:
        activities: List of ActivityData objects
        
    Returns:
        Formatted string with activity summary
    """
    if not activities:
        return "📊 **No Activity Found**\n\nNo activity was recorded in the last 24 hours."
    
    # Calculate totals
    total_tracked = sum(activity.tracked for activity in activities)
    total_active = sum(activity.active_time for activity in activities)
    total_billable = sum(activity.billable or 0 for activity in activities)
    total_manual = sum(activity.manual or 0 for activity in activities)
    total_idle = sum(activity.idle or 0 for activity in activities)
    
    total_tracked_hours = total_tracked / 3600
    total_active_hours = total_active / 3600
    total_billable_hours = total_billable / 3600
    total_manual_hours = total_manual / 3600
    total_idle_hours = total_idle / 3600
    
    # Calculate overall productivity
    overall_productivity = (total_active / total_tracked * 100) if total_tracked > 0 else 0
    
    # Debug: Print activities as JSON
    import json
    from dataclasses import asdict
    
    activities_dict = [asdict(activity) for activity in activities]
    print("🔍 **Activities Debug:**")
    print(json.dumps(activities_dict, indent=2, default=str))
    print("-" * 50)
    
    # Group by user with detailed metrics
    user_activities = {}
    for activity in activities:
        user_name = activity.user_name
        if user_name not in user_activities:
            user_activities[user_name] = {
                'total_tracked': 0,
                'total_active': 0,
                'total_billable': 0,
                'total_manual': 0,
                'total_idle': 0,
                'activities': []
            }
        user_activities[user_name]['total_tracked'] += activity.tracked
        user_activities[user_name]['total_active'] += activity.active_time
        user_activities[user_name]['total_billable'] += activity.billable or 0
        user_activities[user_name]['total_manual'] += activity.manual or 0
        user_activities[user_name]['total_idle'] += activity.idle or 0
        user_activities[user_name]['activities'].append(activity)
    
    # Build summary
    summary = f"📊 **Last 24 Hours Activity Summary**\n\n"
    summary += f"⏰ **Total Time Tracked:** {total_tracked_hours:.1f} hours\n"
    summary += f"🎯 **Active Time:** {total_active_hours:.1f} hours ({overall_productivity:.1f}%)\n"
    summary += f"💰 **Billable Time:** {total_billable_hours:.1f} hours\n"
    summary += f"✏️ **Manual Time:** {total_manual_hours:.1f} hours\n"
    summary += f"😴 **Idle Time:** {total_idle_hours:.1f} hours\n"
    summary += f"👥 **Active Users:** {len(user_activities)}\n"
    summary += f"📝 **Total Activities:** {len(activities)}\n\n"
    
    # Add user breakdown with productivity
    summary += "**User Activity Breakdown:**\n"
    for user_name, data in user_activities.items():
        user_tracked_hours = data['total_tracked'] / 3600
        user_active_hours = data['total_active'] / 3600
        user_productivity = (data['total_active'] / data['total_tracked'] * 100) if data['total_tracked'] > 0 else 0
        user_billable_hours = data['total_billable'] / 3600
        
        summary += f"• 👤 **{user_name}:** {user_tracked_hours:.1f}h tracked, {user_active_hours:.1f}h active ({user_productivity:.1f}%), {user_billable_hours:.1f}h billable\n"
    
    summary += "\n**Recent Activities:**\n"
    
    # Show recent activities (last 10) with productivity info
    recent_activities = sorted(activities, key=lambda x: x.start_time, reverse=True)[:10]
    
    for activity in recent_activities:
        start_time_str = activity.start_time.strftime('%H:%M')
        tracked_hours = activity.tracked / 3600
        active_hours = activity.active_time / 3600
        productivity = activity.productivity_ratio
        
        project_info = ""
        if activity.project_name:
            project_info = f" ({activity.project_name})"
        
        productivity_emoji = "🟢" if productivity >= 80 else "🟡" if productivity >= 50 else "🔴"
        
        summary += f"• 🕐 **{start_time_str}** - {activity.user_name}{project_info}: {tracked_hours:.1f}h tracked, {active_hours:.1f}h active {productivity_emoji} ({productivity:.1f}%)\n"
    
    return summary


def create_hubstaff_api_service(access_token: str) -> HubstaffAPIService:
    """
    Factory function to create Hubstaff API service
    
    Args:
        access_token: User's Hubstaff access token
        
    Returns:
        HubstaffAPIService instance
    """
    return HubstaffAPIService(access_token) 