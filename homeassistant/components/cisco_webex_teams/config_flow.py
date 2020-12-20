"""Config flow for cisco_webex integration."""
import logging

import requests
import voluptuous as vol
import webexteamssdk

from homeassistant import config_entries, core, exceptions
from homeassistant.const import CONF_EMAIL, CONF_TOKEN

from .const import DEFAULT_NAME, DOMAIN, BE_GEO_ID  # pylint:disable=unused-import

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({CONF_TOKEN: str, CONF_EMAIL: str})


class PlaceholderHub:
    """Placeholder class to make tests pass."""

    def validate_config(self, token, email) -> bool:
        """Test if we can authenticate with the host."""
        api = webexteamssdk.WebexTeamsAPI(
            access_token=token,
            be_geo_id=BE_GEO_ID)
        _LOGGER.debug(f"Authenticating Webex.")

        try:
            try:
                # maybe check here it is a bot token as personal access tokens expire after 12 hours.
                api.people.me()
            except webexteamssdk.ApiError as error:
                _LOGGER.error(error)
                if error.status_code == 401:
                    raise InvalidAuth
                raise error

            try:
                people_list = list(api.people.list(email=email))
                if len(people_list) > 0:
                    return True
            except webexteamssdk.ApiError as error:
                _LOGGER.error(error)
                if error.status_code == 400:
                    raise EmailNotFound
                raise error
        except requests.exceptions.ConnectionError as connection_error:
            _LOGGER.error(connection_error)
            raise CannotConnect

        return False


async def validate_token_and_email(hass: core.HomeAssistant, data):
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    try:
        # pylint: disable=no-value-for-parameter
        vol.Email()(data[CONF_EMAIL])
    except vol.error.EmailInvalid:
        raise InvalidEmail

    hub = PlaceholderHub()
    await hass.async_add_executor_job(
        hub.validate_config, data[CONF_TOKEN], data[CONF_EMAIL]
    )

    # Return info that you want to store in the config entry.
    return {"title": f"{DEFAULT_NAME} {data[CONF_EMAIL]}"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for cisco_webex."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                description_placeholders={
                    "bot_docs_url": "https://developer.webex.com/docs/bots"
                },
                data_schema=STEP_USER_DATA_SCHEMA,
            )

        await self.async_set_unique_id(user_input[CONF_TOKEN])
        self._abort_if_unique_id_configured()

        errors = {}

        try:
            info = await validate_token_and_email(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except EmailNotFound:
            errors["base"] = "email_not_found"
        except InvalidEmail:
            errors["base"] = "invalid_email"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors
        )

    async def async_step_import(self, import_config):
        """Import a config entry from configuration.yaml."""
        return self.async_create_entry(title="Demo", data={})


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""


class InvalidEmail(exceptions.HomeAssistantError):
    """Error to indicate there is invalid email."""


class EmailNotFound(exceptions.HomeAssistantError):
    """Error to indicate email is not known to webex."""
