"""Diagnose Groq connectivity: available models, key, and a live test turn."""
import time

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.chatbot import (
    GROQ_MODELS_URL,
    GROQ_API_URL,
    MAX_TOKENS,
    MODEL_FALLBACKS,
    REQUEST_TIMEOUT,
    _error_body,
    _resolve_api_key,
)


class Command(BaseCommand):
    help = 'Check GROQ_API_KEY, list available models, and run one test message.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--models', action='store_true',
            help='List every model the key can use (default: on).',
        )
        parser.add_argument(
            '--message', default='مرحبا',
            help='Test message to send through the chatbot.',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('--- Groq chatbot check ---'))

        root = settings.PROJECT_ROOT
        env_path = root / '.env'
        self.stdout.write(f'GROQ_MODEL           : {MODEL_FALLBACKS[0]}')
        self.stdout.write(f'settings.PROJECT_ROOT: {root}')
        self.stdout.write(f'.env path            : {env_path}')
        self.stdout.write(f'.env exists          : {env_path.exists()}')

        api_key = _resolve_api_key()
        if not api_key:
            raise CommandError(
                'GROQ_API_KEY is not set. Add it to .env or the host environment.'
            )
        self.stdout.write(f'key first 15 chars   : {api_key[:15]}...')
        self.stdout.write(f'key length           : {len(api_key)}')

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }

        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING('--- Models available to this key ---'))
        try:
            r = requests.get(GROQ_MODELS_URL, headers=headers, timeout=REQUEST_TIMEOUT)
        except requests.exceptions.RequestException as exc:
            raise CommandError(f'Could not reach the models endpoint: {exc}')

        if r.status_code != 200:
            raise CommandError(f'HTTP {r.status_code}: {_error_body(r)}')

        model_ids = [m.get('id') for m in r.json().get('data', []) if m.get('id')]
        for model_id in sorted(model_ids):
            mark = ' <- primary' if model_id == MODEL_FALLBACKS[0] else ''
            if model_id in MODEL_FALLBACKS:
                mark += ' [fallback chain]'
            self.stdout.write(f'  - {model_id}{mark}')
        self.stdout.write(f'total: {len(model_ids)}')

        missing = [m for m in MODEL_FALLBACKS if m not in model_ids]
        if missing:
            # A stale fallback would waste a full round trip on every failure.
            self.stdout.write(self.style.WARNING(
                'WARNING: configured fallback(s) not on this key: ' + ', '.join(missing)
            ))

        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING('--- Test message through the fallback chain ---'))
        self.stdout.write(f'message: {options["message"]}')
        self.stdout.write(f'max_tokens: {MAX_TOKENS}   timeout: {REQUEST_TIMEOUT}s')

        messages = [
            {'role': 'system', 'content': 'أنت مساعد طوخي للحج والعمرة. أجب باختصار.'},
            {'role': 'user', 'content': options['message']},
        ]

        last = None
        for model in MODEL_FALLBACKS:
            if model not in model_ids:
                self.stdout.write(f'  {model}: SKIPPED (not available to this key)')
                continue
            started = time.time()
            try:
                r = requests.post(
                    GROQ_API_URL,
                    headers=headers,
                    json={
                        'model': model,
                        'messages': messages,
                        'temperature': 0.4,
                        'max_tokens': MAX_TOKENS,
                        'top_p': 0.9,
                    },
                    timeout=REQUEST_TIMEOUT,
                )
            except requests.exceptions.Timeout:
                self.stdout.write(f'  {model}: TIMEOUT after {REQUEST_TIMEOUT}s')
                last = f'{model} timed out'
                continue
            except requests.exceptions.RequestException as exc:
                self.stdout.write(f'  {model}: ERROR {exc}')
                last = str(exc)
                continue

            elapsed = time.time() - started
            if r.status_code != 200:
                self.stdout.write(f'  {model}: HTTP {r.status_code} in {elapsed:.1f}s')
                self.stdout.write(f'      {_error_body(r, 200)}')
                last = f'HTTP {r.status_code}'
                continue

            choice = r.json()['choices'][0]
            reply = ((choice.get('message') or {}).get('content') or '').strip()
            usage = r.json().get('usage') or {}
            self.stdout.write(
                f'  {model}: HTTP 200 in {elapsed:.1f}s | '
                f'finish_reason={choice.get("finish_reason")} | '
                f'completion_tokens={usage.get("completion_tokens")} | '
                f'reasoning_tokens={(usage.get("completion_tokens_details") or {}).get("reasoning_tokens")}'
            )
            self.stdout.write(f'      reply: {reply}')
            if reply:
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS(
                    f'OK - the chatbot is ready (model: {model}).'
                ))
                return
            self.stdout.write('      empty reply - would trigger the wider-budget retry')
            last = 'empty reply'

        raise CommandError(
            f'No fallback model returned a reply. Last failure: {last}. '
            'Check the key, the account tier, and the rate limit.'
        )
