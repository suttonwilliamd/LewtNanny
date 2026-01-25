# Changelog

All notable changes to LewtNanny will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- PayPal donation button in the application (links to hosted PayPal donation page)
- Enhanced README.md with comprehensive documentation and donation links

### Changed
- Improved UI/UX with modern themes and styling
- Updated donation functionality to open external PayPal page

### Fixed
- Various bugs and performance issues in the overlay system
- Improved database path handling and configuration

## [2024-01-24] - Major Release

### Added
- Real-time chat log monitoring for Entropia Universe
- Comprehensive financial analytics and ROI tracking
- Weapon & crafting database with 14,000+ items
- Session management for hunting/crafting/mining
- Interactive dashboard with visual charts
- Streamer overlay with real-time stats
- Theme support (dark and light themes)
- Data export functionality
- PyInstaller build system for standalone executable

### Changed
- Complete rewrite of the application architecture
- Migrated from simple scripts to modular PyQt6 application
- Enhanced data models and database structure
- Improved performance with async/await patterns

### Fixed
- Memory leaks in chat monitoring
- Data corruption issues in large sessions
- UI responsiveness during heavy data processing
- Configuration file handling bugs

## [2023-12-15] - Beta Release

### Added
- MVP version with basic chat parsing
- Simple weapon selection interface
- Basic financial calculations
- Session tracking functionality
- Initial database schema

### Changed
- Moved from tkinter to PyQt6 for better UI
- Implemented proper logging system
- Added configuration management

### Fixed
- Chat log file reading issues
- Weapon data import problems
- Basic UI layout bugs

## [2023-11-01] - Alpha Release

### Added
- Initial project structure
- Basic chat log parsing
- Simple weapon database
- MVP GUI interface
- Basic session tracking

### Known Issues
- Limited weapon data coverage
- Basic error handling
- Memory usage issues with large chat logs
- Limited configuration options

---

## Version History

### v1.0.0 (2024-01-24)
- First stable release with full feature set
- PayPal donation integration
- Complete documentation
- PyInstaller executable distribution

### v0.9.0 (2023-12-15)
- Beta release with core functionality
- Database integration
- Enhanced UI components

### v0.5.0 (2023-11-01)
- Alpha release with basic features
- Proof of concept implementation

---

## Upcoming Features

### Planned for Next Release
- [ ] Advanced loot analysis with market price integration
- [ ] Multi-language support
- [ ] Cloud sync for session data
- [ ] Mobile companion app
- [ ] API for third-party integrations

### Future Enhancements
- [ ] Machine learning for ROI predictions
- [ ] Social features and leaderboards
- [ ] Automated tax reporting
- [ ] Integration with Entropia Universe API (if available)

---

## Migration Guide

### From v0.9.x to v1.0.0
- No database schema changes
- Configuration format remains compatible
- All existing sessions and data preserved

### From v0.5.x to v0.9.0
- Database migration required for enhanced schema
- Configuration files may need manual updates
- See `tools/migrate_data.py` for automated migration

---

## Contributors

- [@suttonwilliamd](https://github.com/suttonwilliamd) - Creator and maintainer
- Entropia Universe community - Feedback and testing

---

## Support

For questions, bug reports, or feature requests:
- Create an issue on [GitHub](https://github.com/suttonwilliamd/LewtNanny/issues)
- Support development via [PayPal Donation](https://www.paypal.com/donate/?hosted_button_id=C8NM596JX8V8E)