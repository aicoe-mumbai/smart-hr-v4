#!/usr/bin/env python3
"""
BU SMARTNESS and Alignment Report Generator

Generates:
1. SMARTNESS percentage for every BU goal (BU-wise)
2. Alignment percentage between every BU pair

Privacy: NO goal content is displayed in the report
"""

import sqlite3
import pandas as pd
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
import os
from datetime import datetime
import time

# Azure OpenAI Configuration
# Update these with your Azure OpenAI credentials
AZURE_ENDPOINT = os.getenv('OPENAI_ENDPOINT', 'https://your-endpoint.openai.azure.com/')
AZURE_API_KEY = os.getenv('OPENAI_API_KEY', 'your-api-key')
AZURE_MODEL = os.getenv('OPENAI_MODEL_NAME', 'gpt-4')

# Database path
GOALS_DB_PATH = os.path.join(os.path.dirname(__file__), 'goals.db')

# Azure OpenAI client
try:
    client = ChatCompletionsClient(
        endpoint=AZURE_ENDPOINT,
        credential=AzureKeyCredential(AZURE_API_KEY)
    )
    print(f"✓ Azure OpenAI client initialized")
    print(f"  Endpoint: {AZURE_ENDPOINT[:50]}...")
    print(f"  Model: {AZURE_MODEL}")
except Exception as e:
    print(f"✗ Error initializing Azure OpenAI client: {str(e)}")
    print("  Please set environment variables: OPENAI_ENDPOINT, OPENAI_API_KEY, OPENAI_MODEL_NAME")
    exit(1)

# All BU tables in goals.db
BU_TABLES = [
    'AS_AEROSPACE',
    'CORPORATE_CENTER',
    'EPS',
    'FA',
    'HAZIRA_MANUFACTURING',
    'HR',
    'IT_DIGITAL',
    'LPES',
    'MPES',
    'SCM',
    'TIC'
]

BU_DISPLAY_NAMES = {
    'AS_AEROSPACE': 'AS-Aerospace',
    'CORPORATE_CENTER': 'Corporate Center',
    'EPS': 'EPS',
    'FA': 'F&A',
    'HAZIRA_MANUFACTURING': 'Hazira Manufacturing',
    'HR': 'HR',
    'IT_DIGITAL': 'IT & Digital',
    'LPES': 'LPES',
    'MPES': 'MPES',
    'SCM': 'SCM',
    'TIC': 'T&IC'
}

def get_bu_goals(bu_table):
    """Fetch all goals from a BU table"""
    conn = sqlite3.connect(GOALS_DB_PATH)
    cursor = conn.cursor()
    
    query = f"""
    SELECT id, parameter, goal, measure_of_success
    FROM {bu_table}
    """
    
    cursor.execute(query)
    goals = cursor.fetchall()
    conn.close()
    
    return goals

def calculate_smartness(goal_text, measure_of_success):
    """Calculate SMARTNESS percentage using LLM"""
    prompt = f"""Evaluate this goal using SMART criteria (Specific, Measurable, Achievable, Relevant, Time-bound).

Goal: {goal_text}
Measure of Success: {measure_of_success}

Rate on scale 0-100 based on:
- Specific: Is it clear and well-defined?
- Measurable: Can progress be tracked?
- Achievable: Is it realistic?
- Relevant: Does it align with objectives?
- Time-bound: Does it have deadlines?

Return ONLY a number between 0-100. No explanation, no text, just the number."""

    try:
        response = client.complete(
            messages=[
                SystemMessage(content="You are an expert in SMART goal evaluation. Return only numeric scores."),
                UserMessage(content=prompt)
            ],
            model=AZURE_MODEL,
            max_tokens=10,
            temperature=0.3
        )
        
        result = response.choices[0].message.content.strip()
        # Extract number from response
        import re
        match = re.search(r'\d+', result)
        if match:
            score = int(match.group())
            return min(max(score, 0), 100)  # Ensure 0-100 range
        return 50  # Default if parsing fails
        
    except Exception as e:
        print(f"Error calculating SMARTNESS: {str(e)}")
        return 50  # Default on error

