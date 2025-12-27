# Phase 2: Interactive Menu (run.bat)

**Date:** 2025-01-27  
**Status:** Pending  
**Priority:** High  
**Effort:** 2 days  
**Dependencies:** None

## Context Links

- **Parent Plan:** [plan.md](./plan.md)
- **Related Docs:**
  - [Research: Menu UI/UX](./research/researcher-02-menu-ui-ux.md)

## Overview

Create run.bat with interactive menu before GUI launch. Provide quick actions, service management, and configuration options.

## Key Insights

1. **run.bat Missing:** Currently only start.bat exists
2. **Menu Before GUI:** Users want menu options before launching GUI
3. **Quick Actions:** Common actions should be accessible from menu
4. **Service Management:** Need service control from menu

## Requirements

### Functional Requirements
1. Create run.bat with interactive menu
2. Menu options before GUI launch
3. Quick actions (rotate, check status, etc.)
4. Service management (start/stop/status)
5. Configuration access
6. Direct GUI launch option

### Non-Functional Requirements
1. Menu should be user-friendly
2. Clear option descriptions
3. Fast menu response (< 1 second)
4. Error handling

## Architecture

### Menu Structure

```
run.bat Menu:
├── [1] Launch GUI
├── [2] Quick Rotation
├── [3] Check Status
├── [4] Service Management
│   ├── [a] Start Service
│   ├── [b] Stop Service
│   ├── [c] Service Status
│   └── [d] Install Service
├── [5] View Rotation History
├── [6] API Dashboard
├── [7] Configuration
└── [0] Exit
```

## Related Code Files

### Files to Create
- `run.bat` - Interactive menu script
- `scripts/menu_launcher.py` - Python menu launcher (optional)

### Files to Modify
- None (new feature)

## Implementation Steps

### Step 1: Create run.bat Menu (4 hours)
1. Create run.bat with menu display
2. Implement menu loop
3. Add option selection
4. Add input validation
5. Add error handling

### Step 2: Implement Quick Actions (4 hours)
1. Quick rotation function
2. Status check function
3. History view function
4. API dashboard function

### Step 3: Service Management Integration (4 hours)
1. Integrate service manager
2. Add service start/stop
3. Add service status
4. Add service install

### Step 4: Testing & Polish (4 hours)
1. Test all menu options
2. Improve error messages
3. Add help text
4. Polish menu display

## Todo List

- [ ] Create run.bat with menu
- [ ] Implement quick actions
- [ ] Integrate service management
- [ ] Add configuration access
- [ ] Test all menu options
- [ ] Add help/instructions
- [ ] Polish menu display

## Success Criteria

1. ✅ run.bat menu works correctly
2. ✅ All menu options functional
3. ✅ Quick actions work
4. ✅ Service management works
5. ✅ User-friendly interface

## Risk Assessment

### Low Risk
- **Menu Implementation:** Standard batch script
- **Integration:** Uses existing components

## Security Considerations

1. **Input Validation:** Validate all user inputs
2. **Service Operations:** Require admin for service ops

## Next Steps

After Phase 2 completion:
- Proceed to Phase 3: GUI Menu Bar & Navigation

