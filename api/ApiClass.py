import threading
import time
import trading_api.settings
from kiteconnect import WebSocket
from kiteconnect import KiteConnect
import ipdb

# class ApiClass (threading.Thread):
class ApiClass ():

    def __init__(self, access_token, details):
        # threading.Thread.__init__(self)
        self.access_token = access_token
        self.lots = int(details['lots'])
        self.order_type = details['order_type']
        self.exchange = details['exchange']
        self.dpr = float(details['dpr'])
        self.buyprice1 = float(details['buyprice1'])
        self.symbol = details['symbol']
        self.ticksize = float(details['ticksize'])
        self.ins_token = int(details['ins_token'])
        self.product_type = details['product_type']
        self.n = float(details['n'])
        self.to_buy_i = 0
        self.max_buy = 50
        self.curr_qty = 0
        self.order_id = ""
    	# self.work = True
    	
    
    def set_ws(self,ws):
        self.ws = ws

    def set_st(self,st):
        self.st = st

    def set_dsp(self, entry, qty):
        self.entry = float(entry)
        self.qty = int(qty)
