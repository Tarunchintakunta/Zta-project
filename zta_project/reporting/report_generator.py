"""
Report Generation Module for ZTA Research
"""
import os
from datetime import datetime
from typing import Dict, List
import pandas as pd
from tabulate import tabulate


class ReportGenerator:
    """Generates comprehensive research reports"""
    
    def __init__(self, output_dir='results'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def generate_comprehensive_report(self, environment, breach_simulator, 
                                     usability_tester, analyzer) -> str:
        """Generate comprehensive research report"""
        report_lines = []
        
        # Header
        report_lines.append("=" * 80)
        report_lines.append("ZERO TRUST ARCHITECTURE RESEARCH REPORT")
        report_lines.append("Effectiveness in Hybrid Work Environments")
        report_lines.append("=" * 80)
        report_lines.append(f"\nReport Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("\n")
        
        # Executive Summary
        report_lines.append("\n" + "=" * 80)
        report_lines.append("EXECUTIVE SUMMARY")
        report_lines.append("=" * 80)
        
        security_analysis = analyzer.analyze_security_effectiveness()
        usability_analysis = analyzer.analyze_usability_impact()
        
        report_lines.append(f"\nThis research evaluated Zero Trust Architecture (ZTA) implementation in a")
        report_lines.append(f"simulated hybrid work environment with {len(environment.users)} users,")
        report_lines.append(f"{len(environment.devices)} devices, and {len(environment.applications)} applications.")
        report_lines.append(f"\nKey Findings:")
        report_lines.append(f"  • Overall Security Score: {security_analysis['security_score']:.1f}/100")
        report_lines.append(f"  • Breach Prevention Rate: {security_analysis['breach_prevention_rate']*100:.1f}%")
        report_lines.append(f"  • Overall Usability Score: {usability_analysis['usability_score']:.1f}/100")
        report_lines.append(f"  • User Satisfaction: {usability_analysis['user_satisfaction']:.2f}/5.0")
        report_lines.append(f"  • Task Completion Rate: {usability_analysis['task_completion_rate']*100:.1f}%")
        
        # Environment Overview
        report_lines.append("\n\n" + "=" * 80)
        report_lines.append("1. ENVIRONMENT OVERVIEW")
        report_lines.append("=" * 80)
        
        report_lines.append(f"\n1.1 User Distribution")
        user_roles = {}
        for user in environment.users:
            user_roles[user.role] = user_roles.get(user.role, 0) + 1
        
        role_data = [[role, count, f"{count/len(environment.users)*100:.1f}%"] 
                     for role, count in user_roles.items()]
        report_lines.append("\n" + tabulate(role_data, 
                                           headers=['Role', 'Count', 'Percentage'],
                                           tablefmt='grid'))
        
        report_lines.append(f"\n1.2 Device Distribution")
        device_types = {}
        for device in environment.devices:
            device_types[device.device_type] = device_types.get(device.device_type, 0) + 1
        
        device_data = [[dtype, count, f"{count/len(environment.devices)*100:.1f}%"] 
                      for dtype, count in device_types.items()]
        report_lines.append("\n" + tabulate(device_data, 
                                           headers=['Device Type', 'Count', 'Percentage'],
                                           tablefmt='grid'))
        
        report_lines.append(f"\n1.3 Application Security Levels")
        app_levels = {}
        for app in environment.applications:
            app_levels[app.security_level] = app_levels.get(app.security_level, 0) + 1
        
        app_data = [[level, count, f"{count/len(environment.applications)*100:.1f}%"] 
                   for level, count in app_levels.items()]
        report_lines.append("\n" + tabulate(app_data, 
                                           headers=['Security Level', 'Count', 'Percentage'],
                                           tablefmt='grid'))
        
        # Security Effectiveness
        report_lines.append("\n\n" + "=" * 80)
        report_lines.append("2. SECURITY EFFECTIVENESS ANALYSIS")
        report_lines.append("=" * 80)
        
        report_lines.append(f"\n2.1 Overall Security Performance")
        security_data = [
            ['Security Score', f"{security_analysis['security_score']:.1f}/100"],
            ['Breach Prevention Rate', f"{security_analysis['breach_prevention_rate']*100:.1f}%"],
            ['Device Compliance Rate', f"{security_analysis['device_compliance_rate']*100:.1f}%"],
            ['Authentication Success Rate', f"{security_analysis['authentication_success_rate']*100:.1f}%"],
            ['Access Control Effectiveness', f"{security_analysis['access_control_effectiveness']*100:.1f}%"]
        ]
        report_lines.append("\n" + tabulate(security_data, 
                                           headers=['Metric', 'Value'],
                                           tablefmt='grid'))
        
        report_lines.append(f"\n2.2 Breach Simulation Results")
        breach_stats = breach_simulator.get_breach_statistics()
        
        breach_summary = [
            ['Total Breach Attempts', breach_stats['total_attempts']],
            ['Prevented', breach_stats['prevented']],
            ['Successful', breach_stats['successful']],
            ['Prevention Rate', f"{breach_stats['prevention_rate']*100:.1f}%"]
        ]
        report_lines.append("\n" + tabulate(breach_summary, 
                                           headers=['Metric', 'Value'],
                                           tablefmt='grid'))
        
        report_lines.append(f"\n2.3 Breach Type Analysis")
        breach_type_data = []
        for btype, count in breach_stats['breach_distribution'].items():
            prevented = sum(1 for b in breach_simulator.prevented_breaches if b['breach_type'] == btype)
            prevention_rate = (prevented / count * 100) if count > 0 else 0
            breach_type_data.append([
                btype.replace('_', ' ').title(),
                count,
                prevented,
                f"{prevention_rate:.1f}%"
            ])
        
        report_lines.append("\n" + tabulate(breach_type_data, 
                                           headers=['Breach Type', 'Attempts', 'Prevented', 'Prevention Rate'],
                                           tablefmt='grid'))
        
        report_lines.append(f"\n2.4 Device Security Posture")
        device_stats = environment.device_manager.get_compliance_statistics()
        
        device_security = [
            ['Total Devices', device_stats['total_devices']],
            ['Compliant Devices', device_stats['compliant_devices']],
            ['Non-Compliant Devices', device_stats['non_compliant_devices']],
            ['Compliance Rate', f"{device_stats['compliance_rate']*100:.1f}%"],
            ['Quarantined Devices', device_stats['quarantined_devices']]
        ]
        report_lines.append("\n" + tabulate(device_security, 
                                           headers=['Metric', 'Value'],
                                           tablefmt='grid'))
        
        # Usability Analysis
        report_lines.append("\n\n" + "=" * 80)
        report_lines.append("3. USABILITY AND USER EXPERIENCE ANALYSIS")
        report_lines.append("=" * 80)
        
        report_lines.append(f"\n3.1 Overall Usability Performance")
        usability_data = [
            ['Usability Score', f"{usability_analysis['usability_score']:.1f}/100"],
            ['Task Completion Rate', f"{usability_analysis['task_completion_rate']*100:.1f}%"],
            ['Average Task Time', f"{usability_analysis['average_task_time']:.2f} seconds"],
            ['User Satisfaction', f"{usability_analysis['user_satisfaction']:.2f}/5.0"],
            ['SUS Score', f"{usability_analysis['sus_score']:.1f}/100"],
            ['Average Errors per Task', f"{usability_analysis['average_errors']:.2f}"]
        ]
        report_lines.append("\n" + tabulate(usability_data, 
                                           headers=['Metric', 'Value'],
                                           tablefmt='grid'))
        
        report_lines.append(f"\n3.2 Task-Specific Analysis")
        usability_metrics = usability_tester.get_usability_metrics()
        
        task_stats = {}
        for result in usability_tester.test_results:
            task = result['task_name']
            if task not in task_stats:
                task_stats[task] = {
                    'total': 0, 'completed': 0, 'total_time': 0, 
                    'total_errors': 0, 'total_satisfaction': 0
                }
            
            task_stats[task]['total'] += 1
            if result['completed']:
                task_stats[task]['completed'] += 1
                task_stats[task]['total_time'] += result['time_taken']
            task_stats[task]['total_errors'] += result['errors_encountered']
            task_stats[task]['total_satisfaction'] += result['satisfaction_score']
        
        task_data = []
        for task, stats in sorted(task_stats.items()):
            completion_rate = (stats['completed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            avg_time = (stats['total_time'] / stats['completed']) if stats['completed'] > 0 else 0
            avg_errors = stats['total_errors'] / stats['total'] if stats['total'] > 0 else 0
            avg_satisfaction = stats['total_satisfaction'] / stats['total'] if stats['total'] > 0 else 0
            
            task_data.append([
                task.replace('_', ' ').title(),
                stats['total'],
                f"{completion_rate:.1f}%",
                f"{avg_time:.2f}s",
                f"{avg_errors:.2f}",
                f"{avg_satisfaction:.2f}"
            ])
        
        report_lines.append("\n" + tabulate(task_data, 
                                           headers=['Task', 'Attempts', 'Success Rate', 
                                                   'Avg Time', 'Avg Errors', 'Satisfaction'],
                                           tablefmt='grid'))
        
        # Comparative Analysis
        report_lines.append("\n\n" + "=" * 80)
        report_lines.append("4. COMPARATIVE ANALYSIS: ZTA vs TRADITIONAL SECURITY")
        report_lines.append("=" * 80)
        
        comparison = analyzer.perform_comparative_analysis()
        
        comp_data = []
        for metric, data in comparison['improvements'].items():
            comp_data.append([
                metric.replace('_', ' ').title(),
                f"{data['baseline']*100:.1f}%",
                f"{data['zta']*100:.1f}%",
                f"{data['improvement_percent']:+.1f}%"
            ])
        
        report_lines.append("\n" + tabulate(comp_data, 
                                           headers=['Metric', 'Traditional', 'ZTA', 'Improvement'],
                                           tablefmt='grid'))
        
        # Statistical Analysis
        report_lines.append("\n\n" + "=" * 80)
        report_lines.append("5. STATISTICAL ANALYSIS")
        report_lines.append("=" * 80)
        
        stats = analyzer.perform_statistical_analysis()
        
        report_lines.append(f"\n5.1 Device Trust Scores")
        device_trust_data = [
            ['Mean', f"{stats['device_trust']['mean']:.2f}"],
            ['Median', f"{stats['device_trust']['median']:.2f}"],
            ['Standard Deviation', f"{stats['device_trust']['std_dev']:.2f}"],
            ['Minimum', f"{stats['device_trust']['min']:.2f}"],
            ['Maximum', f"{stats['device_trust']['max']:.2f}"]
        ]
        report_lines.append("\n" + tabulate(device_trust_data, 
                                           headers=['Statistic', 'Value'],
                                           tablefmt='grid'))
        
        report_lines.append(f"\n5.2 Task Completion Times")
        task_time_data = [
            ['Mean', f"{stats['task_completion']['mean_time']:.2f} seconds"],
            ['Median', f"{stats['task_completion']['median_time']:.2f} seconds"],
            ['Standard Deviation', f"{stats['task_completion']['std_dev']:.2f} seconds"],
            ['95th Percentile', f"{stats['task_completion']['percentile_95']:.2f} seconds"]
        ]
        report_lines.append("\n" + tabulate(task_time_data, 
                                           headers=['Statistic', 'Value'],
                                           tablefmt='grid'))
        
        # Recommendations
        report_lines.append("\n\n" + "=" * 80)
        report_lines.append("6. RECOMMENDATIONS")
        report_lines.append("=" * 80)
        
        recommendations = analyzer.generate_recommendations()
        report_lines.append("\nBased on the analysis, the following recommendations are proposed:\n")
        
        for i, rec in enumerate(recommendations, 1):
            report_lines.append(f"{i}. {rec}")
        
        # Conclusion
        report_lines.append("\n\n" + "=" * 80)
        report_lines.append("7. CONCLUSION")
        report_lines.append("=" * 80)
        
        report_lines.append(f"\nThis research successfully demonstrated the effectiveness of Zero Trust")
        report_lines.append(f"Architecture in securing hybrid work environments. The implementation achieved:")
        report_lines.append(f"\n• High security effectiveness with {security_analysis['breach_prevention_rate']*100:.1f}% breach prevention")
        report_lines.append(f"• Strong device compliance at {security_analysis['device_compliance_rate']*100:.1f}%")
        report_lines.append(f"• Acceptable usability with {usability_analysis['sus_score']:.1f}/100 SUS score")
        report_lines.append(f"• Positive user satisfaction at {usability_analysis['user_satisfaction']:.2f}/5.0")
        
        report_lines.append(f"\nThe results indicate that ZTA provides significant security improvements")
        report_lines.append(f"over traditional perimeter-based security models while maintaining reasonable")
        report_lines.append(f"usability for end users. The trade-off between security and user experience")
        report_lines.append(f"can be effectively balanced through proper policy configuration and user training.")
        
        report_lines.append(f"\nFuture work should focus on:")
        report_lines.append(f"• Long-term deployment studies in real organizational environments")
        report_lines.append(f"• Advanced machine learning for anomaly detection")
        report_lines.append(f"• Integration with emerging authentication technologies")
        report_lines.append(f"• Scalability testing for larger enterprise deployments")
        
        report_lines.append("\n" + "=" * 80)
        report_lines.append("END OF REPORT")
        report_lines.append("=" * 80)
        
        # Save report
        report_text = "\n".join(report_lines)
        filepath = os.path.join(self.output_dir, 'comprehensive_report.txt')
        with open(filepath, 'w') as f:
            f.write(report_text)
        
        print(f"\nComprehensive report saved to: {filepath}")
        return report_text
    
    def export_data_to_csv(self, environment, breach_simulator, usability_tester):
        """Export all data to CSV files"""
        print("\nExporting data to CSV files...")
        
        # 1. User data
        user_data = []
        for user in environment.users:
            user_data.append(user.get_user_info())
        
        df_users = pd.DataFrame(user_data)
        users_file = os.path.join(self.output_dir, 'users_data.csv')
        df_users.to_csv(users_file, index=False)
        print(f"  Saved: {users_file}")
        
        # 2. Device data
        device_data = []
        for device in environment.devices:
            device_data.append(device.get_device_info())
        
        df_devices = pd.DataFrame(device_data)
        devices_file = os.path.join(self.output_dir, 'devices_data.csv')
        df_devices.to_csv(devices_file, index=False)
        print(f"  Saved: {devices_file}")
        
        # 3. Application data
        app_data = []
        for app in environment.applications:
            app_data.append(app.get_application_info())
        
        df_apps = pd.DataFrame(app_data)
        apps_file = os.path.join(self.output_dir, 'applications_data.csv')
        df_apps.to_csv(apps_file, index=False)
        print(f"  Saved: {apps_file}")
        
        # 4. Breach attempts
        df_breaches = pd.DataFrame(breach_simulator.breach_attempts)
        breaches_file = os.path.join(self.output_dir, 'breach_attempts.csv')
        df_breaches.to_csv(breaches_file, index=False)
        print(f"  Saved: {breaches_file}")
        
        # 5. Usability test results
        df_usability = pd.DataFrame(usability_tester.test_results)
        usability_file = os.path.join(self.output_dir, 'usability_tests.csv')
        df_usability.to_csv(usability_file, index=False)
        print(f"  Saved: {usability_file}")
        
        # 6. Access logs
        df_access = pd.DataFrame(environment.access_controller.access_logs)
        access_file = os.path.join(self.output_dir, 'access_logs.csv')
        df_access.to_csv(access_file, index=False)
        print(f"  Saved: {access_file}")
        
        # 7. Authentication logs
        df_auth = pd.DataFrame(environment.identity_manager.authentication_logs)
        auth_file = os.path.join(self.output_dir, 'authentication_logs.csv')
        df_auth.to_csv(auth_file, index=False)
        print(f"  Saved: {auth_file}")
        
        print("\nAll data exported successfully!")
