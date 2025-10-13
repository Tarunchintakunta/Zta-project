"""
Data Analysis Module for ZTA Research
"""
import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Tuple
from datetime import datetime


class DataAnalyzer:
    """Analyzes ZTA implementation data and generates insights"""
    
    def __init__(self, environment, breach_simulator, usability_tester):
        self.environment = environment
        self.breach_simulator = breach_simulator
        self.usability_tester = usability_tester
        
    def analyze_security_effectiveness(self) -> Dict:
        """Analyze security effectiveness metrics"""
        print("\n" + "=" * 70)
        print("ANALYZING SECURITY EFFECTIVENESS")
        print("=" * 70)
        
        # Get breach statistics
        breach_stats = self.breach_simulator.get_breach_statistics()
        
        # Get access control statistics
        access_stats = self.environment.access_controller.get_access_statistics()
        
        # Get device compliance statistics
        device_stats = self.environment.device_manager.get_compliance_statistics()
        
        # Get authentication statistics
        auth_stats = self.environment.identity_manager.get_authentication_stats()
        
        # Calculate security score (0-100)
        security_score = self._calculate_security_score(
            breach_stats, access_stats, device_stats, auth_stats
        )
        
        results = {
            'security_score': security_score,
            'breach_prevention_rate': breach_stats['prevention_rate'],
            'access_control_effectiveness': access_stats['grant_rate'],
            'device_compliance_rate': device_stats['compliance_rate'],
            'authentication_success_rate': auth_stats['success_rate'],
            'policy_violations': access_stats['denied'],
            'quarantined_devices': device_stats['quarantined_devices']
        }
        
        print(f"\nOverall Security Score: {security_score:.1f}/100")
        print(f"Breach Prevention Rate: {breach_stats['prevention_rate']*100:.1f}%")
        print(f"Device Compliance Rate: {device_stats['compliance_rate']*100:.1f}%")
        print(f"Authentication Success Rate: {auth_stats['success_rate']*100:.1f}%")
        
        return results
    
    def _calculate_security_score(self, breach_stats, access_stats, 
                                  device_stats, auth_stats) -> float:
        """Calculate overall security score"""
        # Weighted scoring
        weights = {
            'breach_prevention': 0.35,
            'device_compliance': 0.25,
            'access_control': 0.20,
            'authentication': 0.20
        }
        
        score = (
            breach_stats['prevention_rate'] * weights['breach_prevention'] * 100 +
            device_stats['compliance_rate'] * weights['device_compliance'] * 100 +
            (1 - access_stats['denial_rate']) * weights['access_control'] * 100 +
            auth_stats['success_rate'] * weights['authentication'] * 100
        )
        
        return min(100, max(0, score))
    
    def analyze_usability_impact(self) -> Dict:
        """Analyze usability and user experience impact"""
        print("\n" + "=" * 70)
        print("ANALYZING USABILITY IMPACT")
        print("=" * 70)
        
        usability_metrics = self.usability_tester.get_usability_metrics()
        
        # Calculate usability score (0-100)
        usability_score = self._calculate_usability_score(usability_metrics)
        
        results = {
            'usability_score': usability_score,
            'task_completion_rate': usability_metrics['completion_rate'],
            'average_task_time': usability_metrics.get('average_completion_time', 0),
            'user_satisfaction': usability_metrics['average_satisfaction'],
            'sus_score': usability_metrics.get('sus_score', 0),
            'average_errors': usability_metrics.get('average_errors', 0)
        }
        
        print(f"\nOverall Usability Score: {usability_score:.1f}/100")
        print(f"Task Completion Rate: {usability_metrics['completion_rate']*100:.1f}%")
        print(f"Average User Satisfaction: {usability_metrics['average_satisfaction']:.2f}/5.0")
        print(f"SUS Score: {usability_metrics.get('sus_score', 0):.1f}/100")
        
        return results
    
    def _calculate_usability_score(self, metrics) -> float:
        """Calculate overall usability score"""
        # Weighted scoring
        weights = {
            'completion_rate': 0.30,
            'satisfaction': 0.40,
            'efficiency': 0.30
        }
        
        # Normalize time (assuming 5 seconds is ideal)
        time_score = 1.0
        if 'average_completion_time' in metrics:
            time_score = max(0, 1 - (metrics['average_completion_time'] - 2) / 10)
        
        score = (
            metrics['completion_rate'] * weights['completion_rate'] * 100 +
            (metrics['average_satisfaction'] / 5.0) * weights['satisfaction'] * 100 +
            time_score * weights['efficiency'] * 100
        )
        
        return min(100, max(0, score))
    
    def perform_comparative_analysis(self) -> Dict:
        """Compare ZTA vs traditional security (simulated baseline)"""
        print("\n" + "=" * 70)
        print("PERFORMING COMPARATIVE ANALYSIS")
        print("=" * 70)
        
        # Simulate traditional security baseline (worse performance)
        traditional_baseline = {
            'breach_prevention_rate': 0.45,  # 45% vs ZTA's higher rate
            'device_compliance_rate': 0.60,
            'authentication_success_rate': 0.75,
            'access_control_effectiveness': 0.70,
            'lateral_movement_prevention': 0.30,
            'insider_threat_detection': 0.40
        }
        
        # Get ZTA metrics
        breach_stats = self.breach_simulator.get_breach_statistics()
        device_stats = self.environment.device_manager.get_compliance_statistics()
        auth_stats = self.environment.identity_manager.get_authentication_stats()
        access_stats = self.environment.access_controller.get_access_statistics()
        
        zta_metrics = {
            'breach_prevention_rate': breach_stats['prevention_rate'],
            'device_compliance_rate': device_stats['compliance_rate'],
            'authentication_success_rate': auth_stats['success_rate'],
            'access_control_effectiveness': access_stats['grant_rate']
        }
        
        # Calculate improvements
        improvements = {}
        for metric in traditional_baseline:
            if metric in zta_metrics:
                baseline_val = traditional_baseline[metric]
                zta_val = zta_metrics[metric]
                improvement = ((zta_val - baseline_val) / baseline_val) * 100
                improvements[metric] = {
                    'baseline': baseline_val,
                    'zta': zta_val,
                    'improvement_percent': improvement
                }
        
        print("\nComparative Analysis Results:")
        print(f"{'Metric':<35} {'Traditional':<15} {'ZTA':<15} {'Improvement'}")
        print("-" * 80)
        
        for metric, data in improvements.items():
            metric_name = metric.replace('_', ' ').title()
            print(f"{metric_name:<35} {data['baseline']*100:<14.1f}% {data['zta']*100:<14.1f}% {data['improvement_percent']:>+.1f}%")
        
        return {
            'traditional_baseline': traditional_baseline,
            'zta_metrics': zta_metrics,
            'improvements': improvements
        }
    
    def perform_statistical_analysis(self) -> Dict:
        """Perform statistical analysis on collected data"""
        print("\n" + "=" * 70)
        print("PERFORMING STATISTICAL ANALYSIS")
        print("=" * 70)
        
        # Analyze authentication success rates
        auth_logs = self.environment.identity_manager.authentication_logs
        auth_success = [1 if log['success'] else 0 for log in auth_logs]
        
        # Analyze access control decisions
        access_logs = self.environment.access_controller.access_logs
        access_granted = [1 if log['granted'] else 0 for log in access_logs]
        
        # Analyze device trust scores
        devices = self.environment.devices if isinstance(self.environment.devices, list) else self.environment.devices.values()
        device_trust_scores = [d.trust_score for d in devices]
        
        # Analyze user risk scores
        user_risk_scores = [u.risk_score for u in self.environment.users]
        
        # Analyze task completion times
        task_times = [t['time_taken'] for t in self.usability_tester.task_completion_data]
        
        results = {
            'authentication': {
                'mean_success_rate': np.mean(auth_success) if auth_success else 0,
                'std_dev': np.std(auth_success) if auth_success else 0,
                'sample_size': len(auth_success)
            },
            'access_control': {
                'mean_grant_rate': np.mean(access_granted) if access_granted else 0,
                'std_dev': np.std(access_granted) if access_granted else 0,
                'sample_size': len(access_granted)
            },
            'device_trust': {
                'mean': np.mean(device_trust_scores) if device_trust_scores else 0,
                'median': np.median(device_trust_scores) if device_trust_scores else 0,
                'std_dev': np.std(device_trust_scores) if device_trust_scores else 0,
                'min': np.min(device_trust_scores) if device_trust_scores else 0,
                'max': np.max(device_trust_scores) if device_trust_scores else 0
            },
            'user_risk': {
                'mean': np.mean(user_risk_scores) if user_risk_scores else 0,
                'median': np.median(user_risk_scores) if user_risk_scores else 0,
                'std_dev': np.std(user_risk_scores) if user_risk_scores else 0
            },
            'task_completion': {
                'mean_time': np.mean(task_times) if task_times else 0,
                'median_time': np.median(task_times) if task_times else 0,
                'std_dev': np.std(task_times) if task_times else 0,
                'percentile_95': np.percentile(task_times, 95) if task_times else 0
            }
        }
        
        print("\nStatistical Analysis Results:")
        print(f"\nDevice Trust Scores:")
        print(f"  Mean: {results['device_trust']['mean']:.2f}")
        print(f"  Median: {results['device_trust']['median']:.2f}")
        print(f"  Std Dev: {results['device_trust']['std_dev']:.2f}")
        
        print(f"\nTask Completion Times:")
        print(f"  Mean: {results['task_completion']['mean_time']:.2f}s")
        print(f"  Median: {results['task_completion']['median_time']:.2f}s")
        print(f"  95th Percentile: {results['task_completion']['percentile_95']:.2f}s")
        
        return results
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        # Analyze breach prevention
        breach_stats = self.breach_simulator.get_breach_statistics()
        if breach_stats['prevention_rate'] < 0.90:
            recommendations.append(
                "Strengthen access control policies to improve breach prevention rate above 90%"
            )
        
        # Analyze device compliance
        device_stats = self.environment.device_manager.get_compliance_statistics()
        if device_stats['compliance_rate'] < 0.85:
            recommendations.append(
                "Implement automated device remediation to improve compliance rate"
            )
        
        # Analyze usability
        usability_metrics = self.usability_tester.get_usability_metrics()
        if usability_metrics['average_satisfaction'] < 3.5:
            recommendations.append(
                "Simplify authentication workflows to improve user satisfaction"
            )
        
        if usability_metrics.get('average_completion_time', 0) > 5:
            recommendations.append(
                "Optimize access control checks to reduce task completion time"
            )
        
        # Analyze authentication
        auth_stats = self.environment.identity_manager.get_authentication_stats()
        if auth_stats['success_rate'] < 0.90:
            recommendations.append(
                "Review authentication methods and provide better user training"
            )
        
        # General recommendations
        recommendations.extend([
            "Continue monitoring and adjusting ZTA policies based on usage patterns",
            "Implement user feedback mechanisms for continuous improvement",
            "Conduct regular security awareness training for all users",
            "Review and update device compliance requirements quarterly"
        ])
        
        return recommendations
    
    def create_summary_dataframe(self) -> pd.DataFrame:
        """Create a summary DataFrame for export"""
        security_analysis = self.analyze_security_effectiveness()
        usability_analysis = self.analyze_usability_impact()
        
        data = {
            'Metric': [
                'Security Score',
                'Breach Prevention Rate',
                'Device Compliance Rate',
                'Authentication Success Rate',
                'Usability Score',
                'Task Completion Rate',
                'User Satisfaction',
                'SUS Score'
            ],
            'Value': [
                f"{security_analysis['security_score']:.1f}/100",
                f"{security_analysis['breach_prevention_rate']*100:.1f}%",
                f"{security_analysis['device_compliance_rate']*100:.1f}%",
                f"{security_analysis['authentication_success_rate']*100:.1f}%",
                f"{usability_analysis['usability_score']:.1f}/100",
                f"{usability_analysis['task_completion_rate']*100:.1f}%",
                f"{usability_analysis['user_satisfaction']:.2f}/5.0",
                f"{usability_analysis['sus_score']:.1f}/100"
            ]
        }
        
        return pd.DataFrame(data)
