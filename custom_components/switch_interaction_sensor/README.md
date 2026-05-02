# Switch Interaction Sensor

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Custom Home Assistant integration that monitors a **switch** or **light** entity and creates a **binary sensor** exposing:

| Attribute          | Type  | Description                                        |
|--------------------|-------|----------------------------------------------------|
| `click_count`      | int   | Number of toggles within the time window           |
| `interaction_type` | str   | `Physical` · `Automation` · `UI` · `Unknown`       |
| `user`             | str   | HA user name (UI) or `Unknown`                     |
| `monitored_entity` | str   | The entity being tracked                           |
| `max_time_window`  | int   | Configured window in seconds                       |

## How it works

Every time the monitored entity changes state (`on` ↔ `off`), the integration inspects the **context** object on the `state_changed` event:

| Interaction | `context.parent_id` | `context.user_id` |
|-------------|---------------------|--------------------|
| Physical    | `None`              | `None`             |
| Automation  | set                 | `None`             |
| UI          | `None`              | set                |

Reference: [HA Context docs](https://data.home-assistant.io/docs/context/) · [Community thread](https://community.home-assistant.io/t/work-with-triggered-by-in-automations/400352/8)

The binary sensor turns **on** at the first click and stays on for `max_time` seconds after the **last** click, counting every toggle.  When the window expires the sensor goes **off** and all counters reset.

## Installation (HACS)

1. Open HACS → **Integrations** → **⋮** → **Custom repositories**.
2. Add this repository URL, category **Integration**.
3. Install **Switch Interaction Sensor**.
4. Restart Home Assistant.
5. Go to **Settings → Devices & Services → Add Integration → Switch Interaction Sensor**.
6. Select the switch/light entity and the click time window (default: 3 s).

## Manual installation

Copy the `custom_components/switch_interaction_sensor/` folder into your `<config>/custom_components/` directory and restart Home Assistant.

## Usage examples

### Double physical click → toggle a ceiling light

```yaml
automation:
  - alias: "Double physical click toggles ceiling light"
    triggers:
      - trigger: state
        entity_id: binary_sensor.my_switch_interaction
        to: "off"
    conditions:
      - condition: template
        value_template: >
          {{ trigger.from_state.attributes.click_count == 2
             and trigger.from_state.attributes.interaction_type == 'Physical' }}
    actions:
      - action: light.toggle
        target:
          entity_id: light.ceiling
```

### Triple click → activate a scene

```yaml
automation:
  - alias: "Triple click activates movie scene"
    triggers:
      - trigger: state
        entity_id: binary_sensor.my_switch_interaction
        to: "off"
    conditions:
      - condition: template
        value_template: >
          {{ trigger.from_state.attributes.click_count == 3
             and trigger.from_state.attributes.interaction_type == 'Physical' }}
    actions:
      - action: scene.turn_on
        target:
          entity_id: scene.movie_mode
```

### Notify when a specific user toggles a switch via UI

```yaml
automation:
  - alias: "Notify admin on child toggle"
    triggers:
      - trigger: state
        entity_id: binary_sensor.my_switch_interaction
        to: "off"
    conditions:
      - condition: template
        value_template: >
          {{ trigger.from_state.attributes.interaction_type == 'UI'
             and trigger.from_state.attributes.user == 'ChildUser' }}
    actions:
      - action: notify.mobile_app_admin
        data:
          message: "ChildUser toggled the switch!"
```

## Supported languages

English · Italian · French · Spanish · German

## License

MIT
