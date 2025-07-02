import logging

from aiogram import types


def log_bot_incomming_message(event):
    """Log incoming messages or callback queries"""
    if isinstance(event, types.Message):
        logging.info(
            "User[%s|%s:@%s]: %r",
            event.chat.id,
            event.from_user.id,
            event.from_user.username,
            event.text,
        )
    elif isinstance(event, types.CallbackQuery):
        logging.info(
            "User[%s|%s:@%s]: CallbackQuery %r",
            event.message.chat.id if event.message else "N/A",
            event.from_user.id,
            event.from_user.username,
            event.data,
        )
    else:
        logging.info("Unknown event type: %s", type(event))


def log_bot_outgoing_message(event, answer):
    """Log outgoing messages or callback responses"""
    if isinstance(event, types.Message):
        logging.info(
            "<<< User[%s|%s:@%s]: %r",
            event.chat.id,
            event.from_user.id,
            event.from_user.username,
            answer,
        )
    elif isinstance(event, types.CallbackQuery):
        logging.info(
            "<<< User[%s|%s:@%s]: CallbackResponse %r",
            event.message.chat.id if event.message else "N/A",
            event.from_user.id,
            event.from_user.username,
            answer,
        )
    else:
        logging.info("<<< Unknown event type %s: %r", type(event), answer)
