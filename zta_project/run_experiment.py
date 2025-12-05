#!/usr/bin/env python3
"""
Experiment Runner - Zero Trust Architecture Framework Implementation

This script implements the comparative experiment methodology from the research paper:
"Developing a Zero Trust Cybersecurity Framework for Malware Prevention"

It runs two scenarios:
1. Baseline Scenario: Traditional security (ZTA controls OFF)
2. ZTA Scenario: Full Zero Trust (ZTA controls ON)

Then compares the results to measure ZTA effectiveness.
"""

import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simulation.experiment import ExperimentRunner

def print_header():
    """Print experiment header"""
    print("\n" + "="*80)
    print("ZERO TRUST ARCHITECTURE COMPARATIVE EXPERIMENT")
    print("="*80)
    print("Implementing Research Methodology:")
    print("Developing a Zero Trust Cybersecurity Framework for Malware Prevention")
    print("\nThis experiment compares:")
    print("  - Baseline Scenario (Traditional Security)")
    print("  - ZTA Scenario (Zero Trust Architecture)")
    print("="*80 + "\n")

def main():
    """Main execution function"""
    print_header()
    
    print(f"Starting experiment at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        # Create experiment runner
        experiment_name = f"zta_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        runner = ExperimentRunner(experiment_name)
        
        # Run full experiment
        results = runner.run_full_experiment()
        
        # Print summary
        comparison = results['comparison']
        
        print(f"\n{'='*80}")
        print("EXPERIMENT RESULTS SUMMARY")
        print(f"{'='*80}")
        
        print("\nBreach Prevention:")
        print(f"  Baseline Rate: {comparison['breach_prevention']['baseline_rate']*100:.1f}%")
        print(f"  ZTA Rate: {comparison['breach_prevention']['zta_rate']*100:.1f}%")
        print(f"  Improvement: {comparison['breach_prevention']['improvement_percent']:.1f}%")
        
        print("\nSecurity Metrics:")
        print(f"  Security Score Improvement: {comparison['security_metrics']['security_score']['improvement']:.1f} points")
        print(f"  Device Compliance Improvement: {comparison['security_metrics']['device_compliance']['improvement']:.1f}%")
        print(f"  Authentication Improvement: {comparison['security_metrics']['authentication_success']['improvement']:.1f}%")
        
        print("\nUsability Impact:")
        usability_change = comparison['usability_metrics']['usability_score']['change']
        print(f"  Usability Score Change: {usability_change:.1f} points")
        
        print("\n[SUCCESS] Experiment completed successfully!")
        print(f"  Results saved to: {runner.results_dir}/")
        
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

