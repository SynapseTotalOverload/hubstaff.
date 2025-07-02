from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware, types

import db_helper
from bot_controller.services import logs
from models import async_session


class DbTransactionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[types.TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: types.TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with async_session() as session:
            data["session"] = session
            return await handler(event, data)


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[types.TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: types.TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        session = data["session"]
        
        # Handle Update objects and extract the actual event
        if hasattr(event, 'message') and event.message:
            # Update with message
            actual_event = event.message
        elif hasattr(event, 'callback_query') and event.callback_query:
            # Update with callback query
            actual_event = event.callback_query
        else:
            # Try to handle the event directly if it's not an Update
            actual_event = event
        
        # Handle the actual event
        if isinstance(actual_event, types.Message):
            # Regular message event
            data["user"] = await db_helper.get_or_create_user(session, actual_event)
        elif isinstance(actual_event, types.CallbackQuery):
            # Callback query event
            data["user"] = await db_helper.get_or_create_user_from_id(session, actual_event.from_user.id)
        else:
            # Fallback - try to get user from various event types
            if hasattr(actual_event, 'from_user') and actual_event.from_user:
                data["user"] = await db_helper.get_or_create_user_from_id(session, actual_event.from_user.id)
            else:
                # Debug information
                print(f"Event type: {type(event)}")
                print(f"Actual event type: {type(actual_event)}")
                print(f"Actual event attributes: {dir(actual_event)}")
                print(f"Has from_user: {hasattr(actual_event, 'from_user')}")
                if hasattr(actual_event, 'from_user'):
                    print(f"From user: {actual_event.from_user}")
                
                raise ValueError(f"Cannot determine user from event type: {type(actual_event)}")
        
        return await handler(event, data)


class AutoReplyMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[types.TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: types.TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Handle Update objects and extract the actual event
        if hasattr(event, 'message') and event.message:
            # Update with message
            message = event.message
            logs.log_bot_incomming_message(message)
            result = await handler(event, data)
            logs.log_bot_outgoing_message(message, result)

            if result is not None:
                if isinstance(result, tuple) and len(result) == 2:
                    # Handle tuple response (message_text, keyboard_markup)
                    message_text, keyboard_markup = result
                    await message.reply(text=message_text, reply_markup=keyboard_markup, disable_web_page_preview=False)
                else:
                    # Handle string response
                    await message.reply(text=result, disable_web_page_preview=False)
        elif hasattr(event, 'callback_query') and event.callback_query:
            # Update with callback query
            callback = event.callback_query
            logs.log_bot_incomming_message(callback)
            result = await handler(event, data)
            logs.log_bot_outgoing_message(callback, result)

            if result is not None:
                # For callback queries, we need to answer differently
                if isinstance(result, str):
                    # Send a new message to the chat if message is available
                    if callback.message:
                        await callback.message.answer(text=result, disable_web_page_preview=False)
                    else:
                        # If no message available, try to answer the callback
                        await callback.answer(text=result[:64])  # Telegram limits callback answer to 64 chars
                elif isinstance(result, tuple) and len(result) == 2:
                    # Handle tuple response (message_text, keyboard_markup)
                    message_text, keyboard_markup = result
                    if callback.message:
                        await callback.message.answer(text=message_text, reply_markup=keyboard_markup, disable_web_page_preview=False)
                    else:
                        await callback.answer(text=message_text[:64])
        else:
            # Fallback for other event types
            result = await handler(event, data)
