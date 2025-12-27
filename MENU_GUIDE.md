# Menu Guide - AugmentCode Unlimited

## Quick Start

### Using run.bat (Interactive Menu)

1. **Double-click `run.bat`** to open the interactive menu
2. Choose from the following options:

#### Main Menu Options

- **[1] Launch GUI** - Opens the graphical user interface
- **[2] Quick Rotation** - Performs a quick rotation immediately
- **[3] Check Status** - Checks token and API status
- **[4] Service Management** - Manage Windows service
  - [a] Start Service
  - [b] Stop Service
  - [c] Service Status
  - [d] Install Service (requires admin)
  - [e] Uninstall Service (requires admin)
- **[5] View Rotation History** - View recent rotation events
- **[6] API Dashboard** - View API health and rate limit status
- **[7] Configuration** - Opens configuration directory
- **[0] Exit** - Exit the menu

### Using GUI (gui_main.py)

#### Menu Bar

**File Menu:**
- **New Rotation** (Ctrl+R) - Start a new rotation
- **Open History** - Switch to Rotation History tab
- **Export Data** - Export rotation history to JSON/CSV
- **Settings** - Open settings dialog
- **Exit** (Ctrl+Q) - Exit application

**Tools Menu:**
- **Quick Rotation** (Ctrl+Shift+R) - Quick rotation
- **Check Status** - Refresh and check system status
- **Service Management** - Manage Windows service
- **API Monitor** - Switch to API Dashboard tab

**View Menu:**
- **Main (Cleaning)** (Ctrl+1) - Main cleaning interface
- **Trial Dashboard** (Ctrl+2) - Trial status dashboard
- **Control Panel** (Ctrl+3) - Automation control panel
- **Rotation History** (Ctrl+4) - Rotation history view
- **API Dashboard** (Ctrl+5) - API health dashboard
- **Log Viewer** - View application logs

**Help Menu:**
- **Documentation** - View documentation
- **Keyboard Shortcuts** - View keyboard shortcuts
- **About** - About dialog

#### Tabs

1. **Main (Cleaning)** - Original cleaning interface
2. **Trial Dashboard** - Real-time trial status, account info
3. **Control Panel** - Automation settings, manual rotation
4. **Rotation History** - Past rotation events and statistics
5. **API Dashboard** - API health, rate limits, usage patterns

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+R | New Rotation |
| Ctrl+Shift+R | Quick Rotation |
| Ctrl+Q | Exit |
| Ctrl+1 | Main Tab |
| Ctrl+2 | Trial Dashboard |
| Ctrl+3 | Control Panel |
| Ctrl+4 | Rotation History |
| Ctrl+5 | API Dashboard |

## Features

### Interactive Menu (run.bat)

- **User-friendly**: Clear menu options with descriptions
- **Quick Actions**: Common operations accessible without GUI
- **Service Management**: Full service control from menu
- **Status Checking**: Quick status checks without opening GUI

### GUI Menu Bar

- **Standard Menu Bar**: File, Tools, View, Help menus
- **Keyboard Shortcuts**: All major actions have shortcuts
- **Tab Navigation**: Easy switching between views
- **Context Menus**: Right-click support (where applicable)

### Tab Organization

- **Main Tab**: Original cleaning interface (preserved)
- **Trial Dashboard**: Real-time monitoring
- **Control Panel**: Automation configuration
- **Rotation History**: Historical data and analytics
- **API Dashboard**: API health monitoring

## Tips

1. **Use run.bat** for quick operations without opening GUI
2. **Use keyboard shortcuts** for faster navigation
3. **Check Trial Dashboard** regularly to monitor status
4. **Use Control Panel** to configure automation
5. **View Rotation History** to track rotation events

## Troubleshooting

### Menu Issues

- **run.bat not working**: Ensure Python is installed and in PATH
- **Service menu errors**: Install pywin32 (`pip install pywin32`)
- **GUI not starting**: Check Python version (3.8+)

### Service Management

- **Service install fails**: Run as administrator
- **Service not starting**: Check Windows Event Viewer
- **Service status unknown**: Verify pywin32 installation

