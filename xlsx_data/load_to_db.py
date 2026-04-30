#!/usr/bin/env python3
"""
Excel -> SQLite Loader for BU Goals Data

Tables created:
  thrust_areas      <- THRUST_AREAS.xlsx
  group_objectives  <- GORUP_OBJECTIVES.xlsx
  <BU_NAME>         <- *_GOALS.xlsx  (one table per BU)

Usage:
  python load_to_db.py
  python load_to_db.py --dir /path/to/files --db goals.db

Dependencies:
  pip install pandas openpyxl
"""

import argparse
import re
import sqlite3
from pathlib import Path

import pandas as pd


def clean_col(name):
    s = str(name).strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


def bu_name_from_filename(filepath):
    stem = Path(filepath).stem
    name = re.sub(r"[_-]?GOALS$", "", stem, flags=re.IGNORECASE)
    name = re.sub(r"[-\s]+", "_", name)
    name = re.sub(r"[^A-Za-z0-9_]", "", name)
    return name.upper()


def is_junk_row(row):
    values = [str(v).strip() for v in row if pd.notna(v) and str(v).strip()]
    if not values:
        return True
    return bool(re.search(r"Times New Roman|Page &P|&\d{2}|&[A-Z]$", " ".join(values)))


def find_col(cols, keywords):
    for kw in keywords:
        for col in cols:
            if kw in col:
                return col
    return None


def detect_header_row(filepath, keywords, exact=False, max_scan=12):
    """
    exact=True  - keyword must equal a full cell value.
                  Use when keyword could be substring of a non-header cell,
                  e.g. 'goal' inside 'Goal Sheet Owner: SC'
                       'objective' inside 'Group Objectives FY27'
    exact=False - keyword may appear as a substring of any cell value.
    """
    df = pd.read_excel(filepath, header=None, dtype=str, nrows=max_scan).fillna("")
    for i, row in df.iterrows():
        vals = [str(v).strip().lower() for v in row]
        if exact:
            if any(kw in vals for kw in keywords):
                return int(i)
        else:
            if any(kw in vals or any(kw in v for v in vals) for kw in keywords):
                return int(i)
    return 0


def load_thrust_areas(filepath, conn):
    df = pd.read_excel(filepath, header=None, dtype=str).fillna("")
    conn.execute("DROP TABLE IF EXISTS thrust_areas")
    conn.execute("""
        CREATE TABLE thrust_areas (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            thrust_area_code  TEXT NOT NULL,
            thrust_area_name  TEXT NOT NULL,
            sub_code          TEXT NOT NULL,
            description       TEXT NOT NULL
        )""")

    current_code, current_name, rows = "", "", 0
    for _, row in df.iterrows():
        if is_junk_row(row):
            continue
        col0 = str(row.iloc[0]).strip()
        col1 = str(row.iloc[1]).strip() if len(row) > 1 else ""
        if not col0 and not col1:
            continue
        if re.match(r"^TA[-\s]?\d+$", col0, re.IGNORECASE):
            current_code = re.sub(r"\s+", "-", col0).upper()
            current_name = col1
        elif col0 and current_code:
            conn.execute(
                "INSERT INTO thrust_areas (thrust_area_code, thrust_area_name, sub_code, description) "
                "VALUES (?, ?, ?, ?)",
                (current_code, current_name, col0, col1))
            rows += 1

    conn.commit()
    return rows


def load_group_objectives(filepath, conn):
    """
    GORUP_OBJECTIVES.xlsx layout:
      Row 0: [empty, empty, 'Group Objectives FY27']   <- title, NOT header
      Row 1: [empty, empty, empty]
      Row 2: ['S No', 'Parameter', 'Group Objectives'] <- REAL header
      Row 3+: data (merged cells forward-filled)

    Uses exact=True: 'objective' in 'Group Objectives FY27' would be a
    false match with exact=False.
    """
    header_row = detect_header_row(
        filepath, keywords=["parameter", "s no"], exact=True
    )
    df = pd.read_excel(filepath, header=header_row, dtype=str).fillna("")
    df = df[~df.apply(is_junk_row, axis=1)].reset_index(drop=True)
    df.columns = [clean_col(c) for c in df.columns]

    sno_col   = find_col(df.columns.tolist(), ["s_no", "_no", "sno"])
    param_col = find_col(df.columns.tolist(), ["parameter", "param"])
    obj_col   = find_col(df.columns.tolist(), ["objective", "group_obj"])

    conn.execute("DROP TABLE IF EXISTS group_objectives")
    conn.execute("""
        CREATE TABLE group_objectives (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            s_no       TEXT,
            parameter  TEXT,
            objective  TEXT NOT NULL
        )""")

    skip = {"group objectives", "objectives", "nan", "none", ""}
    last_sno, last_param, rows = "", "", 0

    for _, row in df.iterrows():
        if is_junk_row(row):
            continue
        sno   = str(row[sno_col]).strip()   if sno_col   else ""
        param = str(row[param_col]).strip() if param_col else ""
        obj   = str(row[obj_col]).strip()   if obj_col   else ""

        if obj.lower() in skip:
            continue
        if sno and sno.lower() not in {"nan", "none", ""}:
            last_sno = sno
        if param and param.lower() not in {"nan", "none", ""}:
            last_param = param
        if not obj or obj.lower() in {"nan", "none"}:
            continue

        conn.execute(
            "INSERT INTO group_objectives (s_no, parameter, objective) VALUES (?, ?, ?)",
            (last_sno, last_param, obj))
        rows += 1

    conn.commit()
    return rows


