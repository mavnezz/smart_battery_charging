# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2024-02-04

### Added
- **GitHub Infrastructure**
  - GitHub Actions workflows for HACS validation, Hassfest, and CodeQL security scanning
  - Issue templates for bug reports and feature requests
  - Pull request template with checklist
  - Dependabot configuration for automatic dependency updates
  - Release validation workflow
- **Documentation**
  - Comprehensive configuration guide in `docs/configuration.md`
  - Complete sensor reference in `docs/sensors.md` with examples
  - Service documentation in `docs/services.md` with automation examples
  - CONTRIBUTING.md with development guidelines
  - Professional README with badges and screenshots
- **Development Setup**
  - DevContainer configuration for easy development
  - VS Code settings and recommended extensions
  - EditorConfig for consistent code formatting
- **Images**
  - Integration overview screenshot
  - Configuration dialog screenshot

### Changed
- Device model name from "Tibber Price Optimizer" to "Smart Battery Charging"
- Device info now displays "Version" instead of "Firmware"
- Enhanced README structure matching professional HACS integrations
- Updated hacs.json with domains, IoT class, and country support

### Fixed
- Added `configuration_url` to device info for direct GitHub access from Home Assistant UI
- Device information now correctly shows integration name

## [0.2.9] - 2024-02-04

### Added
- Profitability check: Now considers efficiency losses before charging/discharging
- New sensor attributes: `is_profitable`, `avg_charge_price`, `avg_discharge_price`, `required_spread`
- Integration icon

### Fixed
- OFF mode now correctly sets battery to Idle state instead of keeping previous state

### Changed
- Default `min_spread` increased to 30% to better account for round-trip losses
- Improved Zendure device detection logic

## [0.2.8] - 2024-01-28

### Added
- Integration icon for better visibility in Home Assistant UI

### Improved
- Enhanced Zendure device detection algorithm
- Better error handling for missing device entities

## [0.2.7] - 2024-01-20

### Added
- Operating mode dropdown: Off, Auto, Charge, Discharge
- Battery control via `min_soc` parameter instead of AC mode
- Better integration with Smart Meter Mode

### Changed
- Switched from AC mode control to min_soc control for better compatibility
- Improved battery state management

### Removed
- AC mode control (replaced by min_soc)

## [0.2.0] - 2024-01-10

### Added
- Initial HACS release
- Tibber integration for real-time and forecast prices
- Automatic price window calculation
- Zendure Solarflow 800 Pro support
- Configurable charging and discharging windows
- Multiple sensors for price monitoring
- Service calls for manual control

### Features
- Percentile-based price analysis
- Configurable time windows
- Real-time price monitoring
- Next window predictions
- Potential savings calculation

## [0.1.0] - 2023-12-15

### Added
- Initial development version
- Basic Tibber API integration
- Simple price-based battery control
