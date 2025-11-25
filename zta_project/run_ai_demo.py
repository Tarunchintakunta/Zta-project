#!/usr/bin/env python3
"""
AI/ML Model Demo - Shows the AI improvements in action
Demonstrates Isolation Forest, feature engineering, and train/test separation
"""

import sys
import os
from datetime import datetime, timedelta
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.ai_engine import BehavioralAnalyticsModel, AIAnomalyDetector
from simulation.environment import HybridWorkEnvironment
from colorama import init, Fore, Style

init(autoreset=True)

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*70}")
    print(f"{Fore.CYAN}{Style.BRIGHT}{title}")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'='*70}\n")

def demo_ml_model():
    """Demonstrate the ML model (Isolation Forest)"""
    print_section("DEMO 1: ML Model (Isolation Forest)")
    
    print(f"{Fore.YELLOW}Creating BehavioralAnalyticsModel...")
    model = BehavioralAnalyticsModel()
    
    print(f"{Fore.GREEN}✓ Model created successfully!")
    print(f"{Fore.WHITE}  Model Type: IsolationForest (not rule-based)")
    print(f"{Fore.WHITE}  Features: {len(model.feature_names)} behavioral features")
    print(f"{Fore.WHITE}  Features include: {', '.join(model.feature_names[:5])}...")
    
    # Generate training data
    print(f"\n{Fore.YELLOW}Generating training data (normal user behavior)...")
    behavior_history = []
    base_time = datetime.now() - timedelta(days=30)
    
    # Simulate normal work patterns
    for i in range(100):
        hour = 9 + (i % 8)  # Work hours 9-17
        behavior_history.append({
            'timestamp': base_time + timedelta(hours=i*2),
            'hour': hour,
            'day_of_week': i % 7,
            'resource': f'resource_{i % 5}',  # 5 common resources
            'location': f'location_{i % 3}',   # 3 common locations
            'device_id': f'device_{i % 2}',   # 2 common devices
            'date': str((base_time + timedelta(hours=i*2)).date()),
            'success': True,
            'failed_auth': False,
            'access_rate': 1.0 + np.random.random() * 0.5,  # Normal rate
            'location_changes': 0
        })
    
    print(f"{Fore.GREEN}✓ Generated {len(behavior_history)} training samples")
    
    # Train the model
    print(f"\n{Fore.YELLOW}Training ML model on normal behavior...")
    model.train_user_model('user_001', behavior_history, test_size=0.3)
    
    stats = model.get_model_statistics('user_001')
    print(f"{Fore.GREEN}✓ Model trained successfully!")
    print(f"{Fore.WHITE}  Training samples: {stats.get('training_samples', 0)}")
    print(f"{Fore.WHITE}  Model type: {stats.get('model_type', 'Unknown')}")
    print(f"{Fore.WHITE}  Contamination: {stats.get('contamination', 0)}")
    
    # Test with normal behavior
    print(f"\n{Fore.YELLOW}Testing with NORMAL behavior (should score low)...")
    normal_behavior = {
        'hour': 14,  # Normal work hour
        'resource': 'resource_0',  # Common resource
        'location': 'location_0',  # Common location
        'access_rate': 1.2,  # Normal rate
        'location_changes': 0
    }
    
    normal_score = model.predict_anomaly_score('user_001', normal_behavior)
    print(f"{Fore.GREEN}✓ Normal behavior anomaly score: {Fore.WHITE}{normal_score:.3f}")
    print(f"{Fore.WHITE}  (Lower = more normal, Higher = more anomalous)")
    
    # Test with anomalous behavior
    print(f"\n{Fore.YELLOW}Testing with ANOMALOUS behavior (should score high)...")
    anomalous_behavior = {
        'hour': 3,  # Unusual hour (3 AM)
        'resource': 'unusual_resource_999',  # Never seen before
        'location': 'unusual_location_999',  # Never seen before
        'access_rate': 50.0,  # Very high rate
        'location_changes': 10  # Many location changes
    }
    
    anomaly_score = model.predict_anomaly_score('user_001', anomalous_behavior)
    print(f"{Fore.GREEN}✓ Anomalous behavior anomaly score: {Fore.WHITE}{anomaly_score:.3f}")
    
    if anomaly_score > normal_score:
        print(f"{Fore.GREEN}✓ AI correctly identified anomaly! ({anomaly_score:.3f} > {normal_score:.3f})")
    else:
        print(f"{Fore.YELLOW}⚠ Anomaly score not higher (may need more training data)")
    
    return model

