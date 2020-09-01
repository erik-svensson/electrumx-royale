from unittest import TestCase
from hashlib import sha256
import codecs
import os

import electrumx.lib.coins as coins
from electrumx.lib.tx import VaultTxType
from tests.helpers.BitcoinRpcProxy import *
from tests.helpers.ElectrumXConnector import *


class __test_key:
    def __init__(self, pub, priv):
        self.pub = pub
        self.priv = priv


TEST_KEYS = [__test_key("03cc5fd59a77051269e8d4bce2bf7478af2f69b5106044da872d05c58f0a1e564b",
                        "cPaZzDmFRuXWpj6eLfss526or4p96YdhwsvEnsZoNLBAEpRrRRXE"),
             __test_key("0366160de766aba138abf20826b322c0787ddb8555b1ea2d119a15a286ee54fdee",
                        "cSgbdPcHWVwyzQxxCfGAQQVuQ6ZAvntoigRiQxq5twUK64QcL7ev")]


def address_to_scripthash(address):
    p2address = coins.BitcoinSegwitTestnet.pay_to_address_script(address)
    return script_to_scripthash(p2address.hex())


def script_to_scripthash(p2hex):
    return sha256(codecs.decode(p2hex.encode('utf_8'), 'hex_codec')).digest()[
           ::-1].hex()


