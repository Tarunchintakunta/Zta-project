"""
Data Loader for Real-World Security Datasets
Supports Microsoft Sentinel, Azure AD, LANL, and CERT Insider Threat datasets

This module loads and preprocesses real-world authentication and access logs
to avoid circular logic in evaluation.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import os
import json
from pathlib import Path


class RealWorldDataLoader:
    """
    Loads and preprocesses real-world security datasets for training and evaluation.
    Separates training and test data to avoid circular logic.
    """
    
    def __init__(self, data_dir: str = "data/real_world"):
        """
        Initialize the data loader.
        
        Args:
            data_dir: Directory containing real-world datasets
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Dataset formats supported
        self.supported_formats = ['sentinel', 'azure_ad', 'lanl', 'cert', 'csv']
        
    def load_dataset(self, dataset_name: str, format_type: str = 'csv', 
                    train_split: float = 0.7, start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None) -> Tuple[List[Dict], List[Dict]]:
        """
        Load a real-world dataset and split into train/test.
        
        Args:
            dataset_name: Name of the dataset file
            format_type: Format type ('sentinel', 'azure_ad', 'lanl', 'cert', 'csv')
            train_split: Proportion of data for training (rest for testing)
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Tuple of (training_data, test_data) as lists of behavior dictionaries
        """
        file_path = self.data_dir / dataset_name
        
        if not file_path.exists():
            print(f"Warning: Dataset file not found: {file_path}")
            print("Creating synthetic dataset structure for reference...")
            return self._create_synthetic_structure()
        
        # Load based on format
        if format_type == 'csv':
            df = pd.read_csv(file_path)
        elif format_type == 'sentinel':
            df = self._load_sentinel_format(file_path)
        elif format_type == 'azure_ad':
            df = self._load_azure_ad_format(file_path)
        elif format_type == 'lanl':
            df = self._load_lanl_format(file_path)
        elif format_type == 'cert':
            df = self._load_cert_format(file_path)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
        
        # Convert to standard format
        behaviors = self._convert_to_standard_format(df, format_type)
        
        # Filter by date if provided
        if start_date or end_date:
            behaviors = self._filter_by_date(behaviors, start_date, end_date)
        
        # Split into train/test (temporal split to avoid data leakage)
        train_data, test_data = self._temporal_split(behaviors, train_split)
        
        return train_data, test_data
    
    def _load_sentinel_format(self, file_path: Path) -> pd.DataFrame:
        """Load Microsoft Sentinel log format"""
        # Sentinel logs are typically JSON or CSV
        if file_path.suffix == '.json':
            with open(file_path, 'r') as f:
                data = json.load(f)
            df = pd.json_normalize(data)
        else:
            df = pd.read_csv(file_path)
        
        # Map Sentinel fields to standard format
        # Expected fields: TimeGenerated, UserPrincipalName, IPAddress, ResultType, etc.
        return df
    
    def _load_azure_ad_format(self, file_path: Path) -> pd.DataFrame:
        """Load Azure AD Identity Protection logs"""
        df = pd.read_csv(file_path)
        # Expected fields: Timestamp, UserId, IPAddress, Result, Location, etc.
        return df
    
    def _load_lanl_format(self, file_path: Path) -> pd.DataFrame:
        """Load LANL authentication dataset format"""
        # LANL format: timestamp, user, computer, authentication type, logon type, etc.
        df = pd.read_csv(file_path, sep=',')
        return df
    
    def _load_cert_format(self, file_path: Path) -> pd.DataFrame:
        """Load CERT Insider Threat dataset format"""
        # CERT format: user, date, time, pc, activity, etc.
        df = pd.read_csv(file_path)
        return df
    
    def _convert_to_standard_format(self, df: pd.DataFrame, format_type: str) -> List[Dict]:
        """
        Convert dataset-specific format to standard behavior dictionary format.
        Standard format: {
            'timestamp': datetime,
            'user_id': str,
            'resource': str,
            'location': str,
            'device_id': str,
            'hour': int,
            'day_of_week': int,
            'success': bool,
            'failed_auth': bool,
            ...
        }
        """
        behaviors = []
        
        for _, row in df.iterrows():
            behavior = {}
            
            # Extract timestamp
            timestamp = self._extract_timestamp(row, format_type)
            behavior['timestamp'] = timestamp
            behavior['date'] = timestamp.date() if timestamp else datetime.now().date()
            behavior['hour'] = timestamp.hour if timestamp else datetime.now().hour
            behavior['day_of_week'] = timestamp.weekday() if timestamp else datetime.now().weekday()
            
            # Extract user ID
            behavior['user_id'] = self._extract_field(row, format_type, 'user_id', 
                                                       ['UserPrincipalName', 'UserId', 'user', 'username'])
            
            # Extract resource/application
            behavior['resource'] = self._extract_field(row, format_type, 'resource',
                                                       ['Application', 'Resource', 'app', 'application'])
            
            # Extract location/IP
            behavior['location'] = self._extract_field(row, format_type, 'location',
                                                       ['Location', 'IPAddress', 'ip', 'location'])
            
            # Extract device
            behavior['device_id'] = self._extract_field(row, format_type, 'device_id',
                                                       ['DeviceId', 'Computer', 'pc', 'device'])
            
            # Extract authentication result
            success = self._extract_success(row, format_type)
            behavior['success'] = success
            behavior['failed_auth'] = not success
            
            # Additional fields
            behavior['access_rate'] = 1.0  # Will be calculated from sequence
            behavior['location_changes'] = 0  # Will be calculated from sequence
            
            behaviors.append(behavior)
        
        # Calculate derived features (access rate, location changes) from sequence
        behaviors = self._calculate_sequence_features(behaviors)
        
        return behaviors
    
    def _extract_timestamp(self, row: pd.Series, format_type: str) -> Optional[datetime]:
        """Extract timestamp from row based on format"""
        timestamp_fields = {
            'sentinel': ['TimeGenerated', 'timestamp'],
            'azure_ad': ['Timestamp', 'TimeGenerated', 'timestamp'],
            'lanl': ['timestamp', 'date', 'time'],
            'cert': ['date', 'time', 'timestamp'],
            'csv': ['timestamp', 'date', 'time', 'datetime']
        }
        
        fields = timestamp_fields.get(format_type, ['timestamp', 'date'])
        for field in fields:
            if field in row and pd.notna(row[field]):
                try:
                    return pd.to_datetime(row[field])
                except:
                    continue
        
        return datetime.now()
    
    def _extract_field(self, row: pd.Series, format_type: str, default_key: str, 
                      possible_keys: List[str]) -> str:
        """Extract a field from row, trying multiple possible column names"""
        # Try default key first
        if default_key in row and pd.notna(row[default_key]):
            return str(row[default_key])
        
        # Try possible keys
        for key in possible_keys:
            if key in row and pd.notna(row[key]):
                return str(row[key])
        
        return f"unknown_{default_key}"
    
    def _extract_success(self, row: pd.Series, format_type: str) -> bool:
        """Extract authentication success from row"""
        success_fields = {
            'sentinel': ['ResultType', 'Result'],
            'azure_ad': ['Result', 'Status'],
            'lanl': ['result', 'success'],
            'cert': ['result', 'success']
        }
        
        fields = success_fields.get(format_type, ['success', 'result'])
        for field in fields:
            if field in row:
                value = str(row[field]).lower()
                if 'success' in value or value in ['0', '200', 'ok', 'true', '1']:
                    return True
                if 'fail' in value or 'denied' in value or value in ['401', '403']:
                    return False
        
        # Default to success if unclear
        return True
    
    def _calculate_sequence_features(self, behaviors: List[Dict]) -> List[Dict]:
        """Calculate sequence-based features like access rate and location changes"""
        if not behaviors:
            return behaviors
        
        # Group by user
        user_behaviors = {}
        for behavior in behaviors:
            user_id = behavior.get('user_id', 'unknown')
            if user_id not in user_behaviors:
                user_behaviors[user_id] = []
            user_behaviors[user_id].append(behavior)
        
        # Calculate features per user
        for user_id, user_behavs in user_behaviors.items():
            # Sort by timestamp
            user_behavs.sort(key=lambda x: x.get('timestamp', datetime.now()))
            
            # Calculate access rate (events per hour)
            for i, behavior in enumerate(user_behavs):
                if i > 0:
                    prev_time = user_behavs[i-1].get('timestamp', datetime.now())
                    curr_time = behavior.get('timestamp', datetime.now())
                    time_diff = (curr_time - prev_time).total_seconds() / 3600.0
                    if time_diff > 0:
                        behavior['access_rate'] = 1.0 / time_diff
                    else:
                        behavior['access_rate'] = 10.0  # Very rapid
                else:
                    behavior['access_rate'] = 1.0
            
            # Calculate location changes
            prev_location = None
            location_changes = 0
            for behavior in user_behavs:
                curr_location = behavior.get('location', '')
                if prev_location and curr_location != prev_location:
                    location_changes += 1
                behavior['location_changes'] = location_changes
                prev_location = curr_location
        
        return behaviors
    
    def _filter_by_date(self, behaviors: List[Dict], start_date: Optional[datetime],
                       end_date: Optional[datetime]) -> List[Dict]:
        """Filter behaviors by date range"""
        filtered = []
        for behavior in behaviors:
            timestamp = behavior.get('timestamp')
            if not timestamp:
                continue
            
            if start_date and timestamp < start_date:
                continue
            if end_date and timestamp > end_date:
                continue
            
            filtered.append(behavior)
        
        return filtered
    
    def _temporal_split(self, behaviors: List[Dict], train_split: float) -> Tuple[List[Dict], List[Dict]]:
        """
        Split behaviors temporally (by time, not randomly) to avoid data leakage.
        Earlier data for training, later data for testing.
        """
        if not behaviors:
            return [], []
        
        # Sort by timestamp
        sorted_behaviors = sorted(behaviors, key=lambda x: x.get('timestamp', datetime.min))
        
        # Split point
        split_idx = int(len(sorted_behaviors) * train_split)
        
        train_data = sorted_behaviors[:split_idx]
        test_data = sorted_behaviors[split_idx:]
        
        return train_data, test_data
    
    def _create_synthetic_structure(self) -> Tuple[List[Dict], List[Dict]]:
        """Create a placeholder structure when real data is not available"""
        print("\n" + "="*70)
        print("REAL-WORLD DATASET NOT FOUND")
        print("="*70)
        print("\nTo use real-world datasets, place them in the 'data/real_world/' directory.")
        print("\nSupported formats:")
        print("  - Microsoft Sentinel: JSON or CSV with TimeGenerated, UserPrincipalName, etc.")
        print("  - Azure AD: CSV with Timestamp, UserId, IPAddress, Result, etc.")
        print("  - LANL Authentication: CSV with timestamp, user, computer, etc.")
        print("  - CERT Insider Threat: CSV with user, date, time, pc, activity, etc.")
        print("\nExample usage:")
        print("  loader = RealWorldDataLoader()")
        print("  train, test = loader.load_dataset('azure_ad_logs.csv', format_type='azure_ad')")
        print("="*70 + "\n")
        
        return [], []
    
    def download_sample_datasets_info(self):
        """Print information about where to download real-world datasets"""
        info = """
REAL-WORLD DATASET SOURCES:
==========================

1. Microsoft Sentinel Sample Data:
   - Source: Microsoft Sentinel GitHub samples
   - URL: https://github.com/Azure/Azure-Sentinel/tree/master/Sample%20Data
   - Format: JSON/CSV with authentication and access logs

2. Azure AD Identity Protection Logs:
   - Source: Azure AD Identity Protection
   - Format: CSV export from Azure Portal
   - Fields: Timestamp, UserId, IPAddress, Result, Location, etc.

3. LANL Authentication Dataset:
   - Source: Los Alamos National Laboratory
   - URL: https://csr.lanl.gov/data/
   - Format: CSV with authentication events
   - Citation: Kent, A. D., & Liebrock, L. M. (2014). Authentication data

4. CERT Insider Threat Dataset:
   - Source: CERT Division, Software Engineering Institute
   - URL: https://www.cert.org/insider-threat/
   - Format: CSV with user activity logs
   - Citation: CERT Insider Threat Dataset v6.2

5. Custom CSV Format:
   - Required columns: timestamp, user_id, resource, location, device_id, success
   - Optional columns: session_duration, failed_auth, etc.

Place downloaded datasets in: data/real_world/
        """
        print(info)
        return info

