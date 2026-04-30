# DEPRECATED: This command is no longer used.
# BU objectives are now managed in goals.db instead of Django models.
# See DUAL_DATABASE_IMPLEMENTATION.md for details.

import openpyxl
import re
import logging
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'DEPRECATED - BU objectives are now in goals.db'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(
            'This command is deprecated. BU objectives are now managed in goals.db.\n'
            'See DUAL_DATABASE_IMPLEMENTATION.md for details.'
        ))