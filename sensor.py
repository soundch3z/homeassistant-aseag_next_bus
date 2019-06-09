import json
import logging
import voluptuous as vol

import homeassistant.helpers.config_validation as cv

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.components.rest.sensor import RestData
from homeassistant.const import (
    ATTR_ATTRIBUTION, CONF_NAME, DEVICE_CLASS_TIMESTAMP
)
from homeassistant.helpers.entity import Entity
from homeassistant.util.dt import utc_from_timestamp

_LOGGER = logging.getLogger(__name__)

CONF_STOP_ID = 'stop_id'
CONF_DIRECTION_ID = 'direction_id'

ATTR_STOP = 'stop'
ATTR_LINE = 'line'
ATTR_DESTINATION = 'destination'

DEFAULT_NAME = 'ASEAG Next Bus'

ICON = 'mdi:bus'
ATTRIBUTION = 'Data provided by ASEAG'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_STOP_ID): cv.string,
    vol.Required(CONF_DIRECTION_ID): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Setup the sensor platform."""

    stop_id = config[CONF_STOP_ID]
    direction_id = config[CONF_DIRECTION_ID]
    name = config.get(CONF_NAME)

    url = 'http://ivu.aseag.de/interfaces/ura/instant_V2?StopId={}&DirectionID={}&ReturnList=stoppointname,linename,destinationtext,estimatedtime'
    endpoint = url.format(stop_id, direction_id)
    rest = RestData('GET', endpoint, None, None, None, True)

    add_entities([AseagNextBusSensor(rest, name, stop_id, direction_id)])

class AseagNextBusSensor(Entity):
    """Representation of a ASEAG Next Bus Sensor."""

    def __init__(self, rest, name, stop_id, direction_id):
        """Initialize the ASEAG Next Bus Sensor."""
        self.rest = rest
        self._name = name
        self._stop_id = stop_id
        self._direction_id = direction_id
        self._state = None
        self._attributes = {}

    @property
    def name(self):
        """Return the name of the ASEAG Next Bus Sensor."""
        return '{} {} {}'.format(self._name, self._stop_id, self._direction_id)

    @property
    def device_class(self):
        """Return the device class."""
        return DEVICE_CLASS_TIMESTAMP

    @property
    def icon(self):
        """Icon to use in the frontend of the ASEAG Next Bus Sensor."""
        return ICON

    @property
    def state(self):
        """Return the state of the ASEAG Next Bus Sensor."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return the state attributes of the ASEAG Next Bus Sensor.."""
        return self._attributes

    def update(self):
        """Fetch new state data for the ASEAG Next Bus Sensor."""
        self.rest.update()
        value = self.rest.data

        if value:
            self._state = None
            self._attributes = {}
            predictions = []

            for line in value.splitlines():
                try:
                    line_list = json.loads(line)
                    if (line_list[0] == 1):
                        predictions.append([line_list[4], line_list[1], line_list[2], line_list[3]])
                except ValueError:
                    _LOGGER.warning("REST result could not be parsed as JSON")
                    _LOGGER.debug("Erroneous JSON: %s", value)

            if predictions:
                predictions.sort(key=lambda prediction: prediction[0])
                self._state = utc_from_timestamp(int(predictions[0][0]) / 1000).isoformat()
                self._attributes[ATTR_STOP] = predictions[0][1]
                self._attributes[ATTR_LINE] = predictions[0][2]
                self._attributes[ATTR_DESTINATION] = predictions[0][3]
                self._attributes[ATTR_ATTRIBUTION] = ATTRIBUTION
        else:
            _LOGGER.warning("Empty reply found when expecting JSON data")
