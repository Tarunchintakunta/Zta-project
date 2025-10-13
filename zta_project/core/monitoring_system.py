"""
Continuous Monitoring and Logging System for ZTA
"""
from datetime import datetime, timedelta
from typing import Dict, List
import random


class MonitoringSystem:
    """Monitors and logs all activities in the ZTA environment"""
    
    def __init__(self):
        self.security_events = []
        self.anomalies = []
        self.alerts = []
        self.metrics = {
            'authentication_events': 0,
            'access_requests': 0,
            'policy_violations': 0,
            'device_posture_checks': 0,
            'security_incidents': 0
        }
        
    def log_event(self, event_type: str, severity: str, description: str, 
                  metadata: Dict = None):
        """Log a security event"""
        event = {
            'timestamp': datetime.now(),
            'event_type': event_type,
            'severity': severity,
            'description': description,
            'metadata': metadata or {}
        }
        
        self.security_events.append(event)
        
        # Update metrics
        if event_type in self.metrics:
            self.metrics[event_type] += 1
        
        # Generate alert for high severity events
        if severity in ['high', 'critical']:
            self.generate_alert(event)
    
    def detect_anomaly(self, user_id: str, device_id: str, behavior_data: Dict) -> Dict:
        """Detect anomalous behavior patterns"""
        anomaly_score = 0
        anomaly_indicators = []
        
        # Check for unusual access times
        current_hour = datetime.now().hour
        if current_hour < 6 or current_hour > 22:
            anomaly_score += 0.2
            anomaly_indicators.append('Unusual access time')
        
        # Check for rapid access attempts
        if behavior_data.get('access_rate', 0) > 10:  # More than 10 per minute
            anomaly_score += 0.3
            anomaly_indicators.append('High access rate')
        
        # Check for access to unusual resources
        if behavior_data.get('unusual_resources', False):
            anomaly_score += 0.25
            anomaly_indicators.append('Access to unusual resources')
        
        # Check for location changes
        if behavior_data.get('location_change', False):
            anomaly_score += 0.15
            anomaly_indicators.append('Rapid location change')
        
        # Check for failed authentication attempts
        if behavior_data.get('failed_auth_count', 0) > 2:
            anomaly_score += 0.35
            anomaly_indicators.append('Multiple failed authentication attempts')
        
        is_anomalous = anomaly_score > 0.5
        
        if is_anomalous:
            anomaly = {
                'timestamp': datetime.now(),
                'user_id': user_id,
                'device_id': device_id,
                'anomaly_score': anomaly_score,
                'indicators': anomaly_indicators,
                'behavior_data': behavior_data
            }
            self.anomalies.append(anomaly)
            
            # Log as security event
            self.log_event(
                'anomaly_detected',
                'high' if anomaly_score > 0.7 else 'medium',
                f'Anomalous behavior detected for user {user_id}',
                {'anomaly_score': anomaly_score, 'indicators': anomaly_indicators}
            )
        
        return {
            'is_anomalous': is_anomalous,
            'anomaly_score': anomaly_score,
            'indicators': anomaly_indicators
        }
    
    def generate_alert(self, event: Dict):
        """Generate security alert for high-priority events"""
        alert = {
            'alert_id': f"ALERT-{len(self.alerts) + 1:05d}",
            'timestamp': event['timestamp'],
            'severity': event['severity'],
            'event_type': event['event_type'],
            'description': event['description'],
            'metadata': event['metadata'],
            'status': 'open',
            'acknowledged': False
        }
        
        self.alerts.append(alert)
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge a security alert"""
        for alert in self.alerts:
            if alert['alert_id'] == alert_id:
                alert['acknowledged'] = True
                alert['acknowledged_at'] = datetime.now()
                return True
        return False
    
    def close_alert(self, alert_id: str, resolution: str) -> bool:
        """Close a security alert"""
        for alert in self.alerts:
            if alert['alert_id'] == alert_id:
                alert['status'] = 'closed'
                alert['closed_at'] = datetime.now()
                alert['resolution'] = resolution
                return True
        return False
    
    def get_security_dashboard(self) -> Dict:
        """Generate security dashboard metrics"""
        # Time-based analysis
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        
        events_24h = [e for e in self.security_events if e['timestamp'] > last_24h]
        anomalies_24h = [a for a in self.anomalies if a['timestamp'] > last_24h]
        
        # Severity distribution
        severity_dist = {}
        for event in self.security_events:
            sev = event['severity']
            severity_dist[sev] = severity_dist.get(sev, 0) + 1
        
        # Event type distribution
        event_type_dist = {}
        for event in self.security_events:
            etype = event['event_type']
            event_type_dist[etype] = event_type_dist.get(etype, 0) + 1
        
        # Open alerts
        open_alerts = [a for a in self.alerts if a['status'] == 'open']
        critical_alerts = [a for a in open_alerts if a['severity'] == 'critical']
        
        return {
            'total_events': len(self.security_events),
            'events_last_24h': len(events_24h),
            'total_anomalies': len(self.anomalies),
            'anomalies_last_24h': len(anomalies_24h),
            'total_alerts': len(self.alerts),
            'open_alerts': len(open_alerts),
            'critical_alerts': len(critical_alerts),
            'severity_distribution': severity_dist,
            'event_type_distribution': event_type_dist,
            'metrics': self.metrics
        }
    
    def get_incident_timeline(self, hours: int = 24) -> List[Dict]:
        """Get timeline of security incidents"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        timeline = []
        
        # Add high severity events
        for event in self.security_events:
            if event['timestamp'] > cutoff and event['severity'] in ['high', 'critical']:
                timeline.append({
                    'timestamp': event['timestamp'],
                    'type': 'event',
                    'severity': event['severity'],
                    'description': event['description']
                })
        
        # Add anomalies
        for anomaly in self.anomalies:
            if anomaly['timestamp'] > cutoff:
                timeline.append({
                    'timestamp': anomaly['timestamp'],
                    'type': 'anomaly',
                    'severity': 'high',
                    'description': f"Anomaly detected: {', '.join(anomaly['indicators'])}"
                })
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return timeline
    
    def generate_compliance_report(self) -> Dict:
        """Generate compliance report for audit purposes"""
        return {
            'report_generated': datetime.now(),
            'total_security_events': len(self.security_events),
            'total_anomalies_detected': len(self.anomalies),
            'total_alerts_generated': len(self.alerts),
            'alerts_resolved': len([a for a in self.alerts if a['status'] == 'closed']),
            'average_response_time': self._calculate_avg_response_time(),
            'policy_violations': self.metrics.get('policy_violations', 0),
            'authentication_events': self.metrics.get('authentication_events', 0),
            'device_posture_checks': self.metrics.get('device_posture_checks', 0)
        }
    
    def _calculate_avg_response_time(self) -> float:
        """Calculate average alert response time"""
        response_times = []
        
        for alert in self.alerts:
            if alert['acknowledged'] and 'acknowledged_at' in alert:
                response_time = (alert['acknowledged_at'] - alert['timestamp']).total_seconds() / 60
                response_times.append(response_time)
        
        return sum(response_times) / len(response_times) if response_times else 0
    
    def export_logs(self, start_date: datetime = None, end_date: datetime = None) -> List[Dict]:
        """Export logs for a specific time period"""
        logs = []
        
        for event in self.security_events:
            if start_date and event['timestamp'] < start_date:
                continue
            if end_date and event['timestamp'] > end_date:
                continue
            logs.append(event)
        
        return logs
