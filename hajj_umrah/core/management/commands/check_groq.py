"""Diagnose the Groq chatbot configuration on a deployed host.

Run this first whenever the chatbot replies "المساعد الذكي غير متاح حالياً":

    python manage.py check_groq

It reports which source the API key came from, then makes one real, tiny API
call so a bad key, a missing model or a network problem is shown verbatim
instead of being swallowed by the chatbot's error handling.
"""

import os

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from dotenv import load_dotenv

from core.chatbot import GROQ_API_URL, GROQ_MODEL, _resolve_api_key


class Command(BaseCommand):
    help = 'Check that GROQ_API_KEY is present, valid and usable.'

    def handle(self, *args, **options):
        self.stdout.write('--- Groq chatbot check ---')
        self.stdout.write(f'GROQ_MODEL           : {os.environ.get("GROQ_MODEL") or GROQ_MODEL}')
        self.stdout.write(f'settings.PROJECT_ROOT: {getattr(settings, "PROJECT_ROOT", "n/a")}')

        env_path = getattr(settings, 'PROJECT_ROOT', None)
        if env_path:
            candidate = os.path.join(str(env_path), '.env')
            self.stdout.write(f'.env path            : {candidate}')
            self.stdout.write(f'.env exists          : {os.path.isfile(candidate)}')

        api_key = _resolve_api_key()
        if not api_key:
            raise CommandError(
                'GROQ_API_KEY not found. Add it to the .env next to the project '
                'root, or export it in the environment. Note .env is in '
                '.gitignore, so `git pull` will NOT deliver it -- create it on '
                'the server by hand.'
            )

        # Enough to identify the key, never enough to leak it.
        self.stdout.write(f'key first 15 chars   : {api_key[:15]}...')
        self.stdout.write(f'key length          : {len(api_key)}')

        try:
            response = requests.post(
                GROQ_API_URL,
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json',
                },
                json={
                    'model': os.environ.get('GROQ_MODEL') or GROQ_MODEL,
                    'messages': [{'role': 'user', 'content': 'مرحبا'}],
                    # gpt-oss-* are reasoning models and spend part of this
                    # budget on reasoning, so keep it well above the token
                    # count a one-word greeting actually needs.
                    'max_tokens': 400,
                    'temperature': 0.4,
                },
                timeout=20,
            )
        except requests.exceptions.RequestException as exc:
            raise CommandError(f'Network failure calling Groq: {exc}')

        self.stdout.write(f'HTTP status         : {response.status_code}')
        if not response.ok:
            raise CommandError(f'Groq rejected the call: {response.text}')

        try:
            choice = response.json()['choices'][0]
            content = choice['message']['content'].strip()
            finish = choice.get('finish_reason')
        except (KeyError, IndexError, ValueError) as exc:
            raise CommandError(f'Unexpected response shape: {exc}\n{response.text}')

        self.stdout.write(f'finish_reason       : {finish}')
        if not content:
            raise CommandError(
                f'Groq returned an empty reply (finish_reason={finish!r}). '
                'The key and model are fine, but the reply was cut off -- raise '
                'max_tokens in core/chatbot.py.'
            )
        self.stdout.write(f'reply               : {content}')
        self.stdout.write(self.style.SUCCESS('OK - the chatbot is ready.'))
