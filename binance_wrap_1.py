import time
import re
import binance.enums
from binance.client import Client
from binance.exceptions import BinanceAPIException
import pprint
import colorama

class BinanceWrapper:

    client = None
    lever = None
    usdt_in_wallet = None


    def __init__(self):
        api_key, secret_key = self.get_credentials()
        self.client = Client(api_key, secret_key)
        self.usdt_in_wallet = self.update_wallet()
        print(f"usdt in wallet {self.usdt_in_wallet}")

    def update_wallet(self):
        for k in self.client.futures_account()['assets']:
            if k['asset'] == 'USDT':
                print(f"USDT wallet ballance = {k['walletBalance']}")
                # self.usdt_in_wallet = float(k['walletBalance'])
                return float(k['walletBalance'])
    def get_credentials(self):
        api_key_pattern = re.compile(r"(?<=binance_api_key ).*")
        secret_key_pattern = re.compile(r"(?<=binance_secret_key ).*")
        with open(r'C:\Users\48530\credentials.txt', 'r') as credentials_file:
            for line in credentials_file:
                if "binance_api_key" in line:
                    api_key = re.findall(api_key_pattern, line)[0]
                if "binance_secret_key" in line:
                    secret_key = re.findall(secret_key_pattern, line)[0]
        return [api_key, secret_key]

class Pair():
    def __init__(self, client, symbol_p):
        self._client = client
        self.lever = 20
        self._symbol_pair = symbol_p
        self.decision = "long"
        self.set_margintype_isolated()
        self.take_profit_percent = 30
        self.stop_loss_percent = 20
        self.entry_price = None

    @property
    def lever(self):
        return self._lever

    @lever.setter
    def lever(self, value):
        if value < 0 or value > 125:
            print(f"leverage must be set in range 1-125")
            self._lever = 20
        else:
            self._lever = value

    def __str__(self):
        output = f"symbol pair: {self.symbol_pair}\n" \
                 f"leverage: {self.lever}\n" \
                 f"actual decision: {self.decision}"
        return output

    def set_margintype_isolated(self):
        try:
            self._client.client.futures_change_margin_type(symbol=self._symbol_pair, marginType='ISOLATED')
        except BinanceAPIException as e:
            print(e.code)
            if "No need to change margin type." in e.message:
                return True
            else:
                return False

    def get_position_entry_price(self):
        for element in self._client.client.futures_position_information():
            if element['symbol'] == self._symbol_pair:
                return float(element['entryPrice'])

    def place_short_market(self):
        price = round(self.get_price(), 4)
        print(price)
        quant = round((self._client.usdt_in_wallet / price * self._lever), 3)
        # print(f'price {quant * 0.97}')
        # self.client.futures_create_order(
        #     symbol=self.symbol_pair,
        #     side=binance.enums.SIDE_SELL,
        #     positionSide="BOTH",
        #     type="MARKET",
        #     quantity=round(quant*0.99, 3),
        #     reduceOnly="false",
        # )
        print(f"============ shorted: {self._symbol_pair}! ============")
        time.sleep(1)
        entry_price = price
        print(f'entry price: {entry_price}')
        self.stop_loss_price = round(entry_price*(1+((self.stop_loss_percent/(100*self._lever)))), 2)
        print(f'stop loss price: {self.stop_loss_price}')
        self.take_profit_price = round(entry_price*(1-(self.take_profit_percent/(100*self._lever))), 2)
        print(f'take profit price: {self.take_profit_price}')
        while self.get_price() > self.take_profit_price and self.get_price() < self.stop_loss_price:
            actual_price = self.get_price()
            # print((actual_price - entry_price / entry_price))
            percent = -((actual_price - entry_price) / entry_price) * self._lever
            # print(f"actual price = {actual_price} percent = {percent}")
            self.progress_bar(percent*100)
            time.sleep(0.5)
        actual_price = self.get_price()
        percent = -((actual_price - entry_price) / entry_price) * self._lever
        self.progress_bar(percent * 100)
        # print((entry_price - take_profit_price)*self._lever/entry_price)
        # self.place_stop_loss_short(round(entry_price*(1+0.15/125), 2))
        # self.place_take_profit_short(round(entry_price*(1-0.2/125), 2))


    def place_take_profit_short(self, price):
        self.client.futures_create_order(
            symbol=self.symbol_pair,
            type='TAKE_PROFIT_MARKET',
            timeInForce='GTC',
            stopPrice=round(price, 3),
            closePosition='true',
            side=binance.enums.SIDE_BUY
        )

    def place_stop_loss_short(self, price):
        self.client.futures_create_order(
            symbol=self.symbol_pair,
            type='STOP_MARKET',
            timeInForce='GTC',
            stopPrice=round(price, 3),
            closePosition='true',
            side=binance.enums.SIDE_BUY
        )


