"""
User model for ZTA simulation
"""
import random
import hashlib
from datetime import datetime
from typing import Dict, List


class User:
    """Represents a user in the hybrid work environment"""
    
    def __init__(self, user_id: str, name: str, role: str, location: str, department: str):
        self.user_id = user_id
        self.name = name
        self.role = role
        self.location = location
        self.department = department
        self.created_at = datetime.now()
        self.last_login = None
        self.failed_login_attempts = 0
        self.risk_score = random.randint(0, 30)  # Initial low risk
        self.authentication_method = self._assign_auth_method()
        self.access_level = self._determine_access_level()
        self.is_active = True
        self.login_history = []
        self.access_patterns = []
        
    def _assign_auth_method(self) -> str:
        """Assign authentication method based on role"""
        if self.role in ['admin', 'executive']:
            return random.choice(['mfa', 'biometric', 'certificate'])
        elif self.role == 'manager':
            return random.choice(['mfa', 'biometric'])
        else:
            return random.choice(['password', 'mfa'])
    
    def _determine_access_level(self) -> int:
        """Determine access level (1-5) based on role"""
        access_mapping = {
            'employee': 2,
            'contractor': 1,
            'manager': 3,
            'admin': 5,
            'executive': 4
        }
        return access_mapping.get(self.role, 1)
    
    def authenticate(self, password: str, mfa_code: str = None) -> bool:
        """Simulate authentication process"""
        # Simulate authentication success rate
        if self.authentication_method == 'password':
            success_rate = 0.85
        elif self.authentication_method == 'mfa':
            success_rate = 0.95 if mfa_code else 0.50
        else:  # biometric or certificate
            success_rate = 0.98
        
        success = random.random() < success_rate
        
        if success:
            self.failed_login_attempts = 0
            self.last_login = datetime.now()
            self.login_history.append({
                'timestamp': datetime.now(),
                'success': True,
                'method': self.authentication_method
            })
        else:
            self.failed_login_attempts += 1
            self.login_history.append({
                'timestamp': datetime.now(),
                'success': False,
                'method': self.authentication_method
            })
        
        return success
    
    def update_risk_score(self, incident_type: str = None):
        """Update user risk score based on behavior"""
        if incident_type:
            risk_increase = {
                'failed_login': 10,
                'anomalous_access': 15,
                'policy_violation': 20,
                'suspicious_activity': 25
            }
            self.risk_score += risk_increase.get(incident_type, 5)
        else:
            # Gradually decrease risk score over time
            self.risk_score = max(0, self.risk_score - 1)
        
        self.risk_score = min(100, self.risk_score)
    
    def record_access(self, resource: str, action: str, granted: bool):
        """Record access attempt to a resource"""
        self.access_patterns.append({
            'timestamp': datetime.now(),
            'resource': resource,
            'action': action,
            'granted': granted
        })
    
    def get_user_info(self) -> Dict:
        """Return user information as dictionary"""
        return {
            'user_id': self.user_id,
            'name': self.name,
            'role': self.role,
            'location': self.location,
            'department': self.department,
            'risk_score': self.risk_score,
            'access_level': self.access_level,
            'auth_method': self.authentication_method,
            'failed_attempts': self.failed_login_attempts,
            'is_active': self.is_active
        }
