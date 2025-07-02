# Hubstaff Service Setup

This service adds Hubstaff login functionality to your Telegram bot.

## Features

- `/hubstaff_login` command that provides a button to login to Hubstaff
- OAuth 2.0 integration with Hubstaff API
- Inline keyboard button for easy access

## Configuration

1. **Get Hubstaff API Credentials:**
   - Go to [Hubstaff Developer Portal](https://developer.hubstaff.com/)
   - Create a new application
   - Note down your `client_id` and `client_secret`

2. **Set Environment Variables:**
   Create a `.env` file in the root directory with the following variables:
   ```bash
   # Telegram Bot Configuration
   TELEGRAM_API_KEY=your_telegram_bot_token_here
   
   # Hubstaff Configuration
   HUBSTAFF_CLIENT_ID=your_hubstaff_client_id_here
   HUBSTAFF_REDIRECT_URI=your_hubstaff_redirect_uri_here
   HUBSTAFF_AUTH_URL=https://app.hubstaff.com/oauth/authorize
   ```
   
   **Important:** Replace the placeholder values with your actual credentials.

3. **Set Redirect URI:**
   - The redirect URI should point to your application's callback endpoint
   - Example: `https://yourdomain.com/hubstaff/callback`

## Usage

Users can now use the `/hubstaff_login` command to get a login button that will redirect them to Hubstaff's authorization page.

## OAuth Flow

1. User sends `/hubstaff_login` command
2. Bot responds with a button containing the OAuth URL
3. User clicks the button and is redirected to Hubstaff
4. User authorizes the application
5. Hubstaff redirects back to your redirect URI with an authorization code
6. Your application can exchange the code for an access token

## Next Steps

To complete the OAuth flow, you'll need to:
1. Create a callback endpoint to handle the authorization code
2. Exchange the code for an access token
3. Store the access token securely
4. Use the token to make API calls to Hubstaff

## Security Notes

- Never expose your `client_secret` in client-side code
- Store access tokens securely
- Implement proper token refresh logic
- Use HTTPS for all OAuth endpoints 