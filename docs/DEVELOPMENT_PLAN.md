# LewtNanny Development Plan

A comprehensive 10-phase development plan for building the LootNanny application with all specified features.

---

## Phase 1: Foundation and Core Infrastructure

**Duration:** 2-3 days  
**Goal:** Establish the base application structure, database schema, and core data models.

### Phase 1 Todo List

- [ ] **Create core data models**
  - [ ] Session model (id, start_time, end_time, activity_type, total_cost, total_return, globals, hofs)
  - [ ] Run model (id, session_id, notes, start_time, end_time, spend, enhancers, extra_spend)
  - [ ] LootItem model (id, run_id, item_name, count, value, markup, total_value)
  - [ ] SkillGain model (id, session_id, skill_name, value, procs, proc_percentage)
  - [ ] WeaponLoadout model (id, name, weapon, amplifier, scope, sight_1, sight_2, ammo_burn, tool_decay)
  - [ ] TwitchConfig model (id, oauth_token, bot_name, channel, command_prefix, enabled_commands)
  - [ ] ScreenshotConfig model (id, enabled, directory, delay_ms, threshold_ped)
  - [ ] ActiveLoadout model (id, selected_loadout_id, ammo_burn, tool_decay)

- [ ] **Design database schema**
  - [ ] Create SQLite schema with proper foreign keys
  - [ ] Create indexes for frequently queried fields
  - [ ] Write database initialization script
  - [ ] Create migration scripts for future schema changes

- [ ] **Set up project structure**
  - [ ] Organize directory structure (src/ui, src/services, src/models, src/core)
  - [ ] Configure pytest and test infrastructure
  - [ ] Set up linting (ruff or flake8)
  - [ ] Configure type checking (mypy)

- [ ] **Create base UI framework**
  - [ ] Implement TabbedMainWindow class with custom tab bar
  - [ ] Create persistent bottom control bar
  - [ ] Set up tab switching logic
  - [ ] Implement basic theme support (dark/light)
  - [ ] Create base widget classes for consistent styling

---

## Phase 2: Loot Tab Implementation

**Duration:** 3-4 days  
**Goal:** Complete the Loot tab with summary section, run log table, and item breakdown table.

### Phase 2 Todo List

- [ ] **Implement Summary Section**
  - [ ] Create 6-label summary display (Creatures Looted, Total Cost, Total Return, % Return, Globals, HOFs)
  - [ ] Implement calculation logic for each metric
  - [ ] Add real-time update mechanism when loot events occur
  - [ ] Style with consistent dark theme

