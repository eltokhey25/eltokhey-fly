#!/usr/bin/env python
"""
manage.py
The project's command-line entry point: `python manage.py <command>`.

Sets DJANGO_SETTINGS_MODULE to config.settings (unless the environment already
says otherwise) and hands the arguments to Django. The ImportError branch is
the stock one that fires when Django is missing or the venv is not active.
"""
import os
import sys


def main():
    """Point Django at this project's settings and run the requested command.

    Raises:
        ImportError: When Django cannot be imported, which almost always
            means the virtual environment is not active.
    """
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
