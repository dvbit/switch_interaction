# Switch Interaction Sensor

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Custom Home Assistant integration that monitors a **switch** or **light** entity and creates a **device** with four entities:

| Entity              | Type          | Description                                      |
|---------------------|---------------|--------------------------------------------------|
| Window              | binary_sensor | `on` while the click window is active            |
| Click Count         | sensor        | Number of toggles in the last window             |
| Interaction Type    | sensor        | `Physical` · `Automation` · `UI` · `Unknown`     |
| User                | sensor        | HA user name (UI) or `Unknown`                   |

All sensor values are **persistent** — they always show the last interaction and are only updated on the next toggle.

## How it works

Every time the monitored entity changes state (`on` ↔ `off`), the integration inspects the **context** object:

| Interaction | `context.parent_id` | `context.user_id` |
|-------------|---------------------|--------------------|
| Physical    | `None`              | `None`             |
| Automation  | set                 | `None`             |
| UI          | `None`              | set                |

Reference: [HA Context docs](https://data.home-assistant.io/docs/context/) · [Community thread](https://community.home-assistant.io/t/work-with-triggered-by-in-automations/400352/8)

## Installation (HACS)

1. HACS → **Integrations** → **⋮** → **Custom repositories** → add this repo URL, category **Integration**.
2. Install **Switch Interaction Sensor** and restart HA.
3. **Settings → Devices & Services → Add Integration → Switch Interaction Sensor**.
4. Select entity, time window, and device name (default: `int_<entity_name>`).

## Usage examples

### Double physical click → toggle ceiling light

```yaml
automation:
  - alias: "Double physical click toggles ceiling"
    triggers:
      - trigger: state
        entity_id: binary_sensor.int_luce_cucina_window
        to: "off"
    conditions:
      - condition: state
        entity_id: sensor.int_luce_cucina_click_count
        state: "2"
      - condition: state
        entity_id: sensor.int_luce_cucina_interaction_type
        state: "Physical"
    actions:
      - action: light.toggle
        target:
          entity_id: light.ceiling
```

### Notify when a specific user toggles via UI

```yaml
automation:
  - alias: "Notify on child toggle"
    triggers:
      - trigger: state
        entity_id: sensor.int_luce_cucina_interaction_type
    conditions:
      - condition: state
        entity_id: sensor.int_luce_cucina_user
        state: "ChildUser"
    actions:
      - action: notify.mobile_app_admin
        data:
          message: "ChildUser toggled the switch!"
```

## Supported languages

English · Italian · French · Spanish · German

## Specification

This integration was built to the following spec:

```
Given a switch or light entity associated with a physical switch,
create a device with sensors exposing:

- Click Count: number of toggles within a configurable time window
- Interaction Type: Physical / Automation / UI
- User: HA user name for UI interactions, Unknown otherwise

Interaction decoding based on context object:
  Physical:   parent_id=None,  user_id=None
  Automation: parent_id!=None, user_id=None
  UI:         parent_id=None,  user_id!=None
```

## License

MIT
