# LewtNanny

A comprehensive loot tracking and financial analytics application for Entropia Universe players.

## Features

- **Real-time Chat Log Monitoring**: Parse game events as they happen
- **Financial Analytics**: Track ROI, costs, and profitability
- **Weapon & Crafting Database**: 14,000+ items with detailed stats
- **Session Management**: Organize tracking by hunting/crafting/mining sessions
- **Data Export**: Analyze your gameplay patterns over time

## Quick Start

### MVP Version (No Dependencies)
```bash
python main_mvp.py
```

### Full Version (Requires Dependencies)
```bash
pip install -r requirements.txt
python main.py
```

## Project Structure

```
LewtNanny/
├── main.py              # Full application entry point
├── main_mvp.py          # MVP version (no external deps)
├── requirements.txt     # Python dependencies
├── cli.py               # CLI interface
├── cli_commands.py      # CLI commands
├── weapon_selector.py   # Weapon selection UI
├── overlay.py           # In-game overlay
├── weapons.json         # Weapon database (290KB)
├── crafting.json        # Crafting blueprints (920KB)
├── src/                 # Source code
│   ├── core/            # Core functionality
│   ├── models/          # Data models
│   ├── services/        # Business logic
│   ├── ui/              # User interface
│   └── utils/           # Utilities
├── config/              # Configuration files
├── data/                # Runtime data storage
├── themes/              # UI themes
├── tools/               # Utility scripts
└── tests/               # Test suite
```

## Running Tests

```bash
pytest tests/
```

## License

MIT License - see LICENSE file for details.
