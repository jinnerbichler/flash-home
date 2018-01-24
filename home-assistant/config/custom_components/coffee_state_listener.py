import logging

from homeassistant.helpers.event import track_state_change

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'coffee_state_listener'

SINGLE_COFFEE_SCRIPT = 'script.coffee_single'
DOUBLE_COFFEE_SCRIPT = 'script.coffee_double'
INIT_COFFEE_SCRIPT = 'script.coffee_init'
FUND_COFFEE_SCRIPT = 'script.coffee_fund'
CLOSE_COFFEE_SCRIPT = 'script.coffee_close'
BALANCE_COFFEE_SENSOR = 'sensor.coffee_machine_balance'
ADDRESSES_COFFEE_SENSOR = 'sensor.coffee_machine_addresses'
PROVIDER_TRANSACTION = 'weblink.coffee_provider_transaction'
COFFEE_TRANSACTION = 'weblink.coffee_machine_transaction'


def setup(hass, config):
    def coffee_state_changed(entity_id, old_state, new_state):
        _LOGGER.info('{} changed to {}'.format(entity_id, new_state.state))

        if new_state.state in ['unknown', 'INITIALISING', 'UNINITIALISED', 'ERROR']:
            # hide all but init
            hide_entity(hass, entity_id=INIT_COFFEE_SCRIPT, hidden=False)
            for e in [SINGLE_COFFEE_SCRIPT, DOUBLE_COFFEE_SCRIPT, FUND_COFFEE_SCRIPT, ADDRESSES_COFFEE_SENSOR,
                      CLOSE_COFFEE_SCRIPT, BALANCE_COFFEE_SENSOR, PROVIDER_TRANSACTION, COFFEE_TRANSACTION]:
                hide_entity(hass, entity_id=e, hidden=True)
        elif new_state.state == 'INITIALISED':
            hide_entity(hass, entity_id=INIT_COFFEE_SCRIPT, hidden=True)
            hide_entity(hass, entity_id=FUND_COFFEE_SCRIPT, hidden=False)
            hide_entity(hass, entity_id=BALANCE_COFFEE_SENSOR, hidden=True)
            hide_entity(hass, entity_id=ADDRESSES_COFFEE_SENSOR, hidden=False)

            # hide_entity(hass, entity_id=SINGLE_COFFEE_SCRIPT, hidden=False)  # ToDo: remove

        elif new_state.state == 'FUNDED':
            hide_entity(hass, entity_id=FUND_COFFEE_SCRIPT, hidden=True)
            hide_entity(hass, entity_id=BALANCE_COFFEE_SENSOR, hidden=False)
            hide_entity(hass, entity_id=CLOSE_COFFEE_SCRIPT, hidden=False)
            hide_entity(hass, entity_id=SINGLE_COFFEE_SCRIPT, hidden=False)
            hide_entity(hass, entity_id=DOUBLE_COFFEE_SCRIPT, hidden=False)
            hide_entity(hass, entity_id=ADDRESSES_COFFEE_SENSOR, hidden=False)
        elif new_state.state == 'CLOSING':
            hide_entity(hass, entity_id=SINGLE_COFFEE_SCRIPT, hidden=True)
            hide_entity(hass, entity_id=DOUBLE_COFFEE_SCRIPT, hidden=True)
        elif new_state.state == 'CLOSED':
            hide_entity(hass, entity_id=INIT_COFFEE_SCRIPT, hidden=False)
            # hide all but init and transaction
            for e in [SINGLE_COFFEE_SCRIPT, DOUBLE_COFFEE_SCRIPT, FUND_COFFEE_SCRIPT, ADDRESSES_COFFEE_SENSOR,
                      CLOSE_COFFEE_SCRIPT, BALANCE_COFFEE_SENSOR, COFFEE_TRANSACTION, PROVIDER_TRANSACTION]:
                hide_entity(hass, entity_id=e, hidden=True)
        elif new_state.state in ['NO_FUNDS', 'NO_ADDRESSES_LEFT']:
            for e in [SINGLE_COFFEE_SCRIPT, DOUBLE_COFFEE_SCRIPT, FUND_COFFEE_SCRIPT,
                      INIT_COFFEE_SCRIPT, PROVIDER_TRANSACTION, COFFEE_TRANSACTION]:
                hide_entity(hass, entity_id=e, hidden=True)
            hide_entity(hass, entity_id=CLOSE_COFFEE_SCRIPT, hidden=False)
            hide_entity(hass, entity_id=BALANCE_COFFEE_SENSOR, hidden=False)

    track_state_change(hass, entity_ids=['sensor.coffee_machine_state'], action=coffee_state_changed)

    return True


def hide_entity(hass, entity_id, hidden):
    _LOGGER.info("Changing hidden state of {} to {}".format(entity_id, hidden))
    entity = hass.states.get(entity_id)
    if entity:
        attributes = {k: v for k, v in entity.attributes.items()}
        attributes['hidden'] = hidden
        hass.states.set(entity_id, entity.state, attributes, force_update=True)
