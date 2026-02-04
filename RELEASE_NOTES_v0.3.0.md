# Release v0.3.0 - Professional Repository Setup

## 🎉 Major Improvements

This release focuses on professionalizing the repository structure and making it a first-class HACS integration.

### ✨ New Features

- **GitHub Actions Workflows**
  - Automatic HACS validation on every commit
  - Hassfest validation for Home Assistant compatibility
  - CodeQL security scanning
  - Release version validation

- **Issue & PR Templates**
  - Structured bug report template
  - Feature request template
  - Pull request checklist
  - Community discussion links

- **DevContainer Support**
  - Full Home Assistant development environment
  - VS Code DevContainer configuration
  - Automatic setup for contributors

- **Comprehensive Documentation**
  - Detailed configuration guide (`docs/configuration.md`)
  - Complete sensor reference (`docs/sensors.md`)
  - Service call documentation with examples (`docs/services.md`)
  - Professional CONTRIBUTING.md guidelines
  - Full CHANGELOG.md history

### 🔧 Fixes

- **Device Information Improvements**
  - Fixed device model name from "Tibber Price Optimizer" to "Smart Battery Charging"
  - Added `configuration_url` for direct GitHub access from Home Assistant UI
  - Device info now shows "Version" instead of "Firmware"
  - Added "Visit" button linking to repository

### 📚 Documentation

- **Enhanced README**
  - Modern badges (GitHub Release, HACS, Activity)
  - Screenshots of integration and configuration
  - Links to detailed documentation
  - Support and community section
  - Professional structure matching top HACS integrations

- **New Documentation Files**
  - Configuration guide with all options explained
  - Sensor documentation with attributes and examples
  - Service documentation with automation examples
  - CHANGELOG with semantic versioning

### 🛠️ Development Experience

- **VS Code Integration**
  - Recommended extensions
  - Python formatting configuration
  - Home Assistant YAML support

- **Code Quality**
  - EditorConfig for consistent formatting
  - Git attributes for line endings
  - Dependabot for dependency updates

### 📦 Repository Structure

```
├── .github/              # GitHub workflows, templates & config
├── .devcontainer/        # Development container setup
├── .vscode/             # VS Code settings
├── custom_components/   # Integration code
├── docs/                # Detailed documentation
├── images/              # Screenshots
├── CHANGELOG.md         # Version history
├── CONTRIBUTING.md      # Contribution guidelines
├── LICENSE              # MIT license
└── README.md            # Main documentation
```

### 📸 Screenshots

This release includes screenshots showing:
- Integration overview with all sensors
- Configuration dialog with all options

### 🔄 Updated Metadata

- **hacs.json** enhanced with:
  - Domain definitions
  - IoT class specification
  - Country support (DE, NO, SE, NL)

## 🚀 Installation

### Via HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three-dot menu → "Custom repositories"
4. Add: `https://github.com/mavnezz/smart_battery_charging`
5. Category: "Integration"
6. Search for "Smart Battery Charging" and install
7. Restart Home Assistant

### Manual Installation

1. Copy `custom_components/smart_battery_charging` to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

## 📝 Full Changelog

See [CHANGELOG.md](CHANGELOG.md) for complete version history.

## 🙏 Contributors

This release brings the repository up to professional standards for the Home Assistant community.

**Author:** [@mavnezz](https://github.com/mavnezz)

---

**Note:** This is a repository structure update. All existing features from v0.2.9 remain functional:
- Profitability check with efficiency consideration
- Tibber price integration
- Zendure battery control
- Multiple operating modes
- Smart price window detection
