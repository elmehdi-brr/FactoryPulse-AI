# Use Cases

**Project:** FactoryPulse AI  
**Version:** 1.0  
**Status:** Draft

---

# 1. Introduction

This document describes the main interactions between users and the FactoryPulse AI platform.

Use Cases provide a detailed description of how users interact with the system to achieve specific objectives.

They complement the User Stories document by describing the expected workflow, actors, preconditions, main flow, alternative flows, and expected outcomes.

---

# 2. Use Case Structure

Each Use Case contains:

- Use Case ID
- Name
- Primary Actor
- Supporting Actors
- Description
- Preconditions
- Trigger
- Main Flow
- Alternative Flows
- Postconditions
- Priority

---

# 3. Authentication Use Cases

## UC-AUTH-001 — User Login

**Primary Actor:** All Users

**Description:**  
Allows an authorized user to securely access the FactoryPulse AI platform.

**Preconditions:**

- The user has an active account.
- The user has valid credentials.
- The platform is available.

**Trigger:**  
The user opens the login page.

### Main Flow

1. The user enters their email or username.
2. The user enters their password.
3. The user submits the login form.
4. The system validates the credentials.
5. The system verifies that the account is active.
6. The system identifies the user's role.
7. The system generates an authentication token.
8. The system redirects the user to the appropriate dashboard.

### Alternative Flows

**A1 — Invalid Credentials**

1. The system detects invalid credentials.
2. The system rejects the login attempt.
3. The system displays an error message.
4. The user can try again.

**A2 — Inactive Account**

1. The system detects that the account is inactive.
2. The system denies access.
3. The system displays an appropriate message.

**Postconditions:**

- The user is authenticated.
- The user's permissions are loaded.
- The user can access authorized features.

**Priority:** High

---

# 4. Machine Monitoring Use Cases

## UC-MON-001 — View Factory Overview

**Primary Actor:** Plant Manager

**Supporting Actors:** Maintenance Manager

**Description:**  
Allows authorized users to view the overall operational status of the factory.

**Preconditions:**

- The user is authenticated.
- Factory data is available.

**Trigger:**  
The user opens the main dashboard.

### Main Flow

1. The user logs into the platform.
2. The system displays the main dashboard.
3. The system retrieves the latest factory data.
4. The system displays the number of machines.
5. The system displays machine health statuses.
6. The system displays active alerts.
7. The system displays key operational KPIs.
8. The user reviews the factory overview.

**Postconditions:**

- The user has an overview of the current factory status.

**Priority:** High

---

## UC-MON-002 — View Machine Details

**Primary Actor:** Maintenance Engineer

**Supporting Actors:** Maintenance Manager, Plant Manager

**Description:**  
Allows a user to inspect detailed information about a specific machine.

**Preconditions:**

- The user is authenticated.
- The machine exists in the system.

**Trigger:**  
The user selects a machine.

### Main Flow

1. The user opens the machine monitoring section.
2. The system displays available machines.
3. The user selects a machine.
4. The system retrieves machine information.
5. The system displays machine metadata.
6. The system displays the current machine status.
7. The system displays recent sensor measurements.
8. The system displays historical sensor data.
9. The system displays active alerts.
10. The system displays maintenance history.
11. The system displays AI-generated risk information.

**Postconditions:**

- The user can analyze the selected machine.

**Priority:** High

---

## UC-MON-003 — Monitor Sensor Data in Real Time

**Primary Actor:** Maintenance Engineer

**Description:**  
Allows an engineer to monitor live sensor measurements.

**Preconditions:**

- The user is authenticated.
- The machine has registered sensors.
- Sensor data is available.

**Trigger:**  
The user opens the real-time monitoring view.

### Main Flow

1. The user selects a machine.
2. The user opens real-time monitoring.
3. The system establishes a real-time data connection.
4. The system receives new sensor measurements.
5. The system updates the displayed values.
6. The system updates real-time charts.
7. The system evaluates sensor values against configured thresholds.
8. The system generates an alert if a critical threshold is exceeded.

**Alternative Flows**

**A1 — Sensor Offline**

1. The system detects that no new data is being received.
2. The system marks the sensor as offline.
3. The system generates an appropriate alert.

**Postconditions:**

- The user can observe current sensor behavior.
- Critical sensor conditions can trigger alerts.

**Priority:** High

---

