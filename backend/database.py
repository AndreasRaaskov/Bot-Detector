# database.py - SQLite database for bot detection analysis
# This module handles database initialization and operations for storing:
# - User metadata from Bluesky
# - DeepSeek LLM analysis results
# - Our bot detection analysis results

import sqlite3
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class BotDetectionDB:
    """
    Database manager for bot detection analysis data

    Stores user profiles, LLM analysis results, and bot detection scores
    for comparative analysis and tracking over time.
    """

    def __init__(self, db_path: str = "bot_detection.db"):
        """
        Initialize database connection

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.connection = None

    def connect(self):
        """Establish database connection"""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row  # Return rows as dictionaries
        logger.info(f"Connected to database: {self.db_path}")

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")

    @contextmanager
    def get_cursor(self):
        """Context manager for database cursor"""
        if not self.connection:
            self.connect()
        cursor = self.connection.cursor()
        try:
            yield cursor
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            cursor.close()

    def initialize_schema(self):
        """
        Create database tables if they don't exist

        Tables:
        - users: User profile metadata
        - deepseek_prompts: LLM prompt definitions
        - deepseek_analyses: LLM analysis results per user per prompt
        - bot_detection_results: Our bot detection analysis results
        """
        with self.get_cursor() as cursor:
            # Users table - stores Bluesky user metadata
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    handle TEXT PRIMARY KEY,
                    description TEXT,
                    following INTEGER,
                    followers INTEGER,
                    ratio REAL,
                    replies_pct REAL,
                    reposts_pct REAL,
                    originals_pct REAL,
                    total_posts INTEGER,
                    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # DeepSeek prompts table - definitions of different analysis prompts
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS deepseek_prompts (
                    name TEXT PRIMARY KEY,
                    description TEXT,
                    prompt_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # DeepSeek analyses table - results from LLM analyses
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS deepseek_analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    handle TEXT NOT NULL,
                    prompt_name TEXT NOT NULL,
                    assessment TEXT NOT NULL,
                    confidence INTEGER NOT NULL,
                    reasoning TEXT,
                    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (handle) REFERENCES users(handle),
                    FOREIGN KEY (prompt_name) REFERENCES deepseek_prompts(name),
                    UNIQUE(handle, prompt_name)
                )
            """)

            # Bot detection results table - our analysis results
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bot_detection_results (
                    handle TEXT PRIMARY KEY,
                    overall_score REAL NOT NULL,
                    confidence REAL NOT NULL,
                    follow_analysis_score REAL,
                    posting_pattern_score REAL,
                    text_analysis_score REAL,
                    llm_analysis_score REAL,
                    summary TEXT,
                    recommendations TEXT,
                    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (handle) REFERENCES users(handle)
                )
            """)

            # Create indices for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_deepseek_handle
                ON deepseek_analyses(handle)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_deepseek_prompt
                ON deepseek_analyses(prompt_name)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_bot_score
                ON bot_detection_results(overall_score)
            """)

            logger.info("Database schema initialized successfully")

    def insert_user(self, handle: str, metadata: Dict[str, Any]):
        """
        Insert or update user metadata

        Args:
            handle: Bluesky handle (primary key)
            metadata: Dictionary with user metadata fields
        """
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT OR REPLACE INTO users
                (handle, description, following, followers, ratio,
                 replies_pct, reposts_pct, originals_pct, total_posts, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                handle,
                metadata.get('description', ''),
                metadata.get('following', 0),
                metadata.get('followers', 0),
                metadata.get('ratio', 0.0),
                metadata.get('replies_pct', 0.0),
                metadata.get('reposts_pct', 0.0),
                metadata.get('originals_pct', 0.0),
                metadata.get('total_posts', 0)
            ))

    def insert_deepseek_analysis(self, handle: str, prompt_name: str,
                                  assessment: str, confidence: int, reasoning: str):
        """
        Insert DeepSeek analysis result

        Args:
            handle: User handle
            prompt_name: Name of the prompt used (e.g., 'prompt1')
            assessment: 'human' or 'ai_bot'
            confidence: Confidence score 0-100
            reasoning: Explanation text
        """
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT OR REPLACE INTO deepseek_analyses
                (handle, prompt_name, assessment, confidence, reasoning, analyzed_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (handle, prompt_name, assessment, confidence, reasoning))

    def insert_bot_detection_result(self, handle: str, result: Dict[str, Any]):
        """
        Insert bot detection analysis result

        Args:
            handle: User handle
            result: Dictionary with analysis results
        """
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT OR REPLACE INTO bot_detection_results
                (handle, overall_score, confidence, follow_analysis_score,
                 posting_pattern_score, text_analysis_score, llm_analysis_score,
                 summary, recommendations, analyzed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                handle,
                result.get('overall_score', 0.0),
                result.get('confidence', 0.0),
                result.get('follow_analysis_score', 0.0),
                result.get('posting_pattern_score', 0.0),
                result.get('text_analysis_score', 0.0),
                result.get('llm_analysis_score', 0.0),
                result.get('summary', ''),
                result.get('recommendations', '')
            ))

    def get_all_handles(self) -> List[str]:
        """Get list of all user handles in database"""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT handle FROM users ORDER BY handle")
            return [row['handle'] for row in cursor.fetchall()]

    def get_user(self, handle: str) -> Optional[Dict[str, Any]]:
        """Get user metadata by handle"""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE handle = ?", (handle,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_deepseek_analyses(self, handle: str) -> List[Dict[str, Any]]:
        """Get all DeepSeek analyses for a user"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM deepseek_analyses
                WHERE handle = ?
                ORDER BY prompt_name
            """, (handle,))
            return [dict(row) for row in cursor.fetchall()]

    def get_bot_detection_result(self, handle: str) -> Optional[Dict[str, Any]]:
        """Get bot detection result for a user"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM bot_detection_results WHERE handle = ?
            """, (handle,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        with self.get_cursor() as cursor:
            stats = {}

            # Total users
            cursor.execute("SELECT COUNT(*) as count FROM users")
            stats['total_users'] = cursor.fetchone()['count']

            # Total DeepSeek analyses
            cursor.execute("SELECT COUNT(*) as count FROM deepseek_analyses")
            stats['total_deepseek_analyses'] = cursor.fetchone()['count']

            # Total bot detection results
            cursor.execute("SELECT COUNT(*) as count FROM bot_detection_results")
            stats['total_bot_detections'] = cursor.fetchone()['count']

            # Average bot score
            cursor.execute("SELECT AVG(overall_score) as avg FROM bot_detection_results")
            stats['avg_bot_score'] = cursor.fetchone()['avg'] or 0.0

            return stats

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


if __name__ == "__main__":
    # Test database initialization
    logging.basicConfig(level=logging.INFO)

    db = BotDetectionDB("bot_detection.db")
    db.connect()
    db.initialize_schema()

    stats = db.get_statistics()
    print(f"Database statistics: {stats}")

    db.close()
