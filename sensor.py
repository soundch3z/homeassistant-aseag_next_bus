import homeassistant.helpers.config_validation as cv
import json
import logging
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.components.rest.sensor import RestData
from homeassistant.const import (
    ATTR_ATTRIBUTION, CONF_NAME, DEVICE_CLASS_TIMESTAMP
)
from homeassistant.helpers.entity import Entity
from homeassistant.util.dt import (
    utc_from_timestamp, utcnow
)

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

    url = 'http://ivu.aseag.de/interfaces/ura/instant_V2?StopId={}&DirectionID={}&ReturnList=stoppointname,linename,destinationtext,tripid,estimatedtime,expiretime'
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
        self._predictions = []
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
        self._state = None
        self._attributes = {}

        self.rest.update()
        result = self.rest.data
        predictions = []

        if result:
            for line in result.splitlines():
                try:
                    line_list = json.loads(line)
                    if (line_list[0] == 1):
                        trip_id = line_list[4]
                        expire_time = utc_from_timestamp(int(line_list[6] / 1000))
                        estimated_time = utc_from_timestamp(int(line_list[5] / 1000))
                        stoppoint_name = line_list[1]
                        line_name = line_list[2]
                        destination_text = line_list[3]
                        predictions.append([trip_id, expire_time, estimated_time, stoppoint_name, line_name, destination_text])
                except ValueError:
                    _LOGGER.warning("REST result could not be parsed as JSON")
                    _LOGGER.debug("Erroneous JSON: %s", line)
        else:
            _LOGGER.warning("Empty reply found when expecting JSON data")

        for p in self._predictions:
            if not any(p[0] in subl for subl in predictions) and p[1] > utcnow() and p[2] > utcnow():
                predictions.append(p)
                _LOGGER.debug("Using old prediction: %s", p)

        if predictions:
            self._predictions = sorted(predictions, key=lambda prediction: prediction[1])
            self._state = self._predictions[0][2].isoformat()
            self._attributes[ATTR_STOP] = self._predictions[0][3]
            self._attributes[ATTR_LINE] = self._predictions[0][4]
            self._attributes[ATTR_DESTINATION] = self._predictions[0][5]
            self._attributes[ATTR_ATTRIBUTION] = ATTRIBUTION
