# src/database/audit_log.py

import sqlite3
import json
from datetime import datetime
from typing import Dict, Optional, List
import os

class AuditLogger:
    """
    Logs order decisions to a SQLite database (compatible with Turso).
    Includes PII masking for privacy compliance.
    """
    
    def __init__(self, db_path: str = "audit_log.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Create the audit_logs table if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                validation_passed BOOLEAN,
                risk_level TEXT,
                risk_score REAL,
                routing_warehouse TEXT,
                estimated_days INTEGER,
                decision_reason TEXT,
                pii_masked BOOLEAN DEFAULT TRUE
            )
        ''')
        
        conn.commit()
        conn.close()

    @staticmethod
    def mask_pii(data: Dict) -> Dict:
        """
        Simple helper to mask PII fields (phone, email).
        """
        if isinstance(data, dict):
            masked = {}
            for key, value in data.items():
                if key in ['phone', 'email']:
                    masked[key] = "***MASKED***"
                else:
                    masked[key] = value
            return masked
        return data

    def log_order(self, order_id: str, validation_result: Dict, routing_result: Dict):
        """
        Saves an order decision record to the database.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Determine validation status
        is_valid = validation_result.get("is_valid", False)
        
        # Determine risk info
        risk_level = validation_result.get("risk_level", "LOW")
        risk_score = validation_result.get("risk_score", 0.0)
        
        # Determine routing info
        warehouse = routing_result.get("warehouse_id", "N/A")
        est_days = routing_result.get("estimated_delivery_days", 0)
        
        # Reason for decision
        if is_valid:
            reason = "AUTO_APPROVED"
        else:
            reason = "; ".join(validation_result.get("errors", ["UNKNOWN_ERROR"]))

        cursor.execute('''
            INSERT INTO audit_logs (
                order_id, validation_passed, risk_level, risk_score,
                routing_warehouse, estimated_days, decision_reason, pii_masked
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            order_id, is_valid, risk_level, risk_score,
            warehouse, est_days, reason, True
        ))
        
        conn.commit()
        conn.close()
        
        return f"Audit log saved for order {order_id}"

    def get_logs(self, limit: int = 10) -> List[Dict]:
        """
        Retrieves recent audit logs.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]