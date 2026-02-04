# Contributing to Smart Battery Charging

First off, thank you for considering contributing to Smart Battery Charging! 🎉

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

- Use the bug report template
- Use a clear and descriptive title
- Describe the exact steps to reproduce the problem
- Include your Home Assistant version and integration version
- Include relevant log output from Home Assistant

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- Use the feature request template
- Use a clear and descriptive title
- Provide a detailed description of the suggested enhancement
- Explain why this enhancement would be useful

### Pull Requests

1. Fork the repository and create your branch from `main`
2. Make your changes
3. Test your changes thoroughly
4. Update documentation if needed
5. Ensure your code follows the existing style
6. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Home Assistant (for testing)
- Git

### Setting Up Your Development Environment

1. Clone your fork:
```bash
git clone https://github.com/YOUR_USERNAME/smart_battery_charging.git
cd smart_battery_charging
```

2. Install in development mode:
```bash
# Create a symbolic link in your Home Assistant config directory
ln -s $(pwd)/custom_components/smart_battery_charging ~/.homeassistant/custom_components/
```

3. Restart Home Assistant

### Using DevContainer (Recommended)

This repository includes a DevContainer configuration for easy development:

1. Install Docker and VS Code with the Remote-Containers extension
2. Open the repository in VS Code
3. Click "Reopen in Container" when prompted
4. The container includes Home Assistant and all dependencies

## Code Style

- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and small
- Add comments for complex logic

## Testing

Before submitting a pull request:

1. Test your changes in a real Home Assistant environment
2. Verify that all existing functionality still works
3. Test edge cases and error conditions
4. Check Home Assistant logs for warnings or errors

## Commit Messages

- Use clear and meaningful commit messages
- Start with a verb in present tense (e.g., "Add", "Fix", "Update")
- Keep the first line under 50 characters
- Add detailed description if needed

Example:
```
Fix profitability calculation for edge cases

- Handle zero price scenarios
- Improve efficiency calculation accuracy
- Add logging for debugging
```

## Project Structure

```
smart_battery_charging/
├── custom_components/smart_battery_charging/
│   ├── __init__.py              # Integration setup
│   ├── config_flow.py           # Configuration flow
│   ├── coordinator.py           # Data coordinator
│   ├── tibber_api.py           # Tibber API client
│   ├── calculation_engine.py    # Price analysis
│   ├── battery_controller.py    # Battery control logic
│   ├── automation_handler.py    # Automation logic
│   ├── sensor.py               # Sensor entities
│   ├── select.py               # Select entities
│   ├── switch.py               # Switch entities
│   └── number.py               # Number entities
├── .github/                    # GitHub workflows and templates
└── docs/                       # Documentation
```

## Key Components

### coordinator.py
Handles data fetching and updates from Tibber API. Updates every 5 minutes.

### calculation_engine.py
Analyzes electricity prices and calculates optimal charging/discharging windows.

### battery_controller.py
Controls the Zendure battery system via min_soc parameter.

### automation_handler.py
Manages automatic mode switching based on price windows.

## Release Process

Maintainers will handle releases:

1. Update version in `manifest.json`
2. Update `CHANGELOG.md`
3. Create a new release on GitHub
4. GitHub Actions will validate the release

## Questions?

Feel free to open an issue with your question or reach out to the maintainers.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
