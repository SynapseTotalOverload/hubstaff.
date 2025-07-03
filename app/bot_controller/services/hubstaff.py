from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from bot_controller.router import Router
from models import User
from settings import HUBSTAFF_CLIENT_ID, HUBSTAFF_REDIRECT_URI, ADMIN_PASSWORD
from bot_controller.services.hubstaff_oauth import hubstaff_oauth


router = Router(name=__name__)


@router.register(
    command="hubstaff_login",
    description=" HUBSTAFF LOGIN",
)
async def hubstaff_login(event, session: AsyncSession, user: User) -> tuple[str, types.InlineKeyboardMarkup]:
    """Handle /hubstaff_login command and return a button with Hubstaff login URL"""
    
    # Get chat ID for state parameter
    if isinstance(event, types.Message):
        chat_id = event.chat.id
    elif isinstance(event, types.CallbackQuery):
        chat_id = event.message.chat.id if event.message else user.external_id
    else:
        chat_id = user.external_id
    print(HUBSTAFF_REDIRECT_URI,55555)
    # Generate auth URL using OIDC discovery with state parameter
    hubstaff_login_url = hubstaff_oauth.get_auth_url(
        client_id=HUBSTAFF_CLIENT_ID,
        redirect_uri=HUBSTAFF_REDIRECT_URI,
        scope="openid profile email hubstaff:read hubstaff:write",
        state=str(chat_id)  # Use chat_id as state for security
    )
    
    # Build inline keyboard with login button
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(
            text="🔐 Login to Hubstaff",
            url=hubstaff_login_url
        )
    )
    
    message_text = "🔐 Click the button below to login to Hubstaff:\n\nThis will redirect you to Hubstaff's authorization page where you can grant access to your account."
    
    return message_text, builder.as_markup()


@router.register(
    command="hubstaff_status",
    description="HUBSTAFF STATUS",
)
async def hubstaff_status(event, session: AsyncSession, user: User) -> tuple[str, types.InlineKeyboardMarkup]:
    """Check if user is connected to Hubstaff and show all user data from Hubstaff API"""
    
    # Check if user has Hubstaff tokens
    has_access_token = bool(user.hubstaff_access_token)
    has_refresh_token = bool(user.hubstaff_refresh_token)
    has_id_token = bool(user.hubstaff_id_token)
    
    if has_access_token and has_refresh_token:
        # User is connected to Hubstaff
        status_emoji = "✅"
        status_text = "Connected"
        
        # Fetch user info from Hubstaff API
        try:
            from bot_controller.services.hubstaff_api import create_hubstaff_api_service
            api_service = create_hubstaff_api_service(user.hubstaff_access_token)
            hubstaff_user = api_service.get_user_info()
        except Exception as e:
            hubstaff_user = {"error": str(e)}
        
        # Format user info
        if hubstaff_user and not hubstaff_user.get("error"):
            user_info_lines = [f"• **{k}**: {v}" for k, v in hubstaff_user.items()]
            user_info_text = "\n".join(user_info_lines)
        else:
            user_info_text = f"❌ Failed to fetch user info: {hubstaff_user.get('error', 'Unknown error')}"
        
        message = (
            f"{status_emoji} **Hubstaff Status: {status_text}**\n\n"
            "🎉 You are successfully connected to Hubstaff!\n\n"
            "**Available Features:**\n"
            "• 📊 Time tracking data\n"
            "• 📈 Reports and analytics\n"
            "• 🔔 Notifications\n"
            "• ⏰ Start/stop tracking\n"
            "• 👥 Team management (if admin)\n\n"
            "**Connection Details:**\n"
            f"• Access Token: {'✅ Present' if has_access_token else '❌ Missing'}\n"
            f"• Refresh Token: {'✅ Present' if has_refresh_token else '❌ Missing'}\n"
            f"• ID Token: {'✅ Present' if has_id_token else '❌ Missing'}\n"
            f"• Admin Access: {'✅ Yes' if user.is_admin else '❌ No'}\n\n"
            "**Hubstaff User Info:**\n"
            f"{user_info_text}\n\n"
            "Use /help to see all available commands!"
        )
        
        # Add logout and change role buttons for connected users
        builder = InlineKeyboardBuilder()
        builder.add(
            types.InlineKeyboardButton(
                text="🔐 Logout from Hubstaff",
                callback_data=f"logout_confirm_{user.external_id}"
            )
        )
        builder.add(
            types.InlineKeyboardButton(
                text="🔄 Change Role",
                callback_data=f"change_role_{user.external_id}"
            )
        )
        
        return message, builder.as_markup()
    else:
        # User is not connected to Hubstaff
        status_emoji = "❌"
        status_text = "Not Connected"
        message = (
            f"{status_emoji} **Hubstaff Status: {status_text}**\n\n"
            "🔗 You are not connected to Hubstaff yet.\n\n"
            "**To connect:**\n"
            "1. Use /hubstaff_login command\n"
            "2. Click the login button\n"
            "3. Authorize the application\n"
            "4. Complete the setup process\n\n"
            "**What you'll get:**\n"
            "• 📊 Access to your time tracking data\n"
            "• 📈 Reports and analytics\n"
            "• 🔔 Real-time notifications\n"
            "• ⏰ Remote time tracking control\n\n"
            "Start by using /hubstaff_login to connect your account!"
        )
        
        return message, None


