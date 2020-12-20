"""Platform for sensor integration."""
import logging

from webexteamssdk import WebexTeamsAPI

from homeassistant.components.binary_sensor import DEVICE_CLASS_PRESENCE, Entity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_TOKEN
from homeassistant.helpers.typing import HomeAssistantType

from .const import DEFAULT_NAME, BE_GEO_ID

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistantType, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up Webex sensor based on a config entry."""

    async_add_entities(
        [
            WebexPresenceSensor(
                token=entry.data[CONF_TOKEN],
                email=entry.data[CONF_EMAIL],
                name=f"{DEFAULT_NAME} {entry.data[CONF_EMAIL]}",
            )
        ]
    )


class WebexPresenceSensor(Entity):
    """Representation of a Webex Presence Sensor."""

    def __init__(self, token, email, name):
        """Initialize the sensor."""
        self._state = None
        self._user_id = None
        self._email = email
        self._attributes = {}
        self._api = WebexTeamsAPI(
            access_token=token,
            be_geo_id=BE_GEO_ID)
        self._name = name

    @property
    def name(self):
        """Return the name of the binary sensor."""
        return self._name

    @property
    def state(self):
        """Return the status of the binary sensor."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @property
    def device_class(self):
        """Return the device class of this binary sensor."""
        return DEVICE_CLASS_PRESENCE

    def update(self):
        """Update device state."""
        if self._user_id is None:

            people_list = list(self._api.people.list(email=self._email))
            if len(people_list) > 0:
                person = people_list[0]
                self._user_id = person.id
                self.update_with_data(person)
                _LOGGER.debug(
                    "WebexPresenceSensor init with _user_id: %s", self._user_id
                )
            else:
                _LOGGER.error("Cannot find any Webex user with email: %s", self._email)

        self.update_with_data(self._api.people.get(self._user_id))

    def update_with_data(self, person):
        """Update local data with the latest person."""
        self._attributes = person.to_dict()
        # available states documented here
        # https://developer.webex.com/docs/api/v1/people/list-people
        self._state = person.status
        _LOGGER.debug("WebexPeopleSensor person state: %s", self._state)
