from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from bot_controller.router import Router
from bot_controller import services
from bot_controller.services.hubstaff import hubstaff_login, hubstaff_status, hubstaff_logout, handle_logout_callback, handle_role_selection, handle_admin_menu
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
        return await handle_role_selection(callback, session, user)
    
    # Handle admin menu callbacks
    elif callback.data and callback.data.startswith("admin_"):
        return await handle_admin_menu(callback, session, user)
    
    await callback.answer("Unknown command")
    return "❌ Unknown command"


@router.register()
async def echo(message: types.Message, session: AsyncSession, user: User) -> str:
    """Handle text messages - check if it's admin password input"""
    # Check if this might be an admin password input
    # We'll assume any text message from a user who has Hubstaff tokens might be a password
    if user.hubstaff_access_token or user.hubstaff_refresh_token:
        # This could be an admin password - try to process it
        from bot_controller.services.hubstaff import handle_admin_password
        return await handle_admin_password(message, session, user)
    
    # If not a password input, just echo the message
    return message.text
