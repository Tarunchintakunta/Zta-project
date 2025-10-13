#!/usr/bin/env python3
"""
Zero Trust Architecture Research Project
Main Execution Script

This script runs a comprehensive simulation and evaluation of Zero Trust Architecture
in hybrid work environments, including security testing, usability evaluation, and
detailed analysis with visualizations.

Author: ZTA Research Team
Date: 2024
"""

import sys
import os
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama for colored output
init(autoreset=True)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simulation import HybridWorkEnvironment, BreachSimulator
from testing import UsabilityTester
from analysis import DataAnalyzer, Visualizer
from reporting import ReportGenerator
import config


def print_header():
    """Print project header"""
    print(Fore.CYAN + Style.BRIGHT + """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║              ZERO TRUST ARCHITECTURE RESEARCH PROJECT                        ║
║         Effectiveness in Securing Hybrid Work Environments                   ║
║                                                                              ║
║  This research evaluates ZTA implementation through:                         ║
║    • Identity Verification & Access Management                               ║
║    • Device Posture Assessment & Compliance                                  ║
║    • Micro-segmentation & Policy Enforcement                                 ║
║    • Continuous Monitoring & Threat Detection                                ║
║    • Security Breach Simulation & Prevention                                 ║
║    • Usability Testing & User Experience Evaluation                          ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)


def print_section(title):
    """Print section header"""
    print(f"\n{Fore.YELLOW}{Style.BRIGHT}{'='*80}")
    print(f"{Fore.YELLOW}{Style.BRIGHT}{title.center(80)}")
    print(f"{Fore.YELLOW}{Style.BRIGHT}{'='*80}\n")


def print_success(message):
    """Print success message"""
    print(f"{Fore.GREEN}✓ {message}")


def print_info(message):
    """Print info message"""
    print(f"{Fore.CYAN}ℹ {message}")


def print_warning(message):
    """Print warning message"""
    print(f"{Fore.YELLOW}⚠ {message}")


def main():
    """Main execution function"""
    start_time = datetime.now()
    
    print_header()
    print_info(f"Simulation started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"Configuration: {config.NUM_USERS} users, {config.NUM_DEVICES} devices, "
               f"{config.NUM_APPLICATIONS} applications")
    print_info(f"Simulation duration: {config.SIMULATION_DAYS} days\n")
    
    try:
        # Phase 1: Environment Setup
        print_section("PHASE 1: ENVIRONMENT SETUP")
        print_info("Initializing hybrid work environment...")
        
        environment = HybridWorkEnvironment()
        environment.setup_environment()
        
        print_success("Environment setup completed successfully!")
        print_info(f"  • Users created: {len(environment.users)}")
        print_info(f"  • Devices registered: {len(environment.devices)}")
        print_info(f"  • Applications configured: {len(environment.applications)}")
        
        # Phase 2: Baseline Assessment
        print_section("PHASE 2: BASELINE VULNERABILITY ASSESSMENT")
        print_info("Performing initial security assessment...")
        
        # Run a few days of normal operations
        for day in range(1, 4):
            print_info(f"  Simulating baseline day {day}/3...")
            environment.simulate_day(day)
        
        print_success("Baseline assessment completed!")
        
        # Phase 3: ZTA Deployment Simulation
        print_section("PHASE 3: ZERO TRUST ARCHITECTURE DEPLOYMENT")
        print_info("Deploying ZTA controls and policies...")
        
        # Continue simulation with ZTA active
        for day in range(4, config.SIMULATION_DAYS + 1):
            if day % 5 == 0:
                print_info(f"  Simulation progress: Day {day}/{config.SIMULATION_DAYS}")
            environment.simulate_day(day)
        
        print_success("ZTA deployment simulation completed!")
        
        # Phase 4: Security Breach Testing
        print_section("PHASE 4: SECURITY BREACH SIMULATION")
        print_info("Testing ZTA effectiveness against various attack scenarios...")
        
        breach_simulator = BreachSimulator(environment)
        breach_simulator.run_all_breach_scenarios(iterations=5)
        
        print_success("Breach simulation completed!")
        
        # Phase 5: Usability Testing
        print_section("PHASE 5: USABILITY TESTING")
        print_info("Evaluating user experience and system usability...")
        
        usability_tester = UsabilityTester(environment)
        usability_tester.run_usability_tests(num_tests=100)
        
        print_success("Usability testing completed!")
        
        # Phase 6: Data Analysis
        print_section("PHASE 6: DATA ANALYSIS")
        print_info("Analyzing collected data and generating insights...")
        
        analyzer = DataAnalyzer(environment, breach_simulator, usability_tester)
        
        print_info("\n  Analyzing security effectiveness...")
        security_results = analyzer.analyze_security_effectiveness()
        
        print_info("\n  Analyzing usability impact...")
        usability_results = analyzer.analyze_usability_impact()
        
        print_info("\n  Performing comparative analysis...")
        comparison_results = analyzer.perform_comparative_analysis()
        
        print_info("\n  Performing statistical analysis...")
        statistical_results = analyzer.perform_statistical_analysis()
        
        print_success("Data analysis completed!")
        
        # Phase 7: Visualization
        print_section("PHASE 7: GENERATING VISUALIZATIONS")
        print_info("Creating charts and graphs...")
        
        visualizer = Visualizer(output_dir=config.CHARTS_DIR)
        
        print_info("  Creating security metrics visualization...")
        visualizer.plot_security_metrics(security_results)
        
        print_info("  Creating usability metrics visualization...")
        visualizer.plot_usability_metrics(usability_results)
        
        print_info("  Creating comparative analysis visualization...")
        visualizer.plot_comparative_analysis(comparison_results)
        
        print_info("  Creating breach analysis visualization...")
        breach_stats = breach_simulator.get_breach_statistics()
        visualizer.plot_breach_analysis(breach_stats)
        
        print_info("  Creating device trust distribution visualization...")
        device_stats = environment.device_manager.get_compliance_statistics()
        visualizer.plot_device_trust_distribution(device_stats)
        
        print_info("  Creating authentication analysis visualization...")
        auth_stats = environment.identity_manager.get_authentication_stats()
        visualizer.plot_authentication_analysis(auth_stats)
        
        print_info("  Creating executive dashboard...")
        visualizer.create_executive_dashboard(security_results, usability_results, 
                                              comparison_results)
        
        print_success("All visualizations created successfully!")
        
        # Phase 8: Report Generation
        print_section("PHASE 8: GENERATING REPORTS")
        print_info("Creating comprehensive research report...")
        
        report_generator = ReportGenerator(output_dir=config.OUTPUT_DIR)
        
        print_info("  Generating comprehensive text report...")
        report_generator.generate_comprehensive_report(
            environment, breach_simulator, usability_tester, analyzer
        )
        
        print_info("  Exporting data to CSV files...")
        report_generator.export_data_to_csv(
            environment, breach_simulator, usability_tester
        )
        
        print_success("All reports generated successfully!")
        
        # Phase 9: Summary and Recommendations
        print_section("PHASE 9: RESEARCH SUMMARY")
        
        print(f"\n{Fore.GREEN}{Style.BRIGHT}KEY FINDINGS:")
        print(f"{Fore.WHITE}{'─'*80}")
        print(f"\n{Fore.CYAN}Security Effectiveness:")
        print(f"  • Overall Security Score: {Fore.GREEN}{security_results['security_score']:.1f}/100")
        print(f"  • Breach Prevention Rate: {Fore.GREEN}{security_results['breach_prevention_rate']*100:.1f}%")
        print(f"  • Device Compliance Rate: {Fore.GREEN}{security_results['device_compliance_rate']*100:.1f}%")
        print(f"  • Authentication Success: {Fore.GREEN}{security_results['authentication_success_rate']*100:.1f}%")
        
        print(f"\n{Fore.CYAN}Usability & User Experience:")
        print(f"  • Overall Usability Score: {Fore.GREEN}{usability_results['usability_score']:.1f}/100")
        print(f"  • Task Completion Rate: {Fore.GREEN}{usability_results['task_completion_rate']*100:.1f}%")
        print(f"  • User Satisfaction: {Fore.GREEN}{usability_results['user_satisfaction']:.2f}/5.0")
        print(f"  • SUS Score: {Fore.GREEN}{usability_results['sus_score']:.1f}/100")
        
        print(f"\n{Fore.CYAN}Comparative Analysis:")
        for metric, data in list(comparison_results['improvements'].items())[:3]:
            improvement = data['improvement_percent']
            color = Fore.GREEN if improvement > 0 else Fore.RED
            print(f"  • {metric.replace('_', ' ').title()}: {color}{improvement:+.1f}% vs Traditional")
        
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}RECOMMENDATIONS:")
        print(f"{Fore.WHITE}{'─'*80}")
        recommendations = analyzer.generate_recommendations()
        for i, rec in enumerate(recommendations[:5], 1):
            print(f"{Fore.CYAN}{i}. {Fore.WHITE}{rec}")
        
        # Final Summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        print_section("EXECUTION COMPLETE")
        print_success(f"Total execution time: {duration.total_seconds():.2f} seconds")
        print_success(f"Results saved to: {config.OUTPUT_DIR}/")
        print_success(f"Charts saved to: {config.CHARTS_DIR}/")
        
        print(f"\n{Fore.GREEN}{Style.BRIGHT}OUTPUT FILES:")
        print(f"{Fore.WHITE}{'─'*80}")
        print(f"{Fore.CYAN}Reports:")
        print(f"  • {config.OUTPUT_DIR}/comprehensive_report.txt")
        print(f"\n{Fore.CYAN}Data Files:")
        print(f"  • {config.OUTPUT_DIR}/users_data.csv")
        print(f"  • {config.OUTPUT_DIR}/devices_data.csv")
        print(f"  • {config.OUTPUT_DIR}/applications_data.csv")
        print(f"  • {config.OUTPUT_DIR}/breach_attempts.csv")
        print(f"  • {config.OUTPUT_DIR}/usability_tests.csv")
        print(f"  • {config.OUTPUT_DIR}/access_logs.csv")
        print(f"  • {config.OUTPUT_DIR}/authentication_logs.csv")
        print(f"\n{Fore.CYAN}Visualizations:")
        print(f"  • {config.CHARTS_DIR}/executive_dashboard.png")
        print(f"  • {config.CHARTS_DIR}/security_metrics.png")
        print(f"  • {config.CHARTS_DIR}/usability_metrics.png")
        print(f"  • {config.CHARTS_DIR}/comparative_analysis.png")
        print(f"  • {config.CHARTS_DIR}/breach_analysis.png")
        print(f"  • {config.CHARTS_DIR}/device_trust.png")
        print(f"  • {config.CHARTS_DIR}/authentication.png")
        
        print(f"\n{Fore.GREEN}{Style.BRIGHT}╔══════════════════════════════════════════════════════════════════════════════╗")
        print(f"{Fore.GREEN}{Style.BRIGHT}║  ZERO TRUST ARCHITECTURE RESEARCH PROJECT COMPLETED SUCCESSFULLY!           ║")
        print(f"{Fore.GREEN}{Style.BRIGHT}╚══════════════════════════════════════════════════════════════════════════════╝\n")
        
        return 0
        
    except Exception as e:
        print(f"\n{Fore.RED}{Style.BRIGHT}ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