@router.register(
    command="debug_permissions",
    description="DEBUG HUBSTAFF PERMISSIONS",
)
async def debug_permissions(event, session: AsyncSession, user: User) -> str:
    """Debug user's Hubstaff permissions"""
    try:
        # Import the API service
        from bot_controller.services.hubstaff_api import create_hubstaff_api_service
        
        # Check if user has access token
        if not user.hubstaff_access_token:
            return "❌ **No Access Token**\n\nYou need to be connected to Hubstaff first. Use /hubstaff_login to connect."
        
        # Create API service
        api_service = create_hubstaff_api_service(user.hubstaff_access_token)
        
        # Test permissions
        permissions = api_service.test_permissions()
        
        # Build debug report
        report = "🔍 **Hubstaff Permissions Debug Report**\n\n"
        
        # Organizations
        if permissions['organizations']:
            report += f"✅ **Organizations:** Access granted ({permissions['organizations_count']} orgs)\n"
        else:
            report += f"❌ **Organizations:** {permissions.get('organizations_error', 'Unknown error')}\n"
        
        # User info
        if permissions['user_info']:
            user_data = permissions.get('user_data', {})
            report += f"✅ **User Info:** Access granted (User: {user_data.get('name', 'Unknown')})\n"
        else:
            report += f"❌ **User Info:** {permissions.get('user_info_error', 'Unknown error')}\n"
        
        # Activities
        if permissions['activities']:
            report += f"✅ **Activities:** Access granted ({permissions['activities_count']} activities)\n"
        else:
            report += f"❌ **Activities:** {permissions.get('activities_error', 'Unknown error')}\n"
        
        report += "\n**Token Info:**\n"
        report += f"• Token length: {len(user.hubstaff_access_token)} characters\n"
        report += f"• Token starts with: {user.hubstaff_access_token[:10]}...\n"
        
        return report
        
    except Exception as e:
        return f"❌ **Debug Error**\n\nFailed to debug permissions: {str(e)}"


