"""
Experiment Runner for Zero Trust Architecture Research
Implements the AI-Powered Zero-Trust Framework methodology from the research paper

This module implements comparative experiments:
- Baseline Scenario: ZTA controls OFF (traditional security)
- ZTA Scenario: ZTA controls ON (full Zero Trust)
"""

import json
from datetime import datetime
from typing import Dict, List
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.environment import HybridWorkEnvironment
from simulation.breach_simulator import BreachSimulator
from testing.usability_tester import UsabilityTester
from analysis.data_analyzer import DataAnalyzer
import config


class ExperimentRunner:
    """Runs comparative experiments between Baseline and ZTA scenarios"""
    
    def __init__(self, experiment_name: str = "zta_comparison"):
        self.experiment_name = experiment_name
        self.results_dir = f"results/experiments/{experiment_name}"
        self.baseline_results = {}
        self.zta_results = {}
        self.comparison_results = {}
        
    def disable_zta_controls(self, environment: HybridWorkEnvironment):
        """Disable ZTA controls for baseline scenario"""
        # Disable strict access control policies
        environment.access_controller.update_policy('require_mfa_for_critical', False)
        environment.access_controller.update_policy('min_device_trust_score', 0)
        environment.access_controller.update_policy('max_user_risk_score', 100)
        environment.access_controller.update_policy('require_compliant_device', False)
        environment.access_controller.update_policy('block_quarantined_devices', False)
        
        # Disable continuous authentication
        environment.identity_manager.enable_continuous_auth = False
        
        # Lower device compliance requirements
        environment.device_manager.min_trust_score = 0
        
    def enable_zta_controls(self, environment: HybridWorkEnvironment):
        """Enable full ZTA controls"""
        # Enable strict access control policies
        environment.access_controller.update_policy('require_mfa_for_critical', True)
        environment.access_controller.update_policy('min_device_trust_score', 70)
        environment.access_controller.update_policy('max_user_risk_score', 50)
        environment.access_controller.update_policy('require_compliant_device', True)
        environment.access_controller.update_policy('block_quarantined_devices', True)
        
        # Enable continuous authentication
        environment.identity_manager.enable_continuous_auth = True
        
        # Set device compliance requirements
        environment.device_manager.min_trust_score = 70
    
    def run_baseline_scenario(self) -> Dict:
        """Run baseline scenario with ZTA controls disabled"""
        print("\n" + "="*80)
        print("RUNNING BASELINE SCENARIO (ZTA Controls: OFF)")
        print("="*80)
        
        # Create fresh environment
        environment = HybridWorkEnvironment()
        environment.setup_environment()
        
        # Disable ZTA controls
        self.disable_zta_controls(environment)
        
        # Run simulation
        print("\nSimulating normal operations...")
        for day in range(1, config.SIMULATION_DAYS + 1):
            if day % 5 == 0:
                print(f"  Day {day}/{config.SIMULATION_DAYS}")
            environment.simulate_day(day)
        
        # Run breach simulations
        print("\nRunning breach simulations...")
        breach_simulator = BreachSimulator(environment)
        breach_simulator.run_all_breach_scenarios(iterations=5)
        
        # Run usability tests
        print("\nRunning usability tests...")
        usability_tester = UsabilityTester(environment)
        usability_tester.run_usability_tests(num_tests=50)
        
        # Analyze results
        print("\nAnalyzing baseline results...")
        analyzer = DataAnalyzer(environment, breach_simulator, usability_tester)
        security_results = analyzer.analyze_security_effectiveness()
        usability_results = analyzer.analyze_usability_impact()
        breach_stats = breach_simulator.get_breach_statistics()
        access_stats = environment.access_controller.get_access_statistics()
        auth_stats = environment.identity_manager.get_authentication_stats()
        
        results = {
            'scenario': 'baseline',
            'timestamp': datetime.now().isoformat(),
            'security': security_results,
            'usability': usability_results,
            'breach_prevention': {
                'total_attempts': breach_stats['total_attempts'],
                'prevented': breach_stats['prevented'],
                'successful': breach_stats['successful'],
                'prevention_rate': breach_stats['prevention_rate']
            },
            'access_control': access_stats,
            'authentication': auth_stats
        }
        
        print("\n✓ Baseline scenario completed!")
        return results
    
    def run_zta_scenario(self) -> Dict:
        """Run ZTA scenario with full Zero Trust controls enabled"""
        print("\n" + "="*80)
        print("RUNNING ZTA SCENARIO (ZTA Controls: ON)")
        print("="*80)
        
        # Create fresh environment
        environment = HybridWorkEnvironment()
        environment.setup_environment()
        
        # Enable ZTA controls
        self.enable_zta_controls(environment)
        
        # Run simulation
        print("\nSimulating normal operations with ZTA...")
        for day in range(1, config.SIMULATION_DAYS + 1):
            if day % 5 == 0:
                print(f"  Day {day}/{config.SIMULATION_DAYS}")
            environment.simulate_day(day)
        
        # Run breach simulations
        print("\nRunning breach simulations...")
        breach_simulator = BreachSimulator(environment)
        breach_simulator.run_all_breach_scenarios(iterations=5)
        
        # Run usability tests
        print("\nRunning usability tests...")
        usability_tester = UsabilityTester(environment)
        usability_tester.run_usability_tests(num_tests=50)
        
        # Analyze results
        print("\nAnalyzing ZTA results...")
        analyzer = DataAnalyzer(environment, breach_simulator, usability_tester)
        security_results = analyzer.analyze_security_effectiveness()
        usability_results = analyzer.analyze_usability_impact()
        breach_stats = breach_simulator.get_breach_statistics()
        access_stats = environment.access_controller.get_access_statistics()
        auth_stats = environment.identity_manager.get_authentication_stats()
        
        results = {
            'scenario': 'zta',
            'timestamp': datetime.now().isoformat(),
            'security': security_results,
            'usability': usability_results,
            'breach_prevention': {
                'total_attempts': breach_stats['total_attempts'],
                'prevented': breach_stats['prevented'],
                'successful': breach_stats['successful'],
                'prevention_rate': breach_stats['prevention_rate']
            },
            'access_control': access_stats,
            'authentication': auth_stats
        }
        
        print("\n✓ ZTA scenario completed!")
        return results
    
    def compare_scenarios(self, baseline: Dict, zta: Dict) -> Dict:
        """Compare baseline and ZTA scenario results"""
        print("\n" + "="*80)
        print("COMPARATIVE ANALYSIS")
        print("="*80)
        
        comparison = {
            'experiment_name': self.experiment_name,
            'timestamp': datetime.now().isoformat(),
            'breach_prevention': {},
            'security_metrics': {},
            'usability_metrics': {},
            'access_control': {},
            'improvements': {}
        }
        
        # Compare breach prevention
        baseline_prevention = baseline['breach_prevention']['prevention_rate']
        zta_prevention = zta['breach_prevention']['prevention_rate']
        improvement = (zta_prevention - baseline_prevention) * 100
        
        comparison['breach_prevention'] = {
            'baseline_rate': baseline_prevention,
            'zta_rate': zta_prevention,
            'improvement_percent': improvement,
            'baseline_prevented': baseline['breach_prevention']['prevented'],
            'zta_prevented': zta['breach_prevention']['prevented'],
            'total_attempts': baseline['breach_prevention']['total_attempts']
        }
        
        # Compare security metrics
        comparison['security_metrics'] = {
            'security_score': {
                'baseline': baseline['security']['security_score'],
                'zta': zta['security']['security_score'],
                'improvement': zta['security']['security_score'] - baseline['security']['security_score']
            },
            'device_compliance': {
                'baseline': baseline['security']['device_compliance_rate'],
                'zta': zta['security']['device_compliance_rate'],
                'improvement': (zta['security']['device_compliance_rate'] - baseline['security']['device_compliance_rate']) * 100
            },
            'authentication_success': {
                'baseline': baseline['security']['authentication_success_rate'],
                'zta': zta['security']['authentication_success_rate'],
                'improvement': (zta['security']['authentication_success_rate'] - baseline['security']['authentication_success_rate']) * 100
            }
        }
        
        # Compare usability
        comparison['usability_metrics'] = {
            'usability_score': {
                'baseline': baseline['usability']['usability_score'],
                'zta': zta['usability']['usability_score'],
                'change': zta['usability']['usability_score'] - baseline['usability']['usability_score']
            },
            'task_completion': {
                'baseline': baseline['usability']['task_completion_rate'],
                'zta': zta['usability']['task_completion_rate'],
                'change': (zta['usability']['task_completion_rate'] - baseline['usability']['task_completion_rate']) * 100
            }
        }
        
        # Compare access control
        baseline_denial_rate = baseline['access_control']['denial_rate']
        zta_denial_rate = zta['access_control']['denial_rate']
        
        comparison['access_control'] = {
            'denial_rate': {
                'baseline': baseline_denial_rate,
                'zta': zta_denial_rate,
                'increase': (zta_denial_rate - baseline_denial_rate) * 100
            },
            'grant_rate': {
                'baseline': baseline['access_control']['grant_rate'],
                'zta': zta['access_control']['grant_rate'],
                'change': (zta['access_control']['grant_rate'] - baseline['access_control']['grant_rate']) * 100
            }
        }
        
        # Calculate overall improvements
        comparison['improvements'] = {
            'breach_prevention_improvement': improvement,
            'security_score_improvement': comparison['security_metrics']['security_score']['improvement'],
            'device_compliance_improvement': comparison['security_metrics']['device_compliance']['improvement'],
            'authentication_improvement': comparison['security_metrics']['authentication_success']['improvement']
        }
        
        return comparison
    
    def run_full_experiment(self) -> Dict:
        """Run complete experiment with both scenarios"""
        print("\n" + "="*80)
        print("ZERO TRUST ARCHITECTURE COMPARATIVE EXPERIMENT")
        print("Following AI-Powered Zero-Trust Framework Methodology")
        print("="*80)
        
        start_time = datetime.now()
        
        # Run baseline scenario
        baseline_results = self.run_baseline_scenario()
        self.baseline_results = baseline_results
        
        # Run ZTA scenario
        zta_results = self.run_zta_scenario()
        self.zta_results = zta_results
        
        # Compare results
        comparison = self.compare_scenarios(baseline_results, zta_results)
        self.comparison_results = comparison
        
        # Generate report
        self.generate_experiment_report(baseline_results, zta_results, comparison)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "="*80)
        print("EXPERIMENT COMPLETE")
        print("="*80)
        print(f"Total execution time: {duration:.2f} seconds")
        print(f"\nKEY FINDINGS:")
        print(f"  • Breach Prevention Improvement: {comparison['breach_prevention']['improvement_percent']:.1f}%")
        print(f"  • Security Score Improvement: {comparison['security_metrics']['security_score']['improvement']:.1f} points")
        print(f"  • Baseline Prevention Rate: {comparison['breach_prevention']['baseline_rate']*100:.1f}%")
        print(f"  • ZTA Prevention Rate: {comparison['breach_prevention']['zta_rate']*100:.1f}%")
        
        return {
            'baseline': baseline_results,
            'zta': zta_results,
            'comparison': comparison,
            'execution_time_seconds': duration
        }
    
    def generate_experiment_report(self, baseline: Dict, zta: Dict, comparison: Dict):
        """Generate comprehensive experiment report"""
        import os
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Save JSON results
        with open(f"{self.results_dir}/baseline_results.json", 'w') as f:
            json.dump(baseline, f, indent=2)
        
        with open(f"{self.results_dir}/zta_results.json", 'w') as f:
            json.dump(zta, f, indent=2)
        
        with open(f"{self.results_dir}/comparison_results.json", 'w') as f:
            json.dump(comparison, f, indent=2)
        
        # Generate text report
        report = f"""
ZERO TRUST ARCHITECTURE COMPARATIVE EXPERIMENT REPORT
Based on AI-Powered Zero-Trust Cybersecurity Framework Methodology

Experiment Name: {self.experiment_name}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

================================================================================
EXECUTIVE SUMMARY
================================================================================

This experiment compares the effectiveness of Zero Trust Architecture (ZTA) 
against traditional security (baseline) using the methodology from the 
AI-Powered Zero-Trust Cybersecurity Framework research paper.

================================================================================
BREACH PREVENTION RESULTS
================================================================================

Baseline Scenario (Traditional Security):
  • Prevention Rate: {comparison['breach_prevention']['baseline_rate']*100:.1f}%
  • Attacks Prevented: {comparison['breach_prevention']['baseline_prevented']}/{comparison['breach_prevention']['total_attempts']}
  • Successful Breaches: {comparison['breach_prevention']['total_attempts'] - comparison['breach_prevention']['baseline_prevented']}

ZTA Scenario (Zero Trust Enabled):
  • Prevention Rate: {comparison['breach_prevention']['zta_rate']*100:.1f}%
  • Attacks Prevented: {comparison['breach_prevention']['zta_prevented']}/{comparison['breach_prevention']['total_attempts']}
  • Successful Breaches: {comparison['breach_prevention']['total_attempts'] - comparison['breach_prevention']['zta_prevented']}

IMPROVEMENT: {comparison['breach_prevention']['improvement_percent']:.1f}% increase in breach prevention

================================================================================
SECURITY METRICS COMPARISON
================================================================================

Security Score:
  • Baseline: {comparison['security_metrics']['security_score']['baseline']:.1f}/100
  • ZTA: {comparison['security_metrics']['security_score']['zta']:.1f}/100
  • Improvement: {comparison['security_metrics']['security_score']['improvement']:.1f} points

Device Compliance Rate:
  • Baseline: {comparison['security_metrics']['device_compliance']['baseline']*100:.1f}%
  • ZTA: {comparison['security_metrics']['device_compliance']['zta']*100:.1f}%
  • Improvement: {comparison['security_metrics']['device_compliance']['improvement']:.1f}%

Authentication Success Rate:
  • Baseline: {comparison['security_metrics']['authentication_success']['baseline']*100:.1f}%
  • ZTA: {comparison['security_metrics']['authentication_success']['zta']*100:.1f}%
  • Improvement: {comparison['security_metrics']['authentication_success']['improvement']:.1f}%

================================================================================
USABILITY IMPACT
================================================================================

Usability Score:
  • Baseline: {comparison['usability_metrics']['usability_score']['baseline']:.1f}/100
  • ZTA: {comparison['usability_metrics']['usability_score']['zta']:.1f}/100
  • Change: {comparison['usability_metrics']['usability_score']['change']:.1f} points

Task Completion Rate:
  • Baseline: {comparison['usability_metrics']['task_completion']['baseline']*100:.1f}%
  • ZTA: {comparison['usability_metrics']['task_completion']['zta']*100:.1f}%
  • Change: {comparison['usability_metrics']['task_completion']['change']:.1f}%

================================================================================
ACCESS CONTROL ANALYSIS
================================================================================

Access Denial Rate:
  • Baseline: {comparison['access_control']['denial_rate']['baseline']*100:.1f}%
  • ZTA: {comparison['access_control']['denial_rate']['zta']*100:.1f}%
  • Increase: {comparison['access_control']['denial_rate']['increase']:.1f}%

Note: Higher denial rate in ZTA is expected and indicates stricter security.

================================================================================
CONCLUSIONS
================================================================================

The Zero Trust Architecture implementation demonstrates significant improvements 
in security effectiveness:

1. Breach Prevention: {comparison['breach_prevention']['improvement_percent']:.1f}% improvement over traditional security
2. Security Score: {comparison['security_metrics']['security_score']['improvement']:.1f} point increase
3. Device Compliance: {comparison['security_metrics']['device_compliance']['improvement']:.1f}% improvement
4. Authentication: {comparison['security_metrics']['authentication_success']['improvement']:.1f}% improvement

The ZTA framework successfully prevents more attacks while maintaining reasonable 
usability. The increased access denials are a trade-off for enhanced security,
which aligns with Zero Trust principles of "never trust, always verify."

================================================================================
"""
        
        with open(f"{self.results_dir}/experiment_report.txt", 'w') as f:
            f.write(report)
        
        print(f"\n✓ Experiment report saved to: {self.results_dir}/experiment_report.txt")
        print(f"✓ Results saved to: {self.results_dir}/")

