"""
Device Management and Posture Assessment component for ZTA
"""
from datetime import datetime, timedelta
from typing import Dict, List
from models.device import Device
from core.ai_engine import AIAnomalyDetector


class DeviceManager:
    """Manages device registration and posture assessment"""
    
    def __init__(self):
        self.devices = {}
        self.posture_check_logs = []
        self.quarantined_devices = set()
        self.compliance_history = []
        self.min_trust_score = 70  # Minimum trust score required for access
        self.ai_detector = AIAnomalyDetector()  # AI-powered threat detection
        self.device_activity_logs = {}  # Track device activity for ML analysis
        
    def register_device(self, device: Device):
        """Register a device in the system"""
        self.devices[device.device_id] = device
        self._log_posture_check(device.device_id, device.is_compliant, device.trust_score)
    
    def perform_posture_assessment(self, device_id: str) -> Dict:
        """Perform comprehensive device posture assessment"""
        if device_id not in self.devices:
            return {
                'compliant': False,
                'reason': 'Device not registered',
                'trust_score': 0
            }
        
        device = self.devices[device_id]
        
        # Check if device is quarantined
        if device_id in self.quarantined_devices:
            return {
                'compliant': False,
                'reason': 'Device is quarantined',
                'trust_score': 0,
                'action_required': 'Contact IT security'
            }
        
        # Perform posture check
        is_compliant = device.perform_posture_check()
        
        # Log the check
        self._log_posture_check(device_id, is_compliant, device.trust_score)
        
        # Determine actions needed
        actions = self._determine_remediation_actions(device)
        
        result = {
            'compliant': is_compliant,
            'trust_score': device.trust_score,
            'security_posture': device.security_posture,
            'compliance_checks': device.compliance_checks,
            'actions_required': actions
        }
        
        # Quarantine if critical issues
        if device.trust_score < 30 or device.security_posture == 'poor':
            self.quarantine_device(device_id, 'Critical security issues detected')
            result['quarantined'] = True
        
        return result
    
    def _determine_remediation_actions(self, device: Device) -> List[str]:
        """Determine what actions are needed to improve device compliance"""
        actions = []
        
        if not device.compliance_checks.get('os_updated'):
            actions.append('Update operating system')
        
        if not device.compliance_checks.get('antivirus_active'):
            actions.append('Enable and update antivirus software')
        
        if not device.compliance_checks.get('encryption_enabled'):
            actions.append('Enable full disk encryption')
        
        if not device.compliance_checks.get('firewall_enabled'):
            actions.append('Enable firewall')
        
        if not device.compliance_checks.get('screen_lock_enabled'):
            actions.append('Enable screen lock with password')
        
        if device.compliance_checks.get('unauthorized_software'):
            actions.append('Remove unauthorized software')
        
        # Check patch status
        days_since_patch = (datetime.now() - device.last_patch_date).days
        if days_since_patch > 30:
            actions.append(f'Apply security patches (last patched {days_since_patch} days ago)')
        
        return actions
    
    def quarantine_device(self, device_id: str, reason: str):
        """Quarantine a non-compliant device"""
        self.quarantined_devices.add(device_id)
        if device_id in self.devices:
            device = self.devices[device_id]
            device.is_compliant = False
            device.record_incident('quarantine', 'high')
    
    def release_from_quarantine(self, device_id: str) -> bool:
        """Release a device from quarantine after remediation"""
        if device_id not in self.devices:
            return False
        
        device = self.devices[device_id]
        
        # Re-check compliance
        assessment = self.perform_posture_assessment(device_id)
        
        if assessment['compliant'] and device.trust_score >= 60:
            self.quarantined_devices.discard(device_id)
            return True
        
        return False
    
    def get_device_by_owner(self, owner_id: str) -> List[Device]:
        """Get all devices owned by a user"""
        return [device for device in self.devices.values() 
                if device.owner_id == owner_id]
    
    def validate_device_for_access(self, device_id: str, required_trust_score: int = 70) -> Dict:
        """Validate if device meets requirements for resource access"""
        if device_id not in self.devices:
            return {
                'valid': False,
                'reason': 'Device not found'
            }
        
        if device_id in self.quarantined_devices:
            return {
                'valid': False,
                'reason': 'Device is quarantined'
            }
        
        device = self.devices[device_id]
        
        if not device.is_compliant:
            return {
                'valid': False,
                'reason': 'Device is not compliant',
                'trust_score': device.trust_score
            }
        
        if device.trust_score < required_trust_score:
            return {
                'valid': False,
                'reason': f'Trust score too low (required: {required_trust_score}, current: {device.trust_score})',
                'trust_score': device.trust_score
            }
        
        return {
            'valid': True,
            'trust_score': device.trust_score,
            'security_posture': device.security_posture
        }
    
    def _log_posture_check(self, device_id: str, compliant: bool, trust_score: int):
        """Log a posture check"""
        self.posture_check_logs.append({
            'timestamp': datetime.now(),
            'device_id': device_id,
            'compliant': compliant,
            'trust_score': trust_score
        })
        
        self.compliance_history.append({
            'timestamp': datetime.now(),
            'device_id': device_id,
            'compliant': compliant
        })
    
    def get_compliance_statistics(self) -> Dict:
        """Get device compliance statistics"""
        total_devices = len(self.devices)
        compliant_devices = sum(1 for d in self.devices.values() if d.is_compliant)
        quarantined = len(self.quarantined_devices)
        
        # Trust score distribution
        trust_distribution = {
            'excellent': sum(1 for d in self.devices.values() if d.trust_score >= 90),
            'good': sum(1 for d in self.devices.values() if 70 <= d.trust_score < 90),
            'fair': sum(1 for d in self.devices.values() if 50 <= d.trust_score < 70),
            'poor': sum(1 for d in self.devices.values() if d.trust_score < 50)
        }
        
        # Security posture distribution
        posture_distribution = {}
        for device in self.devices.values():
            posture = device.security_posture
            posture_distribution[posture] = posture_distribution.get(posture, 0) + 1
        
        return {
            'total_devices': total_devices,
            'compliant_devices': compliant_devices,
            'non_compliant_devices': total_devices - compliant_devices,
            'compliance_rate': compliant_devices / total_devices if total_devices > 0 else 0,
            'quarantined_devices': quarantined,
            'trust_distribution': trust_distribution,
            'posture_distribution': posture_distribution,
            'total_posture_checks': len(self.posture_check_logs)
        }
    
    def detect_malware_threat(self, device_id: str, activity_data: Dict) -> Dict:
        """Use AI to detect malware threats on device"""
        if device_id not in self.devices:
            return {'threat_score': 0.0, 'threat_level': 'low'}
        
        # Track device activity for ML analysis
        if device_id not in self.device_activity_logs:
            self.device_activity_logs[device_id] = []
        
        self.device_activity_logs[device_id].append({
            'timestamp': datetime.now(),
            'activity': activity_data
        })
        
        # Keep only recent activity (last 100 events)
        self.device_activity_logs[device_id] = self.device_activity_logs[device_id][-100:]
        
        # Use AI model to detect threats
        threat_result = self.ai_detector.detect_malware_threat(device_id, activity_data)
        
        # If high threat detected, quarantine device
        if threat_result['threat_level'] == 'high':
            self.quarantine_device(device_id, f"AI detected high malware threat: {threat_result['threat_score']:.2f}")
        
        return threat_result
    
    def get_device_health_report(self) -> List[Dict]:
        """Generate health report for all devices"""
        report = []
        
        for device in self.devices.values():
            report.append({
                'device_id': device.device_id,
                'owner_id': device.owner_id,
                'type': device.device_type,
                'trust_score': device.trust_score,
                'compliant': device.is_compliant,
                'posture': device.security_posture,
                'quarantined': device.device_id in self.quarantined_devices,
                'incident_count': len(device.security_incidents),
                'days_since_patch': (datetime.now() - device.last_patch_date).days
            })
        
        return report
