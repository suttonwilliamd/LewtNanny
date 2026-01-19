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
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## Project Structure

```
LewtNanny/
├── main.py              # Full application entry point
├── main_mvp.py          # MVP version (no external deps)
├── requirements.txt     # Python dependencies
├── Plan.md             # Detailed project plan
├── weapons.json        # Weapon database
├── crafting.json       # Crafting blueprints
├── src/
│   ├── core/           # Core functionality
│   ├── models/         # Data models
│   ├── services/       # Business logic
│   ├── ui/             # User interface
│   └── utils/          # Utilities
└── data/               # Runtime data storage
```

## Data Sources

The application uses JSON databases for:
- **Weapons**: Damage, decay, ammo consumption, eco stats
- **Crafting**: Blueprints, material requirements, costs
- **Sessions**: Tracking data and analytics

## Development Status

This is the MVP version featuring:
- ✅ Basic GUI with tabbed interface
- ✅ Weapon and crafting database loading
- ✅ Event simulation for testing
- ✅ Session management
- ✅ Configuration system

## Next Steps

- [ ] Real chat log parsing
- [ ] OCR integration for screenshot analysis
- [ ] Advanced financial calculations
- [ ] Twitch streaming integration
- [ ] Data visualization graphs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and feature requests, please use the GitHub issue tracker.