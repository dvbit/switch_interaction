"""
Config flow for Switch Interaction Sensor.

Provides a two-step UI setup wizard:
  Step 1 (user)  : select entity + time window
  Step 2 (name)  : choose sensor name, default = int_<entity_friendly_name>

One config entry per monitored entity; duplicates are prevented via
async_set_unique_id() keyed on the entity_id.

Ref: https://developers.home-assistant.io/docs/config_entries_config_flow_handler
"""

from __future__ import annotations

import re
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_ENTITY_ID,
    CONF_MAX_TIME,
    CONF_NAME,
    DEFAULT_MAX_TIME,
    DEFAULT_NAME_PREFIX,
    DOMAIN,
)


class SwitchInteractionSensorConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Switch Interaction Sensor.

    VERSION = 1 — bump when the data schema stored in ConfigEntry.data
    changes, and add a migration in async_migrate_entry().
    """

    VERSION = 1

    def __init__(self) -> None:
        """Initialise flow-scoped storage for multi-step data."""
        self._user_input: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 1 — Select entity and time window.

        Flow:
          1. First call (user_input=None) → show the form.
          2. Second call (user_input filled) → validate → go to step 2.
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
                # Store step-1 data and proceed to name step
                self._user_input = user_input
                return await self.async_step_name()

        # Schema for step 1: entity selector + time window
        schema = vol.Schema(
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

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_name(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 2 — Choose the sensor name.

        Default = int_<friendly_name_slug> of the selected entity.
        e.g. entity "Luce Cucina" → default "int_luce_cucina"
        """
        if user_input is not None:
            # Merge name into the data collected in step 1
            self._user_input[CONF_NAME] = user_input[CONF_NAME]
            return self.async_create_entry(
                title=self._user_input[CONF_NAME],
                data=self._user_input,
            )

        # --- Build default name from entity friendly_name -------------------
        entity_id = self._user_input[CONF_ENTITY_ID]
        state = self.hass.states.get(entity_id)
        if state is not None:
            friendly = state.attributes.get("friendly_name", entity_id)
        else:
            friendly = entity_id

        # Slugify: lowercase, replace non-alnum with _, strip edges
        slug = re.sub(r"[^a-z0-9]+", "_", friendly.lower()).strip("_")
        default_name = f"{DEFAULT_NAME_PREFIX}{slug}"

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=default_name): str,
            }
        )

        return self.async_show_form(
            step_id="name",
            data_schema=schema,
        )
