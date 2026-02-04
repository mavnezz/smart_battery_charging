# Services Documentation

Smart Battery Charging provides service calls for manual control and integration with automations.

## Available Services

### smart_battery_charging.set_battery_state

Manually set the battery state, overriding automatic control.

**Service Data:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `state` | string | Yes | Target state: `charge`, `discharge`, `idle`, or `off` |
| `charge_power` | integer | No | Charging power in Watts (future use) |
| `discharge_power` | integer | No | Discharging power in Watts (future use) |

**States:**
- `charge`: Set battery to charging mode (min_soc = 100%)
- `discharge`: Set battery to discharging mode (min_soc = 10%)
- `idle`: Set battery to idle mode (min_soc = 50%)
- `off`: Disable integration, set battery to idle

**Example:**
```yaml
service: smart_battery_charging.set_battery_state
data:
  state: charge
```

**Use Cases:**
- Manual override during special situations
- Integration with other automations
- Testing battery behavior
- Emergency control

**Notes:**
- This will temporarily override Auto mode
- Switch back to Auto mode to resume automatic control
- Power parameters are reserved for future use

---

### smart_battery_charging.recalculate_windows

Force immediate recalculation of price windows and profitability.

**Service Data:**
None required.

**Example:**
```yaml
service: smart_battery_charging.recalculate_windows
```

**Use Cases:**
- After changing configuration options
- When you suspect stale data
- For debugging purposes
- After Tibber updates tomorrow's prices

**Notes:**
- Normally not needed as recalculation happens automatically
- Useful after manual price data updates
- May cause momentary state changes

---

## Automation Examples

### Override Based on Solar Production

```yaml
automation:
  - alias: "Override Charging During High Solar"
    trigger:
      - platform: numeric_state
        entity_id: sensor.solar_production
        above: 1000  # Watts
    condition:
      - condition: state
        entity_id: sensor.smart_battery_charging_recommended_state
        state: "discharge"
    action:
      - service: smart_battery_charging.set_battery_state
        data:
          state: idle
      - service: notify.mobile_app
        data:
          message: "Overriding discharge due to high solar production"
```

### Manual Control Based on Home Assistant Presence

```yaml
automation:
  - alias: "Force Discharge When Away"
    trigger:
      - platform: state
        entity_id: person.home_owner
        to: "not_home"
        for:
          hours: 2
    condition:
      - condition: numeric_state
        entity_id: sensor.battery_soc
        above: 80
    action:
      - service: smart_battery_charging.set_battery_state
        data:
          state: discharge
```

### Recalculate on Price Updates

```yaml
automation:
  - alias: "Recalculate Windows When Tibber Updates"
    trigger:
      - platform: state
        entity_id: sensor.tibber_prices
    action:
      - service: smart_battery_charging.recalculate_windows
```

### Emergency Stop

```yaml
automation:
  - alias: "Emergency Battery Stop"
    trigger:
      - platform: state
        entity_id: input_boolean.battery_emergency_stop
        to: "on"
    action:
      - service: smart_battery_charging.set_battery_state
        data:
          state: "off"
      - service: notify.all
        data:
          title: "Battery Emergency Stop"
          message: "Battery charging/discharging has been disabled"
```

### Smart Grid Response

```yaml
automation:
  - alias: "Grid Peak Shaving"
    trigger:
      - platform: numeric_state
        entity_id: sensor.grid_power
        above: 5000  # Watts
        for:
          minutes: 5
    condition:
      - condition: numeric_state
        entity_id: sensor.battery_soc
        above: 30
    action:
      - service: smart_battery_charging.set_battery_state
        data:
          state: discharge
      - delay:
          minutes: 30
      - service: smart_battery_charging.set_battery_state
        data:
          state: idle
```

### Time-Based Override

