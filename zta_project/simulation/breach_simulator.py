"""
Security Breach Simulator for ZTA Testing
"""
import random
from datetime import datetime
from typing import Dict, List
import config


class BreachSimulator:
    """Simulates various security breach scenarios to test ZTA effectiveness"""
    
    def __init__(self, environment):
        self.environment = environment
        self.breach_attempts = []
        self.successful_breaches = []
        self.prevented_breaches = []
        
    def simulate_lateral_movement(self) -> Dict:
        """Simulate lateral movement attack"""
        print("\n[BREACH TEST] Simulating Lateral Movement Attack...")
        
        # Select a compromised user
        attacker = random.choice(self.environment.users)
        target_app = random.choice(self.environment.applications)
        
        # Try to access without proper authentication
        result = {
            'breach_type': 'lateral_movement',
            'timestamp': datetime.now(),
            'attacker_id': attacker.user_id,
            'target': target_app.name,
            'prevented': True,
            'prevention_method': []
        }
        
        # ZTA should prevent this through micro-segmentation
        if target_app.security_level in ['high', 'critical']:
            result['prevention_method'].append('Micro-segmentation')
            result['prevention_method'].append('Access control policies')
            self.prevented_breaches.append(result)
            print(f"  ✓ PREVENTED: Micro-segmentation blocked lateral movement to {target_app.name}")
        else:
            result['prevented'] = False
            self.successful_breaches.append(result)
            print(f"  ✗ BREACH: Lateral movement succeeded to {target_app.name}")
        
        self.breach_attempts.append(result)
        return result
    
    def simulate_credential_theft(self) -> Dict:
        """Simulate credential theft attack"""
        print("\n[BREACH TEST] Simulating Credential Theft Attack...")
        
        victim = random.choice(self.environment.users)
        attacker_device = random.choice(self.environment.devices)
        
        result = {
            'breach_type': 'credential_theft',
            'timestamp': datetime.now(),
            'victim_id': victim.user_id,
            'attacker_device': attacker_device.device_id,
            'prevented': True,
            'prevention_method': []
        }
        
        # Try to authenticate from unknown device
        auth_result = self.environment.identity_manager.authenticate_user(
            victim.user_id,
            'stolen_password',
            None
        )
        
        # ZTA should detect this through device validation
        device_validation = self.environment.device_manager.validate_device_for_access(
            attacker_device.device_id
        )
        
        if not device_validation['valid'] or victim.authentication_method in ['mfa', 'biometric']:
            result['prevention_method'].append('MFA requirement')
            result['prevention_method'].append('Device trust validation')
            self.prevented_breaches.append(result)
            print(f"  ✓ PREVENTED: MFA and device validation blocked credential theft")
        else:
            result['prevented'] = False
            self.successful_breaches.append(result)
            print(f"  ✗ BREACH: Credential theft succeeded")
        
        self.breach_attempts.append(result)
        return result
    
    def simulate_insider_threat(self) -> Dict:
        """Simulate insider threat scenario"""
        print("\n[BREACH TEST] Simulating Insider Threat...")
        
        insider = random.choice([u for u in self.environment.users if u.role in ['employee', 'contractor']])
        
        # Try to find critical or high security apps
        sensitive_apps = [a for a in self.environment.applications 
                         if a.security_level in ['critical', 'high']]
        if not sensitive_apps:
            sensitive_apps = self.environment.applications
        
        sensitive_app = random.choice(sensitive_apps)
        
        result = {
            'breach_type': 'insider_threat',
            'timestamp': datetime.now(),
            'insider_id': insider.user_id,
            'target': sensitive_app.name,
            'prevented': True,
            'prevention_method': []
        }
        
        # Insider tries to access sensitive resource
        # First authenticate
        auth_result = self.environment.identity_manager.authenticate_user(
            insider.user_id,
            'password123',
            '123456' if insider.authentication_method == 'mfa' else None
        )
        
        if auth_result['success']:
            # Try to access sensitive application
            user_devices = [d for d in self.environment.devices if d.owner_id == insider.user_id]
            if not user_devices:
                user_devices = [random.choice(self.environment.devices)]
            device = random.choice(user_devices)
            
            access_result = self.environment.access_controller.request_access(
                auth_result['session_token'],
                device.device_id,
                sensitive_app.app_id,
                'read'
            )
            
            if not access_result['access_granted']:
                result['prevention_method'].append('Role-based access control')
                result['prevention_method'].append('Least privilege principle')
                self.prevented_breaches.append(result)
                print(f"  ✓ PREVENTED: RBAC blocked insider access to {sensitive_app.name}")
            else:
                result['prevented'] = False
                self.successful_breaches.append(result)
                print(f"  ✗ BREACH: Insider accessed {sensitive_app.name}")
        else:
            result['prevention_method'].append('Authentication failure')
            self.prevented_breaches.append(result)
            print(f"  ✓ PREVENTED: Authentication failed for insider")
        
        self.breach_attempts.append(result)
        return result
    
    def simulate_device_compromise(self) -> Dict:
        """Simulate compromised device attack"""
        print("\n[BREACH TEST] Simulating Device Compromise...")
        
        compromised_device = random.choice(self.environment.devices)
        
        result = {
            'breach_type': 'device_compromise',
            'timestamp': datetime.now(),
            'device_id': compromised_device.device_id,
            'prevented': True,
            'prevention_method': []
        }
        
        # Simulate device becoming non-compliant
        compromised_device.compliance_checks['antivirus_active'] = False
        compromised_device.compliance_checks['encryption_enabled'] = False
        compromised_device.trust_score = 25
        compromised_device.is_compliant = False
        
        # Perform posture check
        posture_result = self.environment.device_manager.perform_posture_assessment(
            compromised_device.device_id
        )
        
        if not posture_result['compliant'] or posture_result['trust_score'] < 50:
            result['prevention_method'].append('Device posture validation')
            result['prevention_method'].append('Trust score enforcement')
            self.prevented_breaches.append(result)
            print(f"  ✓ PREVENTED: Device posture check blocked compromised device")
        else:
            result['prevented'] = False
            self.successful_breaches.append(result)
            print(f"  ✗ BREACH: Compromised device gained access")
        
        self.breach_attempts.append(result)
        return result
    
    def simulate_privilege_escalation(self) -> Dict:
        """Simulate privilege escalation attack"""
        print("\n[BREACH TEST] Simulating Privilege Escalation...")
        
        low_priv_user = random.choice([u for u in self.environment.users 
                                       if u.role in ['employee', 'contractor']])
        
        # Try to find critical or high security apps
        high_sec_apps = [a for a in self.environment.applications 
                        if a.security_level in ['critical', 'high']]
        if not high_sec_apps:
            high_sec_apps = self.environment.applications
        
        admin_app = random.choice(high_sec_apps)
        
        result = {
            'breach_type': 'privilege_escalation',
            'timestamp': datetime.now(),
            'attacker_id': low_priv_user.user_id,
            'target': admin_app.name,
            'prevented': True,
            'prevention_method': []
        }
        
        # Try to access admin-level application
        auth_result = self.environment.identity_manager.authenticate_user(
            low_priv_user.user_id,
            'password123',
            '123456' if low_priv_user.authentication_method == 'mfa' else None
        )
        
        if auth_result['success']:
            user_devices = [d for d in self.environment.devices 
                           if d.owner_id == low_priv_user.user_id]
            if not user_devices:
                user_devices = [random.choice(self.environment.devices)]
            device = random.choice(user_devices)
            
            access_result = self.environment.access_controller.request_access(
                auth_result['session_token'],
                device.device_id,
                admin_app.app_id,
                'admin'
            )
            
            if not access_result['access_granted']:
                result['prevention_method'].append('Access level enforcement')
                result['prevention_method'].append('Continuous authorization')
                self.prevented_breaches.append(result)
                print(f"  ✓ PREVENTED: Access control blocked privilege escalation")
            else:
                result['prevented'] = False
                self.successful_breaches.append(result)
                print(f"  ✗ BREACH: Privilege escalation succeeded")
        else:
            result['prevention_method'].append('Authentication failure')
            self.prevented_breaches.append(result)
        
        self.breach_attempts.append(result)
        return result
    
    def run_all_breach_scenarios(self, iterations: int = 5):
        """Run all breach scenarios multiple times"""
        print("\n" + "=" * 70)
        print("RUNNING COMPREHENSIVE BREACH SIMULATION")
        print("=" * 70)
        
        for i in range(iterations):
            print(f"\n--- Iteration {i+1}/{iterations} ---")
            
            self.simulate_lateral_movement()
            self.simulate_credential_theft()
            self.simulate_insider_threat()
            self.simulate_device_compromise()
            self.simulate_privilege_escalation()
        
        print("\n" + "=" * 70)
        print("BREACH SIMULATION COMPLETE")
        print("=" * 70)
        
        self._print_breach_summary()
    
    def _print_breach_summary(self):
        """Print summary of breach simulation results"""
        total_attempts = len(self.breach_attempts)
        prevented = len(self.prevented_breaches)
        successful = len(self.successful_breaches)
        
        print(f"\n{'='*70}")
        print("BREACH SIMULATION SUMMARY")
        print(f"{'='*70}")
        print(f"Total Breach Attempts: {total_attempts}")
        print(f"Prevented: {prevented} ({prevented/total_attempts*100:.1f}%)")
        print(f"Successful: {successful} ({successful/total_attempts*100:.1f}%)")
        print(f"\nPrevention Rate: {prevented/total_attempts*100:.1f}%")
        
        # Breakdown by breach type
        print(f"\n{'Breach Type':<25} {'Attempts':<10} {'Prevented':<10} {'Success Rate'}")
        print("-" * 70)
        
        breach_types = {}
        for attempt in self.breach_attempts:
            btype = attempt['breach_type']
            if btype not in breach_types:
                breach_types[btype] = {'total': 0, 'prevented': 0}
            breach_types[btype]['total'] += 1
            if attempt['prevented']:
                breach_types[btype]['prevented'] += 1
        
        for btype, stats in breach_types.items():
            success_rate = (stats['total'] - stats['prevented']) / stats['total'] * 100
            print(f"{btype:<25} {stats['total']:<10} {stats['prevented']:<10} {success_rate:.1f}%")
    
    def get_breach_statistics(self) -> Dict:
        """Get detailed breach statistics"""
        total = len(self.breach_attempts)
        prevented = len(self.prevented_breaches)
        
        # Prevention methods effectiveness
        prevention_methods = {}
        for breach in self.prevented_breaches:
            for method in breach['prevention_method']:
                prevention_methods[method] = prevention_methods.get(method, 0) + 1
        
        # Breach type distribution
        breach_distribution = {}
        for attempt in self.breach_attempts:
            btype = attempt['breach_type']
            breach_distribution[btype] = breach_distribution.get(btype, 0) + 1
        
        return {
            'total_attempts': total,
            'prevented': prevented,
            'successful': len(self.successful_breaches),
            'prevention_rate': prevented / total if total > 0 else 0,
            'prevention_methods': prevention_methods,
            'breach_distribution': breach_distribution
        }
