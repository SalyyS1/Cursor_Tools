# Phase 3: API Integration & Monitoring

**Date:** 2025-01-27  
**Status:** Pending  
**Priority:** High  
**Effort:** 2 weeks  
**Dependencies:** Phase 1, Phase 2

## Context Links

- **Parent Plan:** [plan.md](./plan.md)
- **Dependencies:** 
  - [Phase 1: Core Hybrid System](./phase-01-core-hybrid-system.md)
  - [Phase 2: Hybrid Service Architecture](./phase-02-hybrid-service-architecture.md)
- **Related Docs:**
  - [Research: Cursor Logs](../research/researcher-02-cursor-logs-api.md)

## Overview

Implement Opus 4.5 API monitoring, rate limit detection, and API health dashboard for unlimited access goal.

## Key Insights

1. **API Monitoring:** Passive (log parsing) + Active (test calls) approach
2. **Rate Limit Detection:** Multiple signals (429, 403, usage patterns)
3. **Dashboard:** Real-time status display for user awareness
4. **Integration:** Works with rotation scheduler to trigger rotations

## Requirements

### Functional Requirements
1. Opus 4.5 API health monitoring
2. Rate limit detection from logs
3. Rate limit detection from API responses
4. API usage tracking
5. API health dashboard in GUI
6. Auto-rotation on rate limit detection

### Non-Functional Requirements
1. Rate limit detection accuracy > 90%
2. API monitoring overhead < 5% CPU
3. Dashboard updates every 30 seconds
4. Historical data storage (30 days)

## Architecture

### Component Structure

```
core/
└── api_monitor.py            # Enhanced from Phase 1

gui/
└── api_dashboard.py          # API health dashboard

utils/
└── api_history.py            # API usage history
```

### Data Flow

```
API Monitor → Rate Limit Detection → Rotation Scheduler
     ↓
API Dashboard (GUI)
     ↓
API History (Storage)
```

## Related Code Files

### Files to Enhance
- `core/api_monitor.py` - Enhance from Phase 1
- `gui_main.py` - Add API dashboard tab

### Files to Create
- `gui/api_dashboard.py` - API dashboard widget
- `utils/api_history.py` - API usage history

## Implementation Steps

### Step 1: Enhanced API Monitor (3 days)
1. Enhance `core/api_monitor.py` from Phase 1
2. Add active API health checking
3. Implement rate limit header parsing
4. Add API usage pattern tracking
5. Implement rate limit prediction
6. Add API response caching
7. Write enhanced tests

### Step 2: API History Tracking (2 days)
1. Create `utils/api_history.py`
2. Implement API call logging
3. Implement usage statistics
4. Add historical data storage (JSON/SQLite)
5. Implement data retention (30 days)
6. Add export functionality
7. Write history tests

### Step 3: API Dashboard Widget (3 days)
1. Create `gui/api_dashboard.py`
2. Design dashboard layout
3. Implement real-time status display
4. Add rate limit warnings
5. Add usage statistics display
6. Add historical charts (optional)
7. Integrate with gui_main.py
8. Write GUI tests

### Step 4: Integration with Rotation (2 days)
1. Integrate API monitor with rotation scheduler
2. Add rate limit trigger to scheduler
3. Test auto-rotation on rate limit
4. Add rotation history tracking
5. Update notifications for API events
6. Write integration tests

### Step 5: Testing & Polish (2 days)
1. End-to-end API monitoring testing
2. Rate limit detection accuracy testing
3. Dashboard performance testing
4. User experience testing
5. Documentation
6. Bug fixes

## Todo List

- [ ] Enhance core/api_monitor.py
- [ ] Create utils/api_history.py
- [ ] Create gui/api_dashboard.py
- [ ] Integrate dashboard with gui_main.py
- [ ] Integrate API monitor with rotation scheduler
- [ ] Add rate limit trigger
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Write GUI tests
- [ ] Update documentation

## Success Criteria

1. ✅ API health monitoring works accurately
2. ✅ Rate limit detection accuracy > 90%
3. ✅ Auto-rotation triggers on rate limit
4. ✅ API dashboard displays real-time status
5. ✅ API history tracks usage correctly
6. ✅ Monitoring overhead < 5% CPU
7. ✅ All tests pass

## Risk Assessment

### High Risk
- **API Detection:** May have false positives/negatives
  - **Mitigation:** Multiple detection signals, configurable thresholds

### Medium Risk
- **API Changes:** Cursor may change API structure
  - **Mitigation:** Version detection, adaptive parsing
- **Dashboard Performance:** May slow GUI
  - **Mitigation:** Efficient updates, optional charts

### Low Risk
- **History Storage:** Simple JSON/SQLite storage
- **Integration:** Builds on existing components

## Security Considerations

1. **API Calls:** Don't expose API keys in logs
2. **History Data:** Secure storage, no sensitive info
3. **Dashboard:** Don't display sensitive data

## Next Steps

After Phase 3 completion:
- Proceed to Phase 4: Advanced Features & Polish
- Test API monitoring accuracy
- Gather user feedback on dashboard

