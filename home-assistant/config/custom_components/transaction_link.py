import logging
import json

import homeassistant.loader as loader

_LOGGER = logging.getLogger(__name__)

# The domain of your component. Should be equal to the name of your component.
DOMAIN = 'transaction_link'

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
        bundle_hashes = json.loads(payload)['bundle_hashes']
        _LOGGER.info('Received {}'.format(bundle_hashes))

        hass.states.set('weblink.coffee_machine_transaction', EXPLORER_BASE_URL + bundle_hashes[0],
                        {'hidden': False, 'friendly_name': 'Last Transaction from Coffee Machine'},
                        force_update=True)
        hass.states.set('weblink.coffee_provider_transaction', EXPLORER_BASE_URL + bundle_hashes[1],
                        {'hidden': False, 'friendly_name': 'Last Transaction from Coffee Machine Provider'},
                        force_update=True)

    # Subscribe our listener to a topic.
    mqtt.subscribe(hass, topic, message_received)

    # Return boolean to indicate that initialization was successfully.
    return True

# weblink_name = data.get('weblink_name')
# bundle_hash = data.get('bundle_hash')
# # logger.info("Hello {}".format(name))
#
# link = 'http://iota-node.duckdns.org:8081/#/bundle/{}'.format(bundle_hash)
#
# logger.info('Setting {} to {}'.format(weblink_name, bundle_hash))
#
# hass.states.set(weblink_name, link, {'hidden': False}, force_update=True)
