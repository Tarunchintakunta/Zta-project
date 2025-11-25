#!/usr/bin/env python3
"""
Comprehensive Test Suite - Runs ALL tests and verifies expected outputs
Tests every component and improvement
"""

import sys
import os
from datetime import datetime
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test results tracker
test_results = []
total_tests = 0
passed_tests = 0

def test_result(test_name, passed, message=""):
    """Record test result"""
    global total_tests, passed_tests
    total_tests += 1
    if passed:
        passed_tests += 1
    status = "✓ PASS" if passed else "✗ FAIL"
    test_results.append((test_name, passed, message))
    print(f"{status}: {test_name}")
    if message:
        print(f"      {message}")
    return passed

def print_header(title):
    """Print test section header"""
    print(f"\n{'='*70}")
    print(f"{title}")
    print(f"{'='*70}\n")

def test_1_ml_model_import():
    """Test 1: ML Model Import and Basic Functionality"""
    print_header("TEST 1: ML Model Import and Basic Functionality")
    
    try:
        from core.ai_engine import BehavioralAnalyticsModel
        model = BehavioralAnalyticsModel()
        
        # Check model has required attributes
        assert hasattr(model, 'user_models'), "Missing user_models attribute"
        assert hasattr(model, 'feature_names'), "Missing feature_names attribute"
        assert len(model.feature_names) >= 14, f"Expected 14+ features, got {len(model.feature_names)}"
        
        return test_result("ML Model Import", True, f"Model created with {len(model.feature_names)} features")
    except Exception as e:
        return test_result("ML Model Import", False, str(e))

def test_2_ml_model_training():
    """Test 2: ML Model Training"""
    print_header("TEST 2: ML Model Training")
    
    try:
        from core.ai_engine import BehavioralAnalyticsModel
        from datetime import datetime, timedelta
        import numpy as np
        
        model = BehavioralAnalyticsModel()
        
        # Generate training data
        behavior_history = []
        base_time = datetime.now() - timedelta(days=30)
        
        for i in range(50):
            behavior_history.append({
                'timestamp': base_time + timedelta(hours=i*2),
                'hour': 9 + (i % 8),
                'day_of_week': i % 7,
                'resource': f'resource_{i % 5}',
                'location': f'location_{i % 3}',
                'device_id': f'device_{i % 2}',
                'date': str((base_time + timedelta(hours=i*2)).date()),
                'success': True,
                'failed_auth': False,
                'access_rate': 1.0 + np.random.random() * 0.5,
                'location_changes': 0
            })
        
        # Train model
        model.train_user_model('test_user', behavior_history)
        
        # Verify training
        stats = model.get_model_statistics('test_user')
        assert stats.get('trained', False), "Model not marked as trained"
        assert stats.get('training_samples', 0) > 0, "No training samples recorded"
        
        return test_result("ML Model Training", True, 
                          f"Trained on {stats.get('training_samples', 0)} samples")
    except Exception as e:
        return test_result("ML Model Training", False, str(e))

def test_3_ml_model_prediction():
    """Test 3: ML Model Prediction"""
    print_header("TEST 3: ML Model Prediction")
    
    try:
        from core.ai_engine import BehavioralAnalyticsModel
        from datetime import datetime, timedelta
        import numpy as np
        
        model = BehavioralAnalyticsModel()
        
        # Generate and train
        behavior_history = []
        base_time = datetime.now() - timedelta(days=30)
        for i in range(50):
            behavior_history.append({
                'timestamp': base_time + timedelta(hours=i*2),
                'hour': 9 + (i % 8),
                'day_of_week': i % 7,
                'resource': f'resource_{i % 5}',
                'location': f'location_{i % 3}',
                'device_id': f'device_{i % 2}',
                'date': str((base_time + timedelta(hours=i*2)).date()),
                'success': True,
                'failed_auth': False
            })
        
        model.train_user_model('test_user', behavior_history)
        
        # Test prediction
        behavior = {
            'hour': 14,
            'resource': 'resource_0',
            'location': 'location_0',
            'access_rate': 1.5,
            'location_changes': 0
        }
        
        score = model.predict_anomaly_score('test_user', behavior)
        assert 0.0 <= score <= 1.0, f"Score out of range: {score}"
        
        return test_result("ML Model Prediction", True, f"Prediction score: {score:.3f}")
    except Exception as e:
        return test_result("ML Model Prediction", False, str(e))

