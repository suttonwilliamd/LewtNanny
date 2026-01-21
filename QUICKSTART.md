# LewtNanny - Entropia Universe Loot Tracker

## Quick Start Guide

### Installation
1. Install Python 3.11 or later
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `python main.py`

### Basic Usage
1. **Configure Chat Log**: Go to Config tab and set the path to your Entropia Universe chat log
2. **Start Monitoring**: Click "Start Monitoring" to begin tracking
3. **Start Session**: Click "Start Run" to begin a new session
4. **View Statistics**: Check the Loot, Analysis, and Skills tabs for detailed statistics

### Features

#### Loot Tracking
- Real-time loot parsing from chat log
- Summary statistics (creatures looted, cost, return, % return, globals, HOFs)
- Run log with detailed breakdown
- Item breakdown with TT values and markup

#### Analysis Charts
- TT Return (%) over time
- Cost vs Return scatter plot
- Statistics overlay (average, best, worst)

#### Skills Tracking
- Total skill gain display
- Detailed skills table with procs and proc %

#### Combat Tab
- Combat statistics tracking
- Kills/deaths tracking
- Damage dealt/received metrics

#### Crafting Tab
- Crafting success/failure tracking
- Blueprint management
- Success rate analysis

#### Twitch Bot
- IRC connection to Twitch chat
- Commands: !info, !commands, !toploots, !allreturns, !stats, !loadout, !bestrun, !skills
- Auto-announcements for globals and HOFs

#### Streamer UI
- Large, readable metrics display
- Session timer
- Recent activity ticker
- High-contrast design for streaming

#### Configuration
- Chat log path configuration
- Theme selection (dark/light)
- Database management (backup, reset)

### Configuration Files
- `data/leotnanny.db`: SQLite database storing all session data
- `themes/dark.qss`: Dark theme stylesheet
- `themes/light.qss`: Light theme stylesheet

### Support
For issues and feature requests, please report at the project repository.

---

*LewtNanny Version 1.0.0*
