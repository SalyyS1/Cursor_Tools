# Phase 2: Hybrid Service Architecture

**Date:** 2025-01-27  
**Status:** Pending  
**Priority:** High  
**Effort:** 2 weeks  
**Dependencies:** Phase 1

## Context Links

- **Parent Plan:** [plan.md](./plan.md)
- **Dependencies:** [Phase 1: Core Hybrid System](./phase-01-core-hybrid-system.md)
- **Related Docs:**
  - [Research: Windows Service](../research/researcher-01-windows-service.md)

## Overview

Implement hybrid service architecture: Windows background service for continuous monitoring, scheduled task for backup/proactive rotation, and notification system for user feedback.

## Key Insights

1. **Service + Task:** Hybrid approach provides redundancy and flexibility
2. **Coordination:** Shared state file with locking prevents conflicts
3. **Notifications:** Multiple notification types (toast, tray, log)
4. **Installation:** Service installation requires admin, but can run as user

## Requirements

### Functional Requirements
1. Windows background service for continuous monitoring
2. Scheduled task for backup/proactive rotation
3. Service-task coordination mechanism
4. Notification system (toast, tray, log)
5. Service installation/uninstallation
6. Service health monitoring

### Non-Functional Requirements
1. Service uptime > 99.5%
2. Notification delivery > 99%
3. Service restart on failure
4. Low resource usage (< 50MB RAM)
5. Graceful shutdown

## Architecture

### Component Structure

```
service/
├── rotation_service.py      # Windows service implementation
├── service_manager.py        # Service installation/management
└── __init__.py

utils/
└── notifier.py              # Notification system

config/
└── service_config.py        # Service configuration
```

### Service Architecture

```
Windows Service (Always On)
    ↓
Rotation Scheduler (from Phase 1)
    ↓
Rotation Engine (from Phase 1)
    ↓
Notification System

Scheduled Task (Backup)
    ↓
Health Check
    ↓
Service Status Check
    ↓
Proactive Rotation (if needed)
```

### Coordination Mechanism

```
Shared State File (JSON)
├── service_running: bool
├── last_rotation: timestamp
├── rotation_in_progress: bool
└── lock: file lock
```

## Related Code Files

### Files to Create
- `service/rotation_service.py` - Windows service
- `service/service_manager.py` - Service management
- `service/__init__.py` - Service package
- `utils/notifier.py` - Notification system
- `config/service_config.py` - Service config

### Files to Modify
- `requirements.txt` - Add pywin32
- `config/settings.py` - Add service settings

## Implementation Steps

### Step 1: Windows Service Implementation (3 days)
1. Create `service/` directory
2. Create `service/rotation_service.py`
3. Implement win32serviceutil.ServiceFramework
4. Integrate with RotationScheduler from Phase 1
5. Add service lifecycle methods (start, stop, pause)
6. Add error handling and logging
7. Write service tests

### Step 2: Service Manager (2 days)
1. Create `service/service_manager.py`
2. Implement service installation
3. Implement service uninstallation
4. Implement service start/stop
5. Add service status checking
6. Add admin rights verification
7. Write management tests

### Step 3: Scheduled Task Integration (2 days)
1. Create scheduled task creation script
2. Implement task creation API (using schtasks or Task Scheduler API)
3. Implement task deletion
4. Add task status checking
5. Integrate with rotation scheduler
6. Write task tests

### Step 4: Coordination Mechanism (2 days)
1. Implement shared state file (JSON)
2. Add file locking mechanism (fcntl/msvcrt)
3. Implement service-task coordination logic
4. Add conflict resolution
5. Add state file cleanup
6. Write coordination tests

### Step 5: Notification System (2 days)
1. Create `utils/notifier.py`
2. Implement Windows toast notifications
3. Implement system tray notifications
4. Implement log file notifications
5. Add notification configuration
6. Add quiet hours support
7. Write notification tests

### Step 6: Service Configuration (1 day)
1. Create `config/service_config.py`
2. Add service settings (poll interval, etc.)
3. Add notification settings
4. Add coordination settings
5. Update `config/settings.py`
6. Write config tests

### Step 7: Integration & Testing (2 days)
1. Integrate all components
2. End-to-end testing
3. Service installation testing
4. Failure scenario testing
5. Performance testing
6. Documentation

## Todo List

- [ ] Create service/rotation_service.py
- [ ] Create service/service_manager.py
- [ ] Create service/__init__.py
- [ ] Create utils/notifier.py
- [ ] Create config/service_config.py
- [ ] Update requirements.txt (add pywin32)
- [ ] Update config/settings.py
- [ ] Implement Windows service
- [ ] Implement scheduled task
- [ ] Implement coordination mechanism
- [ ] Implement notification system
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Write service installation guide
- [ ] Update documentation

## Success Criteria

1. ✅ Service installs successfully
2. ✅ Service runs continuously (uptime > 99.5%)
3. ✅ Service auto-restarts on failure
4. ✅ Scheduled task works as backup
5. ✅ Service-task coordination prevents conflicts
6. ✅ Notifications delivered > 99%
7. ✅ Service uses < 50MB RAM
8. ✅ All tests pass

## Risk Assessment

### High Risk
- **Service Installation:** Requires admin rights, may fail
  - **Mitigation:** Clear installation guide, error handling

### Medium Risk
- **Service-Task Coordination:** May have race conditions
  - **Mitigation:** File locking, careful coordination logic
- **Notification Delivery:** May fail on some systems
  - **Mitigation:** Multiple notification types, fallback to log

### Low Risk
- **Service Implementation:** Well-documented libraries
- **Scheduled Task:** Standard Windows feature

## Security Considerations

1. **Service Permissions:** Run as user, not SYSTEM (if possible)
2. **State File:** Secure location, proper permissions
3. **Notifications:** Don't expose sensitive info
4. **Service Logs:** Secure logging, no sensitive data

## Next Steps

After Phase 2 completion:
- Proceed to Phase 3: API Integration & Monitoring
- Test service reliability
- Gather user feedback on notifications

