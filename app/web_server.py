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

def set_bot_instance(bot):
    """Set the bot instance for otifications"""
    global bot_instance
    bot_instance = bot

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
            text="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hubstaff Login Success</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 40px;
            text-align: center;
            max-width: 500px;
            margin: 20px;
            animation: slideIn 0.6s ease-out;
        }
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        .success-icon {
            font-size: 80px;
            margin-bottom: 20px;
            animation: bounce 2s infinite;
        }
        @keyframes bounce {
            0%, 20%, 50%, 80%, 100% {
                transform: translateY(0);
            }
            40% {
                transform: translateY(-10px);
            }
            60% {
                transform: translateY(-5px);
            }
        }
        h1 {
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 28px;
            font-weight: 600;
        }
        .message {
            color: #7f8c8d;
            font-size: 16px;
            line-height: 1.6;
            margin-bottom: 25px;
        }
        .telegram-button {
            background: linear-gradient(45deg, #0088cc, #00a8ff);
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 50px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            transition: all 0.3s ease;
            box-shadow: 0 5px 15px rgba(0,136,204,0.3);
        }
        .telegram-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,136,204,0.4);
        }
        .features {
            margin-top: 30px;
            padding-top: 25px;
            border-top: 1px solid #ecf0f1;
        }
        .feature {
            display: inline-block;
            margin: 10px;
            padding: 8px 16px;
            background: #f8f9fa;
            border-radius: 20px;
            color: #495057;
            font-size: 14px;
            font-weight: 500;
        }
        .confetti {
            position: fixed;
            width: 10px;
            height: 10px;
            background: #f39c12;
            animation: confetti-fall 3s linear infinite;
        }
        @keyframes confetti-fall {
            to {
                transform: translateY(100vh) rotate(360deg);
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="success-icon">🎉</div>
        <h1>🎊 Login Successful! 🎊</h1>
        <div class="message">
            <strong>Congratulations!</strong> Your Hubstaff account has been successfully connected to your Telegram bot.
            <br><br>
            You can now enjoy seamless integration between Hubstaff and Telegram!
        </div>
        <a href="https://t.me/hubstaff_insiders_bot" class="telegram-button">
            🚀 Return to Telegram Bot
        </a>
        <div class="features">
            <span class="feature">📊 Time Tracking</span>
            <span class="feature">📈 Reports</span>
            <span class="feature">👥 Team Management</span>
            <span class="feature">🔔 Notifications</span>
        </div>
    </div>
    
    <script>
        // Add confetti effect
        function createConfetti() {
            const colors = ['#f39c12', '#e74c3c', '#3498db', '#2ecc71', '#9b59b6'];
            for (let i = 0; i < 50; i++) {
                const confetti = document.createElement('div');
                confetti.className = 'confetti';
                confetti.style.left = Math.random() * 100 + 'vw';
                confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
                confetti.style.animationDelay = Math.random() * 3 + 's';
                confetti.style.animationDuration = (Math.random() * 3 + 2) + 's';
                document.body.appendChild(confetti);
                
                setTimeout(() => {
                    confetti.remove();
                }, 5000);
            }
        }
        
        // Trigger confetti on page load
        window.addEventListener('load', createConfetti);
        
        // Auto-close after 10 seconds
        setTimeout(() => {
            window.close();
        }, 10000);
    </script>
</body>
</html>
            """,
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
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            from aiogram import types
            
            message = (
                "✅ Hubstaff login successful!\n\n"
                "Your account has been connected to Hubstaff. "
                "You can now use Hubstaff features in this bot.\n\n"
                "Please select your role:"
            )
            
            # Create inline keyboard with two options
            builder = InlineKeyboardBuilder()
            builder.add(
                types.InlineKeyboardButton(
                    text="👤 I'm User",
                    callback_data=f"role_user_{chat_id}"
                )
            )
            builder.add(
                types.InlineKeyboardButton(
                    text="🔐 I'm Admin",
                    callback_data=f"role_admin_{chat_id}"
                )
            )
            
            await bot_instance.send_message(
                int(chat_id), 
                message, 
                reply_markup=builder.as_markup()
            )
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