@router.register(
    command="my_activity",
    description="SHOW MY ACTIVITY",
)
async def my_activity(event, session: AsyncSession, user: User) -> str:
    """Show user's own activity for the last day"""
    try:
        # Import the API service
        from bot_controller.services.hubstaff_api import create_hubstaff_api_service, format_activities_summary
        
        # Check if user has access token
        if not user.hubstaff_access_token:
            return "❌ **No Access Token**\n\nYou need to be connected to Hubstaff first. Use /hubstaff_login to connect."
        
        # Debug: Show token information
        print(f"🔑 **Bot Token Debug (My Activity):**")
        print(f"User ID: {user.external_id}")
        print(f"Token length: {len(user.hubstaff_access_token)} characters")
        print(f"Token starts with: {user.hubstaff_access_token[:20]}...")
        print(f"Token ends with: ...{user.hubstaff_access_token[-10:]}")
        print(f"Full token: {user.hubstaff_access_token}")
        print("-" * 50)
        
        # Create API service
        api_service = create_hubstaff_api_service(user.hubstaff_access_token)
        
        # Get organizations
        organizations = api_service.get_organizations()
        
        if not organizations:
            return "❌ **No Organizations Found**\n\nYou don't have access to any organizations in Hubstaff."
        
        # Use the first organization
        organization = organizations[0]
        organization_id = organization['id']
        organization_name = organization.get('name', 'Unknown Organization')
        
        # Get last day activities
        all_activities = api_service.get_last_day_activities(organization_id)

        print(all_activities,88888888)
        # Filter activities for current user only
        user_activities = [activity for activity in all_activities if activity.user_id == user.external_id]
        
        if not user_activities:
            return "📊 **No Personal Activity Found**\n\nYou haven't recorded any activity in the last 24 hours."
        
        # Calculate user totals
        total_duration = sum(activity.duration for activity in user_activities)
        total_hours = total_duration / 3600
        
        # Format response
        response = f"👤 **My Activity - Last 24 Hours**\n\n"
        response += f"🏢 **Organization:** {organization_name}\n"
        response += f"⏰ **Total Time Tracked:** {total_hours:.1f} hours\n"
        response += f"📝 **Total Activities:** {len(user_activities)}\n\n"
        
        response += "**Recent Activities:**\n"
        
        # Show recent activities sorted by time
        recent_activities = sorted(user_activities, key=lambda x: x.start_time, reverse=True)[:10]
        
        for activity in recent_activities:
            start_time_str = activity.start_time.strftime('%H:%M')
            duration_hours = activity.duration / 3600
            
            project_info = ""
            if activity.project_name:
                project_info = f" ({activity.project_name})"
            
            response += f"• 🕐 **{start_time_str}**{project_info}: {duration_hours:.1f}h\n"
            
            if activity.note:
                response += f"  📝 Note: {activity.note}\n"
        
        
     
        
        return response
        
    except Exception as e:
        return f"❌ **Error Loading Activity**\n\nFailed to load your activity data: {str(e)}\n\nPlease try again or contact support if the issue persists."


@router.register(
    command="hubstaff_logout",
    description="HUBSTAFF LOGOUT",
)
async def hubstaff_logout(event, session: AsyncSession, user: User) -> tuple[str, types.InlineKeyboardMarkup]:
    """Logout from Hubstaff and clear all tokens"""
    
    # Check if user has tokens to logout from
    has_tokens = bool(user.hubstaff_access_token or user.hubstaff_refresh_token)
    
    if not has_tokens:
        return (
            "❌ **No Active Connection**\n\n"
            "You are not currently connected to Hubstaff.\n"
            "Use /hubstaff_login to connect your account first.",
            None
        )
    
    # Create confirmation keyboard
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(
            text="✅ Yes, Logout",
            callback_data=f"logout_confirm_{user.external_id}"
        )
    )
    builder.add(
        types.InlineKeyboardButton(
            text="❌ Cancel",
            callback_data=f"logout_cancel_{user.external_id}"
        )
    )
    
    message = (
        "🔐 **Hubstaff Logout**\n\n"
        "Are you sure you want to logout from Hubstaff?\n\n"
        "**This will:**\n"
        "• 🗑️ Clear all your access tokens\n"
        "• 🔒 Remove your connection\n"
        "• 📊 Stop access to your data\n"
        "• 🔔 Disable notifications\n\n"
        "**Note:** You can always reconnect later using /hubstaff_login"
    )
    
    return message, builder.as_markup()


