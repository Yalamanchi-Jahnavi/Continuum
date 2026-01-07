import sqlite3
import os
import shutil
from datetime import datetime

DB = "db/continuum.db"

def init_db():
    """Initialize database, handling corruption by recreating if needed"""
    os.makedirs("db", exist_ok=True)
    
    # Check if database exists and is valid
    db_exists = os.path.exists(DB)
    needs_recreate = False
    
    if db_exists:
        conn = None
        try:
            # Try to open and query the database to check if it's valid
            conn = sqlite3.connect(DB)
            result = conn.execute("PRAGMA integrity_check").fetchone()
            if result and result[0] != 'ok':
                raise sqlite3.DatabaseError("Database integrity check failed")
        except (sqlite3.DatabaseError, sqlite3.OperationalError):
            # Database is corrupted, try to backup and recreate
            if conn:
                conn.close()
                conn = None
            # Wait a moment and try to close any lingering connections
            import time
            time.sleep(0.1)
            backup_path = f"{DB}.corrupted.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            try:
                shutil.move(DB, backup_path)
                print(f"⚠️  Database corrupted. Backed up to {backup_path}")
                needs_recreate = True
            except (PermissionError, OSError) as e:
                # File might be locked by another process (e.g., database viewer)
                print(f"⚠️  Database may be corrupted but file is locked.")
                print(f"   Please close any programs using {DB} and restart the server.")
                # Continue anyway - SQLite will handle errors when we try to use it
                needs_recreate = False
        finally:
            if conn:
                conn.close()
    
    # Create or recreate database if needed
    if needs_recreate or not db_exists:
        db_exists = False
    
    conn = sqlite3.connect(DB)
    
    if not db_exists:
        # Create new table with all columns
        conn.execute("""
        CREATE TABLE memory (
            id INTEGER PRIMARY KEY,
            step TEXT,
            output TEXT,
            goal TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        # Create stats table
        conn.execute("""
        CREATE TABLE execution_stats (
            id INTEGER PRIMARY KEY,
            goal TEXT UNIQUE,
            planning INTEGER DEFAULT 0,
            execution INTEGER DEFAULT 0,
            evaluation INTEGER DEFAULT 0,
            self_correction INTEGER DEFAULT 0,
            total_calls INTEGER DEFAULT 0,
            execution_time_seconds REAL,
            execution_time_formatted TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
    else:
        # Check if goal column exists
        try:
            cursor = conn.execute("PRAGMA table_info(memory)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'goal' not in columns:
                conn.execute("ALTER TABLE memory ADD COLUMN goal TEXT")
            
            if 'created_at' not in columns:
                conn.execute("ALTER TABLE memory ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        except sqlite3.OperationalError:
            # Table might not exist, create it
            conn.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                id INTEGER PRIMARY KEY,
                step TEXT,
                output TEXT,
                goal TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
        
        # Create stats table if it doesn't exist
        try:
            conn.execute("SELECT 1 FROM execution_stats LIMIT 1")
        except sqlite3.OperationalError:
            conn.execute("""
            CREATE TABLE execution_stats (
                id INTEGER PRIMARY KEY,
                goal TEXT UNIQUE,
                planning INTEGER DEFAULT 0,
                execution INTEGER DEFAULT 0,
                evaluation INTEGER DEFAULT 0,
                self_correction INTEGER DEFAULT 0,
                total_calls INTEGER DEFAULT 0,
                execution_time_seconds REAL,
                execution_time_formatted TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
    
    conn.commit()
    conn.close()

def save(step, output, goal=None):
    try:
        conn = sqlite3.connect(DB)
        conn.execute("INSERT INTO memory(step, output, goal) VALUES (?,?,?)", (step, output, goal))
        conn.commit()
        conn.close()
    except sqlite3.DatabaseError:
        # Database corrupted, reinitialize
        init_db()
        conn = sqlite3.connect(DB)
        conn.execute("INSERT INTO memory(step, output, goal) VALUES (?,?,?)", (step, output, goal))
        conn.commit()
        conn.close()

def get_all(goal=None):
    try:
        conn = sqlite3.connect(DB)
        if goal:
            cursor = conn.execute("SELECT step, output, created_at FROM memory WHERE goal = ? ORDER BY id", (goal,))
        else:
            cursor = conn.execute("SELECT step, output, created_at FROM memory ORDER BY id")
        results = []
        for row in cursor.fetchall():
            results.append({
                "step": row[0],
                "output": row[1],
                "created_at": row[2] if row[2] else None
            })
        conn.close()
        return results
    except sqlite3.DatabaseError:
        # Database corrupted, return empty results
        return []

def get_execution_time_for_goal(goal):
    """Get the time range for a goal's execution"""
    try:
        conn = sqlite3.connect(DB)
        cursor = conn.execute("""
            SELECT MIN(created_at) as start_time, MAX(created_at) as end_time, COUNT(*) as step_count
            FROM memory 
            WHERE goal = ?
        """, (goal,))
        row = cursor.fetchone()
        conn.close()
        if row and row[0] and row[1]:
            from datetime import datetime
            start = datetime.fromisoformat(row[0]) if isinstance(row[0], str) else row[0]
            end = datetime.fromisoformat(row[1]) if isinstance(row[1], str) else row[1]
            if isinstance(start, datetime) and isinstance(end, datetime):
                duration = (end - start).total_seconds()
                return {
                    "start_time": start.isoformat(),
                    "end_time": end.isoformat(),
                    "duration_seconds": round(duration, 2),
                    "step_count": row[2]
                }
        return None
    except Exception as e:
        return None

def get_latest_goal():
    try:
        conn = sqlite3.connect(DB)
        cursor = conn.execute("SELECT DISTINCT goal FROM memory WHERE goal IS NOT NULL ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    except sqlite3.DatabaseError:
        return None

def get_all_goals():
    """Get all unique goals with their metadata"""
    try:
        conn = sqlite3.connect(DB)
        cursor = conn.execute("""
            SELECT DISTINCT goal, 
                   COUNT(*) as step_count,
                   MIN(created_at) as first_created,
                   MAX(created_at) as last_created
            FROM memory 
            WHERE goal IS NOT NULL 
            GROUP BY goal
            ORDER BY MAX(id) DESC
        """)
        goals = []
        for row in cursor.fetchall():
            goal = row[0]
            step_count = row[1]
            stats = get_execution_stats(goal)
            execution_time = stats["execution_time"] if stats else None
            
            goals.append({
                "goal": goal,
                "step_count": step_count,
                "first_created": row[2],
                "last_created": row[3],
                "execution_time": execution_time,
                "api_statistics": {
                    "planning": stats["planning"] if stats else 0,
                    "execution": stats["execution"] if stats else 0,
                    "evaluation": stats["evaluation"] if stats else 0,
                    "self_correction": stats["self_correction"] if stats else 0,
                    "total": stats["total"] if stats else 0
                } if stats else None
            })
        conn.close()
        return goals
    except sqlite3.DatabaseError:
        return []

def save_execution_stats(goal, stats, execution_time_seconds, execution_time_formatted):
    """Save execution statistics for a goal"""
    try:
        conn = sqlite3.connect(DB)
        conn.execute("""
            INSERT OR REPLACE INTO execution_stats 
            (goal, planning, execution, evaluation, self_correction, total_calls, execution_time_seconds, execution_time_formatted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            goal,
            stats.get('planning', 0),
            stats.get('execution', 0),
            stats.get('evaluation', 0),
            stats.get('self_correction', 0),
            sum(stats.values()),
            execution_time_seconds,
            execution_time_formatted
        ))
        conn.commit()
        conn.close()
    except sqlite3.DatabaseError:
        pass

def get_execution_stats(goal):
    """Get execution statistics for a goal"""
    try:
        conn = sqlite3.connect(DB)
        cursor = conn.execute("""
            SELECT planning, execution, evaluation, self_correction, total_calls, 
                   execution_time_seconds, execution_time_formatted
            FROM execution_stats 
            WHERE goal = ?
        """, (goal,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "planning": row[0],
                "execution": row[1],
                "evaluation": row[2],
                "self_correction": row[3],
                "total": row[4],
                "execution_time": {
                    "seconds": row[5],
                    "formatted": row[6]
                }
            }
        return None
    except sqlite3.DatabaseError:
        return None
