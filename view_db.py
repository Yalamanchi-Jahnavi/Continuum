#!/usr/bin/env python3
"""
Simple script to view the Continuum database contents
Usage: python view_db.py
"""
import sqlite3
import json
from datetime import datetime

DB = "db/continuum.db"

try:
    conn = sqlite3.connect(DB)
    cursor = conn.execute("SELECT id, step, output, goal, created_at FROM memory ORDER BY id")
    
    results = []
    for row in cursor.fetchall():
        results.append({
            "id": row[0],
            "step": row[1],
            "output": row[2] if row[2] else "",
            "goal": row[3] if row[3] else "N/A",
            "created_at": row[4] if row[4] else "N/A"
        })
    
    conn.close()
    
    print("\n" + "="*80)
    print("CONTINUUM DATABASE CONTENTS")
    print("="*80)
    print(f"\nTotal entries: {len(results)}\n")
    
    for i, result in enumerate(results, 1):
        print(f"\n[{i}] ID: {result['id']}")
        print(f"    Goal: {result['goal']}")
        print(f"    Step: {result['step'][:100]}..." if len(result['step']) > 100 else f"    Step: {result['step']}")
        print(f"    Output: {result['output'][:200]}..." if len(result['output']) > 200 else f"    Output: {result['output']}")
        print(f"    Created: {result['created_at']}")
        print("-" * 80)
    
    # Also save as JSON
    with open("db_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Results also saved to db_results.json")
    
except sqlite3.DatabaseError as e:
    print(f"❌ Database error: {e}")
    print("The database might be corrupted. You may need to delete db/continuum.db and restart.")
except Exception as e:
    print(f"❌ Error: {e}")