@router.register()
async def handle_logout_callback(callback: types.CallbackQuery, session: AsyncSession, user: User) -> str | tuple[str, types.InlineKeyboardMarkup]:
    """Handle logout confirmation callbacks"""
    if not callback.data:
        await callback.answer("Invalid callback data")
        return "❌ Invalid request"
    
    # Parse callback data: logout_confirm_123456789 or logout_cancel_123456789
    parts = callback.data.split('_')
    if len(parts) != 3:
        await callback.answer("Invalid callback format")
        return "❌ Invalid request format"
    
    action, confirm_type, user_id = parts
    
    if action == "logout" and confirm_type == "confirm":
        # User confirmed logout - clear all tokens
        user.hubstaff_access_token = None
        user.hubstaff_refresh_token = None
        user.hubstaff_id_token = None
        user.hubstaff_token_expires_at = None
        user.is_admin = False  # Reset admin status on logout
        
        await session.commit()
        await callback.answer("✅ Logged out successfully!")
        
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        
        builder = InlineKeyboardBuilder()
        builder.add(
            types.InlineKeyboardButton(
                text="🔗 Reconnect to Hubstaff",
                callback_data="hubstaff_reconnect"
            )
        )
        
        return (
            "✅ **Logout Successful!**\n\n"
            "You have been successfully logged out from Hubstaff.\n\n"
            "**What happened:**\n"
            "• 🗑️ All access tokens cleared\n"
            "• 🔒 Connection removed\n"
            "• 🔐 Admin privileges reset\n"
            "• 📊 Data access disabled\n\n"
            "**To reconnect:**\n"
            "Click the button below to connect your account again.",
            builder.as_markup()
        )
    
    elif action == "logout" and confirm_type == "cancel":
        # User cancelled logout
        await callback.answer("❌ Logout cancelled")
        return (
            "❌ **Logout Cancelled**\n\n"
            "Your Hubstaff connection remains active.\n"
            "You can continue using all Hubstaff features."
        )
    
    await callback.answer("Unknown logout action")
    return "❌ Unknown logout action"


@router.register()
async def handle_admin_menu(callback: types.CallbackQuery, session: AsyncSession, user: User) -> str:
    """Handle admin menu options"""
    if not callback.data:
        await callback.answer("Invalid callback data")
        return "❌ Invalid request"
    
    # Parse callback data: admin_select_members_123456789
    parts = callback.data.split('_')
    if len(parts) != 4:
        await callback.answer("Invalid callback format")
        return "❌ Invalid request format"
    
    action, menu_type, option, user_id = parts
    
    if action == "admin" and menu_type == "select" and option == "members":
        await callback.answer("Loading team members...")
        return (
            "👥 **Select Team Members**\n\n"
            "**Available Members:**\n"
            "• 👤 John Doe (john.doe@company.com)\n"
            "• 👤 Jane Smith (jane.smith@company.com)\n"
            "• 👤 Mike Johnson (mike.j@company.com)\n"
            "• 👤 Sarah Wilson (sarah.w@company.com)\n\n"
            "**Actions:**\n"
            "• ✅ Select all members\n"
            "• 🔍 Search by name/email\n"
            "• 📊 View member activity\n"
            "• ⚙️ Manage permissions\n\n"
            "This feature will be implemented soon!"
        )
    
    elif action == "admin" and menu_type == "show" and option == "activity":
        await callback.answer("Loading activity data...")
        return (
            "📊 **All Team Activity**\n\n"
            "**Today's Activity:**\n"
            "• 🕐 Total hours tracked: 32.5\n"
            "• 👥 Active members: 8/12\n"
            "• 📈 Projects worked on: 5\n"
            "• ⏰ Average session: 2.1 hours\n\n"
            "**Recent Activity:**\n"
            "• John Doe - Started tracking (2 hours ago)\n"
            "• Jane Smith - Stopped tracking (1 hour ago)\n"
            "• Mike Johnson - Updated project (30 min ago)\n\n"
            "**Activity Summary:**\n"
            "• 🟢 Online now: 3 members\n"
            "• 🟡 Away: 2 members\n"
            "• 🔴 Offline: 7 members\n\n"
            "This feature will be implemented soon!"
        )
    
    elif action == "admin" and menu_type == "generate" and option == "csv":
        await callback.answer("Generating CSV report...")
        return (
            "📄 **Generate CSV Report**\n\n"
            "**Report Options:**\n"
            "• 📊 Time tracking data\n"
            "• 👥 Team member activity\n"
            "• 📈 Project reports\n"
            "• 💰 Billing information\n\n"
            "**Date Range:**\n"
            "• 📅 Last 7 days\n"
            "• 📅 Last 30 days\n"
            "• 📅 Custom range\n\n"
            "**Export Format:**\n"
            "• 📄 CSV (Excel compatible)\n"
            "• 📊 JSON (API format)\n"
            "• 📋 PDF (Printable)\n\n"
            "This feature will be implemented soon!"
        )
    
    await callback.answer("Unknown admin action")
    return "❌ Unknown admin action"


