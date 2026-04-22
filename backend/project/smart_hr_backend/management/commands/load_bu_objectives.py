import openpyxl
import re
import logging
from django.core.management.base import BaseCommand
from smart_hr_backend.models import OrgUnit, BUObjective, BUObjectiveTALink, BUObjectiveGOLink

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Load BU objectives from Excel files into database'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing data before loading')

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            BUObjectiveTALink.objects.all().delete()
            BUObjectiveGOLink.objects.all().delete()
            BUObjective.objects.all().delete()
            OrgUnit.objects.all().delete()
            logger.info("=== CLEARED ALL EXISTING DATA ===")

        files = [
            {
                'path': '/home/aicoe/Desktop/smart-hr-v4/mpes-mes_objectives.xlsx',
                'org_code': 'MPES-MES',
                'org_name': 'MPES-MES',
                'sheet_name': 'MPES-MES Objectives'
            },
            {
                'path': '/home/aicoe/Desktop/smart-hr-v4/qa-qc_objectives.xlsx',
                'org_code': 'QA-QC',
                'org_name': 'QA-QC',
                'sheet_name': 'QA-QC Objectives'
            }
        ]

        for file_info in files:
            self.load_file(file_info)

        self.stdout.write(self.style.SUCCESS('Successfully loaded all BU objectives'))

    def load_file(self, file_info):
        logger.info(f"\n=== LOADING FILE: {file_info['path']} ===")
        self.stdout.write(f"\nProcessing {file_info['org_name']}...")

        org_unit, created = OrgUnit.objects.get_or_create(
            code=file_info['org_code'],
            defaults={
                'name': file_info['org_name'],
                'sheet_name': file_info['sheet_name']
            }
        )
        logger.info(f"OrgUnit: {org_unit.name} ({'created' if created else 'exists'})")

        wb = openpyxl.load_workbook(file_info['path'])
        ws = wb.active

        # Find header row (look for exact 'Goal' column)
        header_row = None
        for row_idx in range(1, 10):
            for col_idx, cell in enumerate(ws[row_idx], start=1):
                if cell.value and str(cell.value).strip() == 'Goal':
                    header_row = row_idx
                    break
            if header_row:
                break
        
        if not header_row:
            logger.error("Could not find header row with 'Goal' column")
            return
        
        logger.info(f"Found headers in row {header_row}")

        headers = {}
        for col_idx, cell in enumerate(ws[header_row], start=1):
            if cell.value:
                headers[str(cell.value).strip()] = col_idx

        logger.info(f"Headers found: {list(headers.keys())}")

        param_col = headers.get('Parameter Name') or headers.get('Goal Category')
        goal_col = headers.get('Goal')
        measure_col = headers.get('Measure of Success')
        ta_col = headers.get('Linkage to Thrust Area')
        go_col = headers.get('Linkage to Group Objective')
        remarks_col = headers.get('Remarks')

        count = 0
        for row_idx in range(header_row + 1, ws.max_row + 1):
            row = ws[row_idx]
            goal_text = self._get_cell_value(row, goal_col)
            if not goal_text or not goal_text.strip():
                continue

            param_name = self._get_cell_value(row, param_col)
            measure = self._get_cell_value(row, measure_col)
            ta_raw = self._get_cell_value(row, ta_col)
            go_raw = self._get_cell_value(row, go_col)
            remarks = self._get_cell_value(row, remarks_col)

            logger.info(f"\n--- Row {row_idx} ---")
            logger.info(f"Parameter: {param_name}")
            logger.info(f"Goal: {goal_text[:100]}...")
            logger.info(f"TA Raw: {ta_raw}")
            logger.info(f"GO Raw: {go_raw}")

            obj = BUObjective.objects.create(
                org_unit=org_unit,
                parameter_name=param_name,
                goal_text=goal_text,
                measure_of_success=measure,
                linkage_ta_raw=ta_raw,
                linkage_go_raw=go_raw,
                source_sheet=file_info['sheet_name'],
                source_row_no=row_idx,
                remarks=remarks
            )

            ta_codes = self._parse_ta_codes(ta_raw)
            for ta_code in ta_codes:
                BUObjectiveTALink.objects.create(
                    objective=obj,
                    ta_code_raw=ta_raw or '',
                    ta_code_normalized=ta_code
                )
                logger.info(f"  Created TA Link: {ta_code}")

            go_codes = self._parse_go_codes(go_raw)
            for go_code in go_codes:
                BUObjectiveGOLink.objects.create(
                    objective=obj,
                    go_code_raw=go_raw or '',
                    go_code_normalized=go_code
                )
                logger.info(f"  Created GO Link: {go_code}")

            count += 1

        logger.info(f"\n=== COMPLETED {file_info['org_name']}: {count} objectives loaded ===")
        self.stdout.write(self.style.SUCCESS(f"  Loaded {count} objectives"))

    def _get_cell_value(self, row, col_idx):
        if not col_idx or col_idx > len(row):
            return None
        cell = row[col_idx - 1]
        return str(cell.value).strip() if cell.value else None

    def _parse_ta_codes(self, raw_value):
        if not raw_value:
            return []
        
        parts = re.split(r'[,/&]|\band\b', str(raw_value), flags=re.IGNORECASE)
        codes = []
        
        for part in parts:
            part = part.strip().upper()
            if not part:
                continue
            
            m = re.search(r'TA\s*[-]?\s*(\d+(?:\.\d+)?)', part)
            if m:
                codes.append(f"TA-{m.group(1)}")
                continue
            
            m = re.match(r'^(\d+(?:\.\d+)?)$', part)
            if m:
                codes.append(f"TA-{m.group(1)}")
        
        return codes

    def _parse_go_codes(self, raw_value):
        if not raw_value:
            return []
        
        parts = re.split(r'[,/&]|\band\b', str(raw_value), flags=re.IGNORECASE)
        codes = []
        
        for part in parts:
            part = part.strip().upper().replace('.', '').replace(' ', '')
            if not part:
                continue
            
            m = re.search(r'GO[-]?(\d+)(?:\(?([A-Z])\)?)?', part)
            if m:
                num = m.group(1)
                alpha = m.group(2)
                codes.append(f"GO-{num}({alpha.lower()})" if alpha else f"GO-{num}")
                continue
            
            m = re.match(r'^(\d+)([A-Z])$', part)
            if m:
                codes.append(f"GO-{m.group(1)}({m.group(2).lower()})")
                continue
            
            m = re.match(r'^(\d+)$', part)
            if m:
                codes.append(f"GO-{m.group(1)}")
        
        return codes