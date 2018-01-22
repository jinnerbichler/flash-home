"""
Support for IOTA wallets.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/iota/
"""
import logging
from datetime import timedelta

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.discovery import load_platform

DOMAIN = 'iota'

REQUIREMENTS = ['pyota==2.0.3']

IOTA_PLATFORMS = ['sensor']

SCAN_INTERVAL = timedelta(minutes=10)

CONF_IRI = 'iri'
CONF_TESTNET = 'testnet'
CONF_WALLETS = 'wallets'
CONF_WALLET_NAME = 'name'
CONF_WALLET_SEED = 'seed'

WALLET_CONFIG = vol.Schema({
    vol.Required(CONF_WALLET_NAME): cv.string,
    vol.Required(CONF_WALLET_SEED): cv.string,
})

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_IRI): cv.string,
        vol.Optional(CONF_TESTNET, default=False): cv.boolean,
        vol.Required(CONF_WALLETS): vol.All(cv.ensure_list, [WALLET_CONFIG])
    })
}, extra=vol.ALLOW_EXTRA)

_LOGGER = logging.getLogger(__name__)


def setup(hass, config):
    """Setup IOTA component."""

    # Load platforms
    iota_config = config[DOMAIN]
    for platform in IOTA_PLATFORMS:
        load_platform(hass, platform, DOMAIN, iota_config, config)

    return True