@router.register()
async def handle_hubstaff_callback(callback: types.CallbackQuery, session: AsyncSession, user: User) -> str:
    """Handle callback queries from Hubstaff login button"""
    await callback.answer("Redirecting to Hubstaff login...")
    return "Please complete the login process in Hubstaff."


@router.register()
async def handle_hubstaff_reconnect(callback: types.CallbackQuery, session: AsyncSession, user: User) -> tuple[str, types.InlineKeyboardMarkup]:
    """Handle reconnect to Hubstaff button"""
    await callback.answer("Starting Hubstaff reconnection...")
    
    # Reuse the existing hubstaff_login logic
    return await hubstaff_login(callback, session, user)


@router.register()
async def handle_role_selection(callback: types.CallbackQuery, session: AsyncSession, user: User) -> str:
    """Handle role selection after Hubstaff login"""
    import os
    
    if not callback.data:
        await callback.answer("Invalid callback data")
        return "❌ Invalid request"
    
    # Parse callback data: role_user_123456789 or role_admin_123456789
    parts = callback.data.split('_')
    if len(parts) != 3:
        await callback.answer("Invalid callback format")
        return "❌ Invalid request format"
    
    role, action, chat_id = parts
    
    if role == "role" and action == "user":
        # User role selected
        if user.is_admin:
            # Switching from admin to user
            user.is_admin = False
            await session.commit()
            await callback.answer("✅ Switched to User role!")
            return (
                "👤 **Switched to User Role!**\n\n"
                "You are now in user mode. You have access to:\n"
                "• 📊 View your time tracking data\n"
                "• 📈 Check your reports\n"
                "• 🔔 Receive notifications\n"
                "• ⏰ Start/stop time tracking\n\n"
                "Use /help to see all available commands!"
            )
        else:
            # Already user role
            await callback.answer("✅ You're already in User role!")
            return (
                "👤 **User Role (Already Active)**\n\n"
                "You are already in user mode. You have access to:\n"
                "• 📊 View your time tracking data\n"
                "• 📈 Check your reports\n"
                "• 🔔 Receive notifications\n"
                "• ⏰ Start/stop time tracking\n\n"
                "Use /help to see all available commands!"
            )
    
    elif role == "role" and action == "admin":
        # Admin role selected
        if user.is_admin:
            # Already admin role
            await callback.answer("✅ You're already in Admin role!")
            return (
                "🔐 **Admin Role (Already Active)**\n\n"
                "You are already in admin mode. You have access to:\n"
                "• 👥 Manage team members\n"
                "• 📊 View all team reports\n"
                "• ⚙️ Configure bot settings\n"
                "• 🔧 System administration\n"
                "• 📈 Advanced analytics\n"
                "• 🛡️ Security controls\n\n"
                "Use /view to access admin menu!"
            )
        else:
            # Switching to admin - check password
            admin_password = ADMIN_PASSWORD
            
            # Create password input keyboard
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            
            builder = InlineKeyboardBuilder()
            builder.add(
                types.InlineKeyboardButton(
                    text="🔙 Back to Role Selection",
                    callback_data=f"role_back_{chat_id}"
                )
            )
            
            await callback.answer("Please enter admin password")
            return (
                "🔐 **Admin Access Required**\n\n"
                "Please enter the admin password to continue.\n\n"
                "Send the password as a message to this bot.",
                builder.as_markup()
            )
    
    elif role == "role" and action == "back":
        # Back to role selection
        await callback.answer("Returning to role selection")
        return await handle_role_selection_initial(callback, session, user)
    
    await callback.answer("Unknown role selection")
    return "❌ Unknown role selection"


