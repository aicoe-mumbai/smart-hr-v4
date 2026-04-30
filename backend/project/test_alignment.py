#!/usr/bin/env python3
"""
Test script to verify alignment flow works correctly
Run from: backend/project directory
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from smart_hr_backend.models import SmartGoal
from smart_hr_backend.goals_db_utils import get_bu_objectives, split_linkage_values
from django.contrib.auth import get_user_model

print("="*80)
print("ALIGNMENT FLOW TEST")
print("="*80)

# Test 1: split_linkage_values
print("\n1. Testing split_linkage_values function:")
test_cases = [
    "TA2, TA3, TA4",
    "GO2, GO3, GO4",
    "1. e), 3.e), 4.e)",
    "TA-1, TA-3 TA-4",
]
for test in test_cases:
    result = split_linkage_values(test)
    print(f"   '{test}' -> {result}")

# Test 2: get_bu_objectives
print("\n2. Testing get_bu_objectives:")
objectives = get_bu_objectives(
    bu_names=["IT & Digital", "Corporate Center"],
    ta_codes=["TA-1"],
    go_codes=["GO-1"]
)
print(f"   Found {len(objectives)} objectives for IT & Digital + Corporate Center with TA-1 and GO-1")
for obj in objectives:
    print(f"   - {obj['bu_name']}: {obj['parameter']} (TA: {obj['thrust_area_str']}, GO: {obj['group_objective_str']})")

# Test 3: SmartGoal alignment
print("\n3. Testing SmartGoal.get_aligned_objectives():")
User = get_user_model()
test_user, _ = User.objects.get_or_create(username='test_alignment_user')

test_goal = SmartGoal(
    user=test_user,
    goal="Test cybersecurity goal",
    measure_of_success="Zero incidents",
    kpi_metrics="Security metrics",
    outcome_defined="Yes",
    quantifiable_objective=100,
    skills_available="Yes",
    obstacles_considered="Yes",
    thrust_area="TA-1 Core Values",
    sub_category="1.1 Mission Zero Harm",
    group_objectives="Environment, Safety, Sustainability & Governance",
    additional_sub_category="1e) Zero Information Security Breach",
    user_bu="IT & Digital",
    crosslinked_bus=["Corporate Center"],
    start_date="2026-04-01",
    end_date="2027-04-30",
    response=""
)

aligned = test_goal.get_aligned_objectives()
print(f"   Found {len(aligned)} aligned objectives")
for obj in aligned:
    print(f"   - {obj['bu_name']}: {obj['parameter']}")

print("\n" + "="*80)
print("TEST COMPLETED SUCCESSFULLY")
print("="*80)
print("\nNext step: Restart Django server and test via frontend")
