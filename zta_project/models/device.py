"""
Device model for ZTA simulation
"""
import random
from datetime import datetime, timedelta
from typing import Dict


class Device:
    """Represents a device in the hybrid work environment"""
    
    def __init__(self, device_id: str, device_type: str, owner_id: str, os_version: str):
        self.device_id = device_id
        self.device_type = device_type
        self.owner_id = owner_id
        self.os_version = os_version
        self.registered_at = datetime.now()
        self.last_seen = datetime.now()
        self.trust_score = random.randint(60, 100)
        self.is_compliant = random.choice([True, True, True, False])  # 75% compliant
        self.compliance_checks = self._initialize_compliance()
        self.security_posture = self._calculate_security_posture()
        self.location = random.choice(['office', 'remote', 'unknown'])
        self.is_managed = random.choice([True, True, True, False])  # 75% managed
        self.last_patch_date = datetime.now() - timedelta(days=random.randint(0, 90))
        self.security_incidents = []
        
    def _initialize_compliance(self) -> Dict:
        """Initialize device compliance checks"""
        return {
            'os_updated': random.random() > 0.15,
            'antivirus_active': random.random() > 0.10,
            'encryption_enabled': random.random() > 0.20,
            'firewall_enabled': random.random() > 0.05,
            'screen_lock_enabled': random.random() > 0.12,
            'unauthorized_software': random.random() < 0.08
        }
    
    def _calculate_security_posture(self) -> str:
        """Calculate overall security posture"""
        # Calculate score: count good checks
        good_checks = 0
        total_checks = len(self.compliance_checks)
        
        for check, value in self.compliance_checks.items():
            if check == 'unauthorized_software':
                if not value:  # False is good for unauthorized_software
                    good_checks += 1
            else:
                if value:  # True is good for others
                    good_checks += 1
                    
        compliance_score = good_checks / total_checks
        
        if compliance_score >= 0.90:
            return 'excellent'
        elif compliance_score >= 0.75:
            return 'good'
        elif compliance_score >= 0.60:
            return 'fair'
        else:
            return 'poor'
    
    def perform_posture_check(self) -> bool:
        """Perform device posture check"""
        self.last_seen = datetime.now()
        
        # Update compliance checks with some randomness
        for check in self.compliance_checks:
            if random.random() < 0.05:  # 5% chance of status change
                self.compliance_checks[check] = not self.compliance_checks[check]
        
        # Recalculate compliance
        # Calculate score: count good checks
        good_checks = 0
        total_checks = len(self.compliance_checks)
        
        for check, value in self.compliance_checks.items():
            if check == 'unauthorized_software':
                if not value:  # False is good for unauthorized_software
                    good_checks += 1
            else:
                if value:  # True is good for others
                    good_checks += 1
        
        # 70% threshold for compliance
        self.is_compliant = (good_checks / total_checks) >= 0.7
        self.security_posture = self._calculate_security_posture()
        
        # Update trust score
        if self.is_compliant:
            self.trust_score = min(100, self.trust_score + random.randint(1, 5))
        else:
            self.trust_score = max(0, self.trust_score - random.randint(5, 15))
        
        return self.is_compliant
    
    def update_location(self, location: str):
        """Update device location"""
        self.location = location
        self.last_seen = datetime.now()
        
        # Location affects trust score
        if location == 'unknown':
            self.trust_score = max(0, self.trust_score - 10)
    
    def record_incident(self, incident_type: str, severity: str):
        """Record a security incident on this device"""
        self.security_incidents.append({
            'timestamp': datetime.now(),
            'type': incident_type,
            'severity': severity
        })
        
        # Decrease trust score based on severity
        severity_impact = {
            'low': 5,
            'medium': 15,
            'high': 30,
            'critical': 50
        }
        self.trust_score = max(0, self.trust_score - severity_impact.get(severity, 10))
        self.is_compliant = False
    
    def patch_device(self):
        """Simulate device patching and remediation"""
        self.last_patch_date = datetime.now()
        
        # Fix all compliance issues
        self.compliance_checks['os_updated'] = True
        self.compliance_checks['antivirus_active'] = True
        self.compliance_checks['encryption_enabled'] = True
        self.compliance_checks['firewall_enabled'] = True
        self.compliance_checks['screen_lock_enabled'] = True
        self.compliance_checks['unauthorized_software'] = False
        
        # Manually set compliance to avoid randomness in perform_posture_check
        self.is_compliant = True
        self.security_posture = 'excellent'
        
        # Boost trust score significantly - ensure it's enough to pass checks
        self.trust_score = max(85, min(100, self.trust_score + 40))
        
        # Update last seen but DO NOT call perform_posture_check() as it introduces randomness
        self.last_seen = datetime.now()
    
    def get_device_info(self) -> Dict:
        """Return device information as dictionary"""
        return {
            'device_id': self.device_id,
            'device_type': self.device_type,
            'owner_id': self.owner_id,
            'os_version': self.os_version,
            'trust_score': self.trust_score,
            'is_compliant': self.is_compliant,
            'security_posture': self.security_posture,
            'location': self.location,
            'is_managed': self.is_managed,
            'days_since_patch': (datetime.now() - self.last_patch_date).days,
            'incident_count': len(self.security_incidents)
        }
