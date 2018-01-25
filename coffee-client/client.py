import json
import os
import logging
import configparser
from enum import Enum
from threading import Thread

import requests
import paho.mqtt.client as mqtt
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('coffeemachine')

PRICE_SINGLE_COFFEE = 300000

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
    NO_FUNDS = 7
    NO_ADDRESSES_LEFT = 8
    ERROR = 9


current_state = State.UNINITIALISED
flash_objects = [None, None]


def set_state(state):
    logger.info('Setting state {}'.format(state.name))
    current_state = state
    publish_state(current_state.name)


def publish_state(state):
    state_json = json.dumps({'state': state})
    mqtt_client.publish(topic='/coffee/state', payload=state_json, retain=True)


def publish_flash():
    flash_json = json.dumps({'flash': flash_objects})
    mqtt_client.publish(topic='/coffee/flash', payload=flash_json, retain=True)


def publish_channel_ids(channel_ids):
    channel_ids_json = json.dumps({'channel_ids': channel_ids})
    mqtt_client.publish(topic='/coffee/channel_ids', payload=channel_ids_json, retain=True)


def publish_transactions(bundle_hashes, reason):
    bundle_json = json.dumps({'bundle_hashes': bundle_hashes, 'reason': reason})
    mqtt_client.publish(topic='/coffee/transactions', payload=bundle_json, retain=True)


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

    def settlement_address(self, **kwargs):
        return self._post(path='/flash/settlement_address', **kwargs)

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
TREE_DEPTH = 4
SIGNERS_COUNT = 2
BALANCE = int(20e6)
DEPOSIT = [BALANCE // 2, BALANCE // 2]
SETTLEMENT_ADDRESSES = []
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

    publish_channel_ids(channel_ids=[c.channel_id for c in flash_clients])

    logger.info('Generating multisignature addresses')
    all_digests = [fo['partialDigests'] for fo in flash_objects]
    for client in flash_clients:
        client.multisignature(allDigests=all_digests)

    logger.info('Fetching settlement addresses')
    global SETTLEMENT_ADDRESSES
    SETTLEMENT_ADDRESSES.clear()
    for client in flash_clients:
        address_response = client.settlement_address()
        SETTLEMENT_ADDRESSES.append(address_response['address'])

    logger.info('Setting settlement addresses')
    for idx, client in enumerate(flash_clients):
        flash_objects[idx] = client.settlement(settlementAddresses=SETTLEMENT_ADDRESSES)

    # publish changes
    set_state(State.INITIALISED)
    publish_flash()
    publish_channel_ids(channel_ids=[c.channel_id for c in flash_clients])


def apply_and_sign(bundles):
    # sign bundles
    logger.info('Signing bundles')
    for client in flash_clients:
        bundles = client.sign(bundles=bundles)

    # applying bundles
    logger.info('Applying bundles')
    for idx, client in enumerate(flash_clients):
        flash_objects[idx] = client.apply(signedBundles=bundles)

    # publish changes
    publish_flash()


def fund():
    logger.info('Funding coffee machine')
    set_state(State.FUNDING)

    try:
        transactions = [client.fund() for client in flash_clients]
        publish_transactions(bundle_hashes=[tx[0]['bundle'] for tx in transactions], reason='Funding')
    except:
        logger.exception('Error while funding channel')

    set_state(State.FUNDED)


def close_and_finalyse():
    logger.info('Closing channel')
    closing_bundles = flash_clients[0].close()
    apply_and_sign(closing_bundles)

    set_state(State.CLOSED)


def make_coffee(mode):
    global flash_objects

    logger.info('Making coffee {}'.format(mode))

    # compute value
    num_coffees = 1 if mode == 'single' else 2
    value = PRICE_SINGLE_COFFEE * num_coffees

    # check state of deposits
    if flash_objects[0]['flash']['deposit'][0] < value:
        time.sleep(2)
        set_state(State.NO_FUNDS)
        return

    # check number of transactions left (at least one must be left for closing the channel)
    if len(flash_objects[0]['flash']['multisigDigestPool']) <= 1:
        time.sleep(2)
        set_state(State.NO_ADDRESSES_LEFT)
        return

    logger.info('Paying {} IOTA for coffee'.format(value))
    pay_for_coffee(value=value)
    publish_state('Payed {} MIOTA for {} coffee'.format(value / 1e6, mode))


def pay_for_coffee(value):
    global SETTLEMENT_ADDRESSES, flash_clients
    transfers = [{'value': value, 'address': SETTLEMENT_ADDRESSES[1]}]
    bundles = flash_clients[0].transfer(transfers=transfers)
    apply_and_sign(bundles)


is_accepting_messages = True


def on_message(client, userdata, msg):
    def handle_message(message):
        global is_accepting_messages
        if is_accepting_messages:
            is_accepting_messages = False
            try:
                if message.topic == '/coffee/make':
                    make_coffee(mode=message.payload.decode('utf-8'))
                if message.topic == '/coffee/init':
                    init_coffee()
                if message.topic == '/coffee/fund':
                    fund()
                if message.topic == '/coffee/close':
                    close_and_finalyse()
            except:
                logger.exception('Error while handling message')
                time.sleep(1)
                set_state(State.ERROR)
            is_accepting_messages = True
        else:
            logger.info('Skipping {}'.format(msg.topic))

    thread = Thread(target=handle_message, args=(msg,))
    thread.start()


def on_connect(client, userdata, flags, rc):
    client.subscribe([('/coffee/make', 0), ('/coffee/init', 0),
                      ('/coffee/fund', 0), ('/coffee/close', 0)])


time.sleep(int(os.getenv('INIT_SLEEP', 0)))

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
