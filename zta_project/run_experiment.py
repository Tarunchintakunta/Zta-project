#!/usr/bin/env python3
"""
Experiment Runner - AI-Powered Zero-Trust Framework Implementation

This script implements the comparative experiment methodology from the research paper:
"Developing an AI-Powered Zero-Trust Cybersecurity Framework for Malware Prevention"

It runs two scenarios:
1. Baseline Scenario: Traditional security (ZTA controls OFF)
2. ZTA Scenario: Full Zero Trust (ZTA controls ON)

Then compares the results to measure ZTA effectiveness.
"""

import sys
import os
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simulation.experiment import ExperimentRunner

def print_header():
    """Print experiment header"""
    print(Fore.CYAN + Style.BRIGHT + """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║      AI-POWERED ZERO-TRUST FRAMEWORK COMPARATIVE EXPERIMENT                  ║
║                                                                              ║
║  Implementing Research Methodology:                                         ║
║  "Developing an AI-Powered Zero-Trust Cybersecurity Framework               ║
║   for Malware Prevention"                                                    ║
║                                                                              ║
║  This experiment compares:                                                  ║
║    • Baseline Scenario (Traditional Security)                                ║
║    • ZTA Scenario (Zero Trust Architecture)                                  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

def main():
    """Main execution function"""
    print_header()
    
    print(f"{Fore.YELLOW}Starting experiment at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        # Create experiment runner
        experiment_name = f"zta_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        runner = ExperimentRunner(experiment_name)
        
        # Run full experiment
        results = runner.run_full_experiment()
        
        # Print summary
        comparison = results['comparison']
        
        print(f"\n{Fore.GREEN}{Style.BRIGHT}{'='*80}")
        print(f"{Fore.GREEN}{Style.BRIGHT}EXPERIMENT RESULTS SUMMARY")
        print(f"{Fore.GREEN}{Style.BRIGHT}{'='*80}")
        
        print(f"\n{Fore.CYAN}Breach Prevention:")
        print(f"  Baseline Rate: {Fore.WHITE}{comparison['breach_prevention']['baseline_rate']*100:.1f}%")
        print(f"  ZTA Rate: {Fore.WHITE}{comparison['breach_prevention']['zta_rate']*100:.1f}%")
        print(f"  {Fore.GREEN}Improvement: {comparison['breach_prevention']['improvement_percent']:.1f}%")
        
        print(f"\n{Fore.CYAN}Security Metrics:")
        print(f"  Security Score Improvement: {Fore.GREEN}{comparison['security_metrics']['security_score']['improvement']:.1f} points")
        print(f"  Device Compliance Improvement: {Fore.GREEN}{comparison['security_metrics']['device_compliance']['improvement']:.1f}%")
        print(f"  Authentication Improvement: {Fore.GREEN}{comparison['security_metrics']['authentication_success']['improvement']:.1f}%")
        
        print(f"\n{Fore.CYAN}Usability Impact:")
        usability_change = comparison['usability_metrics']['usability_score']['change']
        color = Fore.GREEN if usability_change >= 0 else Fore.YELLOW
        print(f"  Usability Score Change: {color}{usability_change:.1f} points")
        
        print(f"\n{Fore.GREEN}✓ Experiment completed successfully!")
        print(f"{Fore.CYAN}  Results saved to: {runner.results_dir}/")
        
        return 0
        
    except Exception as e:
        print(f"\n{Fore.RED}{Style.BRIGHT}ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

