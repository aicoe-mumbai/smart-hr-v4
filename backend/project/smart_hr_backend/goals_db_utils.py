"""
Utility functions to query goals.db for BU objectives, thrust areas, and group objectives.
This database is read-only and used only for alignment and gap analysis.
"""
import sqlite3
import logging
import os

logger = logging.getLogger(__name__)

# Determine goals.db path
try:
    from django.conf import settings
    GOALS_DB_PATH = os.path.join(settings.BASE_DIR.parent.parent, 'xlsx_data', 'goals.db')
except:
    # Fallback for standalone testing
    GOALS_DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'xlsx_data', 'goals.db')
    GOALS_DB_PATH = os.path.abspath(GOALS_DB_PATH)

def get_goals_db_connection():
    """Get a connection to the goals.db database"""
    return sqlite3.connect(GOALS_DB_PATH)

def get_bu_table_name(bu_name):
    """
    Convert BU name to table name in goals.db
    Examples:
    - "MPES" -> "MPES"
    - "IT & Digital" -> "IT_DIGITAL"
    - "F&A" -> "FA"
    - "T&IC" -> "TIC"
    """
    bu_mapping = {
        "MPES": "MPES",
        "EPS": "EPS",
        "LPES": "LPES",
        "IT & Digital": "IT_DIGITAL",
        "IT&Digital": "IT_DIGITAL",
        "F&A": "FA",
        "SCM": "SCM",
        "T&IC": "TIC",
        "Hazira Manufacturing": "HAZIRA_MANUFACTURING",
        "Corporate Center": "CORPORATE_CENTER"
    }
    return bu_mapping.get(bu_name, bu_name.upper().replace(" ", "_").replace("&", ""))

def get_available_bu_tables():
    """Get list of all BU tables in goals.db"""
    conn = get_goals_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        AND name NOT IN ('thrust_areas', 'group_objectives', 'sqlite_sequence')
        ORDER BY name
    """)
    
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    return tables

def split_linkage_values(linkage_text):
    """
    Split multi-line or comma-separated linkage values from goals.db
    Handles multiple formats and normalizes to parent codes:
    - "TA2, TA3, TA4" -> ["TA-2", "TA-3", "TA-4"]
    - "GO2, GO3, GO4" -> ["GO-2", "GO-3", "GO-4"]
    - "1. e), 3.e), 4.e)" -> ["GO-1", "GO-3", "GO-4"]
    - "TA-1a, TA-1b" -> ["TA-1"] (consolidate sub-categories to parent)
    
    Returns normalized parent codes: ["TA-3", "TA-4"] or ["GO-2", "GO-3"]
    """
    if not linkage_text:
        return []
    
    # First split by newline
    parts = str(linkage_text).split('\n')
    
    # Then split each part by comma, ampersand, or space
    all_values = []
    for part in parts:
        # Split by comma, ampersand, or multiple spaces
        import re
        subparts = re.split(r'[,&]|\s{2,}', part)
        for subpart in subparts:
            if subpart.strip():
                all_values.append(subpart.strip())
    
    # Normalize each value to parent code (remove sub-categories)
    normalized = set()  # Use set to avoid duplicates
    for value in all_values:
        value = value.strip().upper()
        if not value:
            continue
        
        # Handle TA codes (TA-3, TA3, TA-3a, TA3a, etc.)
        if value.startswith('TA'):
            # Extract just the number, ignore letters
            import re
            match = re.match(r'TA[-]?(\d+)', value)
            if match:
                num = match.group(1)
                normalized.add(f"TA-{num}")
        
        # Handle GO codes (GO-2, GO2, GO-2a, GO2a, etc.)
        elif value.startswith('GO'):
            # Extract just the number, ignore letters
            import re
            match = re.match(r'GO[-]?(\d+)', value)
            if match:
                num = match.group(1)
                normalized.add(f"GO-{num}")
        
        # Handle bare numbers with sub-categories: "1. e)", "3.e)", "4.e)"
        else:
            import re
            # Match patterns like "1.", "1.e)", "3.e)", etc.
            match = re.match(r'(\d+)', value)
            if match:
                num = match.group(1)
                # Assume GO code for bare numbers (common in GO linkage column)
                normalized.add(f"GO-{num}")
    
    return sorted(list(normalized))

def normalize_go_code(s_no):
    """
    Convert s_no from group_objectives table to GO code
    s_no=1 -> GO-1, s_no=2 -> GO-2, etc.
    """
    if not s_no:
        return None
    
    try:
        # s_no might be string or int
        num = int(s_no)
        return f"GO-{num}"
    except (ValueError, TypeError):
        return None

def get_thrust_areas():
    """
    Fetch all thrust areas from goals.db
    Returns list of dicts with code and description
    """
    conn = get_goals_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT thrust_area_code, thrust_area_name, sub_code, description
        FROM thrust_areas
        ORDER BY thrust_area_code, sub_code
    """)
    
    thrust_areas = []
    for row in cursor.fetchall():
        thrust_areas.append({
            'code': row[0],  # TA-1, TA-2, etc.
            'name': row[1],
            'sub_code': row[2],
            'description': row[3]
        })
    
    conn.close()
    return thrust_areas

