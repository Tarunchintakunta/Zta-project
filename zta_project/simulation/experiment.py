"""
Experiment Orchestration Module
"""
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import pandas as pd
import numpy as np
import config
from simulation.environment import HybridWorkEnvironment
from simulation.breach_simulator import BreachSimulator
from testing.usability_tester import UsabilityTester
from analysis.data_analyzer import DataAnalyzer


class ExperimentRunner:
    """Orchestrates the entire experiment process"""
    
    def __init__(self, experiment_name: str):
        self.experiment_name = experiment_name
        self.results_dir = os.path.join(config.OUTPUT_DIR, 'experiments', experiment_name)
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Initialize components
        self.environment = None
        self.breach_simulator = None
        self.usability_tester = None
        self.analyzer = None
        
        # Results storage
        self.baseline_results = {}
        self.zta_results = {}
        
    def run_full_experiment(self) -> Dict:
        """Run the complete comparative experiment"""
        print(f"\nRunning Experiment: {self.experiment_name}")
        print(f"Results will be saved to: {self.results_dir}")
        
        # 1. Run Baseline Scenario (Traditional Security)
        print("\n" + "="*80)
        print("SCENARIO 1: BASELINE SECURITY (TRADITIONAL)")
        print("="*80)
        self.baseline_results = self.run_baseline_scenario()
        
        # 2. Run ZTA Scenario (Zero Trust Architecture)
        print("\n" + "="*80)
        print("SCENARIO 2: ZERO TRUST ARCHITECTURE")
        print("="*80)
        self.zta_results = self.run_zta_scenario()
        
        # 3. Compare Results
        print("\n" + "="*80)
        print("COMPARATIVE ANALYSIS")
        print("="*80)
        comparison = self.compare_scenarios()
        
        # 4. Generate Report
        self._generate_experiment_report(comparison)
        
        return {
            'baseline': self.baseline_results,
            'zta': self.zta_results,
            'comparison': comparison
        }
    
    def run_baseline_scenario(self) -> Dict:
        """Run the baseline scenario (ZTA controls disabled)"""
        print("\nInitializing Baseline Environment...")
        
        # Setup environment with ZTA disabled
        self.environment = HybridWorkEnvironment(use_realistic_generation=True)
        self.environment.setup_environment()
        
        # Disable ZTA features
        self.environment.access_controller.policies['require_mfa_for_critical'] = False
        self.environment.access_controller.policies['require_compliant_device'] = False
        self.environment.access_controller.policies['min_device_trust_score'] = 0
        self.environment.access_controller.policies['enable_continuous_auth'] = False
        
        # Initialize simulators
        self.breach_simulator = BreachSimulator(self.environment)
        self.usability_tester = UsabilityTester(self.environment)
        self.analyzer = DataAnalyzer(self.environment, self.breach_simulator, self.usability_tester)
        
        # Run Simulation
        print("\nSimulating 30 days of activity...")
        for day in range(1, 31):
            if day % 5 == 0:
                print(f"  - Day {day}/30 completed")
            self.environment.simulate_day(day)
            
        # Run Breach Tests
        print("\nRunning Breach Simulation Tests...")
        self.breach_simulator.run_all_breach_scenarios(iterations=5)
        
        # Run Usability Tests
        print("\nRunning Usability Tests...")
        self.usability_tester.run_standard_usability_suite(iterations=20)
        
        # Analyze Results
        security_metrics = self.analyzer.analyze_security_effectiveness()
        usability_metrics = self.analyzer.analyze_usability_impact()
        breach_stats = self.breach_simulator.get_breach_statistics()
        
        print("\n[SUCCESS] Baseline scenario completed!")
        return {
            'security_metrics': security_metrics,
            'usability_metrics': usability_metrics,
            'breach_stats': breach_stats
        }
    
    def run_zta_scenario(self) -> Dict:
        """Run the ZTA scenario (ZTA controls enabled)"""
        print("\nInitializing ZTA Environment...")
        
        # Setup environment with ZTA enabled (default)
        self.environment = HybridWorkEnvironment(use_realistic_generation=True)
        self.environment.setup_environment()
        
        # Ensure ZTA features are enabled
        self.environment.access_controller.policies['require_mfa_for_critical'] = True
        self.environment.access_controller.policies['require_compliant_device'] = True
        self.environment.access_controller.policies['min_device_trust_score'] = 70
        self.environment.access_controller.policies['enable_continuous_auth'] = True
        
        # Train ML models first (Simulate historical data)
        print("\nTraining AI/ML Models...")
        self._train_ml_models()
        
        # Initialize simulators
        self.breach_simulator = BreachSimulator(self.environment)
        self.usability_tester = UsabilityTester(self.environment)
        self.analyzer = DataAnalyzer(self.environment, self.breach_simulator, self.usability_tester)
        
        # Run Simulation
        print("\nSimulating 30 days of activity...")
        for day in range(1, 31):
            if day % 5 == 0:
                print(f"  - Day {day}/30 completed")
            self.environment.simulate_day(day)
            
        # Run Breach Tests
        print("\nRunning Breach Simulation Tests...")
        self.breach_simulator.run_all_breach_scenarios(iterations=5)
        
        # Run Usability Tests
        print("\nRunning Usability Tests...")
        self.usability_tester.run_standard_usability_suite(iterations=20)
        
        # Analyze Results
        security_metrics = self.analyzer.analyze_security_effectiveness()
        usability_metrics = self.analyzer.analyze_usability_impact()
        breach_stats = self.breach_simulator.get_breach_statistics()
        
        print("\n[SUCCESS] ZTA scenario completed!")
        return {
            'security_metrics': security_metrics,
            'usability_metrics': usability_metrics,
            'breach_stats': breach_stats
        }
        
    def _train_ml_models(self):
        """Train ML models with historical data"""
        # Create a temporary environment to generate training data
        train_env = HybridWorkEnvironment(use_realistic_generation=True)
        train_env.setup_environment()
        
        # Generate 30 days of training data
        print("  - Generating historical training data...")
        train_env.set_training_phase(True, training_days=30)
        for day in range(1, 31):
            train_env.simulate_day(day)
            
        # Transfer trained models to the main environment
        print("  - Transferring trained models...")
        self.environment.identity_manager.ai_detector = train_env.identity_manager.ai_detector
        
    def compare_scenarios(self) -> Dict:
        """Compare Baseline and ZTA results"""
        
        # Calculate improvements
        sec_improvement = self.zta_results['security_metrics']['security_score'] - \
                          self.baseline_results['security_metrics']['security_score']
                          
        breach_prevention_improvement = (self.zta_results['breach_stats']['prevention_rate'] - \
                                        self.baseline_results['breach_stats']['prevention_rate']) * 100
                                        
        usability_change = self.zta_results['usability_metrics']['usability_score'] - \
                           self.baseline_results['usability_metrics']['usability_score']
        
        comparison = {
            'security_metrics': {
                'security_score': {
                    'baseline': self.baseline_results['security_metrics']['security_score'],
                    'zta': self.zta_results['security_metrics']['security_score'],
                    'improvement': sec_improvement
                },
                'device_compliance': {
                    'baseline': self.baseline_results['security_metrics']['device_compliance_rate'],
                    'zta': self.zta_results['security_metrics']['device_compliance_rate'],
                    'improvement': (self.zta_results['security_metrics']['device_compliance_rate'] - 
                                   self.baseline_results['security_metrics']['device_compliance_rate']) * 100
                },
                'authentication_success': {
                    'baseline': self.baseline_results['security_metrics']['authentication_success_rate'],
                    'zta': self.zta_results['security_metrics']['authentication_success_rate'],
                    'improvement': (self.zta_results['security_metrics']['authentication_success_rate'] - 
                                   self.baseline_results['security_metrics']['authentication_success_rate']) * 100
                }
            },
            'breach_prevention': {
                'baseline_rate': self.baseline_results['breach_stats']['prevention_rate'],
                'zta_rate': self.zta_results['breach_stats']['prevention_rate'],
                'improvement_percent': breach_prevention_improvement,
                'baseline_prevented': self.baseline_results['breach_stats']['prevented'],
                'zta_prevented': self.zta_results['breach_stats']['prevented'],
                'total_attempts': self.baseline_results['breach_stats']['total_attempts']
            },
            'usability_metrics': {
                'usability_score': {
                    'baseline': self.baseline_results['usability_metrics']['usability_score'],
                    'zta': self.zta_results['usability_metrics']['usability_score'],
                    'change': usability_change
                },
                'task_completion': {
                    'baseline': self.baseline_results['usability_metrics']['task_completion_rate'],
                    'zta': self.zta_results['usability_metrics']['task_completion_rate'],
                    'change': (self.zta_results['usability_metrics']['task_completion_rate'] - 
                              self.baseline_results['usability_metrics']['task_completion_rate']) * 100
                }
            }
        }
        
        print("\nComparison Summary:")
        print(f"  - Breach Prevention Improvement: {comparison['breach_prevention']['improvement_percent']:.1f}%")
        print(f"  - Security Score Improvement: {comparison['security_metrics']['security_score']['improvement']:.1f} points")
        print(f"  - Baseline Prevention Rate: {comparison['breach_prevention']['baseline_rate']*100:.1f}%")
        print(f"  - ZTA Prevention Rate: {comparison['breach_prevention']['zta_rate']*100:.1f}%")
        
        return comparison
        
    def _generate_experiment_report(self, comparison: Dict):
        """Generate a text report of the experiment"""
        report_lines = []
        
        report_lines.append("="*80)
        report_lines.append("EXPERIMENT REPORT: ZTA vs TRADITIONAL SECURITY")
        report_lines.append("="*80)
        report_lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Experiment ID: {self.experiment_name}")
        report_lines.append("\n")
        
        report_lines.append("1. EXECUTIVE SUMMARY")
        report_lines.append("-" * 40)
        report_lines.append(f"This experiment compared a traditional security model (Baseline) against")
        report_lines.append(f"a Zero Trust Architecture (ZTA) implementation.")
        report_lines.append("\nKey Findings:")
        
        imp = comparison['breach_prevention']['improvement_percent']
        report_lines.append(f"  - Breach Prevention: {'IMPROVED' if imp > 0 else 'DECLINED'} by {abs(imp):.1f}%")
        
        sec_imp = comparison['security_metrics']['security_score']['improvement']
        report_lines.append(f"  - Overall Security Score: {'IMPROVED' if sec_imp > 0 else 'DECLINED'} by {abs(sec_imp):.1f} points")
        
        use_chg = comparison['usability_metrics']['usability_score']['change']
        report_lines.append(f"  - Usability Impact: {'POSITIVE' if use_chg >= 0 else 'NEGATIVE'} change of {abs(use_chg):.1f} points")
        
        report_lines.append("\n")
        report_lines.append("2. BREACH PREVENTION ANALYSIS")
        report_lines.append("-" * 40)
        report_lines.append(f"  - Prevention Rate: {comparison['breach_prevention']['baseline_rate']*100:.1f}%")
        report_lines.append(f"  - Attacks Prevented: {comparison['breach_prevention']['baseline_prevented']}/{comparison['breach_prevention']['total_attempts']}")
        report_lines.append(f"  - Successful Breaches: {comparison['breach_prevention']['total_attempts'] - comparison['breach_prevention']['baseline_prevented']}")
        
        report_lines.append("\nZTA Scenario:")
        report_lines.append(f"  - Prevention Rate: {comparison['breach_prevention']['zta_rate']*100:.1f}%")
        report_lines.append(f"  - Attacks Prevented: {comparison['breach_prevention']['zta_prevented']}/{comparison['breach_prevention']['total_attempts']}")
        report_lines.append(f"  - Successful Breaches: {comparison['breach_prevention']['total_attempts'] - comparison['breach_prevention']['zta_prevented']}")
        
        report_lines.append("\n")
        report_lines.append("3. SECURITY METRICS")
        report_lines.append("-" * 40)
        
        report_lines.append("Security Score:")
        report_lines.append(f"  - Baseline: {comparison['security_metrics']['security_score']['baseline']:.1f}/100")
        report_lines.append(f"  - ZTA: {comparison['security_metrics']['security_score']['zta']:.1f}/100")
        report_lines.append(f"  - Improvement: {comparison['security_metrics']['security_score']['improvement']:.1f} points")
        
        report_lines.append("\nDevice Compliance:")
        report_lines.append(f"  - Baseline: {comparison['security_metrics']['device_compliance']['baseline']*100:.1f}%")
        report_lines.append(f"  - ZTA: {comparison['security_metrics']['device_compliance']['zta']*100:.1f}%")
        report_lines.append(f"  - Improvement: {comparison['security_metrics']['device_compliance']['improvement']:.1f}%")
        
        report_lines.append("\nAuthentication Success:")
        report_lines.append(f"  - Baseline: {comparison['security_metrics']['authentication_success']['baseline']*100:.1f}%")
        report_lines.append(f"  - ZTA: {comparison['security_metrics']['authentication_success']['zta']*100:.1f}%")
        report_lines.append(f"  - Improvement: {comparison['security_metrics']['authentication_success']['improvement']:.1f}%")
        
        report_lines.append("\n")
        report_lines.append("4. USABILITY IMPACT")
        report_lines.append("-" * 40)
        
        report_lines.append("Usability Score:")
        report_lines.append(f"  - Baseline: {comparison['usability_metrics']['usability_score']['baseline']:.1f}/100")
        report_lines.append(f"  - ZTA: {comparison['usability_metrics']['usability_score']['zta']:.1f}/100")
        report_lines.append(f"  - Change: {comparison['usability_metrics']['usability_score']['change']:.1f} points")
        
        report_lines.append("\nTask Completion Rate:")
        report_lines.append(f"  - Baseline: {comparison['usability_metrics']['task_completion']['baseline']*100:.1f}%")
        report_lines.append(f"  - ZTA: {comparison['usability_metrics']['task_completion']['zta']*100:.1f}%")
        report_lines.append(f"  - Change: {comparison['usability_metrics']['task_completion']['change']:.1f}%")
        
        report_lines.append("\n")
        report_lines.append("="*80)
        report_lines.append("END OF REPORT")
        report_lines.append("="*80)
        
        # Save report
        filepath = os.path.join(self.results_dir, 'experiment_report.txt')
        with open(filepath, 'w') as f:
            f.write("\n".join(report_lines))
            
        # Save raw data
        with open(os.path.join(self.results_dir, 'comparison_data.json'), 'w') as f:
            json.dump(comparison, f, indent=4)
            
        print(f"\nExperiment report saved to: {filepath}")
