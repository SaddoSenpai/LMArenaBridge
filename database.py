"""
Database management for LMArena Bridge Dashboard
Handles token storage, usage tracking, and statistics
"""

import json
import os
import secrets
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
import requests

class DashboardDatabase:
    def __init__(self, db_file: str = "dashboard_data.json"):
        self.db_file = db_file
        self.data = self._load_data()
    
    def _load_data(self) -> Dict:
        """Load database from JSON file or create new if doesn't exist"""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return self._create_empty_db()
        return self._create_empty_db()
    
    def _create_empty_db(self) -> Dict:
        """Create empty database structure"""
        return {
            "tokens": {},
            "usage_logs": [],
            "stats": {
                "total_requests": 0,
                "total_tokens": 0,
                "active_tokens": 0
            }
        }
    
    def _save_data(self):
        """Save database to JSON file"""
        with open(self.db_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
    
    def generate_token(self, user_info: Optional[Dict] = None) -> str:
        """Generate a new API token"""
        token = f"lma_{secrets.token_urlsafe(32)}"
        token_id = hashlib.sha256(token.encode()).hexdigest()[:16]
        
        self.data["tokens"][token_id] = {
            "key": token,
            "created_at": datetime.now().isoformat(),
            "last_used": None,
            "is_active": True,
            "user_info": user_info or {},
            "usage_stats": {
                "total_requests": 0,
                "total_tokens": 0,
                "models_used": {},
                "ip_addresses": [],
                "countries": {}
            }
        }
        
        self.data["stats"]["active_tokens"] += 1
        self._save_data()
        return token
    
    def get_token_info(self, token: str) -> Optional[Dict]:
        """Get token information by token string"""
        token_id = hashlib.sha256(token.encode()).hexdigest()[:16]
        return self.data["tokens"].get(token_id)
    
    def get_token_by_id(self, token_id: str) -> Optional[Dict]:
        """Get token information by token ID"""
        return self.data["tokens"].get(token_id)
    
    def validate_token(self, token: str) -> bool:
        """Check if token is valid and active"""
        token_info = self.get_token_info(token)
        return token_info is not None and token_info.get("is_active", False)
    
    def revoke_token(self, token_id: str) -> bool:
        """Revoke a token"""
        if token_id in self.data["tokens"]:
            if self.data["tokens"][token_id]["is_active"]:
                self.data["stats"]["active_tokens"] -= 1
            self.data["tokens"][token_id]["is_active"] = False
            self._save_data()
            return True
        return False
    
    def activate_token(self, token_id: str) -> bool:
        """Activate a token"""
        if token_id in self.data["tokens"]:
            if not self.data["tokens"][token_id]["is_active"]:
                self.data["stats"]["active_tokens"] += 1
            self.data["tokens"][token_id]["is_active"] = True
            self._save_data()
            return True
        return False
    
    def delete_token(self, token_id: str) -> bool:
        """Permanently delete a token"""
        if token_id in self.data["tokens"]:
            if self.data["tokens"][token_id]["is_active"]:
                self.data["stats"]["active_tokens"] -= 1
            del self.data["tokens"][token_id]
            self._save_data()
            return True
        return False
    
    def log_usage(self, token: str, model: str, tokens_used: int, ip: str):
        """Log API usage"""
        token_id = hashlib.sha256(token.encode()).hexdigest()[:16]
        
        if token_id not in self.data["tokens"]:
            return
        
        # Get country from IP
        country = self._get_country_from_ip(ip)
        
        # Update token stats
        token_data = self.data["tokens"][token_id]
        token_data["last_used"] = datetime.now().isoformat()
        token_data["usage_stats"]["total_requests"] += 1
        token_data["usage_stats"]["total_tokens"] += tokens_used
        
        # Track model usage
        if model not in token_data["usage_stats"]["models_used"]:
            token_data["usage_stats"]["models_used"][model] = 0
        token_data["usage_stats"]["models_used"][model] += 1
        
        # Track IP addresses (keep last 100)
        if ip not in token_data["usage_stats"]["ip_addresses"]:
            token_data["usage_stats"]["ip_addresses"].append(ip)
            if len(token_data["usage_stats"]["ip_addresses"]) > 100:
                token_data["usage_stats"]["ip_addresses"].pop(0)
        
        # Track countries
        if country:
            if country not in token_data["usage_stats"]["countries"]:
                token_data["usage_stats"]["countries"][country] = 0
            token_data["usage_stats"]["countries"][country] += 1
        
        # Add to usage logs (keep last 10000)
        self.data["usage_logs"].append({
            "timestamp": datetime.now().isoformat(),
            "token_id": token_id,
            "model": model,
            "tokens": tokens_used,
            "ip": ip,
            "country": country
        })
        
        if len(self.data["usage_logs"]) > 10000:
            self.data["usage_logs"] = self.data["usage_logs"][-10000:]
        
        # Update global stats
        self.data["stats"]["total_requests"] += 1
        self.data["stats"]["total_tokens"] += tokens_used
        
        self._save_data()
    
    def _get_country_from_ip(self, ip: str) -> Optional[str]:
        """Get country from IP address using ip-api.com"""
        if ip in ["127.0.0.1", "localhost", "::1"]:
            return "Local"
        
        try:
            response = requests.get(f"http://ip-api.com/json/{ip}?fields=country", timeout=2)
            if response.status_code == 200:
                data = response.json()
                return data.get("country", "Unknown")
        except:
            pass
        return "Unknown"
    
    def get_all_tokens(self) -> Dict:
        """Get all tokens"""
        return self.data["tokens"]
    
    def get_active_token_count(self) -> int:
        """Get count of active tokens"""
        return self.data["stats"]["active_tokens"]
    
    def get_global_stats(self) -> Dict:
        """Get global statistics"""
        return self.data["stats"]
    
    def get_recent_usage(self, limit: int = 100) -> List[Dict]:
        """Get recent usage logs"""
        return self.data["usage_logs"][-limit:]
    
    def get_token_usage_by_model(self, token_id: str) -> Dict:
        """Get model usage breakdown for a token"""
        if token_id in self.data["tokens"]:
            return self.data["tokens"][token_id]["usage_stats"]["models_used"]
        return {}
    
    def get_token_usage_by_country(self, token_id: str) -> Dict:
        """Get country usage breakdown for a token"""
        if token_id in self.data["tokens"]:
            return self.data["tokens"][token_id]["usage_stats"]["countries"]
        return {}
    
    def get_usage_timeline(self, token_id: Optional[str] = None, days: int = 7) -> List[Dict]:
        """Get usage timeline for charts"""
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        timeline = {}
        for log in self.data["usage_logs"]:
            log_date = datetime.fromisoformat(log["timestamp"])
            if log_date < cutoff_date:
                continue
            
            if token_id and log["token_id"] != token_id:
                continue
            
            date_key = log_date.strftime("%Y-%m-%d")
            if date_key not in timeline:
                timeline[date_key] = {"requests": 0, "tokens": 0}
            
            timeline[date_key]["requests"] += 1
            timeline[date_key]["tokens"] += log["tokens"]
        
        return [{"date": k, **v} for k, v in sorted(timeline.items())]
