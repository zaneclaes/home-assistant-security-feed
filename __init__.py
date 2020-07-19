"""The security_feed component."""
import logging
import os
from .const import DOMAIN, DOMAIN_DATA
import homeassistant.core as ha
from homeassistant.const import (ATTR_ENTITY_ID, CONF_FILE_PATH)

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config):
    hass.data[DOMAIN_DATA] = {}

    @ha.callback
    async def security_feed_event(event):
        _LOGGER.info(f"security feed {event}")
        entity_id = event.data.get('entity_id')
        save = event.data.get('save')
        if not entity_id:
            _LOGGER.error('missing parameter: entity_id')
            return
        feed = hass.data[DOMAIN_DATA][entity_id.split('.')[-1]]
        if not feed:
            _LOGGER.error(f'No feed for entity ID: {entity_id}')
            return
        feed.process(save)

    hass.bus.async_listen(DOMAIN, security_feed_event)

    return True