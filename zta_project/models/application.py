"""
Application model for ZTA simulation
"""
import random
from typing import Dict, List


class Application:
    """Represents an application resource in the organization"""
    
    def __init__(self, app_id: str, name: str, security_level: str, app_type: str):
        self.app_id = app_id
        self.name = name
        self.security_level = security_level
        self.app_type = app_type
        self.required_access_level = self._determine_required_access()
        self.required_auth_methods = self._determine_required_auth()
        self.network_segment = self._assign_network_segment()
        self.access_logs = []
        self.is_cloud_based = random.choice([True, False])
        self.supports_mfa = True
        self.data_classification = self._determine_data_classification()
        
    def _determine_required_access(self) -> int:
        """Determine minimum access level required"""
        level_mapping = {
            'low': 1,
            'medium': 2,
            'high': 3,
            'critical': 4
        }
        return level_mapping.get(self.security_level, 1)
    
    def _determine_required_auth(self) -> List[str]:
        """Determine required authentication methods"""
        if self.security_level == 'critical':
            return ['mfa', 'biometric', 'certificate']
        elif self.security_level == 'high':
            return ['mfa', 'biometric']
        elif self.security_level == 'medium':
            return ['mfa', 'password']
        else:
            return ['password']
    
    def _assign_network_segment(self) -> str:
        """Assign application to network segment (micro-segmentation)"""
        if self.security_level in ['critical', 'high']:
            return f'secure_segment_{random.randint(1, 3)}'
        else:
            return f'general_segment_{random.randint(1, 5)}'
    
    def _determine_data_classification(self) -> str:
        """Determine data classification level"""
        classification_map = {
            'critical': 'confidential',
            'high': 'restricted',
            'medium': 'internal',
            'low': 'public'
        }
        return classification_map.get(self.security_level, 'internal')
    
    def check_access_permission(self, user_access_level: int, user_auth_method: str,
                                device_trust_score: int, user_risk_score: int) -> Dict:
        """Check if access should be granted based on ZTA policies"""
        reasons = []
        granted = True
        
        # Check user access level
        if user_access_level < self.required_access_level:
            granted = False
            reasons.append(f'Insufficient access level (required: {self.required_access_level})')
        
        # Check authentication method
        if user_auth_method not in self.required_auth_methods:
            granted = False
            reasons.append(f'Authentication method not sufficient (required: {self.required_auth_methods})')
        
        # Check device trust score
        min_trust_score = 70 if self.security_level in ['critical', 'high'] else 50
        if device_trust_score < min_trust_score:
            granted = False
            reasons.append(f'Device trust score too low (required: {min_trust_score})')
        
        # Check user risk score
        max_risk_score = 30 if self.security_level in ['critical', 'high'] else 50
        if user_risk_score > max_risk_score:
            granted = False
            reasons.append(f'User risk score too high (max: {max_risk_score})')
        
        return {
            'granted': granted,
            'reasons': reasons if not granted else ['Access granted'],
            'security_level': self.security_level
        }
    
    def log_access_attempt(self, user_id: str, device_id: str, granted: bool, timestamp):
        """Log an access attempt"""
        self.access_logs.append({
            'timestamp': timestamp,
            'user_id': user_id,
            'device_id': device_id,
            'granted': granted
        })
    
    def get_application_info(self) -> Dict:
        """Return application information as dictionary"""
        return {
            'app_id': self.app_id,
            'name': self.name,
            'security_level': self.security_level,
            'app_type': self.app_type,
            'required_access_level': self.required_access_level,
            'network_segment': self.network_segment,
            'is_cloud_based': self.is_cloud_based,
            'data_classification': self.data_classification,
            'total_access_attempts': len(self.access_logs)
        }
