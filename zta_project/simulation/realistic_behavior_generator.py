"""
Realistic Behavior Generator for Synthetic Data
Generates time-based, role-based, and sequence-based behaviors
to avoid fully random data generation.
"""

import random
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict
import config


class RealisticBehaviorGenerator:
    """
    Generates realistic user behaviors based on:
    - Time patterns (work hours, day of week, time zones)
    - Role-based patterns (different roles access different resources)
    - Sequence-based patterns (users follow workflows)
    """
    
    def __init__(self, users: List, devices: List, applications: List):
        self.users = users
        self.devices = devices
        self.applications = applications
        
        # Role-based resource access patterns
        self.role_resource_mapping = self._initialize_role_patterns()
        
        # User-specific patterns (work hours, preferred resources, etc.)
        self.user_patterns = {}
        self._initialize_user_patterns()
        
        # Sequence patterns (workflows)
        self.workflow_patterns = self._initialize_workflows()
        
        # Track user activity history for sequence generation
        self.user_activity_history = defaultdict(list)
        
    def _initialize_role_patterns(self) -> Dict[str, List[str]]:
        """Define which resources each role typically accesses"""
        role_patterns = {
            'employee': ['Email System', 'File Share', 'Video Conferencing'],
            'manager': ['Email System', 'File Share', 'CRM Platform', 'Analytics Dashboard', 'Video Conferencing'],
            'admin': ['Email System', 'File Share', 'Code Repository', 'Analytics Dashboard', 'HR Portal'],
            'contractor': ['Email System', 'File Share', 'Project Management'],
            'executive': ['Email System', 'Analytics Dashboard', 'Financial System', 'Video Conferencing']
        }
        return role_patterns
    
    def _initialize_user_patterns(self):
        """Initialize realistic patterns for each user"""
        for user in self.users:
            # Work hours based on role and location
            work_start, work_end = self._get_work_hours(user.role, user.location)
            
            # Preferred resources based on role
            preferred_resources = self.role_resource_mapping.get(user.role, ['Email System', 'File Share'])
            
            # Primary device (most used)
            user_devices = [d for d in self.devices if d.owner_id == user.user_id]
            primary_device = user_devices[0] if user_devices else random.choice(self.devices)
            
            # Typical location (most common)
            typical_location = user.location
            
            self.user_patterns[user.user_id] = {
                'work_start_hour': work_start,
                'work_end_hour': work_end,
                'preferred_resources': preferred_resources,
                'primary_device': primary_device.device_id,
                'typical_location': typical_location,
                'access_frequency': self._get_access_frequency(user.role),  # Accesses per day
                'weekend_activity': 0.2 if user.role in ['executive', 'admin'] else 0.05
            }
    
    def _get_work_hours(self, role: str, location: str) -> tuple:
        """Get typical work hours based on role and location"""
        # Base hours by role
        if role == 'executive':
            start, end = 7, 20  # Long hours
        elif role == 'admin':
            start, end = 8, 18
        elif role == 'manager':
            start, end = 8, 17
        elif role == 'contractor':
            start, end = 9, 17
        else:  # employee
            start, end = 9, 17
        
        # Adjust for location
        if location == 'remote':
            # Remote workers start slightly later, work more flexibly
            start += random.randint(0, 1)
            end += random.randint(0, 2)
        elif location == 'hybrid':
            # Hybrid workers have flexible hours
            start += random.randint(-1, 1)
            end += random.randint(-1, 1)
        
        return start, end
    
    def _get_access_frequency(self, role: str) -> int:
        """Get typical number of access events per day by role"""
        frequencies = {
            'executive': 15,
            'admin': 40,
            'manager': 30,
            'contractor': 25,
            'employee': 20
        }
        return frequencies.get(role, 20)
    
    def _initialize_workflows(self) -> Dict[str, List[str]]:
        """Define common workflow sequences"""
        workflows = {
            'morning_routine': ['Email System', 'File Share', 'Analytics Dashboard'],
            'project_work': ['File Share', 'Project Management', 'Code Repository'],
            'client_meeting': ['Video Conferencing', 'CRM Platform', 'Customer Database'],
            'reporting': ['Analytics Dashboard', 'File Share', 'Email System'],
            'admin_tasks': ['HR Portal', 'Financial System', 'Analytics Dashboard']
        }
        return workflows
    
    def generate_authentication_event(self, current_time: datetime, day_number: int) -> Optional[Dict]:
        """
        Generate a realistic authentication event based on time patterns.
        Returns None if no event should occur at this time.
        """
        # Select user based on work patterns (not fully random)
        active_users = self._get_active_users(current_time)
        if not active_users:
            return None
        
        # Weight selection by role and typical activity
        user = self._select_user_by_pattern(active_users, current_time)
        if not user:
            return None
        
        pattern = self.user_patterns[user.user_id]
        
        # Check if user should be active at this time
        hour = current_time.hour
        day_of_week = current_time.weekday()
        
        # Weekend check
        if day_of_week >= 5:  # Saturday, Sunday
            if random.random() > pattern['weekend_activity']:
                return None
        
        # Work hours check (with some flexibility)
        work_start = pattern['work_start_hour']
        work_end = pattern['work_end_hour']
        
        # Allow some activity outside work hours (10% chance)
        if not (work_start <= hour <= work_end):
            if random.random() > 0.1:
                return None
        
        # Select device (prefer primary device, but allow others)
        user_devices = [d for d in self.devices if d.owner_id == user.user_id]
        if not user_devices:
            user_devices = [random.choice(self.devices)]
        
        # 70% chance of using primary device
        if random.random() < 0.7 and user_devices:
            device = next((d for d in user_devices if d.device_id == pattern['primary_device']), user_devices[0])
        else:
            device = random.choice(user_devices)
        
        # Generate context
        context = {
            'device_id': device.device_id,
            'location': pattern['typical_location'],
            'ip_address': self._generate_realistic_ip(user.location),
            'timestamp': current_time
        }
        
        return {
            'user': user,
            'device': device,
            'context': context,
            'event_type': 'authentication'
        }
    
    def generate_access_request(self, current_time: datetime, user: Optional[object] = None) -> Optional[Dict]:
        """
        Generate a realistic access request based on role and sequence patterns.
        """
        if not user:
            active_users = self._get_active_users(current_time)
            if not active_users:
                return None
            user = self._select_user_by_pattern(active_users, current_time)
            if not user:
                return None
        
        pattern = self.user_patterns[user.user_id]
        
        # Select resource based on role and sequence
        resource = self._select_resource_by_pattern(user, pattern, current_time)
        if not resource:
            return None
        
        # Select device
        user_devices = [d for d in self.devices if d.owner_id == user.user_id]
        if not user_devices:
            user_devices = [random.choice(self.devices)]
        
        if random.random() < 0.7 and user_devices:
            device = next((d for d in user_devices if d.device_id == pattern['primary_device']), user_devices[0])
        else:
            device = random.choice(user_devices)
        
        return {
            'user': user,
            'device': device,
            'application': resource,
            'context': {
                'location': pattern['typical_location'],
                'timestamp': current_time
            },
            'event_type': 'access_request'
        }
    
    def _get_active_users(self, current_time: datetime) -> List:
        """Get users who should be active at this time based on work patterns"""
        active = []
        hour = current_time.hour
        day_of_week = current_time.weekday()
        
        for user in self.users:
            pattern = self.user_patterns[user.user_id]
            
            # Weekend check
            if day_of_week >= 5:
                if random.random() > pattern['weekend_activity']:
                    continue
            
            # Work hours check (with flexibility)
            work_start = pattern['work_start_hour']
            work_end = pattern['work_end_hour']
            
            if work_start <= hour <= work_end:
                active.append(user)
            elif random.random() < 0.1:  # 10% chance outside work hours
                active.append(user)
        
        return active
    
    def _select_user_by_pattern(self, active_users: List, current_time: datetime) -> Optional[object]:
        """Select user based on activity patterns, not purely random"""
        if not active_users:
            return None
        
        # Weight by role (executives and admins have more activity)
        weights = {
            'executive': 1.5,
            'admin': 1.3,
            'manager': 1.2,
            'contractor': 1.0,
            'employee': 1.0
        }
        
        weighted_users = []
        for user in active_users:
            weight = weights.get(user.role, 1.0)
            weighted_users.extend([user] * int(weight * 10))
        
        return random.choice(weighted_users)
    
    def _select_resource_by_pattern(self, user: object, pattern: Dict, current_time: datetime) -> Optional[object]:
        """
        Select resource based on role patterns and sequence (workflow).
        """
        # Get user's recent activity for sequence-based selection
        recent_activity = self.user_activity_history[user.user_id][-3:]  # Last 3 activities
        
        # Check if we're in a workflow
        if recent_activity:
            last_resource = recent_activity[-1].get('resource_name', '')
            # Continue workflow if applicable
            for workflow_name, workflow_resources in self.workflow_patterns.items():
                if last_resource in workflow_resources:
                    idx = workflow_resources.index(last_resource)
                    if idx < len(workflow_resources) - 1:
                        next_resource_name = workflow_resources[idx + 1]
                        next_resource = next((a for a in self.applications if a.name == next_resource_name), None)
                        if next_resource:
                            return next_resource
        
        # Otherwise, select from preferred resources (70% chance) or all resources (30%)
        preferred = pattern['preferred_resources']
        if random.random() < 0.7 and preferred:
            resource_name = random.choice(preferred)
            resource = next((a for a in self.applications if a.name == resource_name), None)
            if resource:
                return resource
        
        # Fallback to any resource
        return random.choice(self.applications)
    
    def _generate_realistic_ip(self, location: str) -> str:
        """Generate realistic IP address based on location"""
        # Simplified: just generate IP, but could be location-specific
        from faker import Faker
        faker = Faker()
        return faker.ipv4()
    
    def record_activity(self, user_id: str, activity: Dict):
        """Record user activity for sequence-based generation"""
        self.user_activity_history[user_id].append(activity)
        # Keep only last 10 activities per user
        if len(self.user_activity_history[user_id]) > 10:
            self.user_activity_history[user_id] = self.user_activity_history[user_id][-10:]
    
    def generate_time_based_events(self, day_number: int, events_per_day: int) -> List[Dict]:
        """
        Generate events throughout a day based on realistic time patterns.
        More events during work hours, fewer during off-hours.
        """
        events = []
        base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        base_date += timedelta(days=day_number - 1)
        
        # Distribute events throughout the day with higher density during work hours
        hours = list(range(24))
        # Weight hours: work hours (9-17) get higher weight
        hour_weights = [0.3 if 9 <= h <= 17 else 0.1 for h in hours]
        
        for _ in range(events_per_day):
            # Select hour based on weights
            hour = random.choices(hours, weights=hour_weights)[0]
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            
            event_time = base_date.replace(hour=hour, minute=minute, second=second)
            
            # Determine event type based on time patterns
            if hour < 9:  # Early morning: mostly authentication
                event_type_prob = {'authentication': 0.7, 'access_request': 0.3}
            elif 9 <= hour <= 17:  # Work hours: mix of all
                event_type_prob = {'authentication': 0.3, 'access_request': 0.6, 'device_check': 0.1}
            else:  # Evening: mostly access requests
                event_type_prob = {'authentication': 0.4, 'access_request': 0.5, 'device_check': 0.1}
            
            event_type = random.choices(
                list(event_type_prob.keys()),
                weights=list(event_type_prob.values())
            )[0]
            
            if event_type == 'authentication':
                event = self.generate_authentication_event(event_time, day_number)
            elif event_type == 'access_request':
                event = self.generate_access_request(event_time)
            else:
                event = {'event_type': 'device_check', 'timestamp': event_time}
            
            if event:
                event['timestamp'] = event_time
                events.append(event)
        
        # Sort by timestamp
        events.sort(key=lambda x: x.get('timestamp', datetime.now()))
        return events

