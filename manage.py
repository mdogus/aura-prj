#!/usr/bin/env python
import os
import sys
from pathlib import Path


def main():
    project_root = Path(__file__).resolve().parent
    sys.path.insert(0, str(project_root / 'src'))

    # Proje kökündeki .env dosyasını yükle (varsa)
    try:
        from dotenv import load_dotenv
        load_dotenv(project_root / '.env')
    except ImportError:
        pass  # python-dotenv kurulu değilse yoksay

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
