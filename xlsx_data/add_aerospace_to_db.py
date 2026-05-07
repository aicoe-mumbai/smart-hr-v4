#!/usr/bin/env python3
"""
Script to add AS-AEROSPACE BU data to goals.db
"""
import sqlite3
import pandas as pd

# Paths
GOALS_DB_PATH = '/home/aicoe/Desktop/smart-hr-v4/xlsx_data/goals.db'
AEROSPACE_EXCEL_PATH = '/home/aicoe/Desktop/smart-hr-v4/xlsx_data/AS-AEROSPACE_GOALS.xlsx'

def add_aerospace_to_database():
    """Add AS-AEROSPACE BU table and data to goals.db"""
    
    # Read AS-AEROSPACE Excel file
    print(f"Reading {AEROSPACE_EXCEL_PATH}...")
    df = pd.read_excel(AEROSPACE_EXCEL_PATH, header=0)
    
    # Rename columns
    df.columns = ['s_no', 'parameter', 'goal', 'measure_of_success', 
                  'linkage_to_thrust_area', 'linkage_to_group_objective']
    
    # Remove header row and rows where goal is NaN
    df_clean = df[1:].copy()  # Skip first row (header)
    df_clean = df_clean[df_clean['goal'].notna()].copy()
    
    # Forward fill parameter column (for grouped objectives)
    df_clean['parameter'] = df_clean['parameter'].fillna(method='ffill')
    
    print(f"Found {len(df_clean)} AS-AEROSPACE objectives")
    
    # Connect to database
    conn = sqlite3.connect(GOALS_DB_PATH)
    cursor = conn.cursor()
    
    # Check if AS_AEROSPACE table already exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='AS_AEROSPACE'")
    if cursor.fetchone():
        print("⚠️  AS_AEROSPACE table already exists. Dropping and recreating...")
        cursor.execute("DROP TABLE AS_AEROSPACE")
    
    # Create AS_AEROSPACE table with same schema as other BU tables
    print("Creating AS_AEROSPACE table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS "AS_AEROSPACE" (
            id                          INTEGER PRIMARY KEY AUTOINCREMENT,
            parameter                   TEXT,
            goal                        TEXT NOT NULL,
            measure_of_success          TEXT,
            linkage_to_thrust_area      TEXT,
            linkage_to_group_objective  TEXT
        )
    """)
    
    # Insert data
    print("Inserting AS-AEROSPACE objectives...")
    inserted_count = 0
    for idx, row in df_clean.iterrows():
        # Clean up the data
        parameter = str(row['parameter']).strip() if pd.notna(row['parameter']) else None
        goal = str(row['goal']).strip() if pd.notna(row['goal']) else None
        mos = str(row['measure_of_success']).strip() if pd.notna(row['measure_of_success']) else None
        ta = str(row['linkage_to_thrust_area']).strip() if pd.notna(row['linkage_to_thrust_area']) else None
        go = str(row['linkage_to_group_objective']).strip() if pd.notna(row['linkage_to_group_objective']) else None
        
        # Skip if goal is empty or contains only "Goals" text
        if not goal or goal.lower() in ['nan', 'goals', 'r&d goals', 'd&dc goals']:
            continue
        
        cursor.execute("""
            INSERT INTO AS_AEROSPACE (parameter, goal, measure_of_success, 
                                     linkage_to_thrust_area, linkage_to_group_objective)
            VALUES (?, ?, ?, ?, ?)
        """, (parameter, goal, mos, ta, go))
        inserted_count += 1
    
    conn.commit()
    
    # Verify insertion
    cursor.execute("SELECT COUNT(*) FROM AS_AEROSPACE")
    count = cursor.fetchone()[0]
    print(f"✅ Successfully added {count} objectives to AS_AEROSPACE table")
    
    # Display sample data
    print("\n" + "="*80)
    print("AS_AEROSPACE Table Sample (first 10):")
    print("="*80)
    cursor.execute("SELECT * FROM AS_AEROSPACE LIMIT 10")
    for row in cursor.fetchall():
        print(f"\nID: {row[0]}")
        print(f"Parameter: {row[1]}")
        print(f"Goal: {row[2][:80]}...")
        print(f"TA: {row[4]}")
        print(f"GO: {row[5]}")
    
    conn.close()
    print("\n✅ AS-AEROSPACE BU successfully added to goals.db")

if __name__ == "__main__":
    add_aerospace_to_database()
