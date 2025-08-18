"""
Management command to build internationalization files.
Runs makemessages and compilemessages for all configured languages.
"""
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.conf import settings
import os
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Build internationalization files for all configured languages'

    def add_arguments(self, parser):
        parser.add_argument(
            '--make-only',
            action='store_true',
            help='Only run makemessages, skip compilemessages',
        )
        parser.add_argument(
            '--compile-only',
            action='store_true',
            help='Only run compilemessages, skip makemessages',
        )
        parser.add_argument(
            '--language',
            type=str,
            help='Process only specific language code (e.g., ta, hi)',
        )
        parser.add_argument(
            '--ignore-fuzzy',
            action='store_true',
            help='Ignore fuzzy translations when compiling',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting internationalization build process')
        )

        # Get configured languages
        configured_languages = [lang[0] for lang in settings.LANGUAGES if lang[0] != 'en']
        
        if options['language']:
            if options['language'] not in [lang[0] for lang in settings.LANGUAGES]:
                raise CommandError(f"Language '{options['language']}' not in LANGUAGES setting")
            configured_languages = [options['language']]

        self.stdout.write(f'Processing languages: {", ".join(configured_languages)}')

        try:
            # Ensure locale directory exists
            locale_dir = os.path.join(settings.BASE_DIR, 'locale')
            os.makedirs(locale_dir, exist_ok=True)

            # Run makemessages unless compile-only
            if not options['compile_only']:
                self._run_makemessages(configured_languages)

            # Run compilemessages unless make-only
            if not options['make_only']:
                self._run_compilemessages(configured_languages, options['ignore_fuzzy'])

            self.stdout.write(
                self.style.SUCCESS('Internationalization build completed successfully')
            )

        except Exception as e:
            logger.error(f'Error in i18n build: {e}')
            raise CommandError(f'Internationalization build failed: {e}')

    def _run_makemessages(self, languages):
        """Run makemessages for specified languages"""
        self.stdout.write('Running makemessages...')
        
        for lang in languages:
            try:
                self.stdout.write(f'  Creating messages for {lang}...')
                call_command(
                    'makemessages',
                    locale=[lang],
                    verbosity=1,
                    ignore_patterns=[
                        'env/*',
                        'venv/*',
                        '*/migrations/*',
                        'static/admin/*',
                        'node_modules/*',
                    ],
                    extensions=['html', 'py', 'js'],
                    add_location='file',
                )
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Messages created for {lang}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Error creating messages for {lang}: {e}')
                )
                raise

    def _run_compilemessages(self, languages, ignore_fuzzy=False):
        """Run compilemessages for specified languages"""
        self.stdout.write('Running compilemessages...')
        
        # Check for missing translation files
        locale_dir = os.path.join(settings.BASE_DIR, 'locale')
        
        for lang in languages:
            po_file = os.path.join(locale_dir, lang, 'LC_MESSAGES', 'django.po')
            if not os.path.exists(po_file):
                self.stdout.write(
                    self.style.WARNING(
                        f'  ⚠ Translation file not found for {lang}: {po_file}\n'
                        f'    Run with --make-only first or create the file manually'
                    )
                )
                continue

            try:
                self.stdout.write(f'  Compiling messages for {lang}...')
                
                compile_args = {
                    'locale': [lang],
                    'verbosity': 1,
                }
                
                if ignore_fuzzy:
                    compile_args['ignore_fuzzy'] = True

                call_command('compilemessages', **compile_args)
                
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Messages compiled for {lang}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Error compiling messages for {lang}: {e}')
                )
                raise

        # Provide helpful information
        self.stdout.write('\n' + '='*50)
        self.stdout.write('Translation files location:')
        for lang in languages:
            po_file = os.path.join(locale_dir, lang, 'LC_MESSAGES', 'django.po')
            mo_file = os.path.join(locale_dir, lang, 'LC_MESSAGES', 'django.mo')
            
            po_exists = '✓' if os.path.exists(po_file) else '✗'
            mo_exists = '✓' if os.path.exists(mo_file) else '✗'
            
            self.stdout.write(f'  {lang}: .po {po_exists} | .mo {mo_exists}')
            if os.path.exists(po_file):
                self.stdout.write(f'       {po_file}')

        self.stdout.write('\nNext steps:')
        self.stdout.write('1. Edit .po files to add/update translations')
        self.stdout.write('2. Run: python manage.py i18n_build --compile-only')
        self.stdout.write('3. Restart Django server to load new translations')