- [ ] **Implement Run Log Table**
  - [ ] Create QTableWidget with 7 columns (#, Notes, Start Time, End Time, Spend, Enhancers, Extra Spend)
  - [ ] Implement data loading from database
  - [ ] Add sorting functionality (click column headers)
  - [ ] Implement row selection and detail viewing
  - [ ] Add horizontal scroll for long notes
  - [ ] Style with alternating row colors

- [ ] **Implement Item Breakdown Table**
  - [ ] Create QTableWidget with 5 columns (Item Name, Count, Value, Markup, Total Value)
  - [ ] Link to run log selection (shows items for selected run)
  - [ ] Implement empty state when no run selected
  - [ ] Add aggregate calculations for selected run

- [ ] **Implement data integration**
  - [ ] Connect to chat reader for real-time loot parsing
  - [ ] Create loot parsing service to extract items from chat messages
  - [ ] Implement automatic TT value lookup (hardcoded database of item values)
  - [ ] Add markup percentage configuration

- [ ] **Add export functionality**
  - [ ] Export run log to CSV
  - [ ] Export item breakdown to CSV
  - [ ] Export all sessions to JSON

---

## Phase 3: Analysis Tab Implementation

**Duration:** 2-3 days  
**Goal:** Implement chart visualization for return tracking and efficiency analysis.

### Phase 3 Todo List

- [ ] **Implement Chart Infrastructure**
  - [ ] Create ChartWidget base class using PyQtGraph or Matplotlib backend
  - [ ] Set up chart styling (colors, fonts, grid lines)
  - [ ] Implement responsive chart resizing
  - [ ] Add export chart as image functionality

- [ ] **Implement Run TT Return (%) Chart**
  - [ ] Create line/scatter plot for return percentage over runs
  - [ ] X-axis: Run number or timestamp
  - [ ] Y-axis: Return percentage (0% to 200%+ scale)
  - [ ] Add trend line overlay
  - [ ] Add reference line at 100% (break-even)
  - [ ] Implement data point tooltips

- [ ] **Implement Cost to Kill vs Return Chart**
  - [ ] Create scatter plot comparing efficiency
  - [ ] X-axis: Cost per kill (PED)
  - [ ] Y-axis: Return per kill (PED)
  - [ ] Add diagonal break-even line
  - [ ] Color-code points by activity type
  - [ ] Add efficiency zones (profitable/unprofitable)

- [ ] **Implement chart controls**
  - [ ] Date range selector
  - [ ] Activity type filter (hunting, mining, crafting)
  - [ ] Run count limit slider
  - [ ] Refresh/reset button

- [ ] **Add statistical overlays**
  - [ ] Average return line
  - [ ] Standard deviation bands
  - [ ] Best/worst run markers

---

## Phase 4: Skills Tab Implementation

**Duration:** 2 days  
**Goal:** Implement skill gain tracking and analysis.

### Phase 4 Todo List

- [ ] **Implement Skills Summary Field**
  - [ ] Create "Total Skill Gain" label and value display
  - [ ] Calculate aggregate skill gains across all sessions
  - [ ] Format with appropriate decimal places

- [ ] **Implement Skills Table**
  - [ ] Create QTableWidget with 5 columns (#, Skill Name, Value, Procs, Proc %)
  - [ ] Implement sorting by any column
  - [ ] Add filtering by skill category (combat, crafting, mining)
  - [ ] Implement search/filter functionality

- [ ] **Implement skill tracking logic**
  - [ ] Create skill parsing from chat messages
  - [ ] Implement proc counting logic
  - [ ] Calculate proc percentage (procs / total actions)
  - [ ] Aggregate skills across sessions

- [ ] **Add skill analysis features**
  - [ ] Skill gain rate per hour
  - [ ] Top skills gained in session
  - [ ] Skill efficiency rating
  - [ ] Export skills data

---

## Phase 5: Twitch Bot Integration

**Duration:** 5-6 days  
**Goal:** Implement comprehensive Twitch bot with command system and auto-announcements.

### Phase 5 Todo List

- [ ] **Implement OAuth and Connection Management**
  - [ ] Create OAuth token input field
  - [ ] Implement token validation
  - [ ] Build IRC connection handler
  - [ ] Implement reconnection logic (exponential backoff)
  - [ ] Add connection status indicator
  - [ ] Implement message rate limiting (Twitch 20msg/30sec)

- [ ] **Implement Command System**
  - [ ] Create command registry structure
  - [ ] Build command prefix handling (!)
  - [ ] Implement command parser
  - [ ] Create command dispatcher

- [ ] **Implement Core Commands**
  - [ ] `!info` - Bot status and connection info
  - [ ] `!commands` - List available commands
  - [ ] `!toploots` - Top 5 looted items in session
  - [ ] `!allreturns` - Complete return statistics

- [ ] **Implement Advanced Commands**
  - [ ] `!stats` - Real-time PED return %, globals/HOFs count
  - [ ] `!loadout` - Display active weapon/ammo/decay
  - [ ] `!bestrun` - Best run statistics
  - [ ] `!worstrun` - Worst run statistics
  - [ ] `!skills` - Skill gain summary
  - [ ] `!top` - Viewer leaderboard (optional implementation)
  - [ ] `!rank` - User's position on leaderboard

- [ ] **Implement Auto-Announcements**
  - [ ] Global detection and chat announcement
  - [ ] Hall of Fame (HOF) detection and announcement
  - [ ] Milestone announcements (100th kill, 100 PED return, etc.)
  - [ ] Configurable announcement templates

- [ ] **Implement Command Configuration UI**
  - [ ] Enable/disable checkboxes for each command
  - [ ] Cooldown configuration per command
  - [ ] Custom response text builder
  - [ ] Command permission levels (mod/vip/everyone)

- [ ] **Implement Testing Tools**
  - [ ] "Test Command" button for each command
  - [ ] Command log display
  - [ ] Connection test button
  - [ ] Message preview

- [ ] **Implement Whisper Support (Optional)**
  - [ ] Whisper reception handler
  - [ ] Private stat commands via DM
  - [ ] Whisper rate limiting

---

## Phase 6: Config Tab Implementation

**Duration:** 3-4 days  
**Goal:** Complete Config tab with all application settings.

### Phase 6 Todo List

- [ ] **Implement Chat Location Section**
  - [ ] Chat log file path input field
  - [ ] "Find File" browse button
  - [ ] Path validation
  - [ ] Default path suggestion

- [ ] **Implement Character Name Section**
  - [ ] Character name input field (blank by default)
  - [ ] Save to config
  - [ ] Use in chat parsing for personalization

- [ ] **Implement Weapons Management Section**
  - [ ] Create Weapons table (Name, Amp, Scope, Sight 1, Sight 2)
  - [ ] Add "Add Weapon Loadout" button
  - [ ] Add "Create Weapon" button
  - [ ] Implement CRUD operations for loadouts
  - [ ] Row number column (auto-generated)
  - [ ] Scrollable table with placeholder entries (empty on first start)

- [ ] **Implement Active Loadout Section**
  - [ ] "Active Loadout" dropdown (blank by default)
  - [ ] "Ammo Burn" input field (editable)
  - [ ] "Tool Decay" input field (editable)
  - [ ] Save active loadout selection

- [ ] **Implement Screenshot Settings Section**
  - [ ] "Take Screenshot On global/hof" checkbox
  - [ ] "Screenshot Directory" input field with browse
  - [ ] "Screenshot Delay (ms)" input field
  - [ ] "Screenshot Threshold (PED)" input field
  - [ ] Save/enable screenshot functionality

- [ ] **Implement Streamer Window Layout**
  - [ ] Remove JSON editor complexity
  - [ ] Add simple layout preset selector
  - [ ] Preset: Compact, Detailed, Minimal
  - [ ] Add basic customization options

- [ ] **Save/Load Configuration**
  - [ ] Implement config persistence
  - [ ] Add "Reset to Defaults" button
  - [ ] Add config export/import

---

## Phase 7: Combat and Crafting Tabs

**Duration:** 3-4 days  
**Goal:** Implement Combat and Crafting tabs with basic functionality.

### Phase 7 Todo List

- [ ] **Implement Combat Tab**
  - [ ] Create combat statistics summary
  - [ ] Implement damage dealt tracking
  - [ ] Implement damage received tracking
  - [ ] Create kills/deaths table
  - [ ] Add enemy type breakdown
  - [ ] Implement auto-attack detection
  - [ ] Add combat efficiency metrics

- [ ] **Implement Crafting Tab**
  - [ ] Create crafting summary section
  - [ ] Implement material tracking
  - [ ] Create crafting log table
  - [ ] Add success/failure rates
  - [ ] Implement blueprint tracking
  - [ ] Add resource efficiency analysis
  - [ ] Create material cost calculator

- [ ] **Implement chat parsing for new events**
  - [ ] Combat message parsing
  - [ ] Crafting message parsing
  - [ ] Enemy detection
  - [ ] Material extraction

- [ ] **Add tab-specific charts**
  - [ ] Combat: Damage over time
  - [ ] Crafting: Success rate over time

---

## Phase 8: Streamer UI Tab

**Duration:** 2-3 days  
**Goal:** Implement simplified display suitable for live streaming.

### Phase 8 Todo List

- [ ] **Design Streamer-Friendly Layout**
  - [ ] Create large, readable metrics display
  - [ ] Use high-contrast colors
  - [ ] Add simple background option (green screen ready)
  - [ ] Remove cluttered interface elements

- [ ] **Implement Key Metrics Display**
  - [ ] Large TT Return percentage
  - [ ] Current session PED profit/loss
  - [ ] Global/HOF count
  - [ ] Active weapon display
  - [ ] Session timer

- [ ] **Implement Recent Activity Ticker**
  - [ ] Auto-scrolling loot feed
  - [ ] Recent globals/HOFs highlight
  - [ ] Skill gain notifications

- [ ] **Add Streamer Controls**
  - [ ] Quick session start/stop
  - [ ] Pause/resume tracking
  - [ ] Emergency hide controls

- [ ] **Add OBS Integration**
  - [ ] Window transparency option
  - [ ] Always on top toggle
  - [ ] Borderless mode
  - [ ] Profile management

---

## Phase 9: Testing and Polish

**Duration:** 4-5 days  
**Goal:** Comprehensive testing, bug fixes, and UI polish.

### Phase 9 Todo List

- [ ] **Implement Unit Tests**
  - [ ] Test all data models
  - [ ] Test parsing services
  - [ ] Test calculation logic
  - [ ] Test database operations
  - [ ] Test command handlers

- [ ] **Implement Integration Tests**
  - [ ] Test full data flow (chat -> parse -> store -> display)
  - [ ] Test tab switching
  - [ ] Test configuration save/load
  - [ ] Test session lifecycle

- [ ] **Perform UI Testing**
  - [ ] Test on multiple window sizes
  - [ ] Test theme switching
  - [ ] Test scroll behavior
  - [ ] Test table sorting/filtering

- [ ] **Fix Bugs and Issues**
  - [ ] Address all pytest failures
  - [ ] Fix any linting errors
  - [ ] Resolve type checking issues
  - [ ] Fix memory leaks
  - [ ] Optimize performance

- [ ] **Polish UI/UX**
  - [ ] Add loading indicators
  - [ ] Add tooltips
  - [ ] Implement keyboard shortcuts
  - [ ] Add status bar messages
  - [ ] Polish button hover states
  - [ ] Improve empty state messages

---

## Phase 10: Documentation and Release Preparation

**Duration:** 2-3 days  
**Goal:** Complete documentation and prepare for initial release.

### Phase 10 Todo List

- [ ] **Write User Documentation**
  - [ ] Create quick start guide
  - [ ] Document all features
  - [ ] Add screenshot annotations
  - [ ] Write troubleshooting section

- [ ] **Write Technical Documentation**
  - [ ] Document architecture
  - [ ] Document data models
  - [ ] Document API (if applicable)
  - [ ] Add contribution guidelines

- [ ] **Prepare Release**
  - [ ] Create version numbering scheme
  - [ ] Update version in application
  - [ ] Create release notes
  - [ ] Set up CI/CD pipeline
  - [ ] Create installation instructions

- [ ] **Final Testing**
  - [ ] End-to-end testing
  - [ ] Cross-platform testing (Windows)
  - [ ] Performance testing
  - [ ] Security review

---

## Appendix A: Development Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| Phase 1 | 2-3 days | Core infrastructure, database, base UI |
| Phase 2 | 3-4 days | Complete Loot tab |
| Phase 3 | 2-3 days | Analysis charts |
| Phase 4 | 2 days | Skills tracking |
| Phase 5 | 5-6 days | Twitch bot integration |
| Phase 6 | 3-4 days | Config tab |
| Phase 7 | 3-4 days | Combat and Crafting tabs |
| Phase 8 | 2-3 days | Streamer UI |
| Phase 9 | 4-5 days | Testing and polish |
| Phase 10 | 2-3 days | Documentation and release |

**Total Estimated Duration:** 28-38 days

---

## Appendix B: File Structure

```
leotnanny/
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   └── app_config.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── models.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── chat_reader.py
│   │   ├── config_manager.py
│   │   ├── loadout_service.py
│   │   ├── weapon_service.py
│   │   └── twitch_bot.py
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window_tabbed.py
│   │   ├── overlay.py
│   │   ├── settings_dialog.py
│   │   └── components/
│   │       ├── __init__.py
│   │       ├── charts.py
│   │       ├── weapon_selector.py
│   │       └── streamer_widget.py
│   └── utils/
│       ├── __init__.py
│       └── logger.py
├── tests/
│   ├── __init__.py
│   ├── test_core.py
│   ├── test_models.py
│   ├── test_services.py
│   └── test_ui.py
├── data/
│   └── leotnanny.db
├── themes/
│   ├── dark.qss
│   └── light.qss
├── docs/
├── scripts/
├── main.py
├── requirements.txt
├── pytest.ini
└── README.md
```

---

## Appendix C: Database Schema Overview

```sql
-- Sessions table
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time TEXT NOT NULL,
    end_time TEXT,
    activity_type TEXT NOT NULL,
    total_cost REAL DEFAULT 0,
    total_return REAL DEFAULT 0,
    globals INTEGER DEFAULT 0,
    hofs INTEGER DEFAULT 0,
    creatures_looted INTEGER DEFAULT 0,
    total_skill_gain REAL DEFAULT 0,
    notes TEXT
);

-- Runs table (child of sessions)
CREATE TABLE runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT,
    notes TEXT,
    spend REAL DEFAULT 0,
    enhancers REAL DEFAULT 0,
    extra_spend REAL DEFAULT 0,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Loot Items table
CREATE TABLE loot_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    item_name TEXT NOT NULL,
    count INTEGER DEFAULT 1,
    value REAL DEFAULT 0,
    markup REAL DEFAULT 0,
    total_value REAL DEFAULT 0,
    FOREIGN KEY (run_id) REFERENCES runs(id)
);

-- Skill Gains table
CREATE TABLE skill_gains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    skill_name TEXT NOT NULL,
    value REAL DEFAULT 0,
    procs INTEGER DEFAULT 0,
    proc_percentage REAL DEFAULT 0,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Weapon Loadouts table
CREATE TABLE loadouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    weapon TEXT NOT NULL,
    amplifier TEXT,
    scope TEXT,
    sight_1 TEXT,
    sight_2 TEXT,
    damage_enh INTEGER DEFAULT 0,
    accuracy_enh INTEGER DEFAULT 0,
    economy_enh INTEGER DEFAULT 0,
    created_at TEXT,
    updated_at TEXT
);

-- Active Loadout table
CREATE TABLE active_loadout (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    loadout_id INTEGER,
    ammo_burn REAL DEFAULT 0,
    tool_decay REAL DEFAULT 0,
    FOREIGN KEY (loadout_id) REFERENCES loadouts(id)
);

-- Twitch Configuration table
CREATE TABLE twitch_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    oauth_token TEXT,
    bot_name TEXT,
    channel TEXT,
    command_prefix TEXT DEFAULT '!',
    cmd_info INTEGER DEFAULT 1,
    cmd_commands INTEGER DEFAULT 1,
    cmd_toploots INTEGER DEFAULT 1,
    cmd_allreturns INTEGER DEFAULT 1,
    cmd_stats INTEGER DEFAULT 0,
    cmd_loadout INTEGER DEFAULT 0,
    cmd_bestrun INTEGER DEFAULT 0,
    cmd_worstrun INTEGER DEFAULT 0,
    cmd_skills INTEGER DEFAULT 0,
    announce_global INTEGER DEFAULT 1,
    announce_hof INTEGER DEFAULT 1,
    cooldown_info INTEGER DEFAULT 5,
    cooldown_commands INTEGER DEFAULT 10
);

-- Screenshot Configuration table
CREATE TABLE screenshot_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    enabled INTEGER DEFAULT 0,
    directory TEXT,
    delay_ms INTEGER DEFAULT 500,
    threshold_ped REAL DEFAULT 0
);

-- Indexes for performance
CREATE INDEX idx_sessions_start ON sessions(start_time);
CREATE INDEX idx_sessions_activity ON sessions(activity_type);
CREATE INDEX idx_runs_session ON runs(session_id);
CREATE INDEX idx_loot_items_run ON loot_items(run_id);
CREATE INDEX idx_skill_gains_session ON skill_gains(session_id);
```

---

## Appendix D: Chat Message Parsing Patterns

### Loot Messages
```
[Loot] (Creature) dropped: Item Name [Value: X PED]
[Global] (Creature) dropped: Global Item [Value: X PED]
[HOF] (Creature) dropped: Huge Item [Value: X PED]
```

### Skill Messages
```
[Skill] Skill Name increased by X.YY
[Skill] Skill Name reached level X
```

### Combat Messages
```
[Combat] You killed Creature with X damage
[Combat] Creature hit you for Y damage
```

### Crafting Messages
```
[Craft] Successfully crafted Item Name
[Craft] Failed to craft Item Name
```

---

*Document Version: 1.0*  
*Created: January 21, 2026*  
*Last Updated: January 21, 2026*
