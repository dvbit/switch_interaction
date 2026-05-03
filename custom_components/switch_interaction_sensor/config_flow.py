"""
Config flow for Switch Interaction Sensor.

Two-step wizard:
  Step 1 (user) : select entity + time window
  Step 2 (name) : choose sensor name, default = int_<entity_slug>
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
    """Config flow handler."""

    VERSION = 1

    def __init__(self) -> None:
        """Init flow-scoped storage for multi-step data."""
        self._user_input: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 1 — Select entity and time window."""
        errors: dict[str, str] = {}

        if user_input is not None:
            entity_id = user_input[CONF_ENTITY_ID]

            await self.async_set_unique_id(entity_id)
            self._abort_if_unique_id_configured()

            state = self.hass.states.get(entity_id)
            if state is None:
                errors["base"] = "entity_not_found"
            else:
                self._user_input = user_input
                return await self.async_step_name()

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
        """Step 2 — Choose sensor name. Default = int_<friendly_name_slug>."""
        if user_input is not None:
            self._user_input[CONF_NAME] = user_input[CONF_NAME]
            return self.async_create_entry(
                title=self._user_input[CONF_NAME],
                data=self._user_input,
            )

        entity_id = self._user_input[CONF_ENTITY_ID]
        state = self.hass.states.get(entity_id)
        friendly = (
            state.attributes.get("friendly_name", entity_id)
            if state
            else entity_id
        )
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
