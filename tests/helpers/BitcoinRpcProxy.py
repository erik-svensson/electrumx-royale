from tests.helpers.authproxy import AuthServiceProxy, HTTP_TIMEOUT


class RPCProxyWrapper(AuthServiceProxy):
    def __init__(self, rpchost, rpcport, rpcuser, rpcpass, rpcwallet='', datadir=None, service_name=None, timeout=HTTP_TIMEOUT, connection=None):
        self.timeout = timeout
        self.connection = connection
        self.service_name = service_name
        self.datadir = datadir
        self.rpchost = rpchost
        self.rpcport = rpcport
        self.rpcuser = rpcuser
        self.rpcpass = rpcpass
        self.rpcwallet = rpcwallet

        super().__init__(f"http://{self.rpcuser}:{self.rpcpass}@{self.rpchost}:{self.rpcport}/wallet/{self.rpcwallet}", self.service_name, self.timeout, self.connection)

    @classmethod
    def killall(cls):
        import psutil
        import signal
        import time

        [p.send_signal(signal.SIGINT) for p in psutil.process_iter() if p.name() == 'bvaultd']
        time.sleep(2)
        [p.kill() for p in psutil.process_iter() if p.name() == 'bvaultd']
        if 'bvaultd' in [p.name() for p in psutil.process_iter()]: raise RuntimeError('looks like bvaultd is still running')

    def reset(self):
        import os
        import shutil

        if not self.datadir: raise RuntimeError('datadir not set')
        if os.path.exists(self.datadir): shutil.rmtree(self.datadir)
        os.mkdir(self.datadir)

    def listreceivedbyaddress(self, minconf=1, include_empty=True, include_watchonly=True):
        return self.__getattr__('listreceivedbyaddress')(minconf, include_empty, include_watchonly)

    def getblockbyheight(self, height):
        hash = self.__getattr__('getblockhash')(height)
        return self.__getattr__('getblock')(hash)

    def getbestblock(self):
        hash = self.__getattr__('getbestblockhash')()
        return self.__getattr__('getblock')(hash)

    def getrawtransaction(self, txhash, verbose=True):
        return self.__getattr__('getrawtransaction')(txhash, verbose)

    def send(self, addr, amount):
        return self.__getattr__('sendtoaddress')(addr, amount)

    def gen(self, amount, addr):
        return self.__getattr__('generatetoaddress')(amount, addr)

    def get_script_pubkey(self, txid, vout_n):
        txhex = self.gettransaction(txid)['hex']
        tx = self.decoderawtransaction(txhex)
        return tx['vout'][vout_n]['scriptPubKey']
