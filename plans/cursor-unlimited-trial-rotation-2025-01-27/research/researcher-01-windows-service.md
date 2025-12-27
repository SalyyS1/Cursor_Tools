# Research: Windows Service Implementation for Python

**Researcher:** AI Agent  
**Date:** 2025-01-27  
**Topic:** Windows Service implementation for background rotation monitoring

## Key Findings

### Python Windows Service Libraries

1. **pywin32 (win32service)**
   - Standard library for Windows services
   - Requires `pywin32` package
   - Provides `win32serviceutil.ServiceFramework`
   - Pros: Native, well-documented
   - Cons: Windows-only, requires admin for installation

2. **python-windows-service**
   - Wrapper around pywin32
   - Simpler API
   - Less control

3. **NSSM (Non-Sucking Service Manager)**
   - External tool, wraps any executable
   - No code changes needed
   - Pros: Simple, works with any Python script
   - Cons: External dependency

### Recommended Approach: pywin32

```python
import win32serviceutil
import win32service
import servicemanager

class RotationService(win32serviceutil.ServiceFramework):
    _svc_name_ = "CursorRotationService"
    _svc_display_name_ = "Cursor Trial Rotation Service"
    _svc_description_ = "Automated Cursor Pro trial rotation service"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
    
    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
    
    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        self.main()
    
    def main(self):
        # Rotation monitoring loop
        while True:
            # Check rotation conditions
            # Trigger rotation if needed
            # Sleep for polling interval
```

### Installation

```python
# Install service
python service.py install

# Start service
python service.py start

# Stop service
python service.py stop

# Remove service
python service.py remove
```

### Scheduled Task Alternative

- Use Windows Task Scheduler API
- Create task programmatically
- Run Python script on schedule
- Pros: No admin needed for basic tasks
- Cons: Less control, requires task scheduler

### Coordination Strategy

- Shared state file (JSON) with file locking
- Service writes status, Task reads status
- Service takes priority, Task acts as backup
- Use `fcntl` (Linux) or `msvcrt` (Windows) for file locking

## Implementation Considerations

1. **Permissions:** Service needs appropriate permissions (not necessarily admin)
2. **Logging:** Use Windows Event Log via `servicemanager`
3. **Error Handling:** Service must handle crashes gracefully
4. **Restart Policy:** Configure Windows to auto-restart service on failure
5. **Dependencies:** Ensure Python and dependencies available to service

## References

- pywin32 documentation: https://github.com/mhammond/pywin32
- Windows Service best practices: Microsoft docs
- NSSM: https://nssm.cc/

## Unresolved Questions

- Should service run as SYSTEM or user account?
- How to handle Python virtual environment in service context?