# 5. Alert Management Use Cases

## UC-ALERT-001 — View Alerts

**Primary Actor:** Maintenance Manager

**Supporting Actors:** Maintenance Engineer, Technician

**Description:**  
Allows authorized users to view and manage machine alerts.

**Preconditions:**

- The user is authenticated.
- Alerts exist in the system.

**Trigger:**  
The user opens the alerts section.

### Main Flow

1. The user opens the alerts section.
2. The system retrieves active alerts.
3. The system displays alerts.
4. The user filters alerts by severity.
5. The user selects an alert.
6. The system displays alert details.
7. The user reviews the related machine information.
8. The user reviews the alert history.

**Postconditions:**

- The user can identify and investigate active alerts.

**Priority:** High

---

## UC-ALERT-002 — Resolve Alert

**Primary Actor:** Maintenance Engineer

**Supporting Actors:** Technician

**Description:**  
Allows an authorized user to investigate and resolve a machine alert.

**Preconditions:**

- The user is authenticated.
- An active alert exists.

**Trigger:**  
The user selects an active alert.

### Main Flow

1. The user opens the alert.
2. The system displays alert details.
3. The user investigates the related machine.
4. The user determines the appropriate action.
5. The user records the resolution.
6. The user marks the alert as resolved.
7. The system records the resolution date and user.
8. The system updates the alert status.

**Postconditions:**

- The alert is marked as resolved.
- The resolution is stored in the system history.

**Priority:** High

---

# 6. Predictive Maintenance Use Cases

## UC-PRED-001 — View Failure Risk Prediction

**Primary Actor:** Maintenance Manager

**Supporting Actors:** Maintenance Engineer

**Description:**  
Allows authorized users to review AI-generated machine failure risk predictions.

**Preconditions:**

- The user is authenticated.
- Machine sensor data is available.
- A trained AI model is available.

**Trigger:**  
The user opens the machine risk analysis.

### Main Flow

1. The user selects a machine.
2. The system retrieves the latest sensor data.
3. The system sends relevant data to the AI prediction service.
4. The AI model calculates the failure risk.
5. The system receives the prediction.
6. The system displays the failure probability.
7. The system classifies the risk level.
8. The system displays the prediction to the user.

**Postconditions:**

- The user can evaluate the machine's predicted failure risk.

**Priority:** High

---

## UC-PRED-002 — View AI Prediction Explanation

**Primary Actor:** Maintenance Engineer

**Description:**  
Allows an engineer to understand the factors contributing to an AI prediction.

**Preconditions:**

- A machine prediction exists.
- Explainability information is available.

**Trigger:**  
The engineer opens the prediction explanation.

### Main Flow

1. The engineer selects a machine prediction.
2. The system retrieves the prediction explanation.
3. The system identifies the most influential factors.
4. The system displays the contributing sensor values.
5. The system displays the factors that increased or decreased the predicted risk.
6. The engineer reviews the explanation.

**Postconditions:**

- The engineer understands the main factors behind the AI prediction.

**Priority:** High

---

# 7. Maintenance Management Use Cases

## UC-MAINT-001 — Create Maintenance Task

**Primary Actor:** Maintenance Manager

**Supporting Actors:** Maintenance Engineer

**Description:**  
Allows an authorized user to create a maintenance task for a machine.

**Preconditions:**

- The user is authenticated.
- The machine exists.

**Trigger:**  
The user decides that maintenance is required.

### Main Flow

1. The user selects a machine.
2. The user creates a new maintenance task.
3. The user selects the maintenance type.
4. The user enters the task description.
5. The user sets the priority.
6. The user sets the planned maintenance date.
7. The user submits the task.
8. The system validates the information.
9. The system creates the maintenance task.
10. The system stores the task.

**Postconditions:**

- A new maintenance task exists.
- The task can be assigned to a technician.

**Priority:** High

---

## UC-MAINT-002 — Assign Maintenance Task

**Primary Actor:** Maintenance Manager

**Description:**  
Allows a manager to assign a maintenance task to a technician.

**Preconditions:**

- A maintenance task exists.
- At least one technician is available.

**Trigger:**  
The manager opens an unassigned maintenance task.

### Main Flow

1. The manager selects the task.
2. The system displays available technicians.
3. The manager selects a technician.
4. The manager confirms the assignment.
5. The system assigns the task.
6. The system notifies the technician.