def test_4_anomaly_detector():
    """Test 4: AI Anomaly Detector"""
    print_header("TEST 4: AI Anomaly Detector")
    
    try:
        from core.ai_engine import AIAnomalyDetector
        from datetime import datetime, timedelta
        
        detector = AIAnomalyDetector()
        
        # Check components
        assert hasattr(detector, 'behavioral_model'), "Missing behavioral_model"
        assert hasattr(detector, 'threat_model'), "Missing threat_model"
        
        # Test detection
        behavior = {
            'hour': 14,
            'resource': 'resource_0',
            'location': 'location_0',
            'access_rate': 1.5,
            'location_changes': 0
        }
        
        result = detector.detect_behavioral_anomaly('test_user', behavior)
        assert 'is_anomalous' in result, "Missing is_anomalous in result"
        assert 'anomaly_score' in result, "Missing anomaly_score in result"
        assert 0.0 <= result['anomaly_score'] <= 1.0, "Invalid anomaly score"
        
        return test_result("AI Anomaly Detector", True, 
                          f"Detection working, score: {result['anomaly_score']:.3f}")
    except Exception as e:
        return test_result("AI Anomaly Detector", False, str(e))

def test_5_data_loader():
    """Test 5: Real-World Data Loader"""
    print_header("TEST 5: Real-World Data Loader")
    
    try:
        from data_loader import RealWorldDataLoader
        
        loader = RealWorldDataLoader()
        assert hasattr(loader, 'load_dataset'), "Missing load_dataset method"
        assert hasattr(loader, 'supported_formats'), "Missing supported_formats"
        
        # Test loading (will return empty if no file, which is OK)
        train, test = loader.load_dataset('nonexistent.csv', format_type='csv')
        assert isinstance(train, list), "Train data should be list"
        assert isinstance(test, list), "Test data should be list"
        
        return test_result("Real-World Data Loader", True, 
                          f"Loader supports {len(loader.supported_formats)} formats")
    except Exception as e:
        return test_result("Real-World Data Loader", False, str(e))

def test_6_realistic_generator():
    """Test 6: Realistic Behavior Generator"""
    print_header("TEST 6: Realistic Behavior Generator")
    
    try:
        from simulation.realistic_behavior_generator import RealisticBehaviorGenerator
        from models import User, Device, Application
        
        # Create minimal test data
        users = [User(user_id='U1', name='Test', role='employee', location='office', department='IT')]
        devices = [Device(device_id='D1', device_type='laptop', owner_id='U1', os_version='Windows 11')]
        apps = [Application(app_id='A1', name='Email', security_level='medium', app_type='web')]
        
        generator = RealisticBehaviorGenerator(users, devices, apps)
        
        assert hasattr(generator, 'user_patterns'), "Missing user_patterns"
        assert hasattr(generator, 'role_resource_mapping'), "Missing role_resource_mapping"
        
        # Check user patterns initialized
        if 'U1' in generator.user_patterns:
            pattern = generator.user_patterns['U1']
            assert 'work_start_hour' in pattern, "Missing work_start_hour"
            assert 'work_end_hour' in pattern, "Missing work_end_hour"
        
        return test_result("Realistic Behavior Generator", True, "Generator initialized correctly")
    except Exception as e:
        return test_result("Realistic Behavior Generator", False, str(e))

def test_7_environment_setup():
    """Test 7: Environment Setup with Realistic Generation"""
    print_header("TEST 7: Environment Setup")
    
    try:
        from simulation.environment import HybridWorkEnvironment
        
        env = HybridWorkEnvironment(use_realistic_generation=True)
        env.setup_environment()
        
        assert len(env.users) > 0, "No users created"
        assert len(env.devices) > 0, "No devices created"
        assert len(env.applications) > 0, "No applications created"
        assert env.behavior_generator is not None, "Behavior generator not initialized"
        
        return test_result("Environment Setup", True, 
                          f"Created {len(env.users)} users, {len(env.devices)} devices")
    except Exception as e:
        return test_result("Environment Setup", False, str(e))

def test_8_train_test_separation():
    """Test 8: Train/Test Separation"""
    print_header("TEST 8: Train/Test Separation")
    
    try:
        from simulation.environment import HybridWorkEnvironment
        
        env = HybridWorkEnvironment(use_realistic_generation=True)
        env.setup_environment()
        
        # Set training phase
        env.set_training_phase(True, training_days=5)
        env.identity_manager.set_training_phase(True)
        
        # Simulate training days
        for day in range(1, 6):
            env.simulate_day(day)
        
        initial_count = len(env.identity_manager.ai_detector.behavioral_model.user_models)
        
        # Set testing phase
        env.set_training_phase(False, training_days=5)
        env.identity_manager.set_training_phase(False)
        
        # Simulate test days
        for day in range(6, 8):
            env.simulate_day(day)
        
        final_count = len(env.identity_manager.ai_detector.behavioral_model.user_models)
        
        # Models shouldn't increase during testing
        assert final_count <= initial_count, "Models retrained during testing phase"
        
        return test_result("Train/Test Separation", True, 
                          f"Models: {initial_count} before test, {final_count} after (frozen)")
    except Exception as e:
        return test_result("Train/Test Separation", False, str(e))

