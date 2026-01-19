# LewtNanny - Design Proposal

## Executive Summary

LewtNanny is a comprehensive loot tracking and financial analytics application designed specifically for Entropia Universe, a real-cash economy MMORPG. The application provides real-time monitoring, detailed financial analysis, and streaming integration to help players optimize their gameplay decisions and maximize their return on investment in the virtual economy.

## Problem Statement

Entropia Universe features a complex real-money economy where players invest actual currency (Project Entropia Dollars - PED) in activities like hunting, crafting, and mining. Players currently lack tools to:
- Track detailed financial returns in real-time
- Analyze long-term profitability trends
- Monitor equipment efficiency and degradation
- Share live statistics with streaming audiences
- Make data-driven decisions about equipment and activities

## Solution Overview

LewtNanny addresses these needs through a modular desktop application that:
- Monitors game chat logs for real-time event tracking
- Provides comprehensive financial analytics and ROI calculations
- Offers streaming integration with customizable overlays
- Maintains detailed historical databases for trend analysis
- Supports extensive customization and configuration options

## Technical Architecture

### Technology Stack

**Frontend:**
- **Python 3.x** - Primary development language
- **PyQt5** - Cross-platform GUI framework
- **pyqtgraph** - High-performance data visualization
- **PyAutoGUI** - Screen automation and capture

**Data Processing:**
- **pytesseract** - OCR for screenshot analysis
- **PIL/Pillow** - Image processing
- **JSON/YAML** - Configuration and data storage
- **Decimal** - Precise financial calculations

