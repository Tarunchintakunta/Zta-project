"""
Usability Testing Module for ZTA Implementation
"""
import random
import time
from datetime import datetime
from typing import Dict, List
import config


class UsabilityTester:
    """Tests and measures usability metrics of ZTA implementation"""
    
    def __init__(self, environment):
        self.environment = environment
        self.test_results = []
        self.task_completion_data = []
        self.user_satisfaction_scores = []
        
    def simulate_user_task(self, user, task_name: str) -> Dict:
        """Simulate a user completing a task and measure metrics"""
        start_time = time.time()
        
        # Get user's device
        user_devices = [d for d in self.environment.devices if d.owner_id == user.user_id]
        if not user_devices:
            user_devices = [random.choice(self.environment.devices)]
        device = random.choice(user_devices)
        
        # Task-specific simulation
        task_result = {
            'user_id': user.user_id,
            'task_name': task_name,
            'timestamp': datetime.now(),
            'completed': False,
            'time_taken': 0,
            'steps_required': 0,
            'authentication_attempts': 0,
            'errors_encountered': 0,
            'satisfaction_score': 0
        }
        
        # Step 1: Authentication
        auth_attempts = 0
        authenticated = False
        
        while auth_attempts < 3 and not authenticated:
            auth_attempts += 1
            auth_result = self.environment.identity_manager.authenticate_user(
                user.user_id,
                'password123',
                '123456' if user.authentication_method == 'mfa' else None
            )
            authenticated = auth_result['success']
            
            if not authenticated:
                task_result['errors_encountered'] += 1
        
        task_result['authentication_attempts'] = auth_attempts
        
        if not authenticated:
            task_result['completed'] = False
            task_result['time_taken'] = time.time() - start_time
            return task_result
        
        session_token = auth_result['session_token']
        task_result['steps_required'] += 1
        
        # Step 2: Device posture check (simulated delay)
        time.sleep(random.uniform(0.1, 0.3))  # Simulate check time
        posture_result = self.environment.device_manager.perform_posture_assessment(device.device_id)
        task_result['steps_required'] += 1
        
        if not posture_result['compliant'] or posture_result['trust_score'] < 70:
            task_result['errors_encountered'] += 1
            # User might need to remediate
            if random.random() < 0.7:  # 70% chance user can fix it
                time.sleep(random.uniform(1, 3))  # Remediation time
                device.patch_device()
                # Try to release from quarantine if it was quarantined
                self.environment.device_manager.release_from_quarantine(device.device_id)
                task_result['steps_required'] += 1
            else:
                task_result['completed'] = False
                task_result['time_taken'] = time.time() - start_time
                return task_result
        
        # Step 3: Access resource
        # Reset user risk score to simulate a valid user session (or support resolution)
        user.risk_score = 0
        
        # Select an application that the user is allowed to access based on level
        valid_apps = [app for app in self.environment.applications 
                     if user.access_level >= app.required_access_level]
        
        if valid_apps:
            application = random.choice(valid_apps)
        else:
            # Fallback if no apps match (should be rare)
            application = random.choice(self.environment.applications)
            
        time.sleep(random.uniform(0.2, 0.5))  # Simulate access time
        
        access_result = self.environment.access_controller.request_access(
            session_token,
            device.device_id,
            application.app_id,
            'read'
        )
        task_result['steps_required'] += 1
        
        if not access_result['access_granted']:
            task_result['errors_encountered'] += 1
            task_result['completed'] = False
        else:
            task_result['completed'] = True
        
        # Calculate time taken
        task_result['time_taken'] = time.time() - start_time
        
        # Calculate satisfaction score (1-5 scale)
        # Based on completion, time, and errors
        if task_result['completed']:
            base_score = 5
            # Deduct for time taken (if > 5 seconds)
            if task_result['time_taken'] > 5:
                base_score -= 0.5
            # Deduct for errors
            base_score -= task_result['errors_encountered'] * 0.5
            # Deduct for multiple auth attempts
            if task_result['authentication_attempts'] > 1:
                base_score -= 0.5
            
            task_result['satisfaction_score'] = max(1, min(5, base_score))
        else:
            task_result['satisfaction_score'] = random.uniform(1, 2.5)
        
        return task_result
    
    def run_usability_tests(self, num_tests: int = 100):
        """Run comprehensive usability tests"""
        print("\n" + "=" * 70)
        print("RUNNING USABILITY TESTS")
        print("=" * 70)
        
        for i in range(num_tests):
            user = random.choice(self.environment.users)
            task = random.choice(config.USABILITY_TASKS)
            
            result = self.simulate_user_task(user, task)
            self.test_results.append(result)
            
            if result['completed']:
                self.task_completion_data.append(result)
            
            self.user_satisfaction_scores.append(result['satisfaction_score'])
            
            if (i + 1) % 20 == 0:
                print(f"  Completed {i + 1}/{num_tests} tests...")
        
        print("\n" + "=" * 70)
        print("USABILITY TESTING COMPLETE")
        print("=" * 70)
        
        self._print_usability_summary()
    
    def _print_usability_summary(self):
        """Print summary of usability test results"""
        total_tests = len(self.test_results)
        completed = len(self.task_completion_data)
        
        print(f"\n{'='*70}")
        print("USABILITY TEST SUMMARY")
        print(f"{'='*70}")
        print(f"Total Tests: {total_tests}")
        print(f"Completed Successfully: {completed} ({completed/total_tests*100:.1f}%)")
        print(f"Failed: {total_tests - completed} ({(total_tests-completed)/total_tests*100:.1f}%)")
        
        if self.task_completion_data:
            avg_time = sum(t['time_taken'] for t in self.task_completion_data) / len(self.task_completion_data)
            avg_steps = sum(t['steps_required'] for t in self.task_completion_data) / len(self.task_completion_data)
            avg_errors = sum(t['errors_encountered'] for t in self.test_results) / len(self.test_results)
            
            print(f"\nAverage Task Completion Time: {avg_time:.2f} seconds")
            print(f"Average Steps Required: {avg_steps:.1f}")
            print(f"Average Errors per Task: {avg_errors:.2f}")
        
        if self.user_satisfaction_scores:
            avg_satisfaction = sum(self.user_satisfaction_scores) / len(self.user_satisfaction_scores)
            print(f"\nAverage User Satisfaction Score: {avg_satisfaction:.2f}/5.0")
            
            # Calculate System Usability Scale (SUS) equivalent
            sus_score = (avg_satisfaction / 5.0) * 100
            print(f"SUS Score Equivalent: {sus_score:.1f}/100")
            
            if sus_score >= 80:
                rating = "Excellent"
            elif sus_score >= 70:
                rating = "Good"
            elif sus_score >= 50:
                rating = "OK"
            else:
                rating = "Poor"
            
            print(f"Usability Rating: {rating}")
        
        # Task-specific analysis
        print(f"\n{'Task':<30} {'Attempts':<10} {'Success Rate':<15} {'Avg Time'}")
        print("-" * 70)
        
        task_stats = {}
        for result in self.test_results:
            task = result['task_name']
            if task not in task_stats:
                task_stats[task] = {'total': 0, 'completed': 0, 'total_time': 0}
            
            task_stats[task]['total'] += 1
            if result['completed']:
                task_stats[task]['completed'] += 1
                task_stats[task]['total_time'] += result['time_taken']
        
        for task, stats in sorted(task_stats.items()):
            success_rate = stats['completed'] / stats['total'] * 100
            avg_time = stats['total_time'] / stats['completed'] if stats['completed'] > 0 else 0
            print(f"{task:<30} {stats['total']:<10} {success_rate:<14.1f}% {avg_time:.2f}s")
    
    def get_usability_metrics(self) -> Dict:
        """Get detailed usability metrics"""
        total = len(self.test_results)
        completed = len(self.task_completion_data)
        
        metrics = {
            'total_tests': total,
            'completion_rate': completed / total if total > 0 else 0,
            'average_satisfaction': sum(self.user_satisfaction_scores) / len(self.user_satisfaction_scores) if self.user_satisfaction_scores else 0,
        }
        
        if self.task_completion_data:
            metrics.update({
                'average_completion_time': sum(t['time_taken'] for t in self.task_completion_data) / len(self.task_completion_data),
                'average_steps_required': sum(t['steps_required'] for t in self.task_completion_data) / len(self.task_completion_data),
                'average_auth_attempts': sum(t['authentication_attempts'] for t in self.test_results) / len(self.test_results),
                'average_errors': sum(t['errors_encountered'] for t in self.test_results) / len(self.test_results)
            })
        
        # Calculate SUS score
        if self.user_satisfaction_scores:
            sus_score = (metrics['average_satisfaction'] / 5.0) * 100
            metrics['sus_score'] = sus_score
        
        return metrics
    
    def generate_user_feedback(self) -> List[Dict]:
        """Generate simulated user feedback based on test results"""
        feedback = []
        
        # Analyze common issues
        high_error_users = [r for r in self.test_results if r['errors_encountered'] > 2]
        slow_tasks = [r for r in self.task_completion_data if r['time_taken'] > 5]
        failed_tasks = [r for r in self.test_results if not r['completed']]
        
        feedback_templates = {
            'positive': [
                "The security measures give me confidence in data protection.",
                "Authentication process is straightforward once set up.",
                "I appreciate the additional security layers.",
            ],
            'negative': [
                "Too many authentication steps slow down my work.",
                "Device compliance checks are frustrating when they fail.",
                "The system is too restrictive for routine tasks.",
                "MFA requirements add unnecessary friction.",
            ],
            'neutral': [
                "Security is important but it does add some overhead.",
                "The system works well most of the time.",
                "I understand the need for security but it can be inconvenient.",
            ]
        }
        
        # Generate feedback based on satisfaction scores
        for result in random.sample(self.test_results, min(20, len(self.test_results))):
            if result['satisfaction_score'] >= 4:
                sentiment = 'positive'
            elif result['satisfaction_score'] <= 2:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
            
            feedback.append({
                'user_id': result['user_id'],
                'sentiment': sentiment,
                'satisfaction_score': result['satisfaction_score'],
                'comment': random.choice(feedback_templates[sentiment]),
                'task': result['task_name']
            })
        
        return feedback