```yaml
automation:
  - alias: "Night Mode - Keep Battery Reserve"
    trigger:
      - platform: time
        at: "22:00:00"
    condition:
      - condition: state
        entity_id: select.smart_battery_charging_mode
        state: "auto"
    action:
      - service: smart_battery_charging.set_battery_state
        data:
          state: idle

  - alias: "Resume Auto Mode in Morning"
    trigger:
      - platform: time
        at: "06:00:00"
    action:
      - service: select.select_option
        target:
          entity_id: select.smart_battery_charging_mode
        data:
          option: "auto"
```

## Service Call from Scripts

### Script: Charge to Full

```yaml
script:
  charge_battery_full:
    alias: "Charge Battery to Full"
    sequence:
      - service: smart_battery_charging.set_battery_state
        data:
          state: charge
      - wait_template: "{{ states('sensor.battery_soc') | int >= 95 }}"
        timeout: "04:00:00"
      - service: smart_battery_charging.set_battery_state
        data:
          state: idle
      - service: notify.mobile_app
        data:
          message: "Battery fully charged"
```

### Script: Conditional Control

```yaml
script:
  smart_battery_control:
    alias: "Smart Battery Control Decision"
    sequence:
      - choose:
          - conditions:
              - condition: numeric_state
                entity_id: sensor.smart_battery_charging_price_spread
                above: 40
            sequence:
              - service: select.select_option
                target:
                  entity_id: select.smart_battery_charging_mode
                data:
                  option: "auto"
          - conditions:
              - condition: numeric_state
                entity_id: sensor.smart_battery_charging_price_spread
                below: 20
            sequence:
              - service: smart_battery_charging.set_battery_state
                data:
                  state: "off"
        default:
          - service: smart_battery_charging.set_battery_state
            data:
              state: idle
```

## Node-RED Examples

### Basic State Control

```json
[
  {
    "id": "battery_control",
    "type": "api-call-service",
    "name": "Set Battery State",
    "server": "home_assistant",
    "version": 5,
    "service_domain": "smart_battery_charging",
    "service": "set_battery_state",
    "data": "{\"state\":\"charge\"}",
    "mergeContext": "",
    "mustacheAltTags": false,
    "outputProperties": [],
    "queue": "none"
  }
]
```

## REST API Examples

### Using Home Assistant REST API

```bash
# Set battery to charge
curl -X POST \
  https://your-ha-instance.com/api/services/smart_battery_charging/set_battery_state \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"state": "charge"}'

# Recalculate windows
curl -X POST \
  https://your-ha-instance.com/api/services/smart_battery_charging/recalculate_windows \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

## Best Practices

### 1. Use Auto Mode as Default
Let the integration handle decisions automatically. Use manual overrides sparingly.

### 2. Log Service Calls
When using service calls in automations, add logging:
```yaml
- service: logbook.log
  data:
    name: "Smart Battery"
    message: "Manually set to {{ state }}"
```

### 3. Add Conditions
Always add reasonable conditions to prevent unexpected behavior:
```yaml
condition:
  - condition: numeric_state
    entity_id: sensor.battery_soc
    above: 20  # Don't discharge below 20%
```

### 4. Timeout Manual Overrides
If manually overriding, add a timeout to return to auto:
```yaml
- service: smart_battery_charging.set_battery_state
  data:
    state: charge
- delay:
    hours: 2
- service: select.select_option
  target:
    entity_id: select.smart_battery_charging_mode
  data:
    option: "auto"
```

## Troubleshooting

### Service Not Responding
- Check Home Assistant logs
- Verify integration is loaded
- Ensure service name is correct

### State Not Changing
- Check Zendure device is available
- Verify `min_soc` entity exists
- Review automation conditions

### Unexpected Behavior
- Enable debug logging
- Check current operating mode
- Review recent service calls in History

## Future Services (Planned)

These services are planned for future releases:

- `smart_battery_charging.set_custom_windows`: Define custom time windows
- `smart_battery_charging.optimize_for_solar`: Integrate solar forecast
- `smart_battery_charging.set_power_limits`: Configure charge/discharge power
