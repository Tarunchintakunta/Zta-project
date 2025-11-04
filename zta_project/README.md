# Zero Trust Architecture (ZTA) Simulator

## Project Structure and File Descriptions

### Core Application Files

#### `main.py`
This is the entry point of our Zero Trust Architecture simulator. When executed, it initializes all core components and starts the simulation. The main script coordinates between different managers (identity, device, access control) to demonstrate the Zero Trust security model in action. It's responsible for the simulation workflow and generating the final security report.

#### `config.py`
The configuration hub of our application. This file contains all the adjustable parameters like security thresholds, logging levels, and system behaviors. By keeping these settings in one place, we can easily modify the simulation without touching the core logic. It includes settings for authentication requirements, device compliance rules, and access control policies.

#### `requirements.txt`
Lists all Python package dependencies required to run the project. This ensures consistent development environments across different machines. Key dependencies include NumPy for numerical operations, Pandas for data handling, and Matplotlib for generating security visualizations.

### Core Components (`/core/`)

#### `identity_manager.py`
The backbone of our authentication system. This module handles user verification, session management, and permission checks. It implements multi-factor authentication and maintains the user session state. The identity manager works closely with the access controller to enforce security policies at every access attempt.

#### `device_manager.py`
Responsible for monitoring and evaluating the security posture of all devices in the network. It performs real-time compliance checks, calculates trust scores based on device health metrics, and can quarantine non-compliant devices. This component is crucial for maintaining the Zero Trust principle of "never trust, always verify."

#### `access_controller.py`
The policy enforcement point of our Zero Trust architecture. It makes access control decisions by evaluating user identity, device trust score, and contextual factors against defined security policies. Every access request passes through this component, which logs the decision and enforces the principle of least privilege.

### Data Models (`/models/`)

#### `user.py`
Defines the User class and related functionality. This includes user attributes like username, role, authentication status, and associated permissions. The user model supports role-based access control (RBAC) and maintains the authentication state throughout the session.

#### `device.py`
Contains the Device class that represents all endpoints in our network. It tracks device properties such as OS version, patch level, security software status, and network location. The device model includes methods to calculate and update the device's trust score based on these attributes.

#### `application.py`
Models the applications and resources within our system. Each application has defined security requirements and sensitivity levels. This module helps enforce access controls by defining which users with which device trust levels can access specific applications.

### Testing (`/tests/`)

#### `test_core.py`
Contains comprehensive unit tests for all core functionality. This includes tests for user authentication flows, device compliance checks, and access control decisions. The test suite ensures that our security controls work as intended and helps catch regressions as we develop new features.

## Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the simulation:
   ```bash
   python main.py
   ```

3. View the generated reports in the `results/` directory.

## Next Steps

- Implement multi-factor authentication
- Add network segmentation rules
- Enhance logging and monitoring capabilities
- Develop a web-based dashboard for real-time monitoring