**Integration:**
- **twitchio** - Twitch streaming integration
- **File system watchers** - Real-time chat log monitoring

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
├─────────────────────────────────────────────────────────────┤
│  Tabbed Interface  │  Live Overlay  │  Configuration UI    │
├─────────────────────────────────────────────────────────────┤
│                   Business Logic Layer                      │
├─────────────────────────────────────────────────────────────┤
│ Combat Module  │ Crafting Module  │ Twitch Module  │ OCR   │
├─────────────────────────────────────────────────────────────┤
│                      Data Access Layer                      │
├─────────────────────────────────────────────────────────────┤
│ Chat Reader  │ Config Manager  │ Markup Store  │ Analytics│
├─────────────────────────────────────────────────────────────┤
│                    Storage Layer                            │
├─────────────────────────────────────────────────────────────┤
│ JSON Database │ Configuration Files │ Historical Data      │
└─────────────────────────────────────────────────────────────┘
```

## Core Features

### 1. Real-Time Combat Tracking

**Functionality:**
- Monitor game chat logs for combat events
- Track shots fired, damage dealt, critical hits
- Calculate Damage Per PED (DPP) efficiency
- Monitor weapon degradation and enhancer breakage

**Implementation:**
- Regex-based chat log parsing
- Real-time event processing with QTimer
- Weapon database integration for accurate calculations

### 2. Financial Analytics Engine

**Functionality:**
- Comprehensive ROI calculations
- Cost tracking (ammo, decay, enhancers)
- Profit/loss analysis per session and over time
- Support for TT values and market markup

**Implementation:**
- Decimal precision for all financial calculations
- Item database with 14,000+ entries
- Configurable markup system
- Historical data persistence and analysis

### 3. Loot Management System

**Functionality:**
- Automatic loot parsing from game messages
- Screenshot capture for significant events
- Global and HoF achievement tracking
- Item-by-item loot breakdown

**Implementation:**
- Pattern matching for loot messages
- PIL-based screenshot automation
- Event-driven capture triggers
- Database-driven item valuation

### 4. Crafting Analytics

**Functionality:**
- Blueprint tracking and cost analysis
- Resource cost calculations
- Success rate monitoring
- Profitability analysis per blueprint

**Implementation:**
- Crafting recipe database
- Real-time cost calculation engine
- Historical success rate tracking
- Break-even analysis tools

### 5. Streaming Integration

**Functionality:**
- Twitch bot for viewer interaction
- Customizable overlay displays
- Real-time statistics for viewers
- Chat command integration

**Implementation:**
- Twitch IRC bot integration
- Transparent overlay window
- Real-time data synchronization
- Configurable display elements

### 6. Configuration Management

**Functionality:**
- Weapon loadout management
- Custom item definitions
- Screenshot automation settings
- Theme customization

**Implementation:**
- JSON-based configuration system
- Migration support between versions
- Real-time configuration updates
- User preference persistence

## Data Architecture

### Database Schema

**Items Database (JSON):**
```json
{
  "weapons": {
    "weapon_id": {
      "name": "Weapon Name",
      "decay": 0.01,
      "ammo_burn": 5,
      "dps": 15.5,
      "eco": 3.1,
      "type": "ranged/melee"
    }
  },
  "resources": {
    "item_id": {
      "name": "Resource Name",
      "tt_value": 0.50,
      "category": "material"
    }
  }
}
```

**Session Data:**
```json
{
  "session_id": {
    "timestamp": "2024-01-01T12:00:00Z",
    "activity": "hunting/crafting",
    "costs": {
      "ammo": 100.50,
      "decay": 25.30,
      "enhancers": 5.00
    },
    "returns": {
      "tt_value": 130.00,
      "markup": 15.50
    },
    "events": [...]
  }
}
```

### Data Flow

1. **Input:** Chat log monitoring → OCR screenshots → User input
2. **Processing:** Event parsing → Database lookups → Calculations
3. **Storage:** Session data → Historical records → Configuration
4. **Output:** UI updates → Graphs → Overlay display → Exports

## User Interface Design

### Main Application Window

**Layout:**
- Tabbed interface for different modules
- Real-time statistics dashboard
- Historical data tables with sorting/filtering
- Interactive graphs and charts

**Key Views:**
- **Loot Tab:** Real-time loot feed with item details
- **Analysis Tab:** Financial graphs and ROI calculations
- **Combat Tab:** Weapon performance metrics
- **Skills Tab:** Skill gain tracking
- **Crafting Tab:** Blueprint analysis
- **Twitch Tab:** Streaming configuration
- **Config Tab:** Application settings

### Streaming Overlay

**Features:**
- Transparent background for in-game display
- Customizable widget layout
- Real-time statistics updates
- Brand/color customization

## Security Considerations

### Data Protection
- Local file storage only (no cloud transmission)
- Encrypted configuration files for sensitive data
- Secure OCR processing with local Tesseract

### Game Integration Safety
- Read-only chat log access
- No memory injection or game modification
- Respect for game ToS and anti-cheat policies

## Performance Requirements

### Real-Time Processing
- Chat log processing within 100ms
- UI refresh rate of 10Hz for responsive feel
- Background screenshot processing without UI blocking

### Data Handling
- Support for 100,000+ historical records
- Efficient database queries with indexing
- Memory usage under 500MB during normal operation

## Deployment Strategy

### Distribution
- Standalone executable using PyInstaller
- Automatic update mechanism
- Cross-platform support (Windows primary, Linux/Mac secondary)

### Installation
- Simple installer with dependency bundling
- Database initialization on first run
- Configuration wizard for new users

## Development Roadmap

### Phase 1: Core Functionality (Months 1-3)
- Basic chat log parsing and event tracking
- Simple loot tracking and cost calculation
- Basic UI with loot and analysis tabs
- Configuration system foundation

### Phase 2: Advanced Analytics (Months 4-6)
- Comprehensive weapon and item database
- Advanced financial calculations and graphs
- Historical data analysis and trends
- Crafting module implementation

### Phase 3: Integration & Automation (Months 7-9)
- Screenshot capture and OCR integration
- Twitch streaming integration
- Advanced automation features
- Performance optimization

### Phase 4: Polish & Enhancement (Months 10-12)
- UI/UX improvements and themes
- Advanced customization options
- Bug fixes and stability improvements
- Community feedback integration

## Success Metrics

### User Engagement
- Active user count and retention rates
- Session duration and frequency
- Feature usage analytics

### Technical Performance
- Application startup time < 5 seconds
- Real-time processing latency < 100ms
- Crash rate < 1% of sessions

### Community Impact
- User-reported ROI improvements
- Streaming integration adoption
- Community-driven feature requests

## Conclusion

LewtNanny represents a comprehensive solution for Entropia Universe players seeking to optimize their virtual economy participation. By combining real-time monitoring, sophisticated financial analytics, and streaming integration, the application addresses a significant gap in the market for gaming economy analytics tools.

The modular architecture ensures extensibility for future features while maintaining performance and reliability. The focus on user experience, data accuracy, and community integration positions LewtNanny for strong adoption and long-term success in the niche but dedicated Entropia Universe player base.