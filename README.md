# Switch Interaction Tracker

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

A Home Assistant custom component that tracks interactions with switches, lights, and other entities. It distinguishes between physical presses, automation changes, and UI interactions, and counts clicks within a specified time window.

## Features

*   **Interaction Type Detection**: Automatically detects the source of a state change:
    *   `physical`: Triggered physically (e.g., wall switch, button).
    *   `ui`: Triggered via the Home Assistant Dashboard.
    *   `automation`: Triggered by an automation or script.
*   **User Identification**: If triggered via the UI, it identifies the specific Home Assistant user.
*   **Click Counting**: Counts the number of state changes (clicks) within a configurable time window (e.g., detecting double-taps).
*   **Dedicated Sensors**: Creates a separate `binary_sensor` for each monitored entity that reports the interaction details.

## Installation

### HACS (Recommended)

1.  Open HACS in Home Assistant.
2.  Go to **Integrations** > **Explore & Download Repositories**.
3.  Search for **Switch Interaction Tracker**.
4.  Download and restart Home Assistant.

### Manual

1.  Copy the `switch_interaction` directory to your `custom_components` directory.
2.  Restart Home Assistant.

## Configuration

1.  Go to **Settings** > **Devices & Services**.
2.  Click **Add Integration**.
3.  Search for **Switch Interaction Tracker**.
4.  **Entities to monitor**: Select the entities (switches, lights, input_booleans, etc.) you wish to track.
5.  **Max time**: Set the maximum time window (in seconds) to wait for additional clicks (Default: 5 seconds).

### Options

You can modify the monitored entities and the time window later by clicking **Configure** on the integration entry in the Devices & Services page.

## How it Works

For every entity you monitor, a corresponding `binary_sensor` is created (e.g., `binary_sensor.interaction_switch_living_room`).

1.  **Detection**: When the monitored entity changes state, the tracker starts a timer based on your "Max time" setting.
2.  **Counting**: Any subsequent changes within this window are counted as additional clicks.
3.  **Reporting**: Once the time window expires:
    *   The binary sensor turns `on`.
    *   The attributes are updated with the total `clicks`, `interaction` type, and `user`.
    *   After a brief moment (0.1s), the sensor turns `off` automatically, ready for the next event.

## Attributes

The binary sensor exposes the following attributes when it activates:

| Attribute | Description |
| :--- | :--- |
| `interaction` | The source of the action: `physical`, `ui`, `automation`, or `unknown`. |
| `clicks` | The number of times the entity changed state within the time window. |
| `user` | The name of the user (if `interaction` is `ui`), otherwise `unknown`. |
| `monitored_entity` | The entity ID of the device being tracked. |
| `last_changed` | The timestamp of the last detected change. |

## Example Automation

This example triggers an action only when a physical switch is toggled twice (Double Tap).

```yaml
alias: "Living Room Double Tap"
trigger:
  - platform: state
    entity_id: binary_sensor.interaction_switch_living_room
    to: "on"
condition:
  - condition: state
    entity_id: binary_sensor.interaction_switch_living_room
    attribute: interaction
    state: "physical"
  - condition: state
    entity_id: binary_sensor.interaction_switch_living_room
    attribute: clicks
    state: 2
action:
  - service: light.turn_on
    target:
      entity_id: light.bedroom
```
