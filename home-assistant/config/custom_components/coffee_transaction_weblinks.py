import logging
import json

import homeassistant.loader as loader

_LOGGER = logging.getLogger(__name__)

# The domain of your component. Should be equal to the name of your component.
DOMAIN = 'coffee_transaction_weblinks'

# List of component names (string) your component depends upon.
DEPENDENCIES = ['mqtt']

CONF_TOPIC = 'topic'
DEFAULT_TOPIC = '/coffee/transactions'

EXPLORER_BASE_URL = 'http://iota-node.duckdns.org:8081/#/bundle/'


def setup(hass, config):
    mqtt = loader.get_component('mqtt')
    topic = config[DOMAIN].get('topic', DEFAULT_TOPIC)

    # Listener to be called when we receive a message.
    def message_received(topic, payload, qos):
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

    # Subscribe our listener to a topic.
    mqtt.subscribe(hass, topic, message_received)

    # Return boolean to indicate that initialization was successfully.
    return True
