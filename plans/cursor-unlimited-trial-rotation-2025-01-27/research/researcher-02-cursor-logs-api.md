# Research: Cursor Log Parsing & API Detection

**Researcher:** AI Agent  
**Date:** 2025-01-27  
**Topic:** Cursor log file locations and API response parsing

## Key Findings

### Cursor Log Locations (Windows)

1. **Standard Locations:**
   - `%APPDATA%\Cursor\logs\` - Main log directory
   - `%APPDATA%\Cursor\User\logs\` - User-specific logs
   - `%LOCALAPPDATA%\Cursor\logs\` - Local logs
   - `%APPDATA%\Cursor\logs\main.log` - Main process log
   - `%APPDATA%\Cursor\logs\renderer*.log` - Renderer logs
   - `%APPDATA%\Cursor\logs\extension-host*.log` - Extension host logs

2. **Log File Patterns:**
   - `main.log` - Main process, contains API calls
   - `renderer*.log` - UI process logs
   - `extension-host*.log` - Extension logs
   - `*.log` - All log files

### Log Discovery Strategy

1. **Multi-Path Search:**
   - Check standard locations first
   - Scan for Cursor process working directory
   - Query Windows registry for installation path
   - File system scan as fallback

2. **Process-Based Discovery:**
   - Find Cursor process via `psutil` or `tasklist`
   - Get process working directory
   - Search for logs in process directory

3. **Registry-Based Discovery:**
   - `HKEY_CURRENT_USER\Software\Cursor` - User settings
   - `HKEY_LOCAL_MACHINE\SOFTWARE\Cursor` - System settings
   - Extract installation path from registry

### API Response Detection

1. **Log Patterns to Detect:**
   - `401 Unauthorized` - Token expired
   - `403 Forbidden` - Rate limited or blocked
   - `429 Too Many Requests` - Rate limit hit
   - `"token expired"` - Token expiration message
   - `"rate limit"` - Rate limit message

2. **Parsing Strategy:**
   - Tail log files (read last N lines)
   - Parse JSON responses if available
   - Regex patterns for error messages
   - Timestamp correlation

3. **Storage.json Analysis:**
   - `cursorAuth/accessToken` - Access token
   - `cursorAuth/refreshToken` - Refresh token
   - `augmentcode.*` - AugmentCode tokens
   - Check token expiration timestamps if available

### State.vscdb Analysis

- SQLite database with ItemTable
- Keys containing `augment`, `token`, `auth`
- Subscription status records
- Trial expiration dates

### API Health Monitoring

1. **Active Monitoring:**
   - Make test API calls to Cursor backend
   - Check response codes
   - Monitor rate limit headers

2. **Passive Monitoring:**
   - Parse log files for API responses
   - Detect error patterns
   - Track API usage patterns

### Implementation Approach

```python
class CursorLogDiscovery:
    def discover_logs(self) -> List[Path]:
        paths = []
        # Standard locations
        paths.extend(self._check_standard_paths())
        # Process-based
        paths.extend(self._check_process_paths())
        # Registry-based
        paths.extend(self._check_registry_paths())
        return self._validate_paths(paths)

class TokenExpirationMonitor:
    def check_token_status(self) -> Dict:
        # Check storage.json
        # Check state.vscdb
        # Parse logs for errors
        return {"expired": bool, "reason": str}

class APIMonitor:
    def detect_rate_limit(self) -> bool:
        # Parse logs for 429/403
        # Check API health
        return bool
```

## Implementation Considerations

1. **Log File Access:** May be locked by Cursor process
2. **Log Rotation:** Cursor may rotate logs, need to handle multiple files
3. **Performance:** Tail large log files efficiently
4. **Encoding:** Handle UTF-8, UTF-16, BOM issues
5. **Real-time Monitoring:** Use file watchers or polling

## References

- VSCode log structure (Cursor based on VSCode)
- Windows log file best practices
- SQLite database structure

## Unresolved Questions

- Exact log format for Cursor API responses?
- Where does Cursor store trial expiration info?
- How to detect rate limits accurately?

