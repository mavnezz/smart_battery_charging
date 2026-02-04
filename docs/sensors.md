# Sensors Documentation

Smart Battery Charging provides multiple sensors to monitor electricity prices and battery states.

## Price Sensors

### Current Price
**Entity ID:** `sensor.smart_battery_charging_current_price`
**Unit:** €/kWh
**Update Interval:** 5 minutes

The current electricity price from Tibber.

**Attributes:**
- `last_updated`: Timestamp of last update
- `currency`: Currency code (EUR, NOK, etc.)

---

### Average Price
**Entity ID:** `sensor.smart_battery_charging_average_price`
**Unit:** €/kWh

Average price across all available data (today + tomorrow if available).

**Attributes:**
- `period_start`: Start of averaging period
- `period_end`: End of averaging period
- `num_prices`: Number of prices included

---

### Price Spread
**Entity ID:** `sensor.smart_battery_charging_price_spread`
**Unit:** %

Percentage difference between minimum and maximum prices.

**Formula:**
```
spread = ((max_price - min_price) / min_price) × 100%
```

**Attributes:**
- `min_price`: Lowest price in dataset
- `max_price`: Highest price in dataset
- `min_price_time`: When minimum price occurs
- `max_price_time`: When maximum price occurs

**Example:**
- Min: 25¢ at 03:00
- Max: 35¢ at 18:00
- Spread: 40%

---

### Recommended State
**Entity ID:** `sensor.smart_battery_charging_recommended_state`
**States:** `charge`, `discharge`, `idle`

Current recommended battery state based on price analysis and profitability check.

**Attributes:**
- `is_profitable`: Boolean, whether action is economically viable
- `avg_charge_price`: Average price during charging windows
- `avg_discharge_price`: Average price during discharging windows
- `required_spread`: Minimum spread needed for profitability
- `reason`: Why this state was chosen

**State Logic:**
```python
if current_hour in cheap_windows and is_profitable:
    state = "charge"
elif current_hour in expensive_windows and is_profitable:
    state = "discharge"
else:
    state = "idle"
```

---

## Window Sensors

### Cheapest Windows
**Entity ID:** `sensor.smart_battery_charging_cheapest_windows`
**State:** Number of cheap windows

Lists all identified cheap time windows for charging.

**Attributes:**
- `windows`: List of time ranges
- `count`: Number of windows
- `avg_price`: Average price during these windows
- `total_hours`: Total hours in all windows

**Example Attributes:**
```yaml
windows:
  - start: "2024-02-04T02:00:00"
    end: "2024-02-04T03:00:00"
    price: 0.23
  - start: "2024-02-04T03:00:00"
    end: "2024-02-04T04:00:00"
    price: 0.22
count: 6
avg_price: 0.24
total_hours: 6
```

---

### Expensive Windows
**Entity ID:** `sensor.smart_battery_charging_expensive_windows`
**State:** Number of expensive windows

Lists all identified expensive time windows for discharging.

**Attributes:**
- `windows`: List of time ranges
- `count`: Number of windows
- `avg_price`: Average price during these windows
- `total_hours`: Total hours in all windows

**Example Attributes:**
```yaml
windows:
  - start: "2024-02-04T17:00:00"
    end: "2024-02-04T18:00:00"
    price: 0.35
  - start: "2024-02-04T18:00:00"
    end: "2024-02-04T19:00:00"
    price: 0.37
count: 3
avg_price: 0.36
total_hours: 3
```

---

### Next Cheap Window
**Entity ID:** `sensor.smart_battery_charging_next_cheap_window`
**State:** Time until next cheap window

Shows when the next cheap charging window starts.

**Attributes:**
- `start_time`: Window start timestamp
- `end_time`: Window end timestamp
- `price`: Price during this window
- `duration_hours`: Window duration

**States:**
- `"Now"`: Currently in a cheap window
- `"in 2 hours"`: Next window starts in 2 hours
- `"No upcoming window"`: No cheap window found

---

### Next Expensive Window
**Entity ID:** `sensor.smart_battery_charging_next_expensive_window`
**State:** Time until next expensive window

Shows when the next expensive discharging window starts.

**Attributes:**
- `start_time`: Window start timestamp
- `end_time`: Window end timestamp
- `price`: Price during this window
- `duration_hours`: Window duration

**States:**
- `"Now"`: Currently in an expensive window
- `"in 4 hours"`: Next window starts in 4 hours
- `"No upcoming window"`: No expensive window found

---

## Savings Sensor

### Potential Savings
**Entity ID:** `sensor.smart_battery_charging_potential_savings`
**Unit:** €/kWh

Estimated savings per kWh by charging during cheap periods and discharging during expensive periods.

**Formula:**
```
savings = (avg_discharge_price - avg_charge_price) × efficiency
```

**Attributes:**
- `daily_savings_estimate`: Estimated daily savings
- `monthly_savings_estimate`: Estimated monthly savings
- `yearly_savings_estimate`: Estimated yearly savings
- `cycles_per_day`: Estimated charge/discharge cycles

**Example:**
```yaml
state: 0.08  # €0.08 per kWh
daily_savings_estimate: 0.26  # €0.26 per day (with 0.8 kWh battery, 1 cycle)
monthly_savings_estimate: 7.80  # €7.80 per month
yearly_savings_estimate: 93.60  # €93.60 per year
```

---

## Using Sensors in Automations

### Example: Notification on Cheap Window

```yaml
automation:
  - alias: "Notify on Cheap Window"
    trigger:
      - platform: state
        entity_id: sensor.smart_battery_charging_recommended_state
        to: "charge"
    action:
      - service: notify.mobile_app
        data:
          title: "Günstiger Strom!"
          message: >
            Lade-Fenster aktiv.
            Preis: {{ states('sensor.smart_battery_charging_current_price') }}€/kWh
```

### Example: Dashboard Card

```yaml
type: entities
title: Smart Battery Charging
entities:
  - entity: sensor.smart_battery_charging_current_price
    name: Aktueller Preis
  - entity: sensor.smart_battery_charging_recommended_state
    name: Empfehlung
  - entity: sensor.smart_battery_charging_next_cheap_window
    name: Nächstes Ladefenster
  - entity: sensor.smart_battery_charging_potential_savings
    name: Ersparnis
  - entity: select.smart_battery_charging_mode
    name: Modus
```

### Example: Conditional Actions

```yaml
automation:
  - alias: "Manual Battery Control Based on Profitability"
    trigger:
      - platform: time_pattern
        minutes: "/5"
    condition:
      - condition: template
        value_template: >
          {{ state_attr('sensor.smart_battery_charging_recommended_state', 'is_profitable') }}
    action:
      - service: smart_battery_charging.set_battery_state
        data:
          state: "{{ states('sensor.smart_battery_charging_recommended_state') }}"
```

---

## Sensor Update Frequency

| Sensor | Update Interval | Notes |
|--------|----------------|-------|
| Current Price | 5 minutes | From Tibber API |
| All Windows | On price update | Recalculated when new prices available |
| Recommended State | On price update | Checked every calculation cycle |
| Savings | On price update | Based on current windows |

## Debugging

Enable debug logging to see detailed sensor updates:

```yaml
logger:
  default: info
  logs:
    custom_components.smart_battery_charging: debug
```

This will log:
- Price updates
- Window calculations
- Profitability checks
- State changes
