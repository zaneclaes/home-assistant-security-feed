import logging
import os, shutil, mimetypes
from datetime import timedelta
import glob
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.components.folder.sensor import PLATFORM_SCHEMA as FOLDER_SCHEMA, CONF_FILTER, CONF_FOLDER_PATHS, Folder
from homeassistant.helpers.entity import Entity
from homeassistant.const import (CONF_NAME)
from .const import DOMAIN, DOMAIN_DATA, CONF_STORAGE, CONF_WWW, CONF_EMPTY_IMAGE

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=1)

PLATFORM_SCHEMA = FOLDER_SCHEMA.extend(
    {
        vol.Optional(CONF_WWW): cv.string,
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_STORAGE): cv.string
    }
)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the folder sensor."""
    path = config.get(CONF_FOLDER_PATHS)
    storage = config.get(CONF_STORAGE)
    www = config.get(CONF_WWW, '/config/www')
    empty = config.get(CONF_EMPTY_IMAGE, '/config/www/security_feed_empty.jpg')
    name = config.get(CONF_NAME)

    if not hass.config.is_allowed_path(path):
        _LOGGER.error("folder %s is not valid or allowed", path)
    else:
        feed = SecurityFeed(name, path, storage, www, empty, config.get(CONF_FILTER))
        hass.data[DOMAIN_DATA][name] = feed
        add_entities([feed], True)

class SecurityFeed(Entity):
    ICON_ACTIVE = "mdi:motion-sensor"
    ICON_INACTIVE = "mdi:cctv"

    def __init__(self, uid, source, storage, www, empty, filter_term):
        self.entity_id = f"{DOMAIN}.{uid}"
        self._id = uid
        self._folder_path = os.path.join(source, "")  # If no trailing / add it
        self._storage_path = os.path.join(storage, "")  # If no trailing / add it
        self._filter_term = filter_term
        self._www = os.path.join(www, "")
        self._empty_img = empty

    # Update: glob the files from the folder & update the number of files.
    # Everything else is derived from these hidden attributes.
    def update(self):
        query = self._folder_path + self._filter_term
        self._file_list = glob.glob(query)
        self._number_of_files = len(self._file_list)

    # Process (delete) the most recent file, optionally saving it to the storage path.
    def process(self, save):
        if not self.active:
            _LOGGER.error(f'No security feed items to process')
            return
        filename = self.filename
        _LOGGER.info(f"{filename} save? {save}")
        if not os.path.isfile(filename):
            _LOGGER.error(f'{filename} does not exist')
            return
        if save:
            dest = os.path.join(self._storage_path, filename.split('/')[-1])
            shutil.copyfile(filename, dest)
        os.remove(filename)
        self._file_list.pop() # immediately update internal state
        self._number_of_files -= 1 # the scheduled update may be kicked to a thread
        self.schedule_update_ha_state(force_refresh=True)

    @property
    def active(self):
        return self._file_list and self._number_of_files > 0

    @property
    def name(self):
        if not self.active:
            return "Security Feed (Recording)"
        d = self.detection
        return f'[{self._number_of_files}] {d["location"]} ({d["detected"]} {d["confidence"]}%)'

    @property
    def icon(self):
        """Return the icon for the sensor."""
        return self.ICON_ACTIVE if self.active else self.ICON_INACTIVE

    @property
    def entity_picture(self):
        return self.filename.replace(self._www, '/local/')

    @property
    def detection(self):
        fn = self.entity_picture
        p = fn.split('_')
        return {
            'location': p[-3] if self.active else None,
            'detected': p[-2] if self.active else None,
            'confidence': p[-1].split('.')[0] if self.active else 0,
            'filename': fn,
            'mime_type': mimetypes.guess_type(fn)
        }


    @property
    def device_state_attributes(self):
        """Return other details about the sensor state."""
        ret = self.detection
        ret.update({
            "entity_picture": self.entity_picture,
            "path": self._folder_path,
            "filter": self._filter_term,
            "number_of_files": self._number_of_files,
            "active": self.active,
            'friendly_name': self.name
        })
        return ret

    @property
    def filename(self):
        return sorted(self._file_list)[-1] if self.active else self._empty_img

    @property
    def state(self):
        """The state is the URL to the latest image."""
        return self._number_of_files

