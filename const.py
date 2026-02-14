"""Constants for Switch Interaction Tracker integration."""

DOMAIN = "switch_interaction"

# Config flow
CONF_ENTITIES = "entities"
CONF_MAXTIME = "maxtime"
CONF_USER_MAPPING = "user_mapping"

# Defaults
DEFAULT_MAXTIME = 5

# Attributes
ATTR_INTERACTION = "interaction"
ATTR_USER = "user"
ATTR_CLICKS = "clicks"
ATTR_LAST_CHANGED = "last_changed"

# Interaction types
INTERACTION_PHYSICAL = "physical"
INTERACTION_AUTOMATION = "automation"
INTERACTION_UI = "ui"
