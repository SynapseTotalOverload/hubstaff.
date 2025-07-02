from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from bot_controller.router import Router
from models import User
from settings import HUBSTAFF_CLIENT_ID, HUBSTAFF_REDIRECT_URI
from bot_controller.services.hubstaff_oauth import hubstaff_oauth


router = Router(name=__name__)


@router.register(
    command="hubstaff_login",
    description="get Hubstaff login button",
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
    
    # Build Hubstaff OAuth URL with proper parameters including state
    auth_params = {
        "client_id": HUBSTAFF_CLIENT_ID,
        "redirect_uri": HUBSTAFF_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid read write",
        "state": str(chat_id)  # Use chat_id as state for security
    }
    
    # Generate auth URL using OIDC discovery
    hubstaff_login_url = hubstaff_oauth.get_auth_url(
        client_id=HUBSTAFF_CLIENT_ID,
        redirect_uri=HUBSTAFF_REDIRECT_URI,
        scope="openid read write"
    )
    
    # Add state parameter to the URL
    from urllib.parse import urlencode
    hubstaff_login_url = f"{hubstaff_login_url}&{urlencode({'state': str(chat_id)})}"
    
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