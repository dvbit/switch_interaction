"""Config flow for Switch Interaction Tracker integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector
from homeassistant.helpers.schema_config_entry_flow import (
    SchemaFlowFormStep,
    SchemaOptionsFlowHandler,
)

from .const import (
    CONF_ENTITIES,
    CONF_MAXTIME,
    CONF_USER_MAPPING,
    DEFAULT_MAXTIME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class SwitchInteractionConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Switch Interaction Tracker."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate that at least one entity is selected
            if not user_input.get(CONF_ENTITIES):
                errors["base"] = "no_entities"
            else:
                # Create unique ID based on selected entities
                await self.async_set_unique_id(
                    "_".join(sorted(user_input[CONF_ENTITIES]))
                )
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title="Switch Interaction Tracker",
                    data=user_input,
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_ENTITIES): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        multiple=True,
                    ),
                ),
                vol.Optional(CONF_MAXTIME, default=DEFAULT_MAXTIME): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=60)
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> SwitchInteractionOptionsFlow:
        """Get the options flow for this handler."""
        return SwitchInteractionOptionsFlow(config_entry)


class SwitchInteractionOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Switch Interaction Tracker."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_ENTITIES,
                    default=self.config_entry.data.get(CONF_ENTITIES, []),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        multiple=True,
                    ),
                ),
                vol.Optional(
                    CONF_MAXTIME,
                    default=self.config_entry.data.get(CONF_MAXTIME, DEFAULT_MAXTIME),
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
        )
