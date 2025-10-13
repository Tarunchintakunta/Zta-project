"""
Identity and Access Management (IAM) component for ZTA
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from models.user import User


class IdentityManager:
    """Manages user identities and authentication"""
    
    def __init__(self):
        self.users = {}
        self.active_sessions = {}
        self.authentication_logs = []
        self.session_timeout = 30  # minutes
        
    def register_user(self, user: User):
        """Register a user in the identity system"""
        self.users[user.user_id] = user
    
    def authenticate_user(self, user_id: str, password: str, mfa_code: str = None,
                         context: Dict = None) -> Dict:
        """Authenticate a user with context-aware validation"""
        timestamp = datetime.now()
        
        if user_id not in self.users:
            self._log_authentication(user_id, False, 'User not found', context)
            return {
                'success': False,
                'reason': 'User not found',
                'session_token': None
            }
        
        user = self.users[user_id]
        
        # Check if user is active
        if not user.is_active:
            self._log_authentication(user_id, False, 'User account disabled', context)
            return {
                'success': False,
                'reason': 'User account disabled',
                'session_token': None
            }
        
        # Check failed login attempts
        if user.failed_login_attempts >= 3:
            self._log_authentication(user_id, False, 'Account locked due to failed attempts', context)
            return {
                'success': False,
                'reason': 'Account locked - too many failed attempts',
                'session_token': None
            }
        
        # Perform authentication
        auth_success = user.authenticate(password, mfa_code)
        
        if auth_success:
            # Create session token
            session_token = self._create_session(user_id, context)
            self._log_authentication(user_id, True, 'Authentication successful', context)
            
            return {
                'success': True,
                'reason': 'Authentication successful',
                'session_token': session_token,
                'user_info': user.get_user_info()
            }
        else:
            user.update_risk_score('failed_login')
            self._log_authentication(user_id, False, 'Invalid credentials', context)
            
            return {
                'success': False,
                'reason': 'Invalid credentials',
                'session_token': None
            }
    
    def _create_session(self, user_id: str, context: Dict = None) -> str:
        """Create a new session for authenticated user"""
        session_token = secrets.token_hex(32)
        expiry = datetime.now() + timedelta(minutes=self.session_timeout)
        
        self.active_sessions[session_token] = {
            'user_id': user_id,
            'created_at': datetime.now(),
            'expires_at': expiry,
            'context': context or {},
            'last_activity': datetime.now()
        }
        
        return session_token
    
    def validate_session(self, session_token: str) -> Dict:
        """Validate an active session"""
        if session_token not in self.active_sessions:
            return {
                'valid': False,
                'reason': 'Session not found'
            }
        
        session = self.active_sessions[session_token]
        
        # Check expiry
        if datetime.now() > session['expires_at']:
            del self.active_sessions[session_token]
            return {
                'valid': False,
                'reason': 'Session expired'
            }
        
        # Update last activity
        session['last_activity'] = datetime.now()
        
        return {
            'valid': True,
            'user_id': session['user_id'],
            'session_info': session
        }
    
    def terminate_session(self, session_token: str):
        """Terminate a user session"""
        if session_token in self.active_sessions:
            del self.active_sessions[session_token]
    
    def continuous_authentication(self, session_token: str, behavior_data: Dict) -> bool:
        """Perform continuous authentication based on user behavior"""
        session_validation = self.validate_session(session_token)
        
        if not session_validation['valid']:
            return False
        
        user_id = session_validation['user_id']
        user = self.users.get(user_id)
        
        if not user:
            return False
        
        # Analyze behavior for anomalies
        anomaly_score = self._calculate_anomaly_score(user, behavior_data)
        
        if anomaly_score > 0.7:  # High anomaly
            user.update_risk_score('anomalous_access')
            self.terminate_session(session_token)
            return False
        
        return True
    
    def _calculate_anomaly_score(self, user: User, behavior_data: Dict) -> float:
        """Calculate anomaly score based on user behavior"""
        import random
        
        # Simplified anomaly detection
        # In real implementation, this would use ML models
        anomaly_factors = []
        
        # Check location anomaly
        if behavior_data.get('location') != user.location:
            anomaly_factors.append(0.3)
        
        # Check time anomaly (accessing outside normal hours)
        current_hour = datetime.now().hour
        if current_hour < 6 or current_hour > 22:
            anomaly_factors.append(0.2)
        
        # Check access pattern anomaly
        if behavior_data.get('unusual_resource_access'):
            anomaly_factors.append(0.4)
        
        # Add some randomness for simulation
        base_anomaly = sum(anomaly_factors) if anomaly_factors else 0
        return min(1.0, base_anomaly + random.uniform(0, 0.2))
    
    def _log_authentication(self, user_id: str, success: bool, reason: str, context: Dict):
        """Log authentication attempt"""
        self.authentication_logs.append({
            'timestamp': datetime.now(),
            'user_id': user_id,
            'success': success,
            'reason': reason,
            'context': context or {}
        })
    
    def get_authentication_stats(self) -> Dict:
        """Get authentication statistics"""
        total_attempts = len(self.authentication_logs)
        successful = sum(1 for log in self.authentication_logs if log['success'])
        failed = total_attempts - successful
        
        return {
            'total_attempts': total_attempts,
            'successful': successful,
            'failed': failed,
            'success_rate': successful / total_attempts if total_attempts > 0 else 0,
            'active_sessions': len(self.active_sessions)
        }
    
    def get_user_risk_distribution(self) -> Dict:
        """Get distribution of user risk scores"""
        risk_categories = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        
        for user in self.users.values():
            if user.risk_score < 25:
                risk_categories['low'] += 1
            elif user.risk_score < 50:
                risk_categories['medium'] += 1
            elif user.risk_score < 75:
                risk_categories['high'] += 1
            else:
                risk_categories['critical'] += 1
        
        return risk_categories