@router.register()
async def handle_admin_password(event, session: AsyncSession, user: User) -> tuple[str, types.ReplyKeyboardMarkup]:
    """Handle admin password verification"""
    import os
    
    if isinstance(event, types.Message):
        password = event.text
    else:
        await event.answer("Please send the password as a text message")
        return "❌ Invalid input"
    
    admin_password = ADMIN_PASSWORD
    
    if password == admin_password:
        # Password correct - grant admin access
        user.is_admin = True  # Assuming you have this field in User model
        await session.commit()
        
        # Create admin menu with Reply Keyboard
        from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="👥 Select Members"), KeyboardButton(text="📊 Show All Activity")],
                [KeyboardButton(text="📄 Generate CSV"), KeyboardButton(text="🔙 Back to User Menu")],
                [KeyboardButton(text="🔐 Logout from Hubstaff")]
            ],
            resize_keyboard=True,
            one_time_keyboard=False,
            input_field_placeholder="Select admin action..."
        )
        
        return (
            "✅ **Authorization passed**\n\n"
            "🔓 **Admin Access Granted!**\n\n"
            "Welcome, Administrator! You now have access to:\n"
            "• 👥 Manage team members\n"
            "• 📊 View all team reports\n"
            "• ⚙️ Configure bot settings\n"
            "• 🔧 System administration\n"
            "• 📈 Advanced analytics\n"
            "• 🛡️ Security controls\n\n"
            "**Use the keyboard below to navigate:**",
            keyboard
        )
    else:
        return (
            "❌ **Access Denied**\n\n"
            "Incorrect password. Please try again or contact the system administrator."
        )


async def handle_role_selection_initial(callback: types.CallbackQuery, session: AsyncSession, user: User) -> tuple[str, types.InlineKeyboardMarkup]:
    """Show initial role selection menu with active role indication"""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    # Determine current role status
    if user.is_admin:
        current_role = "🔐 Admin"
        role_status = "🟢 **Currently Active: Admin**"
    else:
        current_role = "👤 User"
        role_status = "🟢 **Currently Active: User**"
    
    # Check if user has any Hubstaff connection
    has_connection = bool(user.hubstaff_access_token or user.hubstaff_refresh_token)
    
    if has_connection:
        message = (
            f"🔄 **Change Role**\n\n"
            f"{role_status}\n\n"
            "Select a new role or keep your current one:"
        )
    else:
        message = (
            "✅ **Role Selection**\n\n"
            "🟢 **No role set yet**\n\n"
            "Please select your role:"
        )
    
    builder = InlineKeyboardBuilder()
    
    # Add role buttons with visual indicators
    if user.is_admin:
        # Admin is active - show in green
        builder.add(
            types.InlineKeyboardButton(
                text="🟢 🔐 I'm Admin (Active)",
                callback_data=f"role_admin_{callback.from_user.id}"
            )
        )
        builder.add(
            types.InlineKeyboardButton(
                text="⚪ 👤 I'm User",
                callback_data=f"role_user_{callback.from_user.id}"
            )
        )
    else:
        # User is active - show in green
        builder.add(
            types.InlineKeyboardButton(
                text="⚪ 🔐 I'm Admin",
                callback_data=f"role_admin_{callback.from_user.id}"
            )
        )
        builder.add(
            types.InlineKeyboardButton(
                text="🟢 👤 I'm User (Active)",
                callback_data=f"role_user_{callback.from_user.id}"
            )
        )
    
    return message, builder.as_markup()


@router.register()
async def handle_change_role_callback(callback: types.CallbackQuery, session: AsyncSession, user: User) -> tuple[str, types.InlineKeyboardMarkup]:
    """Handle change role callback and show role selection menu again"""
    # Reuse the role selection initial menu
    return await handle_role_selection_initial(callback, session, user)


