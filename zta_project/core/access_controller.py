"""
Access Control and Policy Enforcement component for ZTA
"""
from datetime import datetime
from typing import Dict, List, Optional
from models.application import Application
from models.user import User
from models.device import Device


class AccessController:
    """Manages access control policies and enforcement"""
    
    def __init__(self, identity_manager, device_manager):
        self.identity_manager = identity_manager
        self.device_manager = device_manager
        self.applications = {}
        self.access_logs = []
        self.policies = self._initialize_policies()
        self.denied_access_count = 0
        self.granted_access_count = 0
        
    def _initialize_policies(self) -> Dict:
        """Initialize default ZTA policies"""
        return {
            'require_mfa_for_critical': True,
            'min_device_trust_score': 70,
            'max_user_risk_score': 50,
            'require_compliant_device': True,
            'block_quarantined_devices': True,
            'enforce_location_policy': False,
            'session_timeout_minutes': 30,
            'max_concurrent_sessions': 3
        }
    
    def register_application(self, application: Application):
        """Register an application in the access control system"""
        self.applications[application.app_id] = application
    
    def request_access(self, session_token: str, device_id: str, app_id: str,
                      action: str = 'read', context: Dict = None) -> Dict:
        """Process an access request using Zero Trust principles"""
        timestamp = datetime.now()
        
        # Validate session
        session_validation = self.identity_manager.validate_session(session_token)
        if not session_validation['valid']:
            return self._deny_access('Invalid or expired session', session_token, 
                                    device_id, app_id, timestamp)
        
        user_id = session_validation['user_id']
        user = self.identity_manager.users.get(user_id)
        
        if not user:
            return self._deny_access('User not found', session_token, 
                                    device_id, app_id, timestamp)
        
        # Validate device using min_trust_score from device_manager
        device_validation = self.device_manager.validate_device_for_access(
            device_id, self.device_manager.min_trust_score)
        
        if not device_validation['valid']:
            return self._deny_access(f"Device validation failed: {device_validation['reason']}", 
                                    session_token, device_id, app_id, timestamp, user_id)
        
        device = self.device_manager.devices.get(device_id)
        
        # Check if device is quarantined
        if self.policies['block_quarantined_devices'] and \
           device_id in self.device_manager.quarantined_devices:
            return self._deny_access('Device is quarantined', session_token, 
                                    device_id, app_id, timestamp, user_id)
        
        # Validate application exists
        if app_id not in self.applications:
            return self._deny_access('Application not found', session_token, 
                                    device_id, app_id, timestamp, user_id)
        
        application = self.applications[app_id]
        
        # Check application-specific access permissions
        access_check = application.check_access_permission(
            user.access_level,
            user.authentication_method,
            device.trust_score,
            user.risk_score
        )
        
        if not access_check['granted']:
            reasons = '; '.join(access_check['reasons'])
            return self._deny_access(reasons, session_token, device_id, 
                                    app_id, timestamp, user_id)
        
        # Perform continuous authentication check
        behavior_data = context or {}
        if not self.identity_manager.continuous_authentication(session_token, behavior_data):
            return self._deny_access('Continuous authentication failed - anomalous behavior detected',
                                    session_token, device_id, app_id, timestamp, user_id)
        
        # All checks passed - grant access
        return self._grant_access(user, device, application, action, timestamp)
    
    def _grant_access(self, user: User, device: Device, application: Application,
                     action: str, timestamp: datetime) -> Dict:
        """Grant access and log the decision"""
        self.granted_access_count += 1
        
        # Log access
        log_entry = {
            'timestamp': timestamp,
            'user_id': user.user_id,
            'device_id': device.device_id,
            'app_id': application.app_id,
            'action': action,
            'granted': True,
            'reason': 'All ZTA policies satisfied'
        }
        self.access_logs.append(log_entry)
        
        # Update application logs
        application.log_access_attempt(user.user_id, device.device_id, True, timestamp)
        
        # Record in user's access patterns
        user.record_access(application.name, action, True)
        
        return {
            'access_granted': True,
            'reason': 'Access granted',
            'application': application.name,
            'action': action,
            'session_valid_until': timestamp,
            'security_level': application.security_level
        }
    
    def _deny_access(self, reason: str, session_token: str, device_id: str,
                    app_id: str, timestamp: datetime, user_id: str = None) -> Dict:
        """Deny access and log the decision"""
        self.denied_access_count += 1
        
        # Log denied access
        log_entry = {
            'timestamp': timestamp,
            'user_id': user_id or 'unknown',
            'device_id': device_id,
            'app_id': app_id,
            'granted': False,
            'reason': reason
        }
        self.access_logs.append(log_entry)
        
        # Update user risk score if user exists
        if user_id and user_id in self.identity_manager.users:
            user = self.identity_manager.users[user_id]
            user.update_risk_score('policy_violation')
            user.record_access(app_id, 'access_attempt', False)
        
        return {
            'access_granted': False,
            'reason': reason,
            'timestamp': timestamp
        }
    
    def enforce_micro_segmentation(self, source_segment: str, 
                                   target_segment: str) -> bool:
        """Enforce network micro-segmentation policies"""
        # Define allowed segment communications
        allowed_communications = {
            'general_segment_1': ['general_segment_2', 'general_segment_3'],
            'general_segment_2': ['general_segment_1', 'general_segment_3'],
            'secure_segment_1': ['secure_segment_2'],
            'secure_segment_2': ['secure_segment_1'],
            'secure_segment_3': []  # Isolated segment
        }
        
        # Check if communication is allowed
        if source_segment == target_segment:
            return True
        
        allowed = allowed_communications.get(source_segment, [])
        return target_segment in allowed
    
    def get_access_statistics(self) -> Dict:
        """Get access control statistics"""
        total_requests = len(self.access_logs)
        granted = self.granted_access_count
        denied = self.denied_access_count
        
        # Analyze denial reasons
        denial_reasons = {}
        for log in self.access_logs:
            if not log['granted']:
                reason = log['reason']
                denial_reasons[reason] = denial_reasons.get(reason, 0) + 1
        
        # Access by application
        app_access = {}
        for log in self.access_logs:
            app_id = log['app_id']
            if app_id not in app_access:
                app_access[app_id] = {'granted': 0, 'denied': 0}
            
            if log['granted']:
                app_access[app_id]['granted'] += 1
            else:
                app_access[app_id]['denied'] += 1
        
        return {
            'total_access_requests': total_requests,
            'granted': granted,
            'denied': denied,
            'grant_rate': granted / total_requests if total_requests > 0 else 0,
            'denial_rate': denied / total_requests if total_requests > 0 else 0,
            'top_denial_reasons': sorted(denial_reasons.items(), 
                                        key=lambda x: x[1], reverse=True)[:5],
            'application_access_summary': app_access
        }
    
    def get_policy_violations(self) -> List[Dict]:
        """Get list of policy violations"""
        violations = []
        
        for log in self.access_logs:
            if not log['granted']:
                violations.append({
                    'timestamp': log['timestamp'],
                    'user_id': log['user_id'],
                    'device_id': log['device_id'],
                    'app_id': log['app_id'],
                    'violation_reason': log['reason']
                })
        
        return violations
    
    def update_policy(self, policy_name: str, value):
        """Update a ZTA policy"""
        if policy_name in self.policies:
            self.policies[policy_name] = value
            return True
        return False
