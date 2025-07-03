from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from bot_controller.router import Router
from bot_controller import services
from bot_controller.services.hubstaff import hubstaff_login, hubstaff_status, hubstaff_logout, my_activity, debug_permissions, handle_logout_callback, handle_role_selection, handle_admin_menu, handle_change_role_callback, handle_admin_password, handle_admin_reply_keyboard
from models import User


router = Router(name=__name__)



@router.register(
    command="help",
    description="VIEW ALL COMMANDS",
)
async def help_command(event, *_) -> tuple[str, types.InlineKeyboardMarkup]:
    """Display all available commands as buttons"""
    # Collect commands from all routers
    all_commands = []
    all_commands.extend(router.command_list)
    all_commands.extend(services.hubstaff_router.command_list)
    
    # Build inline keyboard with command buttons
    builder = InlineKeyboardBuilder()
    
    for command_info in all_commands:
        # Parse command and description from "command - description" format
        if " - " in command_info:
            command, description = command_info.split(" - ", 1)
            # Show only the description
            button_text = description
        else:
            command = command_info
            button_text = command_info.replace("/", "")
        
        # Create callback data for the button
        callback_data = f"cmd_{command.replace('/', '')}"
        
        builder.add(
            types.InlineKeyboardButton(
                text=button_text,
                callback_data=callback_data
            )
        )
    
    # Arrange buttons in a single column for better readability
    builder.adjust(1)
    
    message_text = "View all commands:"
    
    return message_text, builder.as_markup()




@router.register(
    command="user_info",
    description="TELEGRAM USER INFO",
)
async def user_info(event, session: AsyncSession, user: User) -> str:  # noqa; pylint: disable=unused-argument
    # Handle both Message and CallbackQuery
    if isinstance(event, types.Message):
        chat_id = event.chat.id
    elif isinstance(event, types.CallbackQuery):
        chat_id = event.message.chat.id if event.message else "N/A"
    else:
        chat_id = "Unknown"
    
    return f"User ID: {user.external_id}\nChat ID: {chat_id}\nRegistration date: {user.created_at}"


@router.register()
async def handle_command_callback(callback: types.CallbackQuery, session: AsyncSession, user: User) -> str:
    """Handle callback queries from help command buttons - execute the actual command"""
    if callback.data and callback.data.startswith("cmd_"):
        command_name = callback.data.replace("cmd_", "")
        await callback.answer(f"Executing: /{command_name}")
        
        # Execute the actual command based on the command name
        if command_name == "help":
            return await help_command(callback, session, user)
       
        elif command_name == "user_info":
            return await user_info(callback, session, user)
        elif command_name == "hubstaff_login":
            return await hubstaff_login(callback, session, user)
        elif command_name == "hubstaff_status":
            return await hubstaff_status(callback, session, user)
        elif command_name == "hubstaff_logout":
            return await hubstaff_logout(callback, session, user)
        elif command_name == "my_activity":
            return await my_activity(callback, session, user)
        elif command_name == "debug_permissions":
            return await debug_permissions(callback, session, user)
        elif command_name == "view":
            return await view_menu(callback, session, user)
        else:
            return f"❌ Command /{command_name} not found or not implemented for button execution."
    
    # Handle logout callbacks
    elif callback.data and callback.data.startswith("logout_"):
        return await handle_logout_callback(callback, session, user)
    
    # Handle role selection callbacks
    elif callback.data and callback.data.startswith("role_"):
        return await handle_role_selection(callback, session, user)
    
    # Handle change role callbacks
    elif callback.data and callback.data.startswith("change_role_"):
        result = await handle_change_role_callback(callback, session, user)
        if isinstance(result, tuple):
            message, markup = result
            return message, markup
        return result
    
    # Handle admin menu callbacks
    elif callback.data and callback.data.startswith("admin_"):
        return await handle_admin_menu(callback, session, user)
    
    # Handle view menu callbacks
    elif callback.data and callback.data.startswith("show_"):
        result = await handle_view_menu_callback(callback, session, user)
        if isinstance(result, tuple):
            message, markup = result
            return message, markup
        return result
    
    await callback.answer("Unknown command")
    return "❌ Unknown command"