@router.register()
async def handle_admin_reply_keyboard(event: types.Message, session: AsyncSession, user: User) -> str | tuple[str, types.ReplyKeyboardMarkup | types.ReplyKeyboardRemove]:
    """Handle admin Reply Keyboard button presses"""
    
    if not user.is_admin:
        return "❌ You don't have admin access."
    
    text = event.text
    
    if text == "👥 Select Members":
        return (
            "👥 **Select Team Members**\n\n"
            "**Available Members:**\n"
            "• 👤 John Doe (john.doe@company.com)\n"
            "• 👤 Jane Smith (jane.smith@company.com)\n"
            "• 👤 Mike Johnson (mike.j@company.com)\n"
            "• 👤 Sarah Wilson (sarah.w@company.com)\n\n"
            "**Actions:**\n"
            "• ✅ Select all members\n"
            "• 🔍 Search by name/email\n"
            "• 📊 View member activity\n"
            "• ⚙️ Manage permissions\n\n"
            "This feature will be implemented soon!"
        )
    
    elif text == "📊 Show All Activity":
        try:
            # Import the API service
            from bot_controller.services.hubstaff_api import create_hubstaff_api_service, format_activities_summary
            
            # Check if user has access token
            if not user.hubstaff_access_token:
                return "❌ **No Access Token**\n\nYou need to be connected to Hubstaff first. Use /hubstaff_login to connect."
            
            # Debug: Show token information
            print(f"🔑 **Bot Token Debug (My Activity):**")
            print(f"User ID: {user.external_id}")
            print(f"Token length: {len(user.hubstaff_access_token)} characters")
            print(f"Token starts with: {user.hubstaff_access_token[:20]}...")
            print(f"Token ends with: ...{user.hubstaff_access_token[-10:]}")
            print(f"Full token: {user.hubstaff_access_token}")
            print("-" * 50)
            
            # Create API service
            api_service = create_hubstaff_api_service(user.hubstaff_access_token)
            
            # Get organizations
            organizations = api_service.get_organizations()
            
            if not organizations:
                return "❌ **No Organizations Found**\n\nYou don't have access to any organizations in Hubstaff."
            
            # Use the first organization
            organization = organizations[0]
            organization_id = organization['id']
            organization_name = organization.get('name', 'Unknown Organization')
            
            # Get last day activities
            activities = api_service.get_last_day_activities(organization_id)
           
            # Format the response
            summary = format_activities_summary(activities)
            
            # Add organization info and debug link
           
            full_response = f"🏢 **Organization:** {organization_name}\n\n{summary}\n\n"
            
            return full_response
            
        except Exception as e:
            return f"❌ **Error Loading Activity**\n\nFailed to load activity data: {str(e)}\n\nPlease try again or contact support if the issue persists."
    
    elif text == "📄 Generate CSV":
        return (
            "📄 **Generate CSV Report**\n\n"
            "**Report Options:**\n"
            "• 📊 Time tracking data\n"
            "• 👥 Team member activity\n"
            "• 📈 Project reports\n"
            "• 💰 Billing information\n\n"
            "**Date Range:**\n"
            "• 📅 Last 7 days\n"
            "• 📅 Last 30 days\n"
            "• 📅 Custom range\n\n"
            "**Export Format:**\n"
            "• 📄 CSV (Excel compatible)\n"
            "• 📊 JSON (API format)\n"
            "• 📋 PDF (Printable)\n\n"
            "This feature will be implemented soon!"
        )
    
    elif text == "🔙 Back to User Menu":
        # Remove admin status and show user menu
        user.is_admin = False
        await session.commit()
        
        from aiogram.types import ReplyKeyboardRemove
        
        return (
            "👤 **Switched to User Mode**\n\n"
            "You are now in user mode. You have access to:\n"
            "• 📊 View your time tracking data\n"
            "• 📈 Check your reports\n"
            "• 🔔 Receive notifications\n"
            "• ⏰ Start/stop time tracking\n\n"
            "Use /help to see all available commands!",
            ReplyKeyboardRemove()
        )
    
    elif text == "🔐 Logout from Hubstaff":
        # Clear all tokens and logout
        user.hubstaff_access_token = None
        user.hubstaff_refresh_token = None
        user.hubstaff_id_token = None
        user.hubstaff_token_expires_at = None
        user.is_admin = False
        
        await session.commit()
        
        # For now, we'll just return the message with ReplyKeyboardRemove
        # The reconnect button will be available through the /hubstaff_login command
        from aiogram.types import ReplyKeyboardRemove
        
        return (
            "✅ **Logout Successful!**\n\n"
            "You have been successfully logged out from Hubstaff.\n\n"
            "**What happened:**\n"
            "• 🗑️ All access tokens cleared\n"
            "• 🔒 Connection removed\n"
            "• 🔐 Admin privileges reset\n"
            "• 📊 Data access disabled\n\n"
            "**To reconnect:**\n"
            "Use /hubstaff_login to connect your account again.",
            ReplyKeyboardRemove()
        )
    
    return "❌ Unknown admin action. Please use the keyboard buttons." 