def test_9_identity_manager_ai():
    """Test 9: Identity Manager AI Integration"""
    print_header("TEST 9: Identity Manager AI Integration")
    
    try:
        from simulation.environment import HybridWorkEnvironment
        
        env = HybridWorkEnvironment(use_realistic_generation=True)
        env.setup_environment()
        
        assert hasattr(env.identity_manager, 'ai_detector'), "Missing ai_detector"
        assert hasattr(env.identity_manager, 'set_training_phase'), "Missing set_training_phase"
        
        # Test training phase control
        env.identity_manager.set_training_phase(True)
        assert env.identity_manager.training_phase == True, "Training phase not set"
        
        env.identity_manager.set_training_phase(False)
        assert env.identity_manager.training_phase == False, "Testing phase not set"
        
        return test_result("Identity Manager AI Integration", True, "AI integration working")
    except Exception as e:
        return test_result("Identity Manager AI Integration", False, str(e))

def test_10_feature_engineering():
    """Test 10: Feature Engineering"""
    print_header("TEST 10: Feature Engineering")
    
    try:
        from core.ai_engine import BehavioralAnalyticsModel
        from datetime import datetime, timedelta
        
        model = BehavioralAnalyticsModel()
        
        # Check feature extraction
        behavior_history = [{
            'timestamp': datetime.now() - timedelta(hours=i),
            'hour': 9 + (i % 8),
            'day_of_week': i % 7,
            'resource': f'resource_{i % 5}',
            'location': f'location_{i % 3}',
            'device_id': f'device_{i % 2}',
            'date': str((datetime.now() - timedelta(hours=i)).date()),
            'success': True,
            'failed_auth': False
        } for i in range(20)]
        
        # Extract features
        features = model._extract_features(behavior_history)
        assert features.shape[1] == len(model.feature_names), "Feature count mismatch"
        
        # Check cyclical encoding exists
        assert 'hour_sin' in model.feature_names, "Missing hour_sin (cyclical encoding)"
        assert 'hour_cos' in model.feature_names, "Missing hour_cos (cyclical encoding)"
        
        return test_result("Feature Engineering", True, 
                          f"Extracted {features.shape[1]} features correctly")
    except Exception as e:
        return test_result("Feature Engineering", False, str(e))

def test_11_experiment_runner():
    """Test 11: Experiment Runner"""
    print_header("TEST 11: Experiment Runner")
    
    try:
        from simulation.experiment import ExperimentRunner
        
        runner = ExperimentRunner("test_experiment")
        
        assert hasattr(runner, 'run_baseline_scenario'), "Missing run_baseline_scenario"
        assert hasattr(runner, 'run_zta_scenario'), "Missing run_zta_scenario"
        assert hasattr(runner, 'compare_scenarios'), "Missing compare_scenarios"
        assert hasattr(runner, '_train_ml_models'), "Missing _train_ml_models"
        
        return test_result("Experiment Runner", True, "Experiment runner initialized")
    except Exception as e:
        return test_result("Experiment Runner", False, str(e))

def test_12_dependencies():
    """Test 12: Required Dependencies"""
    print_header("TEST 12: Required Dependencies")
    
    dependencies = {
        'sklearn': 'scikit-learn',
        'numpy': 'numpy',
        'pandas': 'pandas',
        'faker': 'faker'
    }
    
    missing = []
    for module, package in dependencies.items():
        try:
            __import__(module)
            test_result(f"Dependency: {package}", True)
        except ImportError:
            missing.append(package)
            test_result(f"Dependency: {package}", False, "Not installed")
    
    if missing:
        return test_result("All Dependencies", False, f"Missing: {', '.join(missing)}")
    else:
        return test_result("All Dependencies", True, "All dependencies installed")

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("COMPREHENSIVE TEST SUITE - ALL IMPROVEMENTS")
    print("="*70)
    print("\nTesting all components and improvements...")
    
    # Run all tests
    tests = [
        test_12_dependencies,  # Check dependencies first
        test_1_ml_model_import,
        test_2_ml_model_training,
        test_3_ml_model_prediction,
        test_4_anomaly_detector,
        test_5_data_loader,
        test_6_realistic_generator,
        test_7_environment_setup,
        test_8_train_test_separation,
        test_9_identity_manager_ai,
        test_10_feature_engineering,
        test_11_experiment_runner,
    ]
    
    for test_func in tests:
        try:
            test_func()
        except Exception as e:
            test_result(test_func.__name__, False, f"Test crashed: {str(e)}")
            traceback.print_exc()
    
    # Print summary
    print_header("TEST SUMMARY")
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
    
    print("\nDetailed Results:")
    print("-" * 70)
    for test_name, passed, message in test_results:
        status = "✓" if passed else "✗"
        print(f"{status} {test_name}")
        if message and not passed:
            print(f"    Error: {message}")
    
    print("\n" + "="*70)
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Everything is working correctly.")
    else:
        print(f"⚠ {total_tests - passed_tests} test(s) failed. Check errors above.")
    print("="*70 + "\n")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

