import logging

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'documentation'


def setup(hass, config):
    hass.states.set('sensor.documentation', '', {
        'custom_ui_state_card': 'state-card-value_only'
        # 'text': summary
    })
    return True
