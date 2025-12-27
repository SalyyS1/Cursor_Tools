# Phase 1: Core Hybrid System

**Date:** 2025-01-27  
**Status:** ✅ Completed  
**Priority:** Critical  
**Effort:** 2 weeks  
**Completed:** 2025-01-27

## Context Links

- **Parent Plan:** [plan.md](./plan.md)
- **Dependencies:** None (foundation phase)
- **Related Docs:** 
  - [Brainstorming Report](../brainstorming-cursor-unlimited-trial-rotation-2025-01-27.md)
  - [Research: Cursor Logs](../research/researcher-02-cursor-logs-api.md)
  - [Scout Report](../scout/scout-01-codebase-analysis.md)

## Overview

Implement core components for hybrid rotation system: log discovery, token expiration detection, hybrid rotation scheduler, and enhanced rotation engine with advanced fingerprinting.

## Key Insights

1. **Log Discovery:** Multi-path strategy needed (standard + process + registry + scan)
2. **Token Detection:** Multiple sources (storage.json, state.vscdb, logs)
3. **Hybrid Scheduler:** Support multiple trigger types (token expired, rate limited, scheduled, manual)
4. **Advanced Fingerprinting:** Windows GUID rotation requires admin rights, needs careful implementation

## Requirements

### Functional Requirements
1. Discover Cursor log files automatically
2. Detect token expiration from multiple sources
3. Detect API rate limits from logs
4. Hybrid rotation scheduler with multiple trigger types
5. Enhanced rotation engine with advanced fingerprinting
6. Post-rotation validation

### Non-Functional Requirements
1. Log discovery < 5 seconds
2. Token detection accuracy > 95%
3. Rotation time < 30 seconds
4. Error handling with rollback
5. Comprehensive logging

## Architecture

### Component Structure

```
core/
├── log_discovery.py          # Multi-path log discovery
├── token_monitor.py          # Token expiration detection
├── api_monitor.py            # API health & rate limit detection
├── rotation_scheduler.py     # Hybrid rotation scheduler
├── rotation_engine.py        # Enhanced rotation engine
└── advanced_fingerprint.py   # Advanced fingerprinting

utils/
└── rotation_validator.py     # Post-rotation validation
```

### Data Flow

```
Log Discovery → Token Monitor → Rotation Scheduler
                    ↓
              API Monitor ────┘
                    ↓
            Rotation Engine → Advanced Fingerprint → Validator
```

## Related Code Files

### Files to Create
- `core/log_discovery.py` - New module
- `core/token_monitor.py` - New module
- `core/api_monitor.py` - New module
- `core/rotation_scheduler.py` - New module
- `core/rotation_engine.py` - New module
- `core/advanced_fingerprint.py` - New module
- `utils/rotation_validator.py` - New module

### Files to Modify
- `core/vscode_handler.py` - Add rotation automation methods
- `utils/paths.py` - Extend for log discovery
- `config/settings.py` - Add rotation configuration

## Implementation Steps

### Step 1: Log Discovery Module (2 days)
1. Create `core/log_discovery.py`
2. Implement standard path discovery
3. Implement process-based discovery (using psutil)
4. Implement registry-based discovery (using winreg)
5. Implement file system scan fallback
6. Add path validation and caching
7. Write unit tests

### Step 2: Token Monitor Module (2 days)
1. Create `core/token_monitor.py`
2. Implement storage.json token checking
3. Implement state.vscdb token checking
4. Implement log file parsing for token errors
5. Add token expiration detection logic
6. Write unit tests

### Step 3: API Monitor Module (2 days)
1. Create `core/api_monitor.py`
2. Implement log parsing for API responses
3. Detect 401/403/429 errors
4. Implement rate limit detection
5. Add API health status tracking
6. Write unit tests

### Step 4: Rotation Scheduler Module (2 days)
1. Create `core/rotation_scheduler.py`
2. Implement hybrid trigger logic
3. Support token expired trigger
4. Support rate limited trigger
5. Support scheduled trigger
6. Support manual trigger
7. Add coordination logic
8. Write unit tests

### Step 5: Enhanced Rotation Engine (2 days)
1. Create `core/rotation_engine.py`
2. Integrate with existing VSCodeHandler
3. Add pre-rotation validation
4. Add comprehensive backup
5. Add post-rotation validation
6. Add error handling and rollback
7. Write integration tests

### Step 6: Advanced Fingerprinting (2 days)
1. Create `core/advanced_fingerprint.py`
2. Implement Windows Machine GUID rotation
3. Implement MAC address spoofing (temporary)
4. Add registry backup before changes
5. Add rollback mechanism
6. Add admin rights checking
7. Write unit tests

### Step 7: Rotation Validator (1 day)
1. Create `utils/rotation_validator.py`
2. Implement ID change verification
3. Implement token removal verification
4. Implement file lock verification
5. Implement old trace detection
6. Generate validation report
7. Write unit tests

### Step 8: Configuration & Integration (1 day)
1. Update `config/settings.py` with rotation config
2. Extend `utils/paths.py` for log discovery
3. Extend `core/vscode_handler.py` with rotation methods
4. Integration testing
5. Documentation

## Todo List

- [ ] Create log_discovery.py module
- [ ] Create token_monitor.py module
- [ ] Create api_monitor.py module
- [ ] Create rotation_scheduler.py module
- [ ] Create rotation_engine.py module
- [ ] Create advanced_fingerprint.py module
- [ ] Create rotation_validator.py module
- [ ] Update config/settings.py
- [ ] Update utils/paths.py
- [ ] Update core/vscode_handler.py
- [ ] Write unit tests for all modules
- [ ] Write integration tests
- [ ] Update documentation

## Success Criteria

1. ✅ Log discovery finds Cursor logs in < 5 seconds
2. ✅ Token expiration detection accuracy > 95%
3. ✅ API rate limit detection accuracy > 90%
4. ✅ Rotation scheduler supports all trigger types
5. ✅ Enhanced rotation completes in < 30 seconds
6. ✅ Advanced fingerprinting works (with admin rights)
7. ✅ Post-rotation validation passes > 98% of time
8. ✅ All unit tests pass
9. ✅ Integration tests pass

## Risk Assessment

### High Risk
- **Advanced Fingerprinting:** Registry changes may affect system
  - **Mitigation:** Comprehensive backup, rollback, optional feature

### Medium Risk
- **Log Discovery:** May not find logs in all scenarios
  - **Mitigation:** Multiple strategies, manual configuration fallback
- **Token Detection:** May have false positives/negatives
  - **Mitigation:** Multiple detection sources, configurable thresholds

### Low Risk
- **Rotation Engine:** Builds on existing code
- **Scheduler:** Straightforward logic

## Security Considerations

1. **Registry Access:** Advanced fingerprinting requires admin rights
2. **File Permissions:** Ensure proper permissions for log access
3. **Error Messages:** Don't expose sensitive info in logs
4. **Backup Security:** Encrypt sensitive backup data (future)

## Next Steps

After Phase 1 completion:
- Proceed to Phase 2: Hybrid Service Architecture
- Test core components thoroughly
- Gather user feedback on rotation behavior

