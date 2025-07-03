#!/usr/bin/env python3
"""
Test script for Hubstaff API service
Usage: python test_hubstaff_api.py <access_token>
"""

import sys
import os
from datetime import datetime, timedelta

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from bot_controller.services.hubstaff_api import create_hubstaff_api_service

def test_api(access_token):
    """Test the Hubstaff API with the provided token"""
    print("🔍 Testing Hubstaff API...")
    print(f"Token: {access_token[:10]}...")
    print("-" * 50)
    
    try:
        # Create API service
        api_service = create_hubstaff_api_service(access_token)
        
        # Test permissions
        print("📋 Testing permissions...")
        permissions = api_service.test_permissions()
        
        for key, value in permissions.items():
            if key.endswith('_error'):
                print(f"❌ {key}: {value}")
            elif isinstance(value, bool):
                status = "✅" if value else "❌"
                print(f"{status} {key}: {value}")
            else:
                print(f"ℹ️  {key}: {value}")
        
        print("-" * 50)
        
        # Test specific endpoints
        if permissions.get('organizations'):
            print("🏢 Testing organizations endpoint...")
            try:
                orgs = api_service.get_organizations()
                print(f"✅ Found {len(orgs)} organizations:")
                for org in orgs:
                    print(f"  • {org.get('name', 'Unknown')} (ID: {org.get('id')})")
            except Exception as e:
                print(f"❌ Organizations error: {e}")
        
        if permissions.get('user_info'):
            print("\n👤 Testing user info endpoint...")
            try:
                user_info = api_service.get_user_info()
                print(f"✅ User: {user_info.get('name', 'Unknown')}")
                print(f"  • Email: {user_info.get('email', 'Unknown')}")
                print(f"  • ID: {user_info.get('id', 'Unknown')}")
            except Exception as e:
                print(f"❌ User info error: {e}")
        
        if permissions.get('organizations') and permissions.get('organizations_count', 0) > 0:
            print("\n📊 Testing activities endpoint...")
            try:
                orgs = api_service.get_organizations()
                first_org = orgs[0]
                print(f"Testing with organization: {first_org.get('name')} (ID: {first_org.get('id')})")
                
                activities = api_service.get_last_day_activities(first_org['id'])
                print(f"✅ Found {len(activities)} activities")
                
                if activities:
                    print("Sample activities:")
                    for i, activity in enumerate(activities[:3]):
                        print(f"  {i+1}. {activity.user_name} - {activity.duration/3600:.1f}h")
                        if activity.project_name:
                            print(f"     Project: {activity.project_name}")
                
            except Exception as e:
                print(f"❌ Activities error: {e}")
        
    except Exception as e:
        print(f"❌ API service error: {e}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python test_hubstaff_api.py <access_token>")
        sys.exit(1)
    
    access_token = sys.argv[1]
    test_api(access_token)

if __name__ == "__main__":
    main() 