def load_bu_goals(filepath, table_name, conn):
    """
    All BU files share this structure:
      Row 0: BU title  e.g. 'EPS Goals FY27'
      Row 1: 'Goal Sheet Owner: <name>'  <- 'goal' appears here as SUBSTRING
      Row 2: blank / sub-header
      Row 3: 'Parameter' | 'Goal' | 'Measure of Success' | ... <- REAL header

    Uses exact=True so 'goal' must be a complete cell value,
    preventing 'Goal Sheet Owner: SC' from being treated as the header.
    """
    header_row = detect_header_row(
        filepath, keywords=["goals", "goal", "parameter"], exact=True
    )
    df = pd.read_excel(filepath, header=header_row, dtype=str).fillna("")
    df = df[~df.apply(is_junk_row, axis=1)].reset_index(drop=True)
    df.columns = [clean_col(c) for c in df.columns]
    cols = df.columns.tolist()

    sno_col     = find_col(cols, ["s_no", "sno"])
    param_col   = find_col(cols, ["parameter", "param"])
    goal_col    = find_col(cols, ["goal"])
    measure_col = find_col(cols, ["measure"])
    ta_col      = find_col(cols, ["thrust", "linkage_to_t", "_ta"])
    go_col      = find_col(cols, ["group", "linkage_to_g", "_go", "linkage_g"])

    conn.execute(f'DROP TABLE IF EXISTS "{table_name}"')
    conn.execute(f"""
        CREATE TABLE "{table_name}" (
            id                          INTEGER PRIMARY KEY AUTOINCREMENT,
            parameter                   TEXT,
            goal                        TEXT NOT NULL,
            measure_of_success          TEXT,
            linkage_to_thrust_area      TEXT,
            linkage_to_group_objective  TEXT
        )""")

    skip_goals = {"goal", "goals", "nan", "none", ""}
    last_param, rows = "", 0

    for _, row in df.iterrows():
        goal = str(row[goal_col]).strip() if goal_col else ""
        if not goal or goal.lower() in skip_goals:
            continue

        param = ""
        if param_col:
            param = str(row[param_col]).strip()
        elif sno_col:
            param = str(row[sno_col]).strip()
        if param and param.lower() not in {"nan", "none", ""}:
            last_param = param

        def safe(col):
            if col is None: return ""
            v = str(row[col]).strip()
            return "" if v.lower() in {"nan", "none"} else v

        conn.execute(
            f'INSERT INTO "{table_name}" '
            "(parameter, goal, measure_of_success, "
            " linkage_to_thrust_area, linkage_to_group_objective) "
            "VALUES (?, ?, ?, ?, ?)",
            (last_param, goal, safe(measure_col), safe(ta_col), safe(go_col)))
        rows += 1

    conn.commit()
    return rows


def main():
    parser = argparse.ArgumentParser(
        description="Load BU Goals Excel files into a SQLite database."
    )
    parser.add_argument("--dir", default="./",
                        help="Directory with xlsx files (default: current dir)")
    parser.add_argument("--db",  default="goals.db",
                        help="Output SQLite db filename (default: goals.db)")
    args = parser.parse_args()

    excel_dir = Path(args.dir)
    if not excel_dir.exists():
        print(f"ERROR: Directory not found: {excel_dir.resolve()}")
        raise SystemExit(1)

    conn = sqlite3.connect(args.db)
    print(f"Database : {args.db}")
    print(f"Source   : {excel_dir.resolve()}\n")

    # 1. Thrust Areas — pick largest file when DB exports are also present
    ta_files = sorted(
        [f for f in excel_dir.glob("*.xlsx")
         if re.search(r"thrust.?area", f.name, re.IGNORECASE)],
        key=lambda x: -x.stat().st_size
    )
    if ta_files:
        f = ta_files[0]
        print(f"[thrust_areas]      <- {f.name}")
        print(f"                       {load_thrust_areas(str(f), conn)} rows inserted\n")
    else:
        print("WARNING: No THRUST_AREAS.xlsx found\n")

    # 2. Group Objectives — pick largest file
    go_files = sorted(
        [f for f in excel_dir.glob("*.xlsx")
         if re.search(r"OBJEC", f.name, re.IGNORECASE)],
        key=lambda x: -x.stat().st_size
    )
    if go_files:
        f = go_files[0]
        print(f"[group_objectives]  <- {f.name}")
        print(f"                       {load_group_objectives(str(f), conn)} rows inserted\n")
    else:
        print("WARNING: No Group Objectives xlsx found\n")

    # 3. BU Goals
    seen, bu_files = set(), []
    for f in sorted(excel_dir.glob("*.xlsx")):
        if re.search(r"_GOALS\.xlsx$", f.name, re.IGNORECASE) and f.stem not in seen:
            seen.add(f.stem)
            bu_files.append(f)

    if bu_files:
        print("BU Goals:")
        for f in bu_files:
            bu = bu_name_from_filename(f.name)
            print(f"  [{bu:<28}] <- {f.name}")
            try:
                n = load_bu_goals(str(f), bu, conn)
                print(f"  {'':28}   {n} rows inserted")
            except Exception as e:
                print(f"  {'':28}   ERROR: {e}")
    else:
        print("WARNING: No *_GOALS.xlsx files found")

    # 4. Summary
    print("\n" + "-" * 58)
    print(f"  {'Table':<35} {'Rows':>8}")
    print("-" * 58)
    total = 0
    for (tbl,) in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name != 'sqlite_sequence' ORDER BY name"
    ).fetchall():
        count = conn.execute(f'SELECT COUNT(*) FROM "{tbl}"').fetchone()[0]
        total += count
        print(f"  {tbl:<35} {count:>8,}")
    print("-" * 58)
    print(f"  {'TOTAL':<35} {total:>8,}")
    print(f"\nDone. Database written to: {args.db}")
    conn.close()


if __name__ == "__main__":
    main()