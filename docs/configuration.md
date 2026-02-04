# Configuration Guide

This guide explains all configuration options for Smart Battery Charging.

## Initial Setup

1. Navigate to **Settings → Devices & Services → Add Integration**
2. Search for "Smart Battery Charging"
3. Enter your Tibber API token
   - Get it from https://developer.tibber.com/settings/access-token
4. If you have multiple homes, select the one you want to use

## Configuration Options

After initial setup, click **Configure** on the integration to access these options:

### Zendure Device

**Type:** String
**Required:** Yes (for battery control)
**Example:** `solarflow_800_pro`

The name of your Zendure device. This is the prefix used in your entity IDs.

**How to find it:**
```
Entity: number.solarflow_800_pro_min_soc
Device name: ^^^^^^^^^^^^^^^^
```

Look for entities ending in `_min_soc` in Developer Tools → States.

### Price Resolution

**Type:** Select
**Default:** Stündlich (Hourly)
**Options:** Stündlich, 15-Minuten

- **Stündlich:** Analyze prices on an hourly basis (recommended for most users)
- **15-Minuten:** Analyze prices in 15-minute intervals (for more granular control)

### Number of Charging Windows

**Type:** Integer
**Default:** 6
**Range:** 1-24

Maximum number of hours identified as "cheap" for charging. The integration will select the cheapest N hours from the available price data.

**Example:**
- Value: 6
- Result: The 6 cheapest hours will be marked as charging windows

### Number of Discharging Windows

**Type:** Integer
**Default:** 3
**Range:** 1-24

Maximum number of hours identified as "expensive" for discharging.

**Example:**
- Value: 3
- Result: The 3 most expensive hours will be marked as discharging windows

### Cheap Percentile

**Type:** Integer
**Default:** 25
**Range:** 0-100
**Unit:** %

Defines which percentage of prices are considered "cheap".

**Examples:**
- 25%: Only prices in the bottom 25% are considered cheap
- 50%: Prices below median are considered cheap
- 10%: Only the very cheapest prices (bottom 10%)

### Expensive Percentile

**Type:** Integer
**Default:** 75
**Range:** 0-100
**Unit:** %

Defines which percentage of prices are considered "expensive".

**Examples:**
- 75%: Only prices in the top 25% are considered expensive
- 90%: Only the very highest prices (top 10%)
- 50%: Prices above median are considered expensive

### Minimum Spread

**Type:** Integer
**Default:** 30
**Range:** 0-100
**Unit:** %

Minimum price difference required between cheap and expensive periods before taking action.

**Formula:**
```
spread = ((max_price - min_price) / min_price) × 100%
```

**Why it matters:**
Due to battery efficiency losses (~85%), you need a minimum spread to make charging/discharging profitable. The default 30% ensures operations are economically viable.

**Examples:**
- Min price: 25¢, Max price: 35¢ → Spread: 40% ✓ (will charge/discharge)
- Min price: 26¢, Max price: 31¢ → Spread: 19% ✗ (stays idle)

### Battery Capacity

**Type:** Float
**Default:** 0.8
**Unit:** kWh

The usable capacity of your battery system.

**For Zendure Solarflow 800 Pro:**
- One AB1000: 0.8 kWh (default)
- Two AB1000: 1.6 kWh
- Three AB1000: 2.4 kWh

This value is used to calculate potential savings.

### Battery Efficiency

**Type:** Integer
**Default:** 85
**Range:** 50-100
**Unit:** %

Round-trip efficiency of your battery system (charging + discharging).

**Typical values:**
- Lithium batteries with inverter: 85-90%
- Lithium batteries (direct DC): 90-95%
- Lead-acid batteries: 70-80%

This value directly affects the profitability calculation.

## Operating Modes

Set via the `select.smart_battery_charging_mode` entity:

### Off
Integration is disabled. Battery is set to Idle (50% min_soc).

### Auto
Automatic mode. The integration switches between charge, discharge, and idle based on price analysis.

### Charge
Forces charging mode (100% min_soc). Overrides automatic decisions.

### Discharge
Forces discharging mode (10% min_soc). Overrides automatic decisions.

## Advanced Configuration

### Smart Meter Mode Compatibility

The integration works seamlessly with Zendure's Smart Meter Mode:
- Smart Battery Charging controls **how much** energy is available (via min_soc)
- Smart Meter Mode controls **when** to use it (zero feed-in)

No special configuration needed - both systems work together automatically.

### Multiple Battery Systems

Currently, the integration supports one Zendure device per instance. To control multiple batteries:
1. Install the integration multiple times
2. Configure each instance with a different device name

## Example Configurations

### Conservative (Maximize Savings)
```yaml
cheap_percentile: 15
expensive_percentile: 85
min_spread: 40
num_charging_windows: 4
num_discharging_windows: 2
```

### Aggressive (More Trading Activity)
```yaml
cheap_percentile: 30
expensive_percentile: 70
min_spread: 20
num_charging_windows: 8
num_discharging_windows: 4
```

### Balanced (Default)
```yaml
cheap_percentile: 25
expensive_percentile: 75
min_spread: 30
num_charging_windows: 6
num_discharging_windows: 3
```

## Troubleshooting

### Battery Not Responding
1. Verify Zendure device name is correct
2. Check that `number.{device}_min_soc` entity exists
3. Ensure Zendure integration is working

### No Actions Despite Price Differences
1. Check `is_profitable` attribute on sensor
2. Compare `price_spread` vs `required_spread`
3. Consider lowering `min_spread` value

### Unexpected Behavior in Auto Mode
1. Review current price window sensors
2. Check Home Assistant logs for debug messages
3. Verify operating mode is set to "Auto"