**Postconditions:**

- The maintenance task is assigned.
- The technician is notified.

**Priority:** High

---

## UC-MAINT-003 — Update Maintenance Task

**Primary Actor:** Technician

**Description:**  
Allows a technician to update the progress of a maintenance task.

**Preconditions:**

- The technician is authenticated.
- The technician has an assigned task.

**Trigger:**  
The technician starts or completes maintenance work.

### Main Flow

1. The technician opens assigned tasks.
2. The technician selects a task.
3. The technician reviews task details.
4. The technician starts the intervention.
5. The technician changes the task status.
6. The technician records actions performed.
7. The technician adds notes.
8. The technician records relevant information.
9. The technician marks the task as completed.
10. The system records the completion.

**Postconditions:**

- The maintenance task status is updated.
- The intervention is recorded in maintenance history.

**Priority:** High

---

# 8. AI Anomaly Detection Use Cases

## UC-AI-001 — Detect Machine Anomaly

**Primary Actor:** System

**Supporting Actors:** Maintenance Engineer

**Description:**  
Automatically identifies abnormal machine behavior using sensor data.

**Preconditions:**

- Sensor data is available.
- An anomaly detection model is available.

**Trigger:**  
New sensor data is received.

### Main Flow

1. The system receives new sensor data.
2. The system validates the data.
3. The system preprocesses the data.
4. The anomaly detection model analyzes the data.
5. The model calculates an anomaly score.
6. The system determines whether the behavior is abnormal.
7. If abnormal behavior is detected, the system creates an alert.
8. The system stores the anomaly event.
9. The system notifies authorized users.

**Postconditions:**

- The anomaly is recorded.
- An alert is created when appropriate.

**Priority:** High

---

# 9. Reporting Use Cases

## UC-REPORT-001 — Generate Operational Report

**Primary Actor:** Plant Manager

**Supporting Actors:** Maintenance Manager

**Description:**  
Allows authorized users to generate reports about factory and equipment performance.

**Preconditions:**

- The user is authenticated.
- Relevant data exists.

**Trigger:**  
The user requests a report.

### Main Flow

1. The user opens the reporting section.
2. The user selects the report type.
3. The user selects the required date range.
4. The user selects relevant machines or departments.
5. The user generates the report.
6. The system retrieves the required data.
7. The system generates the report.
8. The user views the report.
9. The user exports the report.

**Postconditions:**

- The requested report is generated.
- The report can be exported.

**Priority:** Medium

---

# 10. User Management Use Cases

## UC-USER-001 — Manage Users

**Primary Actor:** Administrator

**Description:**  
Allows an administrator to manage platform users.

**Preconditions:**

- The administrator is authenticated.
- The administrator has appropriate permissions.

**Trigger:**  
The administrator opens user management.

### Main Flow

1. The administrator opens the user management section.
2. The system displays registered users.
3. The administrator creates or selects a user.
4. The administrator enters or modifies user information.
5. The administrator assigns a role.
6. The administrator saves the changes.
7. The system validates the information.
8. The system updates the user account.

**Postconditions:**

- The user account is created or updated.
- The user's permissions reflect the assigned role.

**Priority:** High

---

# 11. Use Case Relationships

The main relationships between the platform's use cases are:

```text
User Login
    │
    ├── View Factory Overview
    │
    ├── View Machine Details
    │       │
    │       ├── Monitor Sensor Data
    │       │
    │       ├── View Failure Risk Prediction
    │       │       │
    │       │       └── View AI Prediction Explanation
    │       │
    │       └── View Maintenance History
    │
    ├── View Alerts
    │       │
    │       └── Resolve Alert
    │
    └── Maintenance Management
            │
            ├── Create Maintenance Task
            │
            ├── Assign Maintenance Task
            │
            └── Update Maintenance Task
```

---

# 12. Future Use Cases

The following use cases may be implemented in future versions:

- UC-FUTURE-001 — Interact with AI Assistant
- UC-FUTURE-002 — Connect Real IoT Device
- UC-FUTURE-003 — Manage Spare Parts
- UC-FUTURE-004 — Optimize Maintenance Costs
- UC-FUTURE-005 — Forecast Energy Consumption
- UC-FUTURE-006 — Manage Multiple Factories
- UC-FUTURE-007 — Integrate with ERP or CMMS