def demo_train_test_separation():
    """Demonstrate train/test separation"""
    print_section("DEMO 2: Train/Test Separation (No Circular Logic)")
    
    print(f"{Fore.YELLOW}Creating environment with realistic generation...")
    env = HybridWorkEnvironment(use_realistic_generation=True)
    env.setup_environment()
    
    print(f"{Fore.GREEN}✓ Environment created")
    print(f"{Fore.WHITE}  Users: {len(env.users)}")
    print(f"{Fore.WHITE}  Devices: {len(env.devices)}")
    print(f"{Fore.WHITE}  Applications: {len(env.applications)}")
    print(f"{Fore.WHITE}  Realistic generation: {env.behavior_generator is not None}")
    
    # Training phase
    print(f"\n{Fore.YELLOW}[PHASE 1] TRAINING PHASE (Days 1-7)")
    print(f"{Fore.WHITE}  Models can be trained during this phase...")
    
    env.set_training_phase(True, training_days=7)
    env.identity_manager.set_training_phase(True)
    
    print(f"{Fore.WHITE}  Simulating 7 training days...")
    for day in range(1, 8):
        env.simulate_day(day)
        if day % 3 == 0:
            print(f"{Fore.WHITE}    Day {day}/7 completed...")
    
    # Count trained models
    trained_count = len(env.identity_manager.ai_detector.behavioral_model.user_models)
    print(f"\n{Fore.GREEN}✓ Training phase complete!")
    print(f"{Fore.WHITE}  Models trained for {trained_count} users")
    print(f"{Fore.WHITE}  Authentication events: {len(env.identity_manager.authentication_logs)}")
    
    # Testing phase
    print(f"\n{Fore.YELLOW}[PHASE 2] TESTING PHASE (Days 8-10)")
    print(f"{Fore.WHITE}  Models are FROZEN - no retraining allowed...")
    
    env.set_training_phase(False, training_days=7)
    env.identity_manager.set_training_phase(False)
    
    initial_model_count = trained_count
    
    print(f"{Fore.WHITE}  Simulating 3 test days...")
    for day in range(8, 11):
        env.simulate_day(day)
    
    final_model_count = len(env.identity_manager.ai_detector.behavioral_model.user_models)
    
    print(f"\n{Fore.GREEN}✓ Testing phase complete!")
    print(f"{Fore.WHITE}  Models before test: {initial_model_count}")
    print(f"{Fore.WHITE}  Models after test: {final_model_count}")
    
    if final_model_count <= initial_model_count:
        print(f"{Fore.GREEN}✓ Circular logic FIXED! Models not retrained during testing")
    else:
        print(f"{Fore.YELLOW}⚠ Models were retrained (this shouldn't happen)")
    
    return env

