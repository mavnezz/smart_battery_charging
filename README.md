# Smart Battery Charging

A Home Assistant custom integration that optimizes battery charging and discharging based on dynamic electricity prices from Tibber.

## Features

- **Tibber Integration**: Fetches real-time and forecast electricity prices via Tibber GraphQL API
- **Price Analysis**: Identifies cheapest windows for charging and most expensive windows for discharging
- **Zendure Solarflow Support**: Controls Zendure Solarflow 800 Pro (and compatible devices)
- **Automatic Mode**: Automatically switches between charge/discharge/idle based on current prices
- **Configurable**: Adjustable percentiles, window counts, and efficiency settings

## Sensors

| Sensor | Description |
|--------|-------------|
| Current Price | Current electricity price |
| Average Price | Average price for today/tomorrow |
| Price Spread | Difference between min and max price (%) |
| Recommended State | charge, discharge, or idle |
| Cheapest Windows | Count and times of cheapest price windows |
| Expensive Windows | Count and times of most expensive windows |
| Next Cheap Window | Next upcoming cheap window |
| Next Expensive Window | Next upcoming expensive window |
| Potential Savings | Estimated savings per kWh |

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots menu and select "Custom repositories"
4. Add this repository URL and select "Integration" as category
5. Search for "Smart Battery Charging" and install it
6. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/smart_battery_charging` folder to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to Settings → Devices & Services → Add Integration
2. Search for "Smart Battery Charging"
3. Enter your Tibber API token (get it from https://developer.tibber.com/settings/access-token)
4. Select your home if you have multiple
5. Configure options:
   - Price resolution (hourly or 15-minute)
   - Number of charge/discharge windows
   - Price percentiles
   - Battery capacity and efficiency
   - Zendure device name (from entity IDs)

## Requirements

- Home Assistant 2024.1 or newer
- Tibber account with API access
- For battery control: [Zendure Home Assistant Integration](https://github.com/Zendure/Zendure-HA)

## Usage

### Auto Mode

Enable the "Auto Mode" switch to automatically control your battery:
- **Charges** during the cheapest price windows
- **Discharges** during the most expensive price windows
- **Idles** at other times

### Manual Control

Use the `smart_battery_charging.set_battery_state` service:

```yaml
service: smart_battery_charging.set_battery_state
data:
  state: charge  # or discharge, idle, off
  charge_power: 800  # optional, watts
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please open an issue or pull request.
