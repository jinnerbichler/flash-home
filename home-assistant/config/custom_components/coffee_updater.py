import logging
import json

import homeassistant.loader as loader
import os

_LOGGER = logging.getLogger(__name__)

# The domain of your component. Should be equal to the name of your component.
DOMAIN = 'coffee_updater'

# List of component names (string) your component depends upon.
DEPENDENCIES = ['mqtt']

CONF_TOPIC = 'topic'

EXPLORER_BASE_URL = 'http://iota-node.duckdns.org:8081/#/bundle/'

COFFEE_FLASH_BASE_URL = os.getenv('COFFEE_FLASH_BASE_URL', 'http://localhost:3000')
PROVIDER_FLASH_BASE_URL = os.getenv('PROVIDER_FLASH_BASE_URL', 'http://localhost:3001')


def setup(hass, config):
    mqtt = loader.get_component('mqtt')

    # Listener to be called when we receive a message.
    def transaction_message(topic, payload, qos):
        payload = json.loads(payload)
        _LOGGER.info('Received {}'.format(payload))
        bundle_hashes = payload['bundle_hashes']
        reason = payload['reason']

        hass.states.set('weblink.coffee_machine_transaction', EXPLORER_BASE_URL + bundle_hashes[0],
                        attributes={
                            'hidden': False,
                            'friendly_name': '{} Transaction (Coffee Machine)'.format(reason)
                        },
                        force_update=True)

        if len(bundle_hashes) > 1:
            hass.states.set('weblink.coffee_provider_transaction', EXPLORER_BASE_URL + bundle_hashes[1],
                            attributes={
                                'hidden': False,
                                'friendly_name': '{} Transaction (Coffee Machine Provider)'.format(reason)
                            },
                            force_update=True)

    def flash_init_message(topic, payload, qos):
        payload = json.loads(payload)
        _LOGGER.info('Received {}'.format(payload))
        channel_ids = payload['channel_ids']

        hass.states.set('weblink.coffee_flash_server',
                        '{}/#/channel/{}'.format(COFFEE_FLASH_BASE_URL, channel_ids[0]),
                        attributes={
                            'hidden': False,
                            'friendly_name': 'Link to Flash Server Coffee Machine'
                        },
                        force_update=True)

        if len(channel_ids) > 1:
            hass.states.set('weblink.provider_flash_server',
                            '{}/#/channel/{}'.format(PROVIDER_FLASH_BASE_URL, channel_ids[1]),
                            attributes={
                                'hidden': False,
                                'friendly_name': 'Link to Flash Server Service Provider'
                            },
                            force_update=True)

    # Subscribe our listener to a topic.
    mqtt.subscribe(hass, '/coffee/transactions', transaction_message)
    mqtt.subscribe(hass, '/coffee/channel_ids', flash_init_message)

    # Return boolean to indicate that initialization was successfully.
    return True