def calculate_alignment(bu1_goals, bu2_goals):
    """Calculate alignment percentage between two BUs"""
    if not bu1_goals or not bu2_goals:
        return 0
    
    total_alignment = 0
    comparison_count = 0
    
    # Sample goals if too many (to reduce API calls)
    max_comparisons = 50
    sample_size = min(len(bu1_goals), max_comparisons // len(bu2_goals) + 1)
    
    sampled_bu1 = bu1_goals[:sample_size] if len(bu1_goals) > sample_size else bu1_goals
    
    for goal1 in sampled_bu1:
        goal1_text = goal1[2]  # goal column
        
        for goal2 in bu2_goals[:5]:  # Compare with top 5 from BU2
            goal2_text = goal2[2]
            
            prompt = f"""Calculate alignment percentage between these two organizational goals (0-100).

Goal A: {goal1_text}
Goal B: {goal2_text}

Consider:
- Topic/domain overlap
- Strategic direction alignment
- Outcome alignment
- Complementary nature

Return ONLY a number between 0-100. No explanation."""

            try:
                response = client.complete(
                    messages=[
                        SystemMessage(content="You are an expert in organizational goal alignment. Return only numeric scores."),
                        UserMessage(content=prompt)
                    ],
                    model=AZURE_MODEL,
                    max_tokens=10,
                    temperature=0.3
                )
                
                result = response.choices[0].message.content.strip()
                import re
                match = re.search(r'\d+', result)
                if match:
                    score = int(match.group())
                    total_alignment += min(max(score, 0), 100)
                    comparison_count += 1
                
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                print(f"Error calculating alignment: {str(e)}")
                continue
    
    if comparison_count == 0:
        return 0
    
    return round(total_alignment / comparison_count, 1)

def generate_bu_smartness_report():
    """Generate SMARTNESS report for all BUs"""
    print("="*80)
    print("GENERATING BU SMARTNESS REPORT")
    print("="*80)
    
    all_bu_data = {}
    total_bus = len(BU_TABLES)
    
    for bu_idx, bu_table in enumerate(BU_TABLES, 1):
        bu_name = BU_DISPLAY_NAMES[bu_table]
        print(f"\n[{bu_idx}/{total_bus}] Processing {bu_name}...")
        
        goals = get_bu_goals(bu_table)
        
        if not goals:
            print(f"  No goals found for {bu_name}")
            continue
        
        bu_smartness = []
        total_smartness = 0
        total_goals = len(goals)
        
        for idx, goal in enumerate(goals, 1):
            goal_id, parameter, goal_text, mos = goal
            
            # Progress indicator
            progress = (idx / total_goals) * 100
            print(f"  Analyzing goal {idx}/{total_goals} ({progress:.1f}%)...", end='\r')
            
            smartness = calculate_smartness(goal_text, mos)
            total_smartness += smartness
            
            bu_smartness.append({
                'Goal ID': goal_id,
                'Parameter': parameter if parameter else 'N/A',
                'SMARTNESS %': smartness
            })
            
            time.sleep(0.5)  # Rate limiting
        
        avg_smartness = round(total_smartness / len(goals), 1) if goals else 0
        
        all_bu_data[bu_name] = {
            'average': avg_smartness,
            'goals': bu_smartness
        }
        
        overall_progress = (bu_idx / total_bus) * 100
        print(f"\n  ✓ {bu_name}: Average SMARTNESS = {avg_smartness}%")
        print(f"  Overall Progress: {overall_progress:.1f}% ({bu_idx}/{total_bus} BUs completed)")
    
    return all_bu_data

def generate_bu_alignment_report():
    """Generate alignment report between all BU pairs"""
    print("\n" + "="*80)
    print("GENERATING BU ALIGNMENT REPORT")
    print("="*80)
    
    # Load all BU goals
    all_bu_goals = {}
    for bu_table in BU_TABLES:
        bu_name = BU_DISPLAY_NAMES[bu_table]
        goals = get_bu_goals(bu_table)
        if goals:
            all_bu_goals[bu_name] = goals
    
    alignment_data = {}
    total_bus = len(all_bu_goals)
    total_comparisons = total_bus * (total_bus - 1)
    completed_comparisons = 0
    
    for bu1_idx, bu1_name in enumerate(all_bu_goals.keys(), 1):
        print(f"\n[{bu1_idx}/{total_bus}] Calculating alignment for {bu1_name}...")
        
        bu1_alignments = {}
        
        for bu2_idx, bu2_name in enumerate(all_bu_goals.keys(), 1):
            if bu1_name == bu2_name:
                continue
            
            print(f"  vs {bu2_name}...", end='\r')
            
            alignment = calculate_alignment(
                all_bu_goals[bu1_name],
                all_bu_goals[bu2_name]
            )
            
            bu1_alignments[bu2_name] = alignment
            completed_comparisons += 1
            
            overall_progress = (completed_comparisons / total_comparisons) * 100
            print(f"  vs {bu2_name}: {alignment}% | Overall: {overall_progress:.1f}%", end='\r')
        
        alignment_data[bu1_name] = bu1_alignments
        print(f"\n  ✓ {bu1_name} alignment calculated ({bu1_idx}/{total_bus} BUs)")
    
    return alignment_data

def export_to_excel(smartness_data, alignment_data, output_file):
    """Export report to Excel"""
    print("\n" + "="*80)
    print("EXPORTING TO EXCEL")
    print("="*80)
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Summary sheet
        summary_data = []
        for bu_name, data in smartness_data.items():
            summary_data.append({
                'Business Unit': bu_name,
                'Average SMARTNESS %': data['average'],
                'Total Goals': len(data['goals'])
            })
        
        summary_df = pd.DataFrame(summary_data)
        summary_df = summary_df.sort_values('Average SMARTNESS %', ascending=False)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Individual BU sheets
        for bu_name, data in smartness_data.items():
            # SMARTNESS table
            smartness_df = pd.DataFrame(data['goals'])
            
            # Alignment table
            if bu_name in alignment_data:
                alignment_list = [
                    {'Target BU': target_bu, 'Alignment %': alignment}
                    for target_bu, alignment in sorted(
                        alignment_data[bu_name].items(),
                        key=lambda x: x[1],
                        reverse=True
                    )
                ]
                alignment_df = pd.DataFrame(alignment_list)
            else:
                alignment_df = pd.DataFrame()
            
            # Write to sheet
            sheet_name = bu_name[:31]  # Excel sheet name limit
            
            # Write SMARTNESS section
            smartness_df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=0)
            
            # Write header for alignment section
            start_row = len(smartness_df) + 3
            worksheet = writer.sheets[sheet_name]
            worksheet.cell(row=start_row, column=1, value=f"{bu_name} ALIGNMENT WITH OTHER BUs")
            
            # Write alignment table
            if not alignment_df.empty:
                alignment_df.to_excel(
                    writer,
                    sheet_name=sheet_name,
                    index=False,
                    startrow=start_row + 1
                )
    
    print(f"✓ Report exported to: {output_file}")

