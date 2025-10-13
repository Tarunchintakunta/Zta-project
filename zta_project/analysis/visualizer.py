"""
Visualization Module for ZTA Research Results
"""
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from typing import Dict, List
import os


class Visualizer:
    """Creates visualizations for ZTA research findings"""
    
    def __init__(self, output_dir='charts'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Set style
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 10
        
    def plot_security_metrics(self, security_data: Dict, filename='security_metrics.png'):
        """Plot security effectiveness metrics"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Zero Trust Architecture - Security Effectiveness Metrics', 
                     fontsize=16, fontweight='bold')
        
        # 1. Security Score Gauge
        ax1 = axes[0, 0]
        score = security_data['security_score']
        colors = ['#d32f2f', '#f57c00', '#fbc02d', '#689f38', '#388e3c']
        color_idx = min(4, int(score / 20))
        
        ax1.barh(['Security Score'], [score], color=colors[color_idx], height=0.5)
        ax1.set_xlim(0, 100)
        ax1.set_xlabel('Score')
        ax1.set_title('Overall Security Score')
        ax1.text(score + 2, 0, f'{score:.1f}', va='center', fontweight='bold')
        
        # 2. Breach Prevention Rate
        ax2 = axes[0, 1]
        prevention_rate = security_data['breach_prevention_rate'] * 100
        categories = ['Prevented', 'Successful']
        values = [prevention_rate, 100 - prevention_rate]
        colors_pie = ['#4caf50', '#f44336']
        
        ax2.pie(values, labels=categories, autopct='%1.1f%%', colors=colors_pie, startangle=90)
        ax2.set_title('Breach Prevention Rate')
        
        # 3. Compliance Rates
        ax3 = axes[1, 0]
        metrics = ['Device\nCompliance', 'Authentication\nSuccess', 'Access Control\nEffectiveness']
        values = [
            security_data['device_compliance_rate'] * 100,
            security_data['authentication_success_rate'] * 100,
            security_data['access_control_effectiveness'] * 100
        ]
        colors_bar = ['#2196f3', '#9c27b0', '#ff9800']
        
        bars = ax3.bar(metrics, values, color=colors_bar)
        ax3.set_ylim(0, 100)
        ax3.set_ylabel('Rate (%)')
        ax3.set_title('Key Security Metrics')
        ax3.axhline(y=90, color='r', linestyle='--', alpha=0.5, label='Target: 90%')
        ax3.legend()
        
        for bar in bars:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        # 4. Policy Violations
        ax4 = axes[1, 1]
        violations = security_data['policy_violations']
        quarantined = security_data['quarantined_devices']
        
        categories = ['Policy\nViolations', 'Quarantined\nDevices']
        values = [violations, quarantined]
        colors_bar2 = ['#ff5722', '#e91e63']
        
        bars = ax4.bar(categories, values, color=colors_bar2)
        ax4.set_ylabel('Count')
        ax4.set_title('Security Incidents')
        
        for bar in bars:
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        print(f"  Saved: {filepath}")
        plt.close()
    
    def plot_usability_metrics(self, usability_data: Dict, filename='usability_metrics.png'):
        """Plot usability and user experience metrics"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Zero Trust Architecture - Usability & User Experience Metrics', 
                     fontsize=16, fontweight='bold')
        
        # 1. Usability Score
        ax1 = axes[0, 0]
        score = usability_data['usability_score']
        sus_score = usability_data['sus_score']
        
        scores = [score, sus_score]
        labels = ['Usability\nScore', 'SUS\nScore']
        colors = ['#3f51b5', '#00bcd4']
        
        bars = ax1.bar(labels, scores, color=colors)
        ax1.set_ylim(0, 100)
        ax1.set_ylabel('Score')
        ax1.set_title('Overall Usability Scores')
        ax1.axhline(y=70, color='g', linestyle='--', alpha=0.5, label='Good: 70+')
        ax1.legend()
        
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}', ha='center', va='bottom', fontweight='bold')
        
        # 2. Task Completion Rate
        ax2 = axes[0, 1]
        completion_rate = usability_data['task_completion_rate'] * 100
        failure_rate = 100 - completion_rate
        
        values = [completion_rate, failure_rate]
        labels = ['Completed', 'Failed']
        colors_pie = ['#4caf50', '#ff9800']
        
        ax2.pie(values, labels=labels, autopct='%1.1f%%', colors=colors_pie, startangle=90)
        ax2.set_title('Task Completion Rate')
        
        # 3. User Satisfaction
        ax3 = axes[1, 0]
        satisfaction = usability_data['user_satisfaction']
        
        # Create a horizontal bar showing satisfaction on 1-5 scale
        ax3.barh(['User Satisfaction'], [satisfaction], color='#8bc34a', height=0.5)
        ax3.set_xlim(0, 5)
        ax3.set_xlabel('Rating (1-5)')
        ax3.set_title('Average User Satisfaction')
        ax3.text(satisfaction + 0.1, 0, f'{satisfaction:.2f}', va='center', fontweight='bold')
        
        # Add reference lines
        ax3.axvline(x=3, color='orange', linestyle='--', alpha=0.5, label='Acceptable: 3.0')
        ax3.axvline(x=4, color='green', linestyle='--', alpha=0.5, label='Good: 4.0')
        ax3.legend()
        
        # 4. Average Task Time and Errors
        ax4 = axes[1, 1]
        avg_time = usability_data['average_task_time']
        avg_errors = usability_data['average_errors']
        
        x = np.arange(2)
        metrics = ['Avg Task\nTime (s)', 'Avg Errors\nper Task']
        values = [avg_time, avg_errors]
        colors_bar = ['#ff5722', '#e91e63']
        
        bars = ax4.bar(x, values, color=colors_bar)
        ax4.set_xticks(x)
        ax4.set_xticklabels(metrics)
        ax4.set_ylabel('Value')
        ax4.set_title('Task Performance Metrics')
        
        for bar in bars:
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f}', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        print(f"  Saved: {filepath}")
        plt.close()
    
    def plot_comparative_analysis(self, comparison_data: Dict, filename='comparative_analysis.png'):
        """Plot comparison between traditional security and ZTA"""
        fig, ax = plt.subplots(figsize=(14, 8))
        fig.suptitle('Comparative Analysis: Traditional Security vs Zero Trust Architecture', 
                     fontsize=16, fontweight='bold')
        
        improvements = comparison_data['improvements']
        
        metrics = []
        traditional_vals = []
        zta_vals = []
        
        for metric, data in improvements.items():
            metrics.append(metric.replace('_', ' ').title())
            traditional_vals.append(data['baseline'] * 100)
            zta_vals.append(data['zta'] * 100)
        
        x = np.arange(len(metrics))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, traditional_vals, width, label='Traditional Security', 
                      color='#ff7043', alpha=0.8)
        bars2 = ax.bar(x + width/2, zta_vals, width, label='Zero Trust Architecture', 
                      color='#66bb6a', alpha=0.8)
        
        ax.set_ylabel('Rate (%)')
        ax.set_title('Security Metrics Comparison')
        ax.set_xticks(x)
        ax.set_xticklabels(metrics, rotation=45, ha='right')
        ax.legend()
        ax.set_ylim(0, 110)
        ax.grid(axis='y', alpha=0.3)
        
        # Add value labels on bars
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.1f}%', ha='center', va='bottom', fontsize=8)
        
        plt.tight_layout()
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        print(f"  Saved: {filepath}")
        plt.close()
    
    def plot_breach_analysis(self, breach_stats: Dict, filename='breach_analysis.png'):
        """Plot breach simulation results"""
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle('Security Breach Simulation Results', fontsize=16, fontweight='bold')
        
        # 1. Overall Prevention Rate
        ax1 = axes[0]
        prevention_rate = breach_stats['prevention_rate'] * 100
        success_rate = 100 - prevention_rate
        
        values = [prevention_rate, success_rate]
        labels = ['Prevented', 'Successful']
        colors = ['#4caf50', '#f44336']
        explode = (0.1, 0)
        
        ax1.pie(values, labels=labels, autopct='%1.1f%%', colors=colors, 
               explode=explode, startangle=90, shadow=True)
        ax1.set_title('Overall Breach Prevention Rate')
        
        # 2. Breach Type Distribution
        ax2 = axes[1]
        breach_dist = breach_stats['breach_distribution']
        
        types = [t.replace('_', ' ').title() for t in breach_dist.keys()]
        counts = list(breach_dist.values())
        colors_bar = plt.cm.Set3(np.linspace(0, 1, len(types)))
        
        bars = ax2.barh(types, counts, color=colors_bar)
        ax2.set_xlabel('Number of Attempts')
        ax2.set_title('Breach Attempts by Type')
        
        for bar in bars:
            width = bar.get_width()
            ax2.text(width, bar.get_y() + bar.get_height()/2.,
                    f'{int(width)}', ha='left', va='center', fontweight='bold')
        
        plt.tight_layout()
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        print(f"  Saved: {filepath}")
        plt.close()
    
    def plot_device_trust_distribution(self, device_stats: Dict, filename='device_trust.png'):
        """Plot device trust score distribution"""
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle('Device Trust and Compliance Analysis', fontsize=16, fontweight='bold')
        
        # 1. Trust Score Distribution
        ax1 = axes[0]
        trust_dist = device_stats['trust_distribution']
        
        categories = list(trust_dist.keys())
        values = list(trust_dist.values())
        colors = ['#4caf50', '#8bc34a', '#ffc107', '#ff5722']
        
        bars = ax1.bar(categories, values, color=colors)
        ax1.set_ylabel('Number of Devices')
        ax1.set_title('Device Trust Score Distribution')
        ax1.set_xlabel('Trust Level')
        
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom', fontweight='bold')
        
        # 2. Compliance Status
        ax2 = axes[1]
        compliant = device_stats['compliant_devices']
        non_compliant = device_stats['non_compliant_devices']
        quarantined = device_stats['quarantined_devices']
        
        categories = ['Compliant', 'Non-Compliant', 'Quarantined']
        values = [compliant, non_compliant, quarantined]
        colors_pie = ['#4caf50', '#ff9800', '#f44336']
        
        ax2.pie(values, labels=categories, autopct='%1.1f%%', colors=colors_pie, startangle=90)
        ax2.set_title('Device Compliance Status')
        
        plt.tight_layout()
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        print(f"  Saved: {filepath}")
        plt.close()
    
    def plot_authentication_analysis(self, auth_stats: Dict, filename='authentication.png'):
        """Plot authentication statistics"""
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle('Authentication Analysis', fontsize=16, fontweight='bold')
        
        # 1. Success vs Failure
        ax1 = axes[0]
        successful = auth_stats['successful']
        failed = auth_stats['failed']
        
        values = [successful, failed]
        labels = ['Successful', 'Failed']
        colors = ['#4caf50', '#f44336']
        
        ax1.pie(values, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
        ax1.set_title(f"Authentication Success Rate: {auth_stats['success_rate']*100:.1f}%")
        
        # 2. Active Sessions
        ax2 = axes[1]
        active_sessions = auth_stats['active_sessions']
        
        ax2.bar(['Active Sessions'], [active_sessions], color='#2196f3', width=0.5)
        ax2.set_ylabel('Count')
        ax2.set_title('Current Active Sessions')
        ax2.text(0, active_sessions, f'{active_sessions}', ha='center', va='bottom', 
                fontweight='bold', fontsize=14)
        
        plt.tight_layout()
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        print(f"  Saved: {filepath}")
        plt.close()
    
    def create_executive_dashboard(self, security_data: Dict, usability_data: Dict, 
                                   comparison_data: Dict, filename='executive_dashboard.png'):
        """Create comprehensive executive dashboard"""
        fig = plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        fig.suptitle('Zero Trust Architecture - Executive Dashboard', 
                     fontsize=18, fontweight='bold')
        
        # 1. Overall Scores
        ax1 = fig.add_subplot(gs[0, :])
        scores = {
            'Security Score': security_data['security_score'],
            'Usability Score': usability_data['usability_score'],
            'SUS Score': usability_data['sus_score']
        }
        
        x = np.arange(len(scores))
        colors = ['#4caf50', '#2196f3', '#ff9800']
        bars = ax1.bar(x, list(scores.values()), color=colors, width=0.6)
        ax1.set_xticks(x)
        ax1.set_xticklabels(list(scores.keys()))
        ax1.set_ylim(0, 100)
        ax1.set_ylabel('Score')
        ax1.set_title('Overall Performance Scores', fontweight='bold')
        ax1.axhline(y=70, color='g', linestyle='--', alpha=0.3, label='Target: 70')
        ax1.legend()
        
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}', ha='center', va='bottom', fontweight='bold', fontsize=12)
        
        # 2. Security Metrics
        ax2 = fig.add_subplot(gs[1, 0])
        prevention_rate = security_data['breach_prevention_rate'] * 100
        ax2.pie([prevention_rate, 100-prevention_rate], labels=['Prevented', 'Breached'],
               autopct='%1.1f%%', colors=['#4caf50', '#f44336'], startangle=90)
        ax2.set_title('Breach Prevention', fontweight='bold')
        
        # 3. Compliance Rate
        ax3 = fig.add_subplot(gs[1, 1])
        compliance = security_data['device_compliance_rate'] * 100
        ax3.pie([compliance, 100-compliance], labels=['Compliant', 'Non-Compliant'],
               autopct='%1.1f%%', colors=['#2196f3', '#ff9800'], startangle=90)
        ax3.set_title('Device Compliance', fontweight='bold')
        
        # 4. User Satisfaction
        ax4 = fig.add_subplot(gs[1, 2])
        satisfaction = usability_data['user_satisfaction']
        ax4.barh(['Satisfaction'], [satisfaction], color='#8bc34a', height=0.5)
        ax4.set_xlim(0, 5)
        ax4.set_title('User Satisfaction (1-5)', fontweight='bold')
        ax4.text(satisfaction, 0, f'{satisfaction:.2f}', ha='left', va='center', 
                fontweight='bold', fontsize=12)
        
        # 5. Comparative Analysis
        ax5 = fig.add_subplot(gs[2, :])
        improvements = comparison_data['improvements']
        metrics = [m.replace('_', ' ').title()[:20] for m in list(improvements.keys())[:4]]
        improvement_pcts = [improvements[m]['improvement_percent'] for m in list(improvements.keys())[:4]]
        
        colors_bar = ['#4caf50' if x > 0 else '#f44336' for x in improvement_pcts]
        bars = ax5.barh(metrics, improvement_pcts, color=colors_bar)
        ax5.set_xlabel('Improvement over Traditional Security (%)')
        ax5.set_title('ZTA Improvements vs Traditional Security', fontweight='bold')
        ax5.axvline(x=0, color='black', linestyle='-', linewidth=0.8)
        
        for bar in bars:
            width = bar.get_width()
            ax5.text(width, bar.get_y() + bar.get_height()/2.,
                    f'{width:+.1f}%', ha='left' if width > 0 else 'right', 
                    va='center', fontweight='bold')
        
        plt.tight_layout()
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        print(f"  Saved: {filepath}")
        plt.close()
