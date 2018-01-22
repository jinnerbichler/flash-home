import json
import os
import logging
import configparser
from enum import Enum

import requests
import paho.mqtt.client as mqtt
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('coffeemachine')

# reading MQTT config
config = configparser.ConfigParser()
config.read('config.ini')

mqtt_client = None


# state handling of coffee machine
class State(Enum):
    UNINITIALISED = 0
    INITIALISING = 1
    INITIALISED = 2
    FUNDING = 3
    FUNDED = 4
    CLOSING = 5
    CLOSED = 6
    FINALISING = 7
    FINALISED = 8
    ERROR = 9


current_state = State.UNINITIALISED
flash_objects = [None, None]


def set_state(state):
    logger.info('Setting state {}'.format(state.name))
    current_state = state
    publish_state(current_state.name)


def publish_state(state):
    state_json = json.dumps({'state': state,
                             'flash': flash_objects})
    mqtt_client.publish(topic='/coffee/state', payload=state_json, retain=True)


class FlashClient:

    def __init__(self, url, username=None, password=None):
        self.url = url
        self.username = username
        self.password = password
        self.channel_id = None
        self.api_token = None

    def authenticate(self):
        auth = (self.username, self.password) if self.username else None
        response = self._post(path='/token', auth=auth)
        self.api_token = response['token']

    def init(self, **kwargs):
        response = self._post(path='/flash/init', **kwargs)
        self.channel_id = response['channelId']
        return response['flash']

    def multisignature(self, **kwargs):
        return self._post(path='/flash/multisignature/' + self.channel_id, **kwargs)

    def settlement(self, **kwargs):
        return self._post(path='/flash/settlement/' + self.channel_id, **kwargs)

    def transfer(self, **kwargs):
        return self._post(path='/flash/transfer/' + self.channel_id, **kwargs)

    def sign(self, **kwargs):
        return self._post(path='/flash/sign/' + self.channel_id, **kwargs)

    def apply(self, **kwargs):
        return self._post(path='/flash/apply/' + self.channel_id, **kwargs)

    def close(self, **kwargs):
        return self._post(path='/flash/close/' + self.channel_id, **kwargs)

    def fund(self, **kwargs):
        return self._post(path='/flash/fund/' + self.channel_id, **kwargs)

    def finalize(self, **kwargs):
        return self._post(path='/flash/finalize/' + self.channel_id, **kwargs)

    def _post(self, path, auth=None, **kwargs):
        headers = {}
        if self.api_token:
            headers['authorization'] = "Bearer " + self.api_token
        response = requests.post(self.url + path, json=kwargs, auth=auth, headers=headers)
        if response.status_code >= 400:
            logger.info(response.text)
        response.raise_for_status()
        return response.json()


# reading Flash config
SECURITY = 2
TREE_DEPTH = 3
SIGNERS_COUNT = 2
BALANCE = 4000
DEPOSIT = [2000, 2000]
SETTLEMENT_ADDRESSES = [
    'USERONE9ADDRESS9USERONE9ADDRESS9USERONE9ADDRESS9USERONE9ADDRESS9USERONE9ADDRESS9U',
    'USERTWO9ADDRESS9USERTWO9ADDRESS9USERTWO9ADDRESS9USERTWO9ADDRESS9USERTWO9ADDRESS9U']
flash_clients = []

# Flash server of coffee machine
flash_coffee_config = {k: os.getenv('FLASH_COFFEE_' + k.upper(), v)
                       for k, v in dict(config['FLASH_COFFEE']).items()}
flash_clients.append(FlashClient(**flash_coffee_config))

# FLash server of provider of coffee machine
flash_provider_config = {k: os.getenv('FLASH_PROVIDER_' + k.upper(), v)
                         for k, v in dict(config['FLASH_PROVIDER']).items()}
flash_clients.append(FlashClient(**flash_provider_config))


def init_coffee():
    logger.info('Init coffee')
    set_state(State.INITIALISING)

    for idx, client in enumerate(flash_clients):
        flash_objects[idx] = client.init(userIndex=idx, security=SECURITY, depth=TREE_DEPTH,
                                         signersCount=len(flash_clients), balance=BALANCE, deposit=DEPOSIT)

    logger.info('Generating multisignature addresses')
    all_digests = [fo['partialDigests'] for fo in flash_objects]
    for client in flash_clients:
        client.multisignature(allDigests=all_digests)

    logger.info('Setting settlement addresses')
    for idx, client in enumerate(flash_clients):
        flash_objects[idx] = client.settlement(settlementAddresses=SETTLEMENT_ADDRESSES)

    set_state(State.INITIALISED)


def pay_coffee(num):
    value = 20 * num
    logger.info('Paying {} IOTA for coffee'.format(value))
    transfers = [{'value': value, 'address': SETTLEMENT_ADDRESSES[1]}]
    bundles = flash_clients[0].transfer(transfers=transfers)
    apply_and_sign(bundles)
    return value


def apply_and_sign(bundles):
    # sign bundles
    logger.info('Signing bundles')
    for client in flash_clients:
        bundles = client.sign(bundles=bundles)

    # applying bundles
    logger.info('Applying bundles')
    for idx, client in enumerate(flash_clients):
        flash_objects[idx] = client.apply(signedBundles=bundles)


def fund():
    logger.info('Funding coffee machine')
    set_state(State.FUNDING)
    for client in flash_clients:
        client.fund()
    set_state(State.FUNDED)


def make_coffee(mode):
    logger.info('Making coffee {}'.format(mode))
    num_coffees = 1 if mode == 'single' else 2
    payed_value = pay_coffee(num=num_coffees)
    publish_state('Payed {} IOTA for {} coffee'.format(payed_value, mode))


def on_message(client, userdata, msg):
    try:
        if msg.topic == '/coffee/make':
            make_coffee(mode=msg.payload.decode('utf-8'))
        if msg.topic == '/coffee/init':
            init_coffee()
        if msg.topic == '/coffee/fund':
            fund()
    except:
        logger.exception('Error while handling message')
        time.sleep(1)
        set_state(State.ERROR)


def on_connect(client, userdata, flags, rc):
    client.subscribe(topic='/coffee/#')


# setup Flash client
logger.info('Initializing Flash clients')
for client in flash_clients:
    client.authenticate()

# init MQTT client
logger.info('Initializing MQTT client')
mqtt_config = {k: os.getenv('MQTT_' + k.upper(), v) for k, v in dict(config['MQTT']).items()}
mqtt_client = mqtt.Client(client_id='coffeemachine')
mqtt_client.username_pw_set(username=mqtt_config['username'], password=mqtt_config['password'])
mqtt_client.on_message = on_message
mqtt_client.on_connect = on_connect
mqtt_client.connect(mqtt_config['host'], int(mqtt_config['port']), keepalive=600)

set_state(State.UNINITIALISED)

logger.info('Starting MQTT loop')
mqtt_client.loop_forever()
