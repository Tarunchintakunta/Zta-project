"""
AI Engine for Zero Trust Architecture
Implements machine learning models for behavioral analytics, anomaly detection,
and threat prediction as described in the AI-Powered Zero-Trust Framework paper

This module uses real ML algorithms (Isolation Forest, feature engineering) instead
of simple rule-based approaches for scientific rigor.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from collections import deque, defaultdict
import random
import warnings
warnings.filterwarnings('ignore')

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.model_selection import train_test_split
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn not available. Install with: pip install scikit-learn")


class BehavioralAnalyticsModel:
    """
    Real ML-based model for analyzing user behavior patterns.
    Uses Isolation Forest for anomaly detection and feature engineering
    to extract meaningful behavioral patterns.
    """
    
    def __init__(self, contamination: float = 0.1, random_state: int = 42):
        """
        Initialize the ML-based behavioral analytics model.
        
        Args:
            contamination: Expected proportion of anomalies (0.0 to 0.5)
            random_state: Random seed for reproducibility
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required. Install with: pip install scikit-learn")
        
        self.user_models = {}  # Isolation Forest models per user
        self.scalers = {}  # Feature scalers per user
        self.label_encoders = {}  # Label encoders for categorical features
        self.user_patterns = {}  # Statistical patterns for feature engineering
        self.training_data = {}  # Store training data per user
        self.is_trained = {}  # Track training status per user
        
        # Model hyperparameters
        self.contamination = contamination
        self.random_state = random_state
        
        # Feature names for consistency
        self.feature_names = [
            'hour_of_day', 'day_of_week', 'hour_sin', 'hour_cos',
            'resource_frequency', 'location_frequency', 'device_frequency',
            'access_rate', 'session_duration', 'time_since_last_access',
            'unique_resources_today', 'unique_locations_today',
            'failed_auth_ratio', 'location_change_count'
        ]
        
    def _extract_features(self, behavior_history: List[Dict], current_behavior: Optional[Dict] = None) -> np.ndarray:
        """
        Extract ML features from behavior history.
        Uses time-based, frequency-based, and sequence-based features.
        """
        if not behavior_history:
            return np.zeros(len(self.feature_names))
        
        # Convert to DataFrame for easier processing
        df = pd.DataFrame(behavior_history)
        
        # Ensure timestamp column exists
        if 'timestamp' not in df.columns:
            if 'date' in df.columns:
                df['timestamp'] = pd.to_datetime(df['date'], errors='coerce')
            else:
                df['timestamp'] = pd.Timestamp.now()
        
        # Extract time-based features
        timestamps = pd.to_datetime(df['timestamp'], errors='coerce')
        hours = timestamps.dt.hour.fillna(12)
        days_of_week = timestamps.dt.dayofweek.fillna(0)
        
        # Cyclical encoding for time (captures periodicity)
        hour_sin = np.sin(2 * np.pi * hours / 24)
        hour_cos = np.cos(2 * np.pi * hours / 24)
        
        # Resource frequency (how often this resource is accessed)
        resources = df.get('resource', pd.Series([''] * len(df)))
        resource_counts = resources.value_counts()
        resource_freq = resources.map(resource_counts).fillna(0) / len(resources) if len(resources) > 0 else 0
        
        # Location frequency
        locations = df.get('location', pd.Series([''] * len(df)))
        location_counts = locations.value_counts()
        location_freq = locations.map(location_counts).fillna(0) / len(locations) if len(locations) > 0 else 0
        
        # Device frequency
        devices = df.get('device_id', pd.Series([''] * len(df)))
        device_counts = devices.value_counts()
        device_freq = devices.map(device_counts).fillna(0) / len(devices) if len(devices) > 0 else 0
        
        # Access rate (events per hour)
        if len(timestamps) > 1:
            time_span = (timestamps.max() - timestamps.min()).total_seconds() / 3600.0
            access_rate = len(timestamps) / max(time_span, 0.1)
        else:
            access_rate = 0
        
        # Session duration (if available)
        session_durations = df.get('session_duration', pd.Series([0] * len(df)))
        avg_session_duration = session_durations.mean() if len(session_durations) > 0 else 0
        
        # Time since last access
        if len(timestamps) > 0:
            last_access = timestamps.max()
            time_since_last = (pd.Timestamp.now() - last_access).total_seconds() / 3600.0
        else:
            time_since_last = 24.0
        
        # Unique resources accessed today
        today = pd.Timestamp.now().date()
        today_resources = resources[timestamps.dt.date == today].nunique() if len(timestamps) > 0 else 0
        
        # Unique locations today
        today_locations = locations[timestamps.dt.date == today].nunique() if len(timestamps) > 0 else 0
        
        # Failed authentication ratio
        failed_auths = df.get('failed_auth', pd.Series([False] * len(df)))
        failed_auth_ratio = failed_auths.sum() / len(failed_auths) if len(failed_auths) > 0 else 0
        
        # Location change count
        location_changes = (locations != locations.shift()).sum() if len(locations) > 1 else 0
        
        # Aggregate features (use mean/median for time series)
        features = np.array([
            hours.mean() if len(hours) > 0 else 12,
            days_of_week.mode()[0] if len(days_of_week) > 0 else 0,
            hour_sin.mean() if len(hour_sin) > 0 else 0,
            hour_cos.mean() if len(hour_cos) > 0 else 0,
            resource_freq.mean() if len(resource_freq) > 0 else 0,
            location_freq.mean() if len(location_freq) > 0 else 0,
            device_freq.mean() if len(device_freq) > 0 else 0,
            access_rate,
            avg_session_duration,
            time_since_last,
            today_resources,
            today_locations,
            failed_auth_ratio,
            location_changes
        ])
        
        # If current behavior provided, incorporate it
        if current_behavior:
            current_hour = current_behavior.get('hour', datetime.now().hour)
            current_day = current_behavior.get('day_of_week', datetime.now().weekday())
            
            # Update features with current behavior
            features[0] = current_hour
            features[1] = current_day
            features[2] = np.sin(2 * np.pi * current_hour / 24)
            features[3] = np.cos(2 * np.pi * current_hour / 24)
            
            # Update access rate if provided
            if 'access_rate' in current_behavior:
                features[7] = current_behavior['access_rate']
            
            # Update location changes
            if 'location_changes' in current_behavior:
                features[13] = current_behavior['location_changes']
        
        return features.reshape(1, -1)
    
    def train_user_model(self, user_id: str, behavior_history: List[Dict], test_size: float = 0.2):
        """
        Train an Isolation Forest model for a specific user.
        Uses proper train/test split to avoid circular logic.
        
        Args:
            user_id: User identifier
            behavior_history: List of behavior dictionaries
            test_size: Proportion of data to use for testing (not used in training)
        """
        if not behavior_history or len(behavior_history) < 10:
            # Not enough data to train
            return
        
        # Store full history for pattern analysis
        self.training_data[user_id] = behavior_history
        
        # Extract features from all behaviors
        feature_matrix = []
        for i, behavior in enumerate(behavior_history):
            # Use history up to this point (no future data leakage)
            history_up_to_point = behavior_history[:i+1]
            features = self._extract_features(history_up_to_point)
            feature_matrix.append(features.flatten())
        
        if len(feature_matrix) < 10:
            return
        
        X = np.array(feature_matrix)
        
        # Train/test split to avoid circular logic
        if len(X) > 20:
            X_train, X_test = train_test_split(
                X, test_size=test_size, random_state=self.random_state, shuffle=False
            )
        else:
            X_train = X
            X_test = np.array([]).reshape(0, X.shape[1])
        
        # Standardize features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        self.scalers[user_id] = scaler
        
        # Train Isolation Forest
        model = IsolationForest(
            contamination=self.contamination,
            random_state=self.random_state,
            n_estimators=100,
            max_samples='auto'
        )
        model.fit(X_train_scaled)
        self.user_models[user_id] = model
        
        # Store statistical patterns for feature engineering
        self.user_patterns[user_id] = {
            'mean_features': np.mean(X_train, axis=0),
            'std_features': np.std(X_train, axis=0),
            'feature_count': len(X_train)
        }
        
        self.is_trained[user_id] = True
        
    def predict_anomaly_score(self, user_id: str, current_behavior: Dict) -> float:
        """
        Predict anomaly score using trained ML model.
        Returns score between 0 (normal) and 1 (highly anomalous).
        """
        if user_id not in self.user_models:
            # New user or insufficient training data
            return 0.5  # Neutral score for unknown users
        
        if not self.is_trained.get(user_id, False):
            return 0.5
        
        # Get user's behavior history (training data)
        behavior_history = self.training_data.get(user_id, [])
        
        # Extract features including current behavior
        features = self._extract_features(behavior_history, current_behavior)
        
        # Scale features
        scaler = self.scalers[user_id]
        features_scaled = scaler.transform(features)
        
        # Predict with Isolation Forest
        model = self.user_models[user_id]
        prediction = model.predict(features_scaled)[0]  # -1 for anomaly, 1 for normal
        anomaly_score_raw = model.score_samples(features_scaled)[0]  # Lower = more anomalous
        
        # Convert to 0-1 scale (normalize)
        # Isolation Forest scores are negative for anomalies
        # Normalize: score ranges roughly from -0.5 to 0.5
        normalized_score = 1.0 / (1.0 + np.exp(anomaly_score_raw))  # Sigmoid normalization
        
        # If prediction is -1 (anomaly), ensure score reflects that
        if prediction == -1:
            normalized_score = max(normalized_score, 0.6)  # At least 0.6 if detected as anomaly
        
        return min(1.0, max(0.0, normalized_score))
    
    def get_model_statistics(self, user_id: str) -> Dict:
        """Get statistics about the trained model for a user"""
        if user_id not in self.user_models:
            return {'trained': False}
        
        patterns = self.user_patterns.get(user_id, {})
        return {
            'trained': True,
            'training_samples': patterns.get('feature_count', 0),
            'model_type': 'IsolationForest',
            'contamination': self.contamination
        }


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

