from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from urllib.parse import urlencode

from bot_controller.router import Router
from models import User
from settings import HUBSTAFF_CLIENT_ID, HUBSTAFF_REDIRECT_URI, HUBSTAFF_AUTH_URL


router = Router(name=__name__)


@router.register(
    command="hubstaff_login",
    description="get Hubstaff login button",
)
async def hubstaff_login(message: types.Message, session: AsyncSession, user: User) -> tuple[str, types.InlineKeyboardMarkup]:
    """Handle /hubstaff_login command and return a button with Hubstaff login URL"""
    
    # Build Hubstaff OAuth URL with proper parameters
    oauth_params = {
        'client_id': HUBSTAFF_CLIENT_ID,
        'redirect_uri': HUBSTAFF_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'read write'  # Adjust scopes as needed for your application
    }
    hubstaff_login_url = f"{HUBSTAFF_AUTH_URL}?{urlencode(oauth_params)}"
    print(hubstaff_login_url)
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


@router.register()
async def handle_hubstaff_callback(callback: types.CallbackQuery, session: AsyncSession, user: User) -> str:
    """Handle callback queries from Hubstaff login button"""
    await callback.answer("Redirecting to Hubstaff login...")
    return "Please complete the login process in Hubstaff." 