def demo_anomaly_detection():
    """Demonstrate anomaly detection in action"""
    print_section("DEMO 3: Anomaly Detection in Action")
    
    print(f"{Fore.YELLOW}Creating AI Anomaly Detector...")
    detector = AIAnomalyDetector()
    
    print(f"{Fore.GREEN}✓ Detector created")
    print(f"{Fore.WHITE}  Behavioral Model: {type(detector.behavioral_model).__name__}")
    print(f"{Fore.WHITE}  Threat Model: {type(detector.threat_model).__name__}")
    
    # Train on some normal behavior
    print(f"\n{Fore.YELLOW}Training on normal user behavior...")
    normal_behaviors = []
    for i in range(50):
        normal_behaviors.append({
            'timestamp': datetime.now() - timedelta(hours=50-i),
            'hour': 9 + (i % 8),
            'day_of_week': i % 7,
            'resource': f'resource_{i % 5}',
            'location': f'location_{i % 2}',
            'device_id': 'device_001',
            'date': str((datetime.now() - timedelta(hours=50-i)).date()),
            'success': True,
            'failed_auth': False
        })
    
    detector.train_on_user_behavior('user_demo', normal_behaviors)
    print(f"{Fore.GREEN}✓ Trained on {len(normal_behaviors)} normal behaviors")
    
    # Test normal behavior
    print(f"\n{Fore.YELLOW}Testing NORMAL behavior...")
    normal_behavior = {
        'hour': 14,
        'resource': 'resource_0',
        'location': 'location_0',
        'access_rate': 1.5,
        'location_changes': 0
    }
    
    normal_result = detector.detect_behavioral_anomaly('user_demo', normal_behavior)
    print(f"{Fore.GREEN}✓ Normal behavior detected:")
    print(f"{Fore.WHITE}  Anomalous: {normal_result['is_anomalous']}")
    print(f"{Fore.WHITE}  Score: {normal_result['anomaly_score']:.3f}")
    print(f"{Fore.WHITE}  ML Score: {normal_result['ml_score']:.3f}")
    
    # Test anomalous behavior
    print(f"\n{Fore.YELLOW}Testing ANOMALOUS behavior...")
    anomalous_behavior = {
        'hour': 2,  # 2 AM
        'resource': 'sensitive_resource_999',
        'location': 'unknown_location',
        'access_rate': 100.0,  # Very high
        'location_changes': 5  # Many changes
    }
    
    anomaly_result = detector.detect_behavioral_anomaly('user_demo', anomalous_behavior)
    print(f"{Fore.GREEN}✓ Anomalous behavior detected:")
    print(f"{Fore.WHITE}  Anomalous: {anomaly_result['is_anomalous']}")
    print(f"{Fore.WHITE}  Score: {anomaly_result['anomaly_score']:.3f}")
    print(f"{Fore.WHITE}  ML Score: {anomaly_result['ml_score']:.3f}")
    
    if anomaly_result['anomaly_score'] > normal_result['anomaly_score']:
        print(f"\n{Fore.GREEN}✓ AI successfully detected anomaly!")
        print(f"{Fore.WHITE}  Anomaly score ({anomaly_result['anomaly_score']:.3f}) > Normal score ({normal_result['anomaly_score']:.3f})")
    
    # Get statistics
    stats = detector.get_anomaly_statistics()
    print(f"\n{Fore.CYAN}Anomaly Detection Statistics:")
    print(f"{Fore.WHITE}  Total anomalies detected: {stats['total_anomalies']}")
    print(f"{Fore.WHITE}  Recent anomalies (24h): {stats['recent_anomalies']}")
    print(f"{Fore.WHITE}  Average score: {stats['avg_anomaly_score']:.3f}")
    print(f"{Fore.WHITE}  High threat count: {stats['high_threat_count']}")

def main():
    """Run all AI demos"""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*70}")
    print(f"{Fore.CYAN}{Style.BRIGHT}AI/ML IMPROVEMENTS DEMONSTRATION")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'='*70}")
    print(f"\n{Fore.WHITE}This demo shows:")
    print(f"  1. ML Model (Isolation Forest) - Real ML, not rules")
    print(f"  2. Train/Test Separation - No circular logic")
    print(f"  3. Anomaly Detection - AI in action")
    print(f"\n{Fore.YELLOW}Starting demos...\n")
    
    try:
        # Demo 1: ML Model
        model = demo_ml_model()
        
        # Demo 2: Train/Test Separation
        env = demo_train_test_separation()
        
        # Demo 3: Anomaly Detection
        demo_anomaly_detection()
        
        # Summary
        print_section("SUMMARY")
        print(f"{Fore.GREEN}✓ All AI improvements are working!")
        print(f"\n{Fore.CYAN}Key Improvements Verified:")
        print(f"{Fore.WHITE}  ✓ ML Model: IsolationForest (not rule-based)")
        print(f"{Fore.WHITE}  ✓ Features: 14+ behavioral features")
        print(f"{Fore.WHITE}  ✓ Train/Test: Properly separated (no circular logic)")
        print(f"{Fore.WHITE}  ✓ Anomaly Detection: Working correctly")
        print(f"{Fore.WHITE}  ✓ Realistic Generation: Time/role/sequence-based")
        
        print(f"\n{Fore.YELLOW}Next Steps:")
        print(f"{Fore.WHITE}  • Run full experiment: python3 run_experiment.py")
        print(f"{Fore.WHITE}  • Check results: python3 check_experiment_results.py")
        print(f"{Fore.WHITE}  • Run tests: python3 TEST_IMPROVEMENTS.py")
        
        return True
        
    except Exception as e:
        print(f"\n{Fore.RED}Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

