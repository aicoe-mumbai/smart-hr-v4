"""
Django management command to load BU objectives from xlsx_data folder
Handles Thrust Areas, Group Objectives, and all BU goal files
"""

from django.core.management.base import BaseCommand
from smart_hr_backend.models import (
    ThrustArea, GroupObjective, BUObjective, OrgUnit,
    BUObjectiveTALink, BUObjectiveGOLink
)
import pandas as pd
import os
import re
from pathlib import Path


class Command(BaseCommand):
    help = 'Load BU objectives from xlsx_data folder'

    def __init__(self):
        super().__init__()
        self.ta_mapping = {}  # Maps TA codes to their sub-codes
        self.go_mapping = {}  # Maps GO codes to their sub-codes
        
    def handle(self, *args, **options):
        base_path = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
        xlsx_folder = base_path / 'xlsx_data'
        
        self.stdout.write(self.style.SUCCESS(f'Loading data from: {xlsx_folder}'))
        
        # Step 1: Load Thrust Areas
        self.load_thrust_areas(xlsx_folder / 'THRUST_AREAS.xlsx')
        
        # Step 2: Load Group Objectives
        self.load_group_objectives(xlsx_folder / 'GORUP_OBJECTIVES.xlsx')
        
        # Step 3: Load BU Goals
        bu_files = [
            ('CORPORATE_CENTER_GOALS.xlsx', 'Corporate Center'),
            ('EPS_GOALS.xlsx', 'EPS'),
            ('F&A_GOALS.xlsx', 'F&A'),
            ('HAZIRA_MANUFACTURING_GOALS.xlsx', 'Hazira Manufacturing'),
            ('IT_DIGITAL_GOALS.xlsx', 'IT & Digital'),
            ('LPES_GOALS.xlsx', 'LPES'),
            ('SCM_GOALS.xlsx', 'SCM'),
            ('T&IC_GOALS.xlsx', 'T&IC'),
        ]
        
        for filename, bu_name in bu_files:
            file_path = xlsx_folder / filename
            if file_path.exists():
                self.load_bu_goals(file_path, bu_name)
            else:
                self.stdout.write(self.style.WARNING(f'File not found: {filename}'))
        
        self.stdout.write(self.style.SUCCESS('Data loading complete!'))
        self.print_statistics()
    
    def load_thrust_areas(self, file_path):
        """Load thrust areas with main headings and sub-headings"""
        self.stdout.write(f'Loading Thrust Areas from {file_path.name}...')
        
        df = pd.read_excel(file_path, header=0)
        
        current_main_ta = None
        for _, row in df.iterrows():
            code = str(row['Unnamed: 0']).strip() if pd.notna(row['Unnamed: 0']) else None
            description = str(row['Thrust Areas FY27']).strip() if pd.notna(row['Thrust Areas FY27']) else None
            
            if not code or not description or code == 'nan':
                continue
            
            # Main TA (e.g., TA-1, TA-2)
            if code.startswith('TA-'):
                current_main_ta = code
                self.ta_mapping[code] = []
                ThrustArea.objects.update_or_create(
                    code=code,
                    defaults={'description': description, 'is_sub_heading': False}
                )
                self.stdout.write(f'  Created TA: {code} - {description}')
            
            # Sub-heading (e.g., 1.1, 2.1, 3.1)
            elif '.' in code and current_main_ta:
                sub_code = f"{current_main_ta}.{code.split('.')[1]}"
                self.ta_mapping[current_main_ta].append(sub_code)
                ThrustArea.objects.update_or_create(
                    code=sub_code,
                    defaults={
                        'description': description,
                        'is_sub_heading': True,
                        'parent_code': current_main_ta
                    }
                )
                self.stdout.write(f'    Sub: {sub_code} - {description[:50]}...')
        
        self.stdout.write(self.style.SUCCESS(f'Loaded {ThrustArea.objects.count()} Thrust Areas'))
    
    def load_group_objectives(self, file_path):
        """Load group objectives with main headings and sub-headings"""
        self.stdout.write(f'Loading Group Objectives from {file_path.name}...')
        
        df = pd.read_excel(file_path, header=2)
        
        current_main_go = None
        current_parameter = None
        
        for _, row in df.iterrows():
            s_no = row['S No'] if pd.notna(row['S No']) else None
            parameter = str(row['Parameter']).strip() if pd.notna(row['Parameter']) else None
            objective_text = str(row['Group Objectives']).strip() if pd.notna(row['Group Objectives']) else None
            
            if not objective_text or objective_text == 'nan':
                continue
            
            # Main GO number (e.g., 1.0, 2.0, 3.0)
            if s_no and isinstance(s_no, (int, float)):
                main_num = int(s_no)
                current_main_go = f"GO-{main_num}"
                current_parameter = parameter
                self.go_mapping[current_main_go] = []
                
                # Extract sub-code from objective text (e.g., "a)", "b)")
                match = re.match(r'^([a-z])\)', objective_text)
                if match:
                    sub_letter = match.group(1)
                    sub_code = f"{current_main_go}{sub_letter}"
                    self.go_mapping[current_main_go].append(sub_code)
                    
                    GroupObjective.objects.update_or_create(
                        code=sub_code,
                        defaults={
                            'description': objective_text,
                            'parameter': current_parameter,
                            'is_sub_heading': True,
                            'parent_code': current_main_go
                        }
                    )
                    self.stdout.write(f'  Created GO: {sub_code} - {objective_text[:50]}...')
            
            # Sub-heading (starts with letter like a), b), c))
            elif current_main_go:
                match = re.match(r'^([a-z])\)', objective_text)
                if match:
                    sub_letter = match.group(1)
                    sub_code = f"{current_main_go}{sub_letter}"
                    self.go_mapping[current_main_go].append(sub_code)
                    
                    GroupObjective.objects.update_or_create(
                        code=sub_code,
                        defaults={
                            'description': objective_text,
                            'parameter': current_parameter,
                            'is_sub_heading': True,
                            'parent_code': current_main_go
                        }
                    )
                    self.stdout.write(f'    Sub: {sub_code} - {objective_text[:50]}...')
        
        self.stdout.write(self.style.SUCCESS(f'Loaded {GroupObjective.objects.count()} Group Objectives'))
    
    def load_bu_goals(self, file_path, bu_name):
        """Load BU goals from individual BU files"""
        self.stdout.write(f'Loading {bu_name} goals from {file_path.name}...')
        
        # Get or create BU
        org_unit, created = OrgUnit.objects.get_or_create(
            name=bu_name,
            defaults={'description': f'{bu_name} Business Unit'}
        )
        
        # Try different header rows
        df = None
        for header_row in range(5):
            try:
                test_df = pd.read_excel(file_path, header=header_row)
                cols = [str(c).lower() for c in test_df.columns]
                if any('goal' in c for c in cols) and any('thrust' in c or 'ta' in c for c in cols):
                    df = test_df
                    break
            except:
                continue
        
        if df is None:
            self.stdout.write(self.style.WARNING(f'Could not find valid headers in {file_path.name}'))
            return
        
        # Find column names
        goal_col = self.find_column(df, ['goal'], exclude=['group', 'objective'])
        measure_col = self.find_column(df, ['measure'])
        ta_col = self.find_column(df, ['thrust', 'linkage to thrust'])
        go_col = self.find_column(df, ['linkage to group', 'group objective'])
        parameter_col = self.find_column(df, ['parameter'])
        
        if not goal_col:
            self.stdout.write(self.style.WARNING(f'Could not find goal column in {file_path.name}'))
            return
        
        count = 0
        for idx, row in df.iterrows():
            goal_text = str(row[goal_col]).strip() if pd.notna(row[goal_col]) else None
            
            if not goal_text or goal_text == 'nan' or len(goal_text) < 10:
                continue
            
            measure = str(row[measure_col]).strip() if measure_col and pd.notna(row[measure_col]) else None
            ta_raw = str(row[ta_col]).strip() if ta_col and pd.notna(row[ta_col]) else None
            go_raw = str(row[go_col]).strip() if go_col and pd.notna(row[go_col]) else None
            parameter = str(row[parameter_col]).strip() if parameter_col and pd.notna(row[parameter_col]) else None
            
            # Create BU Objective
            bu_obj = BUObjective.objects.create(
                org_unit=org_unit,
                parameter_name=parameter,
                goal_text=goal_text,
                measure_of_success=measure,
                linkage_ta_raw=ta_raw,
                linkage_go_raw=go_raw,
                source_sheet=file_path.name,
                source_row_no=idx + 1
            )
            
            # Parse and link TA codes
            if ta_raw:
                ta_codes = self.parse_ta_codes(ta_raw)
                for ta_code in ta_codes:
                    BUObjectiveTALink.objects.create(
                        objective=bu_obj,
                        ta_code_raw=ta_raw,
                        ta_code_normalized=ta_code
                    )
            
            # Parse and link GO codes
            if go_raw:
                go_codes = self.parse_go_codes(go_raw)
                for go_code in go_codes:
                    BUObjectiveGOLink.objects.create(
                        objective=bu_obj,
                        go_code_raw=go_raw,
                        go_code_normalized=go_code
                    )
            
            count += 1
        
        self.stdout.write(self.style.SUCCESS(f'  Loaded {count} objectives for {bu_name}'))
    
    def find_column(self, df, keywords, exclude=None):
        """Find column name containing any of the keywords, excluding certain patterns"""
        exclude = exclude or []
        for col in df.columns:
            col_lower = str(col).lower()
            # Check if any exclude pattern is in the column name
            if any(ex in col_lower for ex in exclude):
                continue
            # Check if any keyword is in the column name
            if any(keyword in col_lower for keyword in keywords):
                return col
        return None
    
    def parse_ta_codes(self, ta_raw):
        """Parse TA codes from raw text, expanding main codes to include all sub-codes"""
        if not ta_raw or ta_raw == 'nan':
            return []
        
        codes = set()
        
        # Find all TA patterns: TA-1, TA-2, TA1, TA2, TA-1.1, etc.
        # Updated regex to handle both TA-1 and TA1 formats
        patterns = re.findall(r'TA-?\d+(?:\.\d+)?', ta_raw, re.IGNORECASE)
        
        for pattern in patterns:
            # Normalize to TA-X format
            normalized = pattern.upper()
            if not '-' in normalized:
                # Convert TA1 to TA-1
                normalized = normalized.replace('TA', 'TA-')
            
            codes.add(normalized)
            
            # If it's a main code (e.g., TA-1), add all its sub-codes
            if '.' not in normalized and normalized in self.ta_mapping:
                codes.update(self.ta_mapping[normalized])
        
        # Also check for standalone numbers that might be TA codes
        if not patterns:
            numbers = re.findall(r'\b(\d+)\b', ta_raw)
            for num in numbers:
                ta_code = f'TA-{num}'
                if ta_code in self.ta_mapping:
                    codes.add(ta_code)
                    codes.update(self.ta_mapping[ta_code])
        
        return sorted(codes)
    
    def parse_go_codes(self, go_raw):
        """Parse GO codes from raw text with improved handling"""
        if not go_raw or go_raw == 'nan':
            return []
        
        codes = set()
        has_specific_subcodes = False
        
        # Pattern 1: GO-1, GO-2, GO1, GO2 (with or without hyphen)
        go_main_patterns = re.findall(r'GO-?(\d+)(?![a-z\(\)])', go_raw, re.IGNORECASE)
        
        # Pattern 2: Specific sub-codes like 1(a), 2(b), 1a, 2b, 3)a, 4.e)
        # This includes formats: 1(a), 1a, 1)a, 1.a)
        sub_patterns = re.findall(r'(\d+)\s*[\)\.]?\s*[\(]?\s*([a-z])\s*[\)]?', go_raw, re.IGNORECASE)
        
        # If we found specific sub-codes, use only those (don't expand)
        if sub_patterns:
            has_specific_subcodes = True
            for num, letter in sub_patterns:
                sub_code = f'GO-{num}{letter.lower()}'
                codes.add(sub_code)
        
        # If we found main GO codes (GO2, GO3, etc.) without specific sub-codes
        if go_main_patterns and not has_specific_subcodes:
            for num in go_main_patterns:
                go_code = f'GO-{num}'
                codes.add(go_code)
                # Only expand if no specific sub-codes were found
                if go_code in self.go_mapping:
                    codes.update(self.go_mapping[go_code])
        
        # Pattern 3: Handle "to" ranges like "2)c to 2)f" or "7)a to 7)d"
        range_pattern = re.search(r'(\d+)\s*\)?\s*([a-z])\s*to\s*(\d+)\s*\)?\s*([a-z])', go_raw, re.IGNORECASE)
        if range_pattern:
            start_num = range_pattern.group(1)
            start_letter = range_pattern.group(2).lower()
            end_num = range_pattern.group(3)
            end_letter = range_pattern.group(4).lower()
            
            # Generate range of codes
            if start_num == end_num:
                for letter_code in range(ord(start_letter), ord(end_letter) + 1):
                    codes.add(f'GO-{start_num}{chr(letter_code)}')
        
        # Pattern 4: Handle comma-separated sub-codes like "3 a, b, c" or "5 a, b"
        # First, find the main number
        comma_pattern = re.search(r'(\d+)\s+([a-z])(?:\s*,\s*([a-z]))+', go_raw, re.IGNORECASE)
        if comma_pattern:
            main_num = comma_pattern.group(1)
            # Extract all letters after the number
            letters = re.findall(r'\b([a-z])\b', comma_pattern.group(0)[len(main_num):], re.IGNORECASE)
            for letter in letters:
                codes.add(f'GO-{main_num}{letter.lower()}')
        
        # Pattern 5: Handle "&" separated codes like "1(c & d)"
        and_pattern = re.findall(r'(\d+)\s*\(?\s*([a-z])\s*&\s*([a-z])\s*\)?', go_raw, re.IGNORECASE)
        for num, letter1, letter2 in and_pattern:
            codes.add(f'GO-{num}{letter1.lower()}')
            codes.add(f'GO-{num}{letter2.lower()}')
        
        # If still no codes found, try standalone numbers
        if not codes:
            numbers = re.findall(r'\b(\d+)\b', go_raw)
            for num in numbers:
                go_code = f'GO-{num}'
                if go_code in self.go_mapping:
                    codes.add(go_code)
                    codes.update(self.go_mapping[go_code])
        
        return sorted(codes)
    
    def print_statistics(self):
        """Print loading statistics"""
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.SUCCESS('LOADING STATISTICS'))
        self.stdout.write('=' * 80)
        self.stdout.write(f'Thrust Areas: {ThrustArea.objects.count()}')
        self.stdout.write(f'Group Objectives: {GroupObjective.objects.count()}')
        self.stdout.write(f'Business Units: {OrgUnit.objects.count()}')
        self.stdout.write(f'BU Objectives: {BUObjective.objects.count()}')
        self.stdout.write(f'TA Links: {BUObjectiveTALink.objects.count()}')
        self.stdout.write(f'GO Links: {BUObjectiveGOLink.objects.count()}')
        self.stdout.write('=' * 80)
