"""
Constants for the Switch Interaction Sensor integration.

Centralises every magic string and default value.

Interaction decoding from context object:
  | Interaction | parent_id | user_id |
  |-------------|-----------|---------|
  | Physical    | None      | None    |
  | Automation  | set       | None    |
  | UI          | None      | set     |

Ref: https://data.home-assistant.io/docs/context/
Ref: https://community.home-assistant.io/t/400352/8
"""

# Domain — must match the directory name under custom_components/
DOMAIN = "switch_interaction_sensor"

# Configuration keys — stored in ConfigEntry.data
CONF_ENTITY_ID = "entity_id"
CONF_MAX_TIME = "max_time"
CONF_NAME = "name"

# Defaults
DEFAULT_MAX_TIME = 3
DEFAULT_NAME_PREFIX = "int_"

# Interaction type labels
INTERACTION_PHYSICAL = "Physical"
INTERACTION_AUTOMATION = "Automation"
INTERACTION_UI = "UI"
INTERACTION_UNKNOWN = "Unknown"