def get_group_objectives():
    """
    Fetch all group objectives from goals.db
    Returns list of dicts with code (GO-1, GO-2, etc.) and description
    """
    conn = get_goals_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT s_no, parameter, objective
        FROM group_objectives
        ORDER BY s_no
    """)
    
    group_objectives = []
    seen_codes = set()
    
    for row in cursor.fetchall():
        s_no = row[0]
        parameter = row[1]
        objective = row[2]
        
        # Convert s_no to GO code
        go_code = normalize_go_code(s_no)
        
        if go_code and go_code not in seen_codes:
            # Only add main GO codes (GO-1, GO-2, etc.), not duplicates
            seen_codes.add(go_code)
            group_objectives.append({
                'code': go_code,
                'parameter': parameter or 'N/A',
                'description': objective
            })
    
    conn.close()
    return group_objectives

def get_bu_objectives(bu_names, ta_codes=None, go_codes=None):
    """
    Fetch BU objectives from goals.db for specified BUs
    Optionally filter by TA codes and/or GO codes
    
    Args:
        bu_names: List of BU names (e.g., ["MPES", "EPS"])
        ta_codes: List of TA codes to filter (e.g., ["TA-1", "TA-3"])
        go_codes: List of GO codes to filter (e.g., ["GO-1", "GO-2"])
    
    Returns:
        List of dicts with objective details
    """
    if not bu_names:
        return []
    
    conn = get_goals_db_connection()
    cursor = conn.cursor()
    
    all_objectives = []
    
    for bu_name in bu_names:
        table_name = get_bu_table_name(bu_name)
        
        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """, (table_name,))
        
        if not cursor.fetchone():
            logger.warning(f"BU table '{table_name}' not found in goals.db")
            continue
        
        # Fetch all objectives from this BU table
        cursor.execute(f"""
            SELECT id, parameter, goal, measure_of_success, 
                   linkage_to_thrust_area, linkage_to_group_objective
            FROM {table_name}
        """)
        
        for row in cursor.fetchall():
            obj_id = row[0]
            parameter = row[1]
            goal = row[2]
            measure_of_success = row[3]
            linkage_ta = row[4]
            linkage_go = row[5]
            
            # Split multi-line linkages
            obj_ta_codes = split_linkage_values(linkage_ta)
            obj_go_codes = split_linkage_values(linkage_go)
            
            # Filter by TA codes if provided (parent code matching)
            if ta_codes:
                # Extract parent codes from user's selection
                user_ta_parents = set()
                for ta in ta_codes:
                    # TA-1, TA-1a, TA-1b all become TA-1
                    import re
                    match = re.match(r'(TA-\d+)', ta)
                    if match:
                        user_ta_parents.add(match.group(1))
                
                # Check if any objective TA parent matches user's TA parents
                if not any(ta in user_ta_parents for ta in obj_ta_codes):
                    continue
            
            # Filter by GO codes if provided (parent code matching)
            if go_codes:
                # Extract parent codes from user's selection
                user_go_parents = set()
                for go in go_codes:
                    # GO-1, GO-1a, GO-1b all become GO-1
                    import re
                    match = re.match(r'(GO-\d+)', go)
                    if match:
                        user_go_parents.add(match.group(1))
                
                # Check if any objective GO parent matches user's GO parents
                if not any(go in user_go_parents for go in obj_go_codes):
                    continue
            
            all_objectives.append({
                'id': f"{table_name}_{obj_id}",  # Unique ID across all BU tables
                'bu_name': bu_name,
                'bu_table': table_name,
                'parameter': parameter,
                'goal_text': goal,
                'measure_of_success': measure_of_success,
                'thrust_areas': obj_ta_codes,
                'group_objectives': obj_go_codes,
                'thrust_area_str': ', '.join(obj_ta_codes),
                'group_objective_str': ', '.join(obj_go_codes)
            })
    
    conn.close()
    
    logger.info(f"Fetched {len(all_objectives)} objectives from goals.db")
    logger.info(f"  BUs: {bu_names}")
    logger.info(f"  TA filter: {ta_codes}")
    logger.info(f"  GO filter: {go_codes}")
    
    return all_objectives

def get_all_ta_codes():
    """Get all unique TA codes from thrust_areas table"""
    thrust_areas = get_thrust_areas()
    return sorted(list(set(ta['code'] for ta in thrust_areas)))

def get_all_go_codes():
    """Get all unique main GO codes (GO-1, GO-2, etc.)"""
    group_objectives = get_group_objectives()
    return sorted(list(set(go['code'] for go in group_objectives)))

def test_goals_db_connection():
    """Test connection to goals.db and print summary"""
    try:
        conn = get_goals_db_connection()
        cursor = conn.cursor()
        
        print(f"✅ Connected to goals.db at: {GOALS_DB_PATH}")
        
        # Get BU tables
        bu_tables = get_available_bu_tables()
        print(f"\n📊 Available BU Tables ({len(bu_tables)}):")
        for table in bu_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  - {table}: {count} objectives")
        
        # Get thrust areas
        tas = get_thrust_areas()
        print(f"\n🎯 Thrust Areas: {len(tas)}")
        for ta in tas[:5]:
            print(f"  - {ta['code']}: {ta['description'][:60]}...")
        
        # Get group objectives
        gos = get_group_objectives()
        print(f"\n📋 Group Objectives: {len(gos)}")
        for go in gos[:5]:
            print(f"  - {go['code']}: {go['description'][:60]}...")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to goals.db: {str(e)}")
        return False

if __name__ == "__main__":
    # Test the connection
    test_goals_db_connection()
