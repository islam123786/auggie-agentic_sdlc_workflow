"""
Database migration script to update existing .state.db files to the new schema

This script adds the new columns to the tasks table:
- current_phase
- failed_at
- error_message
- UNIQUE constraint on task_id
- CHECK constraints on status and current_phase
"""

import sqlite3
import sys
from pathlib import Path


def migrate_database(db_path: str):
    """Migrate database to new schema"""
    
    print(f"🔄 Migrating database: {db_path}")
    
    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if migration is needed
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'current_phase' in columns:
            print("✅ Database is already up to date!")
            conn.close()
            return True
        
        print("📋 Backing up tasks table...")
        
        # Create backup of tasks table
        cursor.execute("""
            CREATE TABLE tasks_backup AS SELECT * FROM tasks
        """)
        
        # Drop old tasks table
        print("🗑️  Dropping old tasks table...")
        cursor.execute("DROP TABLE tasks")
        
        # Create new tasks table with updated schema
        print("🆕 Creating new tasks table with enhanced schema...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id TEXT NOT NULL,
                task_id TEXT NOT NULL UNIQUE,
                task_title TEXT,
                status TEXT CHECK(status IN ('running', 'completed', 'failed')),
                current_phase TEXT CHECK(current_phase IN ('implementation', 'testing', 'documentation', 'completed')),
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                failed_at TIMESTAMP,
                error_message TEXT,
                FOREIGN KEY (workflow_id) REFERENCES workflows(id)
            )
        """)
        
        # Migrate data from backup
        print("📊 Migrating existing task data...")
        cursor.execute("""
            INSERT INTO tasks (workflow_id, task_id, task_title, status, current_phase, started_at, completed_at)
            SELECT 
                workflow_id,
                task_id,
                task_title,
                CASE 
                    WHEN status = 'completed' THEN 'completed'
                    ELSE 'completed'  -- Default old tasks to completed
                END,
                CASE 
                    WHEN status = 'completed' THEN 'completed'
                    ELSE 'completed'  -- Default old tasks to completed phase
                END,
                started_at,
                completed_at
            FROM tasks_backup
        """)
        
        migrated_count = cursor.rowcount
        print(f"✅ Migrated {migrated_count} tasks")
        
        # Drop backup table
        print("🗑️  Cleaning up backup table...")
        cursor.execute("DROP TABLE tasks_backup")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print("✅ Migration completed successfully!")
        print()
        print("📝 Changes applied:")
        print("  ✅ Added 'current_phase' column")
        print("  ✅ Added 'failed_at' column")
        print("  ✅ Added 'error_message' column")
        print("  ✅ Added UNIQUE constraint on task_id")
        print("  ✅ Added CHECK constraints on status and current_phase")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print()
        print("⚠️  Attempting to restore from backup...")
        try:
            cursor.execute("DROP TABLE IF EXISTS tasks")
            cursor.execute("ALTER TABLE tasks_backup RENAME TO tasks")
            conn.commit()
            print("✅ Backup restored successfully")
        except Exception as restore_error:
            print(f"❌ Failed to restore backup: {restore_error}")
            print("⚠️  MANUAL INTERVENTION REQUIRED!")
        finally:
            conn.close()
        return False


def main():
    """Main migration function"""
    if len(sys.argv) < 2:
        print("Usage: python3 -m orchestrator.migrate_db <path_to_.state.db>")
        print()
        print("Example:")
        print("  python3 -m orchestrator.migrate_db /path/to/workspace/.state.db")
        sys.exit(1)
    
    db_path = sys.argv[1]
    
    print("╔" + "═"*68 + "╗")
    print("║" + " "*20 + "🔧 Database Migration Tool" + " "*22 + "║")
    print("╚" + "═"*68 + "╝")
    print()
    
    success = migrate_database(db_path)
    
    if success:
        print("🎉 Migration completed successfully!")
        print()
        print("💡 Next steps:")
        print("  1. Test the workflow with: python3 -m orchestrator.cli status --workspace <workspace>")
        print("  2. Resume failed workflows with: python3 -m orchestrator.cli resume --workspace <workspace>")
    else:
        print("❌ Migration failed. Please check the error messages above.")
        sys.exit(1)


if __name__ == '__main__':
    main()
