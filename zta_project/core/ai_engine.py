"""
AI Engine for Zero Trust Architecture
Implements machine learning models for behavioral analytics, anomaly detection,
and threat prediction as described in the AI-Powered Zero-Trust Framework paper
"""

import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from collections import deque
import random


class BehavioralAnalyticsModel:
    """ML model for analyzing user behavior patterns"""
    
    def __init__(self):
        self.user_patterns = {}  # Store behavioral patterns per user
        self.model_weights = {
            'access_time': 0.25,
            'access_frequency': 0.20,
            'resource_pattern': 0.25,
            'location_consistency': 0.15,
            'device_preference': 0.15
        }
        self.training_data = {}
        
    def train_user_model(self, user_id: str, behavior_history: List[Dict]):
        """Train a behavioral model for a specific user"""
        if not behavior_history:
            return
            
        # Analyze patterns
        access_times = [b.get('hour', 0) for b in behavior_history]
        resources = [b.get('resource', '') for b in behavior_history]
        locations = [b.get('location', '') for b in behavior_history]
        
        pattern = {
            'typical_hours': self._calculate_typical_hours(access_times),
            'common_resources': self._get_common_resources(resources),
            'typical_locations': self._get_common_locations(locations),
            'avg_access_rate': len(behavior_history) / max(1, len(set([b.get('date', '') for b in behavior_history]))),
            'device_preferences': self._analyze_device_usage(behavior_history)
        }
        
        self.user_patterns[user_id] = pattern
        self.training_data[user_id] = behavior_history
        
    def predict_anomaly_score(self, user_id: str, current_behavior: Dict) -> float:
        """Predict anomaly score using ML model"""
        if user_id not in self.user_patterns:
            # New user, moderate anomaly score
            return 0.4
            
        pattern = self.user_patterns[user_id]
        anomaly_factors = []
        
        # Time-based anomaly
        current_hour = datetime.now().hour
        typical_hours = pattern['typical_hours']
        if not self._is_typical_hour(current_hour, typical_hours):
            time_anomaly = 1.0 - (min(abs(current_hour - h) for h in typical_hours) / 24.0)
            anomaly_factors.append(('access_time', time_anomaly * self.model_weights['access_time']))
        
        # Resource pattern anomaly
        current_resource = current_behavior.get('resource', '')
        if current_resource not in pattern['common_resources'][:5]:  # Top 5 resources
            anomaly_factors.append(('resource_pattern', self.model_weights['resource_pattern']))
        
        # Location anomaly
        current_location = current_behavior.get('location', '')
        if current_location not in pattern['typical_locations']:
            anomaly_factors.append(('location_consistency', self.model_weights['location_consistency']))
        
        # Access rate anomaly
        access_rate = current_behavior.get('access_rate', 0)
        avg_rate = pattern['avg_access_rate']
        if access_rate > avg_rate * 2:  # More than 2x normal rate
            rate_anomaly = min(1.0, (access_rate - avg_rate) / avg_rate)
            anomaly_factors.append(('access_frequency', rate_anomaly * self.model_weights['access_frequency']))
        
        # Calculate weighted anomaly score
        total_score = sum(weight for _, weight in anomaly_factors)
        return min(1.0, total_score)
    
    def _calculate_typical_hours(self, hours: List[int]) -> List[int]:
        """Calculate typical access hours using clustering"""
        if not hours:
            return list(range(9, 18))  # Default business hours
            
        # Simple clustering: find most common hour ranges
        hour_counts = {}
        for h in hours:
            hour_counts[h] = hour_counts.get(h, 0) + 1
        
        # Get top 6 most common hours (typical work span)
        typical = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:6]
        return [h for h, _ in typical]
    
    def _get_common_resources(self, resources: List[str]) -> List[str]:
        """Get commonly accessed resources"""
        resource_counts = {}
        for r in resources:
            resource_counts[r] = resource_counts.get(r, 0) + 1
        return sorted(resource_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    def _get_common_locations(self, locations: List[str]) -> List[str]:
        """Get typical access locations"""
        return list(set(locations))
    
    def _analyze_device_usage(self, behavior_history: List[Dict]) -> Dict[str, float]:
        """Analyze device usage patterns"""
        device_usage = {}
        total = len(behavior_history)
        for b in behavior_history:
            device = b.get('device_id', '')
            device_usage[device] = device_usage.get(device, 0) + 1
        
        # Normalize to probabilities
        return {d: count/total for d, count in device_usage.items()}
    
    def _is_typical_hour(self, hour: int, typical_hours: List[int]) -> bool:
        """Check if hour is within typical range"""
        if not typical_hours:
            return 9 <= hour <= 17
        # Allow 2-hour window
        return any(abs(hour - th) <= 2 for th in typical_hours)


class ThreatDetectionModel:
    """AI model for detecting malware and threats"""
    
    def __init__(self):
        self.malware_signatures = {
            'suspicious_file_operations': 0.8,
            'encryption_patterns': 0.9,
            'unusual_network_traffic': 0.7,
            'process_injection': 0.85,
            'registry_modifications': 0.75
        }
        self.threat_indicators = deque(maxlen=100)
        
    def analyze_file_activity(self, file_events: List[Dict]) -> float:
        """Analyze file activity for malware patterns"""
        if not file_events:
            return 0.0
            
        threat_score = 0.0
        
        # Check for rapid encryption (ransomware pattern)
        encryption_count = sum(1 for e in file_events if e.get('type') == 'encrypt')
        if encryption_count > 10:
            threat_score += self.malware_signatures['encryption_patterns'] * 0.5
            
        # Check for suspicious file operations
        suspicious_ops = sum(1 for e in file_events 
                          if e.get('operation') in ['delete', 'modify', 'rename'] 
                          and e.get('file_count', 0) > 50)
        if suspicious_ops > 0:
            threat_score += self.malware_signatures['suspicious_file_operations'] * 0.4
            
        # Check for unusual access patterns
        unique_files = len(set(e.get('file_path', '') for e in file_events))
        if unique_files > 100 and len(file_events) > 50:
            threat_score += 0.3
            
        return min(1.0, threat_score)
    
    def detect_lateral_movement(self, access_patterns: List[Dict]) -> float:
        """Detect lateral movement using ML patterns"""
        if len(access_patterns) < 3:
            return 0.0
            
        # Features for lateral movement detection
        unique_resources = len(set(p.get('resource_id') for p in access_patterns))
        time_span = (access_patterns[-1].get('timestamp', datetime.now()) - 
                    access_patterns[0].get('timestamp', datetime.now())).total_seconds()
        
        # Rapid access to multiple resources indicates lateral movement
        if unique_resources > 5 and time_span < 300:  # 5+ resources in 5 minutes
            return 0.85
            
        # Access to high-value resources in sequence
        high_value_access = sum(1 for p in access_patterns 
                               if p.get('security_level') in ['high', 'critical'])
        if high_value_access >= 3:
            return 0.75
            
        return 0.0
    
    def predict_threat_level(self, behavior_features: Dict) -> Dict:
        """Predict overall threat level using ML model"""
        base_threat = 0.0
        
        # File activity analysis
        if 'file_events' in behavior_features:
            file_threat = self.analyze_file_activity(behavior_features['file_events'])
            base_threat = max(base_threat, file_threat)
        
        # Network activity
        if 'network_anomaly' in behavior_features:
            base_threat += behavior_features['network_anomaly'] * 0.3
            
        # Process anomalies
        if 'suspicious_processes' in behavior_features:
            base_threat += min(0.5, behavior_features['suspicious_processes'] * 0.2)
        
        # Lateral movement detection
        if 'access_patterns' in behavior_features:
            lateral_threat = self.detect_lateral_movement(behavior_features['access_patterns'])
            base_threat = max(base_threat, lateral_threat)
        
        threat_level = 'low'
        if base_threat >= 0.7:
            threat_level = 'high'
        elif base_threat >= 0.4:
            threat_level = 'medium'
            
        return {
            'threat_score': min(1.0, base_threat),
            'threat_level': threat_level,
            'confidence': min(1.0, base_threat + 0.2)
        }


class AIAnomalyDetector:
    """AI-powered anomaly detection engine"""
    
    def __init__(self):
        self.behavioral_model = BehavioralAnalyticsModel()
        self.threat_model = ThreatDetectionModel()
        self.anomaly_history = []
        
    def detect_behavioral_anomaly(self, user_id: str, behavior_data: Dict) -> Dict:
        """Detect behavioral anomalies using ML model"""
        # Get anomaly score from behavioral model
        anomaly_score = self.behavioral_model.predict_anomaly_score(user_id, behavior_data)
        
        # Additional rule-based checks (hybrid approach)
        rule_based_score = 0.0
        
        # Check for unusual access frequency
        if behavior_data.get('access_rate', 0) > 20:  # More than 20 accesses per minute
            rule_based_score += 0.3
            
        # Check for location jumping
        if behavior_data.get('location_changes', 0) > 2:  # Multiple location changes quickly
            rule_based_score += 0.25
        
        # Combine ML and rule-based scores
        final_score = max(anomaly_score, rule_based_score)
        
        is_anomalous = final_score > 0.6
        
        result = {
            'is_anomalous': is_anomalous,
            'anomaly_score': final_score,
            'ml_score': anomaly_score,
            'rule_based_score': rule_based_score,
            'timestamp': datetime.now()
        }
        
        if is_anomalous:
            self.anomaly_history.append({
                'user_id': user_id,
                'score': final_score,
                'timestamp': datetime.now(),
                'behavior_data': behavior_data
            })
        
        return result
    
    def detect_malware_threat(self, device_id: str, activity_data: Dict) -> Dict:
        """Detect malware threats using AI models"""
        threat_result = self.threat_model.predict_threat_level(activity_data)
        
        if threat_result['threat_level'] in ['medium', 'high']:
            self.anomaly_history.append({
                'device_id': device_id,
                'threat_level': threat_result['threat_level'],
                'threat_score': threat_result['threat_score'],
                'timestamp': datetime.now()
            })
        
        return threat_result
    
    def train_on_user_behavior(self, user_id: str, behavior_history: List[Dict]):
        """Train the behavioral model on user's historical behavior"""
        self.behavioral_model.train_user_model(user_id, behavior_history)
    
    def get_anomaly_statistics(self) -> Dict:
        """Get statistics about detected anomalies"""
        if not self.anomaly_history:
            return {
                'total_anomalies': 0,
                'avg_anomaly_score': 0.0,
                'high_threat_count': 0
            }
        
        recent_anomalies = [a for a in self.anomaly_history 
                          if (datetime.now() - a['timestamp']).total_seconds() < 86400]  # Last 24 hours
        
        avg_score = np.mean([a.get('anomaly_score', a.get('threat_score', 0)) 
                            for a in recent_anomalies]) if recent_anomalies else 0.0
        
        high_threat = sum(1 for a in recent_anomalies 
                         if a.get('threat_level') == 'high' or a.get('anomaly_score', 0) > 0.7)
        
        return {
            'total_anomalies': len(self.anomaly_history),
            'recent_anomalies': len(recent_anomalies),
            'avg_anomaly_score': avg_score,
            'high_threat_count': high_threat
        }

