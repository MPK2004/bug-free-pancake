import sqlite3
import json
import os
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "chat_history.db")

class DBManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._initialize_db()

    @contextmanager
    def get_connection(self):
        """
        Thread-safe context manager for SQLite connections.
        Ensures WAL mode and Foreign Keys are enabled.
        """
        conn = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA foreign_keys = ON;")
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _initialize_db(self):
        with self.get_connection() as conn:
            # 1. Users
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 2. Threads
            conn.execute("""
                CREATE TABLE IF NOT EXISTS threads (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            # 3. Snapshots (Immutable State)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    thread_id TEXT NOT NULL,
                    step_index INTEGER NOT NULL,
                    narrative TEXT,
                    data_ledger JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(thread_id) REFERENCES threads(id) ON DELETE CASCADE
                )
            """)

            # 4. Messages (Event Stream)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    thread_id TEXT NOT NULL,
                    role TEXT CHECK(role IN ('system', 'user', 'assistant', 'tool')),
                    content TEXT NOT NULL,
                    meta_data JSON,
                    step_index INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(thread_id) REFERENCES threads(id) ON DELETE CASCADE
                )
            """)

            # Indices for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_thread_order ON messages(thread_id, step_index);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_thread_step ON snapshots(thread_id, step_index);")

    # --- CRUD Operations ---

    def ensure_user(self, user_id):
        with self.get_connection() as conn:
            conn.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (user_id,))

    def create_thread(self, thread_id, user_id, title=None):
        self.ensure_user(user_id)
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO threads (id, user_id, title) VALUES (?, ?, ?)",
                (thread_id, user_id, title)
            )

    def save_message(self, thread_id, role, content, step_index, meta_data=None):
        with self.get_connection() as conn:
            conn.execute(
                """INSERT INTO messages (thread_id, role, content, step_index, meta_data) 
                   VALUES (?, ?, ?, ?, ?)""",
                (thread_id, role, content, step_index, json.dumps(meta_data) if meta_data else None)
            )

    def save_snapshot(self, thread_id, step_index, narrative, data_ledger):
        with self.get_connection() as conn:
            conn.execute(
                """INSERT INTO snapshots (thread_id, step_index, narrative, data_ledger) 
                   VALUES (?, ?, ?, ?)""",
                (thread_id, step_index, narrative, json.dumps(data_ledger) if data_ledger else None)
            )

    def get_thread_messages(self, thread_id):
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT role, content, meta_data, step_index FROM messages WHERE thread_id = ? ORDER BY step_index ASC, id ASC",
                (thread_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_latest_snapshot(self, thread_id):
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT narrative, data_ledger, step_index FROM snapshots WHERE thread_id = ? ORDER BY step_index DESC LIMIT 1",
                (thread_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_user_threads(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT id, title, created_at FROM threads WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def delete_thread(self, thread_id):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM threads WHERE id = ?", (thread_id,))
