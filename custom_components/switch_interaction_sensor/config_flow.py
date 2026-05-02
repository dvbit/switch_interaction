"""
Config flow for Switch Interaction Sensor.

Provides a UI-based setup wizard (Settings → Devices & Services → Add).
The user selects a switch or light entity and a click time window.

One config entry per monitored entity; duplicates are prevented via
async_set_unique_id() keyed on the entity_id.

Ref: https://developers.home-assistant.io/docs/config_entries_config_flow_handler
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_ENTITY_ID,
    CONF_MAX_TIME,
    DEFAULT_MAX_TIME,
    DOMAIN,
)

# ---------------------------------------------------------------------------
# Schema for the "user" step — rendered as form fields in the UI.
#
# entity_id : EntitySelector filtered to switch + light domains
# max_time  : NumberSelector 1-30 s, shown as input box
#
# Ref: https://developers.home-assistant.io/docs/data_entry_flow_index
# ---------------------------------------------------------------------------
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ENTITY_ID): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain=["switch", "light"],
            ),
        ),
        vol.Optional(
            CONF_MAX_TIME, default=DEFAULT_MAX_TIME
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=1,
                max=30,
                step=1,
                unit_of_measurement="s",
                mode=selector.NumberSelectorMode.BOX,
            ),
        ),
    }
)


class SwitchInteractionSensorConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Switch Interaction Sensor.

    VERSION = 1 — bump when the data schema stored in ConfigEntry.data
    changes, and add a migration in async_migrate_entry().
    """

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial (and only) configuration step.

        Flow:
          1. First call (user_input=None) → show the form.
          2. Second call (user_input filled) → validate + create entry.
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            entity_id = user_input[CONF_ENTITY_ID]

            # --- Uniqueness guard -------------------------------------------
            # One binary_sensor per monitored entity; abort if already set up.
            await self.async_set_unique_id(entity_id)
            self._abort_if_unique_id_configured()

            # --- Entity existence check -------------------------------------
            state = self.hass.states.get(entity_id)
            if state is None:
                errors["base"] = "entity_not_found"
            else:
                # All good — persist config and create the entry.
                # Title uses the entity's friendly_name for readability.
                return self.async_create_entry(
                    title=state.attributes.get("friendly_name", entity_id),
                    data=user_input,
                )

        # Show (or re-show on error) the configuration form.
        # Labels come from strings.json / translations/<lang>.json.
        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
