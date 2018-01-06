import logging
from collections import namedtuple

from libs.flash import FlashClient
from libs.iota_api import IotaApi

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# Flash setup
USER_ONE_HOST = 'http://localhost:3000'
USER_ONE_SETTLEMENT = 'BIYIEOEMEXSDOMTPUVWWBBXJ9TKNU9CHJFAHMKNUH9UEDUZTOCT9WPIGNWPLNZNLDBV9WAYSTSZJGVRED'
USER_TWO_HOST = 'http://localhost:3001'
USER_TWO_SETTLEMENT = 'JDNYBMMGUHCMROALCED9FEQIKPGOMERDX9EOHKSBQUTSOVDVINAVXZDYQTVKKXACDSYUCDMGBKPLDEYTX'
SECURITY = 2
TREE_DEPTH = 3
SIGNERS_COUNT = 2
BALANCE = 4000
DEPOSIT = [2000, 2000]

# Wallet setup
IRI_NODE = 'http://iota-node.duckdns.org:14267'
USER_ONE_SEED = 'ECRUQZGHBGSIGINQV9FK9EWZZTODYCKTGLITLHUNFKIOAFQYWSUIXQDSKZYHOVLBIXWKRIXDNARDYADKU'
USER_TWO_SEED = 'UXSVWCUKNZKOVYTWPWEF9KBHZLNSDGYDVBJGNYJKF9MZIOTSFCHRYNCKUQIYXBCILTVXL9NFMFIKQLUGX'

User = namedtuple('User', ['flash', 'api'])


# noinspection PyUnusedLocal
def main():
    user_one = User(flash=FlashClient(url=USER_ONE_HOST),
                    api=IotaApi(seed=USER_ONE_SEED, node_url=IRI_NODE))
    user_two = User(flash=FlashClient(url=USER_TWO_HOST),
                    api=IotaApi(seed=USER_TWO_SEED, node_url=IRI_NODE))

    # logger.info('Initial user one balance {} IOTA'.format(user_one.api.get_account_balance()))
    # logger.info('Initial user two balance {} IOTA'.format(user_two.api.get_account_balance()))

    ##########################################################
    # Step 1: Initialise Flash channel
    ##########################################################
    logger.info('############# Initializing Flash channel #############')
    user_one_flash = user_one.flash.init(userIndex=0, index=0, security=SECURITY, depth=TREE_DEPTH,
                                         signersCount=2, balance=BALANCE, deposit=DEPOSIT)
    user_two_flash = user_two.flash.init(userIndex=1, index=0, security=SECURITY, depth=TREE_DEPTH,
                                         signersCount=2, balance=BALANCE, deposit=DEPOSIT)

    ##########################################################
    # Step 2: Generate multisignature addresses
    ##########################################################
    logger.info('############# Generating multisignature addresses #############')
    all_digests = [user_one_flash['partialDigests'], user_two_flash['partialDigests']]
    user_one.flash.multisignature(allDigests=all_digests)
    user_two.flash.multisignature(allDigests=all_digests)

    ##########################################################
    # Step 3: Set settlement addresses
    ##########################################################
    logger.info('############# Setting settlement addresses #############')
    settlement_addresses = [USER_ONE_SETTLEMENT, USER_TWO_SETTLEMENT]
    user_one_flash = user_one.flash.settlement(settlementAddresses=settlement_addresses)
    user_two_flash = user_two.flash.settlement(settlementAddresses=settlement_addresses)

    ##########################################################
    # Step 4: Fund channel
    ##########################################################
    # logger.info('############# Funding channel #############')
    # transactions_one = user_one.flash.fund()
    # user_one.api.wait_for_confirmation([t['hash'] for t in transactions_one])
    # transactions_two = user_two.flash.fund()
    # user_one.api.wait_for_confirmation([t['hash'] for t in transactions_two])
    # logger.info(transactions_one)

    ##########################################################
    # Step 5: Transfer IOTA within channel
    ##########################################################
    logger.info('############# Initiating transfer #############')
    transfers = [{'value': 200, 'address': USER_TWO_SETTLEMENT}]
    bundles = user_one.flash.transfer(transfers=transfers)

    ##########################################################
    # Step 6: Sign bundles
    ##########################################################
    logger.info('############# Signing bundles #############')
    signed_bundles = user_one.flash.sign(bundles=bundles)
    signed_bundles = user_two.flash.sign(bundles=signed_bundles)

    ##########################################################
    # Step 7: Applying signed bundles to Flash object
    ##########################################################
    logger.info('############# Applying signed bundles #############')
    user_one_flash = user_one.flash.apply(signedBundles=signed_bundles)
    user_two_flash = user_two.flash.apply(signedBundles=signed_bundles)

    ##########################################################
    # Step 7: Performing multiple transactions
    ##########################################################
    num_transactions = 32
    logger.info('############# Performing {} transactions  #############'.format(num_transactions))
    for _ in range(num_transactions):
        transfers = [{'value': 1, 'address': USER_TWO_SETTLEMENT}]
        bundles = user_one.flash.transfer(transfers=transfers)
        signed_bundles = user_one.flash.sign(bundles=bundles)
        signed_bundles = user_two.flash.sign(bundles=signed_bundles)
        user_one_flash = user_one.flash.apply(signedBundles=signed_bundles)
        user_two_flash = user_two.flash.apply(signedBundles=signed_bundles)

    ##########################################################
    # Step 8: Closing channel
    ##########################################################
    logger.info('############# Closing channel #############')
    closing_bundles = user_one.flash.close()
    signed_bundles = user_one.flash.sign(bundles=closing_bundles)
    signed_bundles = user_two.flash.sign(bundles=signed_bundles)
    user_one_flash = user_one.flash.apply(signedBundles=signed_bundles)
    user_two_flash = user_two.flash.apply(signedBundles=signed_bundles)

    ##########################################################
    # Step 9: Finalizing channel
    ##########################################################
    logger.info('############# Finalizing channel #############')
    finalisation = user_one.flash.finalize()

    logger.info('Done!')


if __name__ == '__main__':
    main()