def main():
    print("\n" + "="*80)
    print("BU SMARTNESS AND ALIGNMENT REPORT GENERATOR")
    print("="*80)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Database: {GOALS_DB_PATH}")
    print(f"Total BUs: {len(BU_TABLES)}")
    print("="*80)
    
    start_time = time.time()
    
    # Phase 1: SMARTNESS Analysis
    print("\n[PHASE 1/3] SMARTNESS ANALYSIS")
    print("-" * 80)
    smartness_data = generate_bu_smartness_report()
    phase1_time = time.time() - start_time
    print(f"\n✓ Phase 1 completed in {phase1_time/60:.1f} minutes")
    
    # Phase 2: Alignment Analysis
    print("\n[PHASE 2/3] ALIGNMENT ANALYSIS")
    print("-" * 80)
    alignment_data = generate_bu_alignment_report()
    phase2_time = time.time() - start_time - phase1_time
    print(f"\n✓ Phase 2 completed in {phase2_time/60:.1f} minutes")
    
    # Phase 3: Export to Excel
    print("\n[PHASE 3/3] EXPORTING TO EXCEL")
    print("-" * 80)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'BU_SMARTNESS_ALIGNMENT_REPORT_{timestamp}.xlsx'
    export_to_excel(smartness_data, alignment_data, output_file)
    phase3_time = time.time() - start_time - phase1_time - phase2_time
    print(f"\n✓ Phase 3 completed in {phase3_time:.1f} seconds")
    
    total_time = time.time() - start_time
    
    print("\n" + "="*80)
    print("REPORT GENERATION COMPLETE")
    print("="*80)
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Time: {total_time/60:.1f} minutes")
    print(f"Output File: {output_file}")
    print("\nSummary:")
    print(f"  - BUs Analyzed: {len(smartness_data)}")
    print(f"  - Total Goals: {sum(len(data['goals']) for data in smartness_data.values())}")
    print(f"  - BU Pairs Compared: {len(alignment_data) * (len(alignment_data) - 1)}")
    print("="*80)

if __name__ == "__main__":
    main()
