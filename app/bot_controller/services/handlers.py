from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from bot_controller.router import Router
from bot_controller import services
from models import User


router = Router(name=__name__)


@router.register(
    command="start",
    description="base command for user registration",
)
async def send_welcome(event, *_) -> str:
    return "Welcome! Use /help to see all available commands."


@router.register(
    command="help",
    description="view all commands",
)
async def help_command(*_) -> tuple[str, types.InlineKeyboardMarkup]:
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
            button_text = f"{command} - {description}"
        else:
            command = command_info
            button_text = command_info
        
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
    
    message_text = "🤖 Available Commands:\n\nClick on any command below to see more information:"
    
    return message_text, builder.as_markup()


@router.register(
    command="hello",
    description="just hello command",
)
async def hello(*_) -> str:
    return "Well, hello!"




@router.register(
    command="user_info",
    description="user info",
)
async def user_info(message: types.Message, session: AsyncSession, user: User) -> str:  # noqa; pylint: disable=unused-argument
    return f"User ID: {user.external_id}\nChat ID: {message.chat.id}\nRegistration date: {user.created_at}"


@router.register()
async def handle_command_callback(callback: types.CallbackQuery, session: AsyncSession, user: User) -> str:
    """Handle callback queries from help command buttons - execute the actual command"""
    if callback.data and callback.data.startswith("cmd_"):
        command_name = callback.data.replace("cmd_", "")
        await callback.answer(f"Executing: /{command_name}")
        
        # Execute the actual command based on the command name
        if command_name == "start":
            return await send_welcome(callback, session, user)
        elif command_name == "help":
            return await help_command(callback, session, user)
        elif command_name == "hello":
            return await hello(callback, session, user)
        elif command_name == "user_info":
            return await user_info(callback, session, user)
        elif command_name == "hubstaff_login":
            return await hubstaff_login(callback, session, user)
        else:
            return f"❌ Command /{command_name} not found or not implemented for button execution."
    
    await callback.answer("Unknown command")
    return "❌ Unknown command"


@router.register()
async def echo(message: types.Message, *_) -> str:
    return message.text
