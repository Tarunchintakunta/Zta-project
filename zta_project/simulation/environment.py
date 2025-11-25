"""
Hybrid Work Environment Simulator
Uses realistic behavior generation (time-based, role-based, sequence-based)
instead of fully random generation for scientific rigor.
"""
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from faker import Faker

from models import User, Device, Application
from core import IdentityManager, DeviceManager, AccessController, MonitoringSystem
from simulation.realistic_behavior_generator import RealisticBehaviorGenerator
import config


class HybridWorkEnvironment:
    """
    Simulates a hybrid work environment with ZTA implementation.
    Uses realistic behavior generation to avoid circular logic.
    """
    
    def __init__(self, use_realistic_generation: bool = True):
        self.faker = Faker()
        self.use_realistic_generation = use_realistic_generation
        
        # Initialize core components
        self.identity_manager = IdentityManager()
        self.device_manager = DeviceManager()
        self.access_controller = AccessController(self.identity_manager, self.device_manager)
        self.monitoring_system = MonitoringSystem()
        
        # Data stores
        self.users = []
        self.devices = []
        self.applications = []
        
        # Realistic behavior generator (initialized after users/devices/apps are created)
        self.behavior_generator: Optional[RealisticBehaviorGenerator] = None
        
        # Simulation state
        self.current_day = 0
        self.simulation_logs = []
        
        # Track training vs testing phase to avoid circular logic
        self.training_phase = True
        self.training_days = None  # Will be set based on train/test split
        
    def setup_environment(self):
        """Set up the simulated environment with users, devices, and applications"""
        print("Setting up hybrid work environment...")
        
        # Create users
        print(f"Creating {config.NUM_USERS} users...")
        self._create_users()
        
        # Create devices
        print(f"Creating {config.NUM_DEVICES} devices...")
        self._create_devices()
        
        # Create applications
        print(f"Creating {config.NUM_APPLICATIONS} applications...")
        self._create_applications()
        
        # Initialize realistic behavior generator
        if self.use_realistic_generation:
            self.behavior_generator = RealisticBehaviorGenerator(
                self.users, self.devices, self.applications
            )
            print("Realistic behavior generator initialized (time-based, role-based, sequence-based)")
        
        print("Environment setup complete!\n")
    
    def _create_users(self):
        """Create simulated users"""
        departments = ['IT', 'Finance', 'HR', 'Sales', 'Marketing', 'Operations', 'Engineering']
        
        for i in range(config.NUM_USERS):
            user = User(
                user_id=f"USER-{i+1:04d}",
                name=self.faker.name(),
                role=random.choice(config.USER_ROLES),
                location=random.choice(config.WORK_LOCATIONS),
                department=random.choice(departments)
            )
            
            self.users.append(user)
            self.identity_manager.register_user(user)
    
    def _create_devices(self):
        """Create simulated devices"""
        os_versions = ['Windows 11', 'Windows 10', 'macOS 13', 'macOS 12', 'Ubuntu 22.04', 'iOS 16', 'Android 13']
        
        for i in range(config.NUM_DEVICES):
            # Assign device to a random user
            owner = random.choice(self.users)
            
            device = Device(
                device_id=f"DEV-{i+1:04d}",
                device_type=random.choice(config.DEVICE_TYPES),
                owner_id=owner.user_id,
                os_version=random.choice(os_versions)
            )
            
            self.devices.append(device)
            self.device_manager.register_device(device)
    
    def _create_applications(self):
        """Create simulated applications"""
        app_names = [
            'Email System', 'File Share', 'CRM Platform', 'HR Portal',
            'Financial System', 'Project Management', 'Code Repository',
            'Customer Database', 'Analytics Dashboard', 'Video Conferencing'
        ]
        
        app_types = ['web', 'desktop', 'mobile', 'cloud']
        
        for i in range(config.NUM_APPLICATIONS):
            application = Application(
                app_id=f"APP-{i+1:04d}",
                name=app_names[i] if i < len(app_names) else f"Application-{i+1}",
                security_level=random.choice(config.SECURITY_LEVELS),
                app_type=random.choice(app_types)
            )
            
            self.applications.append(application)
            self.access_controller.register_application(application)
    
    def set_training_phase(self, training: bool, training_days: Optional[int] = None):
        """
        Set whether we're in training or testing phase.
        This helps avoid circular logic: train on early data, test on later data.
        """
        self.training_phase = training
        self.training_days = training_days
    
    def simulate_day(self, day_number: int):
        """
        Simulate one day of activity in the hybrid work environment.
        Uses realistic behavior generation if enabled.
        """
        self.current_day = day_number
        
        # Use realistic generation if enabled
        if self.use_realistic_generation and self.behavior_generator:
            self._simulate_day_realistic(day_number)
        else:
            # Fallback to original random generation
            self._simulate_day_random()
    
    def _simulate_day_realistic(self, day_number: int):
        """Simulate day using realistic behavior generation"""
        # Generate time-based events
        events = self.behavior_generator.generate_time_based_events(
            day_number, config.EVENTS_PER_DAY
        )
        
        for event in events:
            event_type = event.get('event_type', 'authentication')
            
            if event_type == 'authentication':
                self._simulate_authentication_realistic(event)
            elif event_type == 'access_request':
                self._simulate_access_request_realistic(event)
            elif event_type == 'device_check':
                self._simulate_device_check()
            else:
                # Fallback for anomalies
                if random.random() < 0.05:  # 5% chance of anomaly
                    self._simulate_anomalous_behavior()
    
    def _simulate_day_random(self):
        """Original random simulation (fallback)"""
        for _ in range(config.EVENTS_PER_DAY):
            event_type = random.choices(
                ['authentication', 'access_request', 'device_check', 'anomaly'],
                weights=[0.4, 0.45, 0.10, 0.05]
            )[0]
            
            if event_type == 'authentication':
                self._simulate_authentication()
            elif event_type == 'access_request':
                self._simulate_access_request()
            elif event_type == 'device_check':
                self._simulate_device_check()
            elif event_type == 'anomaly':
                self._simulate_anomalous_behavior()
    
    def _simulate_authentication_realistic(self, event: Dict):
        """Simulate authentication using realistic event data"""
        user = event.get('user')
        device = event.get('device')
        context = event.get('context', {})
        
        if not user or not device:
            return self._simulate_authentication()  # Fallback
        
        result = self.identity_manager.authenticate_user(
            user.user_id,
            'password123',
            '123456' if user.authentication_method == 'mfa' else None,
            context
        )
        
        # Log event
        self.monitoring_system.log_event(
            'authentication',
            'low' if result['success'] else 'medium',
            f"Authentication {'successful' if result['success'] else 'failed'} for user {user.user_id}",
            {'user_id': user.user_id, 'device_id': device.device_id}
        )
        
        self.monitoring_system.metrics['authentication_events'] += 1
        
        # Record activity for sequence-based generation
        if self.behavior_generator:
            self.behavior_generator.record_activity(user.user_id, {
                'resource_name': 'authentication',
                'timestamp': context.get('timestamp', datetime.now())
            })
        
        return result
    
    def _simulate_access_request_realistic(self, event: Dict):
        """Simulate access request using realistic event data"""
        user = event.get('user')
        device = event.get('device')
        application = event.get('application')
        context = event.get('context', {})
        
        if not user or not device or not application:
            return self._simulate_access_request()  # Fallback
        
        # First authenticate
        auth_result = self.identity_manager.authenticate_user(
            user.user_id,
            'password123',
            '123456' if user.authentication_method == 'mfa' else None
        )
        
        if not auth_result['success']:
            return
        
        session_token = auth_result['session_token']
        
        # Request access
        access_result = self.access_controller.request_access(
            session_token,
            device.device_id,
            application.app_id,
            'read',
            context
        )
        
        # Log event
        self.monitoring_system.log_event(
            'access_request',
            'low' if access_result['access_granted'] else 'medium',
            f"Access {'granted' if access_result['access_granted'] else 'denied'} for {user.user_id} to {application.name}",
            {
                'user_id': user.user_id,
                'device_id': device.device_id,
                'app_id': application.app_id,
                'granted': access_result['access_granted']
            }
        )
        
        self.monitoring_system.metrics['access_requests'] += 1
        
        if not access_result['access_granted']:
            self.monitoring_system.metrics['policy_violations'] += 1
        
        # Record activity for sequence-based generation
        if self.behavior_generator:
            self.behavior_generator.record_activity(user.user_id, {
                'resource_name': application.name,
                'timestamp': context.get('timestamp', datetime.now())
            })
    
    def _simulate_authentication(self):
        """Simulate user authentication attempt"""
        user = random.choice(self.users)
        device = random.choice([d for d in self.devices if d.owner_id == user.user_id] or self.devices)
        
        # Simulate authentication
        context = {
            'device_id': device.device_id,
            'location': user.location,
            'ip_address': self.faker.ipv4()
        }
        
        result = self.identity_manager.authenticate_user(
            user.user_id,
            'password123',  # Simulated password
            '123456' if user.authentication_method == 'mfa' else None,
            context
        )
        
        # Log event
        self.monitoring_system.log_event(
            'authentication',
            'low' if result['success'] else 'medium',
            f"Authentication {'successful' if result['success'] else 'failed'} for user {user.user_id}",
            {'user_id': user.user_id, 'device_id': device.device_id}
        )
        
        self.monitoring_system.metrics['authentication_events'] += 1
        
        return result
    
    def _simulate_access_request(self):
        """Simulate access request to an application"""
        user = random.choice(self.users)
        device = random.choice([d for d in self.devices if d.owner_id == user.user_id] or self.devices)
        application = random.choice(self.applications)
        
        # First authenticate
        auth_result = self.identity_manager.authenticate_user(
            user.user_id,
            'password123',
            '123456' if user.authentication_method == 'mfa' else None
        )
        
        if not auth_result['success']:
            return
        
        session_token = auth_result['session_token']
        
        # Request access
        context = {
            'location': user.location,
            'unusual_resource_access': random.random() < 0.05
        }
        
        access_result = self.access_controller.request_access(
            session_token,
            device.device_id,
            application.app_id,
            'read',
            context
        )
        
        # Log event
        self.monitoring_system.log_event(
            'access_request',
            'low' if access_result['access_granted'] else 'medium',
            f"Access {'granted' if access_result['access_granted'] else 'denied'} for {user.user_id} to {application.name}",
            {
                'user_id': user.user_id,
                'device_id': device.device_id,
                'app_id': application.app_id,
                'granted': access_result['access_granted']
            }
        )
        
        self.monitoring_system.metrics['access_requests'] += 1
        
        if not access_result['access_granted']:
            self.monitoring_system.metrics['policy_violations'] += 1
    
    def _simulate_device_check(self):
        """Simulate device posture check"""
        device = random.choice(self.devices)
        
        result = self.device_manager.perform_posture_assessment(device.device_id)
        
        # Log event
        self.monitoring_system.log_event(
            'device_posture_check',
            'low' if result['compliant'] else 'high',
            f"Device {device.device_id} posture check: {'compliant' if result['compliant'] else 'non-compliant'}",
            {
                'device_id': device.device_id,
                'trust_score': result['trust_score'],
                'compliant': result['compliant']
            }
        )
        
        self.monitoring_system.metrics['device_posture_checks'] += 1
    
    def _simulate_anomalous_behavior(self):
        """Simulate anomalous user behavior"""
        user = random.choice(self.users)
        device = random.choice([d for d in self.devices if d.owner_id == user.user_id] or self.devices)
        
        behavior_data = {
            'access_rate': random.randint(5, 20),
            'unusual_resources': random.choice([True, False]),
            'location_change': random.choice([True, False]),
            'failed_auth_count': random.randint(0, 5)
        }
        
        anomaly_result = self.monitoring_system.detect_anomaly(
            user.user_id,
            device.device_id,
            behavior_data
        )
        
        if anomaly_result['is_anomalous']:
            self.monitoring_system.metrics['security_incidents'] += 1
    
    def run_simulation(self, days: int = None):
        """Run the complete simulation"""
        if days is None:
            days = config.SIMULATION_DAYS
        
        print(f"\nRunning {days}-day simulation...")
        print("=" * 60)
        
        for day in range(1, days + 1):
            print(f"\nSimulating Day {day}/{days}...")
            self.simulate_day(day)
            
            if day % 7 == 0:  # Weekly summary
                print(f"\n--- Week {day // 7} Summary ---")
                self._print_weekly_summary()
        
        print("\n" + "=" * 60)
        print("Simulation complete!")
    
    def _print_weekly_summary(self):
        """Print weekly summary statistics"""
        auth_stats = self.identity_manager.get_authentication_stats()
        device_stats = self.device_manager.get_compliance_statistics()
        access_stats = self.access_controller.get_access_statistics()
        
        print(f"  Authentication Success Rate: {auth_stats['success_rate']:.2%}")
        print(f"  Device Compliance Rate: {device_stats['compliance_rate']:.2%}")
        print(f"  Access Grant Rate: {access_stats['grant_rate']:.2%}")
        print(f"  Active Sessions: {auth_stats['active_sessions']}")
        print(f"  Quarantined Devices: {device_stats['quarantined_devices']}")
    
    def get_environment_state(self) -> Dict:
        """Get current state of the environment"""
        return {
            'users': len(self.users),
            'devices': len(self.devices),
            'applications': len(self.applications),
            'current_day': self.current_day,
            'identity_stats': self.identity_manager.get_authentication_stats(),
            'device_stats': self.device_manager.get_compliance_statistics(),
            'access_stats': self.access_controller.get_access_statistics(),
            'security_dashboard': self.monitoring_system.get_security_dashboard()
        }
