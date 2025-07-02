from typing import Callable, List, Optional

import aiogram
from aiogram.filters import Command

from bot_controller.decorators import skip_empty_command


class Router(aiogram.Router):
    def __init__(self, *, name: Optional[str] = None) -> None:
        super().__init__(name=name)
        self.command_list: List[str] = []

    def register(
        self,
        command: Optional[str] = None,
        description: Optional[str] = None,
        skip_empty_messages: bool = False,
    ) -> Callable:
        def decorator(command_handler: Callable) -> Callable:
            if command is None:
                # Check if the handler is for callback queries by inspecting its signature
                import inspect
                sig = inspect.signature(command_handler)
                params = list(sig.parameters.values())
                
                # If first parameter is CallbackQuery, register as callback handler
                if params and 'callback' in str(params[0].annotation).lower():
                    self.callback_query()(command_handler)
                else:
                    # Register for both message and callback query to be safe
                    self.message()(command_handler)
                    self.callback_query()(command_handler)
                return command_handler

            command_filter = Command(command)
            handler = command_handler
            if skip_empty_messages:
                handler = skip_empty_command(command=command)(command_handler)

            self.message(command_filter)(handler)

            if description:
                self.command_list.append(f"/{command} - {description}")

            return handler

        return decorator
