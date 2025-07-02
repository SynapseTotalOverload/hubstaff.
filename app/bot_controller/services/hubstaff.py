from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

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
        scope="openid",
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
    """Check if user is connected to Hubstaff"""
    
    # Check if user has Hubstaff tokens
    has_access_token = bool(user.hubstaff_access_token)
    has_refresh_token = bool(user.hubstaff_refresh_token)
    has_id_token = bool(user.hubstaff_id_token)
    
    if has_access_token and has_refresh_token:
        # User is connected to Hubstaff
        status_emoji = "✅"
        status_text = "Connected"
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
async def handle_logout_callback(callback: types.CallbackQuery, session: AsyncSession, user: User) -> str:
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
        
        return (
            "✅ **Logout Successful!**\n\n"
            "You have been successfully logged out from Hubstaff.\n\n"
            "**What happened:**\n"
            "• 🗑️ All access tokens cleared\n"
            "• 🔒 Connection removed\n"
            "• 🔐 Admin privileges reset\n"
            "• 📊 Data access disabled\n\n"
            "**To reconnect:**\n"
            "Use /hubstaff_login to connect your account again."
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
        await callback.answer("✅ User role confirmed!")
        return (
            "👤 **User Role Confirmed!**\n\n"
            "Welcome! You now have access to:\n"
            "• 📊 View your time tracking data\n"
            "• 📈 Check your reports\n"
            "• 🔔 Receive notifications\n"
            "• ⏰ Start/stop time tracking\n\n"
            "Use /help to see all available commands!"
        )
    
    elif role == "role" and action == "admin":
        # Admin role selected - check password
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
async def handle_admin_password(event, session: AsyncSession, user: User) -> str:
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
        
        # Create admin menu with inline buttons
        builder = InlineKeyboardBuilder()
        builder.add(
            types.InlineKeyboardButton(
                text="👥 Select Members",
                callback_data=f"admin_select_members_{user.external_id}"
            )
        )
        builder.add(
            types.InlineKeyboardButton(
                text="📊 Show All Activity",
                callback_data=f"admin_show_activity_{user.external_id}"
            )
        )
        builder.add(
            types.InlineKeyboardButton(
                text="📄 Generate CSV",
                callback_data=f"admin_generate_csv_{user.external_id}"
            )
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
            "**Select an option below:**",
            builder.as_markup()
        )
    else:
        return (
            "❌ **Access Denied**\n\n"
            "Incorrect password. Please try again or contact the system administrator."
        )


async def handle_role_selection_initial(callback: types.CallbackQuery, session: AsyncSession, user: User) -> tuple[str, types.InlineKeyboardMarkup]:
    """Show initial role selection menu"""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    message = (
        "✅ Hubstaff login successful!\n\n"
        "Your account has been connected to Hubstaff. "
        "You can now use Hubstaff features in this bot.\n\n"
        "Please select your role:"
    )
    
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(
            text="👤 I'm User",
            callback_data=f"role_user_{callback.from_user.id}"
        )
    )
    builder.add(
        types.InlineKeyboardButton(
            text="🔐 I'm Admin",
            callback_data=f"role_admin_{callback.from_user.id}"
        )
    )
    
    return message, builder.as_markup()


@router.register()
async def handle_change_role_callback(callback: types.CallbackQuery, session: AsyncSession, user: User) -> str:
    """Handle change role callback and show role selection menu again"""
    # Reuse the role selection initial menu
    from bot_controller.services.hubstaff import handle_role_selection_initial
    return await handle_role_selection_initial(callback, session, user) 