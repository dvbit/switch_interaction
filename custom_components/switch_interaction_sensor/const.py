"""
Constants for the Switch Interaction Sensor integration.

Centralises every magic string and default value used across the
integration.  Grouped by purpose:

- Domain identifier
- Configuration keys (config_flow / ConfigEntry.data)
- Default values
- Interaction-type labels (exposed as entity attributes)
"""

# ---------------------------------------------------------------------------
# Domain — must match the directory name under custom_components/
# Ref: https://developers.home-assistant.io/docs/creating_integration_manifest
# ---------------------------------------------------------------------------
DOMAIN = "switch_interaction_sensor"

# ---------------------------------------------------------------------------
# Configuration keys — stored in ConfigEntry.data
# ---------------------------------------------------------------------------
CONF_ENTITY_ID = "entity_id"   # switch.* or light.* entity to monitor
CONF_MAX_TIME = "max_time"     # click-counting window in seconds
CONF_NAME = "name"             # user-chosen name for the binary sensor

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULT_MAX_TIME = 3  # seconds — time window for multi-click detection
DEFAULT_NAME_PREFIX = "int_"  # prefix for auto-generated sensor name

# ---------------------------------------------------------------------------
# Interaction type labels — exposed via extra_state_attributes
#
# Decoded from the context object attached to every state_changed event:
#
#   | Interaction | parent_id | user_id |
#   |-------------|-----------|---------|
#   | Physical    | None      | None    |  ← hardware toggle
#   | Automation  | set       | None    |  ← triggered by an automation
#   | UI          | None      | set     |  ← dashboard / companion app
#   | Unknown     | —         | —       |  ← initial state (no interaction yet)
#
# Ref: https://data.home-assistant.io/docs/context/
# Ref: https://community.home-assistant.io/t/400352/8
# ---------------------------------------------------------------------------
INTERACTION_PHYSICAL = "Physical"
INTERACTION_AUTOMATION = "Automation"
INTERACTION_UI = "UI"
INTERACTION_UNKNOWN = "Unknown"