class TestRpcMethods(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.btcvd = RPCProxyWrapper(
            rpchost=os.getenv('DAEMON_RPCHOST', '127.0.0.1'),
            rpcport=os.getenv('DAEMON_RPCPORT', 8332),
            rpcuser=os.getenv('DAEMON_RPCUSER', 'user'),
            rpcpass=os.getenv('DAEMON_RPCPASS', 'pass')
        )

        cls.electrumx = ElectrumXConnector(
            host=os.getenv('ELECTRUMX_HOST', 'localhost'),
            port=os.getenv('ELECTRUMX_PORT', 50001),
            ssl=False,
            timeout=5
        )

        # Create wallets
        cls.btcvd.createwallet('legacy.dat')
        cls.load_wallet('legacy.dat')

        cls.miner_address = cls.btcvd.getnewaddress()
        cls.legacy_address = cls.btcvd.getnewaddress()

        cls.two_keys_history = []
        cls.three_keys_history = []

        cls.setup_chain()

    @classmethod
    def setup_chain(cls):
        # Get chain's current height
        current_height = cls.btcvd.getmininginfo()['blocks']

        # Pre-mining
        cls.btcvd.generatetoaddress(300, cls.miner_address)
        current_height += 300

        # Load wallet
        cls.btcvd.createwallet('two-keys.dat')
        cls.load_wallet('two-keys.dat')

        # Create two-keys address
        cls.two_keys_address = cls.btcvd.getnewvaultalertaddress(TEST_KEYS[0].pub)
        cls.two_keys_address_info = cls.btcvd.getaddressinfo(cls.two_keys_address['address'])

        # Fund addresses
        cls.load_wallet('legacy.dat')
        current_height += 1
        txid = cls.btcvd.sendtoaddress(cls.two_keys_address['address'], 200)
        cls.two_keys_history.append((txid, current_height, VaultTxType.NONVAULT.name))
        cls.btcvd.generatetoaddress(1, cls.miner_address)  # +301

        # Send alert transaction
        cls.load_wallet('two-keys.dat')
        txid = cls.btcvd.sendalerttoaddress(cls.legacy_address, 199.99)
        cls.btcvd.generatetoaddress(1, cls.miner_address)  # +302
        current_height += 1
        cls.two_keys_history.append((txid, current_height, VaultTxType.ALERT_PENDING.name))

        # Confirm alert
        cls.btcvd.generatetoaddress(144, cls.miner_address)  # +446
        current_height += 144
        cls.two_keys_history.append((txid, current_height, VaultTxType.ALERT_CONFIRMED.name))

        # Load wallet
        cls.btcvd.createwallet('three-keys.dat')
        cls.load_wallet('three-keys.dat')

        # Create three-keys address
        cls.three_keys_address = cls.btcvd.getnewvaultinstantaddress(TEST_KEYS[0].pub, TEST_KEYS[1].pub)

        # Fund address
        cls.load_wallet('legacy.dat')
        current_height += 1
        txid = cls.btcvd.sendtoaddress(cls.two_keys_address['address'], 150)
        cls.two_keys_history.append((txid, current_height, VaultTxType.NONVAULT.name))
        txid = cls.btcvd.sendtoaddress(cls.three_keys_address['address'], 200)
        cls.three_keys_history.append((txid, current_height, VaultTxType.NONVAULT.name))
        cls.btcvd.generatetoaddress(1, cls.miner_address)  # +447

        # Send instant transaction
        cls.load_wallet('three-keys.dat')
        txid = cls.btcvd.sendinstanttoaddress(cls.legacy_address, 149.99, [TEST_KEYS[0].priv])
        cls.btcvd.generatetoaddress(10, cls.miner_address)  # +448
        current_height += 10

        # Send alert transaction
        cls.load_wallet('two-keys.dat')
        txid = cls.btcvd.sendalerttoaddress(cls.three_keys_address['address'], 12)
        current_height += 1
        cls.btcvd.generatetoaddress(1, cls.miner_address)  # +449
        cls.two_keys_history.append((txid, current_height, VaultTxType.ALERT_PENDING.name))
        cls.three_keys_history.append((txid, current_height, VaultTxType.ALERT_PENDING.name))
        current_height += 10
        cls.btcvd.generatetoaddress(10, cls.miner_address)  # +459

        # Wait for ElectrumX to synchronize
        time.sleep(10)

        # Set protocol version
        cls.electrumx.send('server.version', 'ElectrumX Connector', '2.0')

    @classmethod
    def load_wallet(cls, name):
        cls.btcvd.loadwallet(name)
        cls.btcvd = RPCProxyWrapper(
            rpchost=cls.btcvd.rpchost,
            rpcport=cls.btcvd.rpcport,
            rpcuser=cls.btcvd.rpcuser,
            rpcpass=cls.btcvd.rpcpass,
            rpcwallet=name
        )

    def test_blockchain_scripthash_get_history(self):
        def assertEqualHistories(actual, expected):
            assert len(actual) == len(expected)
            assert all((tx['tx_hash'], tx['height'], tx['tx_type']) in expected for tx in actual)

        history_two_keys = self.electrumx.send('blockchain.scripthash.get_history', address_to_scripthash(self.two_keys_address['address']))
        assertEqualHistories(history_two_keys, self.two_keys_history)

        history_three_keys = self.electrumx.send('blockchain.scripthash.get_history', address_to_scripthash(self.three_keys_address['address']))
        assertEqualHistories(history_three_keys, self.three_keys_history)

    def test_blockchain_scripthash_get_balance(self):
        balance_two_keys = self.electrumx.send('blockchain.scripthash.get_balance', address_to_scripthash(self.two_keys_address['address']))
        balance_three_keys = self.electrumx.send('blockchain.scripthash.get_balance', address_to_scripthash(self.three_keys_address['address']))

        assert balance_two_keys['alert_outgoing'] == 15000000000
        assert balance_three_keys['alert_incoming'] == 1200000000

    def test_blockchain_scripthash_listunspent(self):
        def assertEqualUnspentLists(btcvdList, electrumxList):
            electrumxList = [{'tx_hash': utxo['tx_hash'], 'vout': utxo['tx_pos']} for utxo in electrumxList]
            assert all({'tx_hash': utxo['txid'], 'vout': utxo['vout']} in electrumxList for utxo in btcvdList)

        self.load_wallet('two-keys.dat')
        btcvd_unspent_two_keys = self.btcvd.listunspent(0, 9999999, [self.two_keys_address['address']])
        electrumx_unspent_two_keys = self.electrumx.send('blockchain.scripthash.listunspent', address_to_scripthash(self.two_keys_address['address']))
        assertEqualUnspentLists(btcvd_unspent_two_keys, electrumx_unspent_two_keys)

        self.load_wallet('three-keys.dat')
        btcvd_unspent_three_keys = self.btcvd.listunspent(0, 9999999, [self.three_keys_address['address']])
        electrumx_unspent_three_keys = self.electrumx.send('blockchain.scripthash.listunspent', address_to_scripthash(self.three_keys_address['address']))
        assertEqualUnspentLists(btcvd_unspent_three_keys, electrumx_unspent_three_keys)



