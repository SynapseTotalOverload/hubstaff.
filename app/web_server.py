import asyncio
import logging
from aiohttp import web, ClientSession
from urllib.parse import parse_qs
import json

from bot_controller.services.hubstaff_oauth import hubstaff_oauth
from settings import HUBSTAFF_CLIENT_ID, HUBSTAFF_CLIENT_SECRET, HUBSTAFF_REDIRECT_URI
from models import async_session, User
from sqlalchemy import select

# Global bot instance reference (will be set from main.py)
bot_instance = None

async def handle_callback(request):
    """Handle Hubstaff OAuth callback"""
    try:
        # Get query parameters
        query_string = request.query_string
        params = parse_qs(query_string)
        
        code = params.get('code', [None])[0]
        state = params.get('state', [None])[0]  # Telegram chat ID
        
        if not code or not state:
            return web.Response(text="Missing code or state parameter", status=400)
        
        # Exchange code for tokens
        token_data = await exchange_code_for_tokens(code)
        
        if not token_data:
            return web.Response(text="Failed to exchange code for tokens", status=400)
        
        # Save tokens to database
        await save_tokens_to_db(state, token_data)
        
        # Notify user via Telegram
        await notify_user_via_telegram(state, token_data)
        
        return web.Response(
            text="Login successful! You can return to Telegram.",
            content_type='text/html'
        )
        
    except Exception as e:
        logging.error(f"Error in callback handler: {e}")
        return web.Response(text="Internal server error", status=500)

async def exchange_code_for_tokens(code: str) -> dict:
    """Exchange authorization code for access tokens"""
    try:
        oidc_config = hubstaff_oauth.get_oidc_config()
        
        async with ClientSession() as session:
            data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": HUBSTAFF_REDIRECT_URI,
                "client_id": HUBSTAFF_CLIENT_ID,
                "client_secret": HUBSTAFF_CLIENT_SECRET
            }
            
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            
            async with session.post(oidc_config.token_endpoint, data=data, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logging.error(f"Token exchange failed: {response.status} - {error_text}")
                    return None
                    
    except Exception as e:
        logging.error(f"Error exchanging code for tokens: {e}")
        return None

async def save_tokens_to_db(chat_id: str, token_data: dict):
    """Save access and refresh tokens to database"""
    try:
        async with async_session() as session:
            # Find user by external_id (chat_id)
            stmt = select(User).where(User.external_id == int(chat_id))
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if user:
                # Save tokens (you might want to encrypt these in production)
                user.hubstaff_access_token = token_data.get("access_token")
                user.hubstaff_refresh_token = token_data.get("refresh_token")
                user.hubstaff_id_token = token_data.get("id_token")
                user.hubstaff_token_expires_at = token_data.get("expires_in")
                
                await session.commit()
                logging.info(f"Saved tokens for user {chat_id}")
            else:
                logging.error(f"User not found for chat_id: {chat_id}")
                
    except Exception as e:
        logging.error(f"Error saving tokens to database: {e}")

async def notify_user_via_telegram(chat_id: str, token_data: dict):
    """Notify user via Telegram about successful login"""
    try:
        if bot_instance:
            message = (
                "✅ Hubstaff login successful!\n\n"
                "Your account has been connected to Hubstaff. "
                "You can now use Hubstaff features in this bot."
            )
            await bot_instance.send_message(int(chat_id), message)
        else:
            logging.warning("Bot instance not available for notification")
            
    except Exception as e:
        logging.error(f"Error notifying user via Telegram: {e}")

def create_web_app():
    """Create and configure the web application"""
    app = web.Application()
    app.router.add_get('/callback', handle_callback)
    return app

async def start_web_server(host='0.0.0.0', port=8080):
    """Start the web server"""
    app = create_web_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    logging.info(f"Web server started on {host}:{port}")
    return runner 