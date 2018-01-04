import logging
from collections import namedtuple

from flash import FlashClient
from iota_api import IotaApi

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Flash setup
USER_ONE_HOST = 'http://localhost:3000'
USER_ONE_SETTLEMENT = 'BIYIEOEMEXSDOMTPUVWWBBXJ9TKNU9CHJFAHMKNUH9UEDUZTOCT9WPIGNWPLNZNLDBV9WAYSTSZJGVREDQRRIUHAFY'
USER_TWO_HOST = 'http://localhost:3001'
USER_TWO_SETTLEMENT = 'JDNYBMMGUHCMROALCED9FEQIKPGOMERDX9EOHKSBQUTSOVDVINAVXZDYQTVKKXACDSYUCDMGBKPLDEYTXJCSAGMXOX'
SECURITY = 2
TREE_DEPTH = 4
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

    logger.info('Initial user one balance {} IOTA'.format(user_one.api.get_account_balance()))
    logger.info('Initial user two balance {} IOTA'.format(user_two.api.get_account_balance()))

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
    # Step 4: Transfer IOTA within channel
    ##########################################################
    logger.info('############# Initiating transfer #############')
    transfers = [{'value': 200, 'address': USER_TWO_SETTLEMENT}]
    bundles = user_one.flash.transfer(transfers=transfers)

    ##########################################################
    # Step 5: Sign bundles
    ##########################################################
    logger.info('############# Signing bundles #############')
    signed_bundles = user_one.flash.sign(bundles=bundles)
    signed_bundles = user_two.flash.sign(bundles=signed_bundles)

    ##########################################################
    # Step 6: Applying signed bundles to Flash object
    ##########################################################
    logger.info('############# Applying signed bundles #############')
    user_one_flash = user_one.flash.apply(signedBundles=signed_bundles)
    user_two_flash = user_two.flash.apply(signedBundles=signed_bundles)

    ##########################################################
    # Step 7: Closing channel
    ##########################################################
    logger.info('############# Closing channel #############')
    closing_bundles = user_one.flash.close()
    signed_bundles = user_one.flash.sign(bundles=closing_bundles)
    signed_bundles = user_two.flash.sign(bundles=signed_bundles)

    logger.info('Done!')


if __name__ == '__main__':
    main()
