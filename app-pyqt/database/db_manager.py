import sqlite3
from datetime import datetime
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

class DatabaseManager:
    def __init__(self, db_path: str):
        """
        Initialize database manager
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        """Initialize database tables if they don't exist"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create analysis results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_path TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    colony_count INTEGER NOT NULL,
                    results_json TEXT NOT NULL,
                    notes TEXT
                )
            ''')
            
            # Create settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            ''')
            
            conn.commit()
    
    def save_analysis(self, image_path: str, results: Dict[str, Any], notes: Optional[str] = None) -> int:
        """
        Save analysis results to database
        
        Args:
            image_path: Path to analyzed image
            results: Dictionary containing analysis results
            notes: Optional notes about the analysis
            
        Returns:
            ID of the inserted record
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO analysis_results (
                    image_path,
                    timestamp,
                    colony_count,
                    results_json,
                    notes
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                image_path,
                datetime.now().isoformat(),
                results['count'],
                json.dumps(results),
                notes
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def get_analysis(self, analysis_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve analysis results by ID
        
        Args:
            analysis_id: ID of the analysis record
            
        Returns:
            Dictionary containing analysis results or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT image_path, timestamp, colony_count, results_json, notes
                FROM analysis_results
                WHERE id = ?
            ''', (analysis_id,))
            
            row = cursor.fetchone()
            if row is None:
                return None
                
            return {
                'image_path': row[0],
                'timestamp': datetime.fromisoformat(row[1]),
                'colony_count': row[2],
                'results': json.loads(row[3]),
                'notes': row[4]
            }
    
    def get_recent_analyses(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most recent analysis results
        
        Args:
            limit: Maximum number of results to return
            
        Returns:
            List of analysis result dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, image_path, timestamp, colony_count, notes
                FROM analysis_results
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            return [{
                'id': row[0],
                'image_path': row[1],
                'timestamp': datetime.fromisoformat(row[2]),
                'colony_count': row[3],
                'notes': row[4]
            } for row in cursor.fetchall()]
    
    def save_setting(self, key: str, value: Any):
        """Save a setting to the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO settings (key, value)
                VALUES (?, ?)
            ''', (key, json.dumps(value)))
            
            conn.commit()
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting from the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
            row = cursor.fetchone()
            
            if row is None:
                return default
            
            return json.loads(row[0])
