"""
Configuration file for Zero Trust Architecture Simulation
"""

# Simulation Parameters
NUM_USERS = 50
NUM_DEVICES = 75
NUM_APPLICATIONS = 10
SIMULATION_DAYS = 30
EVENTS_PER_DAY = 100

# User Roles
USER_ROLES = ['employee', 'manager', 'admin', 'contractor', 'executive']

# Device Types
DEVICE_TYPES = ['laptop', 'desktop', 'mobile', 'tablet']

# Work Locations
WORK_LOCATIONS = ['office', 'remote', 'hybrid']

# Security Levels
SECURITY_LEVELS = ['low', 'medium', 'high', 'critical']

# Authentication Methods
AUTH_METHODS = ['password', 'mfa', 'biometric', 'certificate']

# Device Compliance Criteria
DEVICE_COMPLIANCE = {
    'os_updated': 0.85,  # 85% devices should have updated OS
    'antivirus_active': 0.90,  # 90% should have active antivirus
    'encryption_enabled': 0.80,  # 80% should have encryption
    'firewall_enabled': 0.95  # 95% should have firewall enabled
}

# ZTA Policy Thresholds
ZTA_THRESHOLDS = {
    'max_failed_attempts': 3,
    'session_timeout_minutes': 30,
    'device_trust_score_min': 70,
    'user_risk_score_max': 50,
    'anomaly_threshold': 0.7
}

# Breach Simulation Parameters
BREACH_SCENARIOS = {
    'lateral_movement': {'probability': 0.15, 'severity': 'high'},
    'credential_theft': {'probability': 0.20, 'severity': 'critical'},
    'insider_threat': {'probability': 0.10, 'severity': 'high'},
    'device_compromise': {'probability': 0.12, 'severity': 'medium'},
    'privilege_escalation': {'probability': 0.08, 'severity': 'critical'}
}

# Usability Metrics
USABILITY_TASKS = [
    'login_to_system',
    'access_file_share',
    'connect_to_database',
    'use_web_application',
    'access_email',
    'join_video_conference',
    'upload_document',
    'download_report'
]

# Report Output Directory
OUTPUT_DIR = 'results'
LOGS_DIR = 'logs'
CHARTS_DIR = 'charts'