########################################################################################
    def place_long_market(self):
        price = self.get_price()
        quant = round((self.usdt_in_wallet / price * 100), 3)
        self.client.futures_create_order(
            symbol=self.symbol_pair,
            side=binance.enums.SIDE_BUY,
            positionSide="BOTH",
            type="MARKET",
            quantity=round(quant * 0.97, 3),
            reduceOnly="false",
        )

        print(f"============ long: {cli.symbol_pair}! ============")
        time.sleep(1)
        entry_price = price
        print(f'entry price: {entry_price}')
        print(f'stop loss price: {round(entry_price * (1 - 0.2 / 125), 2)}')
        print(f'take profit price: {round(entry_price * (1 + 0.2 / 125), 2)}')
        self.place_stop_loss_long(round(entry_price * (1 - 0.15 / 125), 2))
        self.place_take_profit_long(round(entry_price * (1 + 0.2 / 125), 2))

    def place_take_profit_long(self, price):
        self.client.futures_create_order(
            symbol=self.symbol_pair,
            type='TAKE_PROFIT_MARKET',
            timeInForce='GTC',
            stopPrice=round(price, 3),
            closePosition='true',
            side=binance.enums.SIDE_SELL
        )

    def place_stop_loss_long(self, price):
        self.client.futures_create_order(
            symbol=self.symbol_pair,
            type='STOP_MARKET',
            timeInForce='GTC',
            stopPrice=round(price, 3),
            closePosition='true',
            side=binance.enums.SIDE_SELL
            )

    def cleanup(self):
        self.client.futures_cancel_all_open_orders(symbol=self.symbol_pair)

    def get_open_orders(self):
        return self.client.futures_get_open_orders(symbol=self.symbol_pair)

    def get_price(self):
        futures = self._client.client.futures_position_information()
        for i in futures:
            if i['symbol'] == self._symbol_pair:
                return  round(float(i['markPrice']), 3)

    def change_decission(self):
        if self.decision == "short":
            self.decision = "long"
        else:
            self.decision = "short"

    def progress_bar(self, progress):
        if progress < 0:
            negative_bar = ' '* (50 + int(progress/2)) + '█' * -int(progress/2)
            positive_bar = ' '* 50
        else:
            negative_bar = ' ' * 50
            positive_bar = '█' * int((progress/2)) + ' '* (50  - int(progress/2))

        print(f"\r{colorama.Fore.RED + negative_bar}{colorama.Fore.GREEN + positive_bar} | earn / loss: {progress} ", end = "\r")
############################################


cli = BinanceWrapper()
cli.get_credentials()
# print(BinanceWrapper.__dict__)


btc = Pair(cli, "BTCUSDT")
btc.lever = -19
print(btc.lever)
btc.lever = 34
btc.place_short_market()




# wallet = cli.usdt_in_wallet
# exit_criteria = wallet * 0.5
# print(cli)
# print(f"wallet: {cli.usdt_in_wallet}")
# while cli.usdt_in_wallet > exit_criteria:
#     if cli.decision == "short":
#         cli.place_short_market()
#         while len(cli.get_open_orders())>1:
#             time.sleep(2)
#         cli.cleanup()
#     else:
#         cli.place_long_market()
#         while len(cli.get_open_orders()) > 1:
#             time.sleep(2)
#         cli.cleanup()
#     time.sleep(1)
#     print(f"actual wallet: {cli.usdt_in_wallet}")
#     print(f"oreviously: {wallet}")
#     if cli.usdt_in_wallet < wallet:
#         wallet = cli.usdt_in_wallet
#         cli.change_decission()