@router.register()
async def echo(message: types.Message, session: AsyncSession, user: User) -> str:
    """Handle text messages - check if it's admin password input or Reply Keyboard button"""
    text = message.text
    
    # Check if user is admin and this might be a Reply Keyboard button
    if user.is_admin:
        # Check if it's one of the admin Reply Keyboard buttons
        admin_buttons = ["👥 Select Members", "📊 Show All Activity", "📄 Generate CSV", "🔙 Back to User Menu", "🔐 Logout from Hubstaff"]
        if text in admin_buttons:
            result = await handle_admin_reply_keyboard(message, session, user)
            if isinstance(result, tuple):
                message_text, markup = result
                return message_text, markup
            return result
    
    # Check if this is a user keyboard button
    user_buttons = ["📊 My Activity", "🔙 Back to Main Menu"]
    if text in user_buttons:
        if text == "📊 My Activity":
            return await my_activity(message, session, user)
        elif text == "🔙 Back to Main Menu":
            from aiogram.types import ReplyKeyboardRemove
            return (
                "👤 **Back to Main Menu**\n\n"
                "You're back to the main menu. Use /help to see all available commands!",
                ReplyKeyboardRemove()
            )
    
    # Check if this might be an admin password input
    # Only check if user has Hubstaff tokens AND is not currently admin (meaning they're trying to become admin)
    if (user.hubstaff_access_token or user.hubstaff_refresh_token) and not user.is_admin:
        # This could be an admin password - try to process it
        result = await handle_admin_password(message, session, user)
        if isinstance(result, tuple):
            message_text, markup = result
            return message_text, markup
        return result
    
    # If not a password input or keyboard button, ignore the message
    return None


@router.register(
    command="view",
    description="VIEW MENU",
)
async def view_menu(event, session: AsyncSession, user: User) -> tuple[str, types.InlineKeyboardMarkup]:
    """Display menu based on user role"""
    
    # Build inline keyboard with role-specific buttons
    builder = InlineKeyboardBuilder()
    
    if user.is_admin:
        # Admin menu
        builder.add(
            types.InlineKeyboardButton(
                text="🔓 Show Admin Menu",
                callback_data=f"show_admin_menu_{user.external_id}"
            )
        )
        message_text = "🔓 **Admin Menu**\n\nYou have admin privileges. Select an option below:"
    else:
        # User menu
        builder.add(
            types.InlineKeyboardButton(
                text="👤 Show User Menu",
                callback_data=f"show_user_menu_{user.external_id}"
            )
        )
        message_text = "👤 **User Menu**\n\nYou are in user mode. Select an option below:"
    
    # Add common buttons for both roles
    builder.add(
        types.InlineKeyboardButton(
            text="🔄 Change Role",
            callback_data=f"change_role_{user.external_id}"
        )
    )
    
    # Arrange buttons in a single column
    builder.adjust(1)
    
    return message_text, builder.as_markup()


@router.register()
async def handle_view_menu_callback(callback: types.CallbackQuery, session: AsyncSession, user: User) -> str:
    """Handle view menu callback queries"""
    if not callback.data:
        await callback.answer("Invalid callback data")
        return "❌ Invalid request"
    
    # Parse callback data: show_admin_menu_123456789 or show_user_menu_123456789
    parts = callback.data.split('_')
    if len(parts) != 4:
        await callback.answer("Invalid callback format")
        return "❌ Invalid request format"
    
    action, menu_type, role, user_id = parts
    
    if action == "show" and menu_type == "admin" and role == "menu":
        # Show admin menu
        await callback.answer("Loading admin menu...")
        
        # Create admin Reply Keyboard
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
            "🔓 **Admin Menu Activated!**\n\n"
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
    
    elif action == "show" and menu_type == "user" and role == "menu":
        # Show user menu
        await callback.answer("Loading user menu...")
        
        # Check if user has Hubstaff connection
        has_connection = bool(user.hubstaff_access_token or user.hubstaff_refresh_token)
        
        if has_connection:
            # Create user Reply Keyboard with activity button
            from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
            
            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="📊 My Activity")],
                    [KeyboardButton(text="🔙 Back to Main Menu")]
                ],
                resize_keyboard=True,
                one_time_keyboard=False,
                input_field_placeholder="Select user action..."
            )
            
            return (
                "👤 **User Menu Activated!**\n\n"
                "Welcome! You have access to:\n"
                "• 📊 View your time tracking data\n"
                "• 📈 Check your reports\n"
                "• 🔔 Receive notifications\n"
                "• ⏰ Start/stop time tracking\n\n"
                "**Use the keyboard below to navigate:**",
                keyboard
            )
        else:
            # Remove any existing keyboard and show user options
            from aiogram.types import ReplyKeyboardRemove
            
            return (
                "👤 **User Menu**\n\n"
                "Welcome! You have access to:\n"
                "• 📊 View your time tracking data\n"
                "• 📈 Check your reports\n"
                "• 🔔 Receive notifications\n"
                "• ⏰ Start/stop time tracking\n"
                "• 🔄 Change your role (if you have admin credentials)\n\n"
                "**Available Commands:**\n"
                "• /hubstaff_status - Check your connection status\n"
                "• /hubstaff_login - Connect to Hubstaff\n"
                "• /help - View all commands\n\n"
                "Use /help to see all available commands!",
                ReplyKeyboardRemove()
            )
    
    await callback.answer("Unknown menu action")
    return "❌ Unknown menu action"
