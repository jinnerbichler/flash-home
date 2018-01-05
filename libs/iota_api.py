import logging
import operator

import time
from iota import Iota, ProposedTransaction, Address, TryteString, Tag, STANDARD_UNITS
from iota.adapter.wrappers import RoutingWrapper
from iota.crypto.types import Seed

logger = logging.getLogger(__name__)


class IotaApi:
    # noinspection PyProtectedMember
    def __init__(self, seed, node_url, commands=None, depth=3):

        # create adpater
        adapter = RoutingWrapper(node_url)
        commands = commands if commands else {}
        for command, url in commands.items():
            adapter.add_route(command=command, adapter=url)

        # set proper loggers
        for a in list(adapter.routes.values()) + [adapter]:
            a.set_logger(logger)
        adapter._logger.setLevel(logging.DEBUG)

        # convert seed
        seed = Seed(string2trytes_bytes(seed))

        self.api = Iota(adapter=adapter, seed=seed)
        self.api.adapter.set_logger(logger)
        self.depth = depth

    def get_node_info(self):
        return self.api.get_node_info()

    def get_new_address(self, start=0):
        """
        Fetch new address from IRI (deterministically)
        :return: tuple: address -> str, address_with_check_sum --> str
        """
        response = self.api.get_new_addresses(index=start, count=None)
        return (trytes2string(response['addresses'][0]),
                trytes2string(response['addresses'][0].with_valid_checksum()))

    def get_address_balance(self, address):
        address = Address(string2trytes_bytes(address))
        return self.api.get_balances([address])[address]

    def get_account_balance(self):
        return self.api.get_inputs()['totalBalance']

    def get_bundles(self, transaction):
        return self.api.get_bundles(transaction=transaction)['bundles']

    def replay_bundle(self, transaction):
        return self.api.replay_bundle(transaction=transaction, depth=self.depth)

    def get_inclusion_states(self, transactions, milestone=None):
        milestone = milestone if milestone else self.get_node_info()['latestMilestone']
        return self.api.get_inclusion_states(transactions=transactions, tips=[milestone])['states']

    def get_transfers(self, inclusion_states=False):
        return self.api.get_transfers(inclusion_states=inclusion_states)['bundles']

    def get_account_data(self, inclusion_states=False, start=0):
        return self.api.get_account_data(start=start, inclusion_states=inclusion_states)

    def get_transactions_for_addresses(self, addresses):
        return self.api.find_transactions(addresses=addresses)

    def transfer(self, receiver_address, change_address, value, tag=None, message=None):
        if message:
            message = TryteString.from_string(message)

        # convert addresses
        receiver_address = Address(string2trytes_bytes(receiver_address))
        change_address = Address(string2trytes_bytes(change_address))

        tag = Tag(b'INNERFLASH') if not tag else tag

        # construct transaction
        transaction = ProposedTransaction(address=receiver_address, value=value, tag=tag, message=message)

        # trigger transfer
        logger.info('########################## STARTING PoW ###########################################')
        bundle = self.api.send_transfer(depth=self.depth,
                                        transfers=[transaction],
                                        change_address=change_address)
        logger.info('########################## FINISHED PoW ###########################################')

        return bundle['bundle']

    def wait_for_confirmation(self, transaction_hashes):
        inclusion_states = [False for _ in transaction_hashes]
        while not all(inclusion_states):
            time.sleep(10)
            inclusion_states = self.get_inclusion_states(transactions=transaction_hashes)


class InsufficientBalanceException(Exception):
    def __init__(self, *args, user, proposed_amount, balance):
        self.user = user
        self.proposed_amount = proposed_amount
        self.balance = balance
        message = '{} has not enough balance ({}) for sending {} IOTA'.format(user, balance, proposed_amount)
        super().__init__(message, *args)


def new_seed():
    """
    Creates a new seed and returns the string representation.
    :return: String (ascii) representation of new seed.
    """
    return trytes2string(Seed.random())


def trytes2string(trytes):
    return str(trytes)


def string2trytes_bytes(string):
    return string.encode('utf-8')


def normalize_value(value, unit):
    return int(value * STANDARD_UNITS[unit])


def iota_display_format(amount):
    previous_unit = 'i'
    for unit, decimal in sorted(STANDARD_UNITS.items(), key=operator.itemgetter(1)):
        if decimal >= amount / 10:
            break
        previous_unit = unit
    return amount / STANDARD_UNITS[previous_unit], previous_unit
