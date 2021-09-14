from django.shortcuts import render, HttpResponse, HttpResponseRedirect
from django.views.generic import TemplateView
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from .forms import UserForm
from django.shortcuts import render
from django.http import JsonResponse
from django.http import Http404
import pandas as pd
import talib
import os
import pytz
from pandas.tseries.offsets import BDay
from datetime import datetime, timedelta
import winsound
import shutil
import time

from ibapi.client import EClient
from ibapi.order import Order
from ibapi.order_state import OrderState
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.common import *
from ibapi.tag_value import TagValue

tz = 'Asia/Kolkata'
time = datetime.now(pytz.timezone(tz)).strftime("%H:%M:%S")

dict_out = {}
dict_out_backup = {}


def home(request):
    return render(request, 'first/index.html')


def event(request):
    if request.method == 'GET':
        df = pd.read_csv("C://interactive_brokers//media//Upstox_stocklist.csv")
        lst = os.listdir("C://interactive_brokers//media//market_watchlist")
        fullmarketwatchlist = []
        for watchlist in lst:
            fullmarketwatchlist.append(watchlist.split('.')[0])

        contract = df['ContractSymbol'].tolist()

        contract2 = fullmarketwatchlist
        context = {'contract': contract, 'contract2': contract2}
        return render(request, 'first/event.html', context=context)

    if request.method == 'POST':
        df = pd.read_csv("C://interactive_brokers//media//Upstox_stocklist.csv")
        lst = os.listdir("C://interactive_brokers//media//market_watchlist")
        fullmarketwatchlist = []
        for watchlist in lst:
            fullmarketwatchlist.append(watchlist.split('.')[0])

        contract = df['ContractSymbol'].tolist()

        contract2 = fullmarketwatchlist
        context = {'contract': contract, 'contract2': contract2}
        return render(request, 'first/event.html', context=context)


def login_user(request):
    if request.method == "GET":
        return render(request, 'first/userdetails.html')
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return render(request, 'first/event.html')
            else:
                return render(request, 'first/userdetails.html', {'error_message': 'Your account has been disabled'})
        else:
            return render(request, 'first/userdetails.html', {'error_message': 'Invalid login'})


def register(request):
    form = UserForm(request.POST or None)
    if form.is_valid():
        user = form.save(commit=False)
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user.set_password(password)
        user.save()
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)

                return render(request, 'first/userdetails.html')
    context = {
        "form": form,
    }
    return render(request, 'first/register.html', context)


def initial_capital(request):
    url = request.get_full_path
    print(url)
    params = str(url)[:-3].split('?')[1]
    params = str(params).split('$$')[0]

    print(params)

    try:
        df_StockDetail = pd.read_csv('C://interactive_brokers//media//Initial_Capital.csv')
        df_StockDetail['Risk_Percentage'].iloc[0] = str(params).split('*')[0]
        df_StockDetail.to_csv('C://interactive_brokers//media//Initial_Capital.csv', index=False)

    except:
        print("error in updating")

    error = ""
    return JsonResponse({"error": error})


class TestAppGainer(EWrapper, EClient):

    def __init__(self, broker=None):
        EClient.__init__(self, self)

        self.stock = pd.DataFrame(columns=["Symbol", "Date", "Open", "High", "Low", "Close"])
        self.stocks_at_nine = pd.DataFrame()
        self.stk_at_nine = pd.DataFrame(columns=["Stocks", "Close_At_Nine"])
        self.previous_day_close_written = 0

        self.stocks_at_nine_fifteen = pd.DataFrame()
        self.bid_size_stock = pd.DataFrame()
        self.ask_size_stock = pd.DataFrame()

        self.bidsize_asksize_return = pd.DataFrame()

        stocklist = pd.read_csv("C://interactive_brokers//media//UpstoxList_marketwatch.csv")

        # self.bar_close_at_nine = dict.fromkeys(stocklist['IBSymbol'], 0)

        self.bar_close_at_nine_fifteen = dict.fromkeys(stocklist['ContractSymbol'], 0)

        # self.bar_written_for_nine = dict.fromkeys(stocklist['IBSymbol'], 0)

        self.bar_written_for_nine_fifteen = dict.fromkeys(stocklist['ContractSymbol'], 0)

        self.bid_size = dict.fromkeys(stocklist['ContractSymbol'], 0)
        self.bid_size_written = dict.fromkeys(stocklist['ContractSymbol'], 0)

        self.ask_size = dict.fromkeys(stocklist['ContractSymbol'], 0)
        self.ask_size_written = dict.fromkeys(stocklist['ContractSymbol'], 0)
        self.volume_ratio_written = 0
        self.account_value = pd.read_csv("C://interactive_brokers//media//Account.csv")

    def historicalData(self, reqId: int, bar: BarData):
        c = self.contracts[reqId]

        df = pd.DataFrame([[c.symbol, bar.date, bar.open, bar.low, bar.high, bar.close]],
                          columns=["Symbol", "Date", "Open", "High", "Low", "Close"])
        self.stock = pd.concat([self.stock, df])

    def historicalDataEnd(self, reqId: int, start: str, end: str):
        super().historicalDataEnd(reqId, start, end)
        c = self.contracts[reqId]
        self.stock['EMA_High'] = talib.EMA(self.stock["High"], 12)
        self.stock['EMA_Low'] = talib.EMA(self.stock["Low"], 12)
        self.stock.to_csv(
            'C://interactive_brokers//media//Stock_Data//' + c.symbol + '.csv',
            index=False)
        self.stock = pd.DataFrame(columns=["Symbol", "Date", "Open", "High", "Low", "Close"])
        winsound.Beep(500, 400)

    def my_reqAccountSummary1(self, reqId: int, groupName: str, tags: str):
        self.reqAccountSummary(reqId, "All", "TotalCashValue")

    # The received data is passed to accountSummary()
    def accountSummary(self, reqId: int, account: str, tag: str, value: str, currency: str):
        super().accountSummary(reqId, account, tag, value, currency)
        print("Acct# Summary. ReqId>:", reqId, "Acct:", account, "Tag: ", tag, "Value:", value, "Currency:", currency)
        self.account_value["Capital"].iloc[0] = float(value)
        self.account_value.to_csv("C://interactive_brokers//media//Account.csv", index=False)
        return value  # This is my attempt which doesn't work


'''
    # All the Callback functions will come here

    def tickPrice(self, reqId: TickerId, tickType, price: float, attrib):
        super().tickPrice(reqId, tickType, price, attrib)

        # c = self.contracts[reqId]
        print("Tick by Tick----->", price)
        time = datetime.now(pytz.timezone(tz)).strftime("%H:%M:%S")

        c = self.contracts[reqId]

        if time >= "11:08:00" and self.previous_day_close_written == 0:

            path = 'C://interactive_brokers//media//Stock_Data'
            STOCKS = os.listdir(path)

            for stk in STOCKS:
                self.stk_at_nine = pd.read_csv('C://interactive_brokers//media//Stock_Data//' + stk, usecols=["Symbol", "Close"])
                self.stocks_at_nine = pd.concat([self.stocks_at_nine, self.stk_at_nine])

            self.stocks_at_nine.to_csv("C://interactive_brokers//media//Previous_Day_Closing_Price.csv", index=False)
            print("Previous day data done")
            self.previous_day_close_written = 1
            winsound.Beep(500, 5000)

        if time >= "11:10:00" and self.bar_written_for_nine_fifteen[c.symbol] == 0:

            if price > 0:
                self.bar_close_at_nine_fifteen[c.symbol] = price

                self.bar_written_for_nine_fifteen[c.symbol] = 1

            if all(x == 1 for x in self.bar_written_for_nine_fifteen.values()):
                self.stocks_at_nine_fifteen = pd.DataFrame(self.bar_close_at_nine_fifteen, index=[0])

                self.stocks_at_nine_fifteen = self.stocks_at_nine_fifteen.T

                self.stocks_at_nine_fifteen = self.stocks_at_nine_fifteen.sort_index()

                self.stocks_at_nine_fifteen = self.stocks_at_nine_fifteen.rename(columns={0: 'Close_At_Nine_Fifteen'})

                self.stocks_at_nine_fifteen = self.stocks_at_nine_fifteen.reset_index()

                self.stocks_at_nine_fifteen = self.stocks_at_nine_fifteen.rename(columns={'index': 'Stocks'})

                self.stocks_at_nine_fifteen.to_csv(
                    "C://interactive_brokers//media//stocks_at_nine_fifteen.csv", index=False)

                print("Today's data done")
                winsound.Beep(500, 5000)

    def updateMktDepth(self, reqId: TickerId, position: int, operation: int, side: int, price: float, size: int):
        super().updateMktDepth(reqId, position, operation, side, price, size)  # Call back function of req market data.

        c = self.contracts[reqId]
        #print(str(c.symbol)+"******size*****>>>>", size)
        time = datetime.now(pytz.timezone(tz)).strftime("%H:%M:%S")

        if time >= "11:18:00" and self.volume_ratio_written == 0:
            if side == 0:
                self.ask_size[c.symbol] = size
                self.ask_size_written[c.symbol] = 1

            if side == 1:
                self.bid_size[c.symbol] = size
                self.bid_size_written[c.symbol] = 1

            #print("*******************BID",sum(self.bid_size_written.values()))
            #print("$$$$$$$$$$$$$$$$$$$$ASK", sum(self.ask_size_written.values()))

            if all(x == 1 for x in self.bid_size_written.values()) and all(y == 1 for y in self.ask_size_written.values()):
                print("*******************")

                self.bid_size_stock = pd.DataFrame(self.bid_size, index=[0])
                self.bid_size_stock = self.bid_size_stock.T
                self.bid_size_stock = self.bid_size_stock.sort_index()
                self.bid_size_stock = self.bid_size_stock.rename(columns={0: 'BidSize'})
                self.bid_size_stock = self.bid_size_stock.reset_index()
                self.bid_size_stock = self.bid_size_stock.rename(columns={'index': 'Stocks'})
                self.bid_size_stock.to_csv("C://interactive_brokers//media//Bid_Size.csv",
                                           index=False)

                self.ask_size_stock = pd.DataFrame(self.ask_size, index=[0])
                self.ask_size_stock = self.ask_size_stock.T
                self.ask_size_stock = self.ask_size_stock.sort_index()
                self.ask_size_stock = self.ask_size_stock.rename(columns={0: 'AskSize'})
                self.ask_size_stock = self.ask_size_stock.reset_index()
                self.ask_size_stock = self.ask_size_stock.rename(columns={'index': 'Stocks'})
                self.ask_size_stock.to_csv("C://interactive_brokers//media//Ask_Size.csv",
                                           index=False)

                df_bid_size = pd.read_csv("C://interactive_brokers//media//Bid_Size.csv")
                df_ask_size = pd.read_csv("C://interactive_brokers//media//Ask_Size.csv")

                df_previous_day_close = pd.read_csv(
                    "C://interactive_brokers//media//Previous_Day_Closing_Price.csv")
                df_today_close = pd.read_csv(
                    "C://interactive_brokers//media//stocks_at_nine_fifteen.csv")
                df_top = pd.concat([df_previous_day_close, df_today_close['Close_At_Nine_Fifteen']], axis=1)
                df_top["Return"] = ((df_top["Close_At_Nine_Fifteen"] - df_top["Previous_Day_Close"]) / df_top["Previous_Day_Close"]) * 100

                self.bidsize_asksize_return = pd.concat([df_bid_size, df_ask_size['AskSize']], axis=1)
                self.bidsize_asksize_return = pd.concat([self.bidsize_asksize_return, df_top["Return"]], axis=1)

                for i in range(len(self.bidsize_asksize_return)):

                    if self.bidsize_asksize_return["BidSize"].iloc[i] > self.bidsize_asksize_return["AskSize"].iloc[i]:
                        self.bidsize_asksize_return["BidAskSizeRatio"].iloc[i] = \
                        self.bidsize_asksize_return["BidSize"].iloc[i] / self.bidsize_asksize_return["AskSize"].iloc[i]

                    if self.bidsize_asksize_return["AskSize"].iloc[i] > self.bidsize_asksize_return["BidSize"].iloc[i]:
                        self.bidsize_asksize_return["BidAskSizeRatio"].iloc[i] = \
                        self.bidsize_asksize_return["AskSize"].iloc[i] / self.bidsize_asksize_return["BidSize"].iloc[i]

                # Finally
                self.bidsize_asksize_return = pd.to_csv(
                    "C://interactive_brokers//media//BidSize_AskSize_Return.csv", index=False)
                print("Ask Size Bid Size Return Completed")
                self.volume_ratio_written = 1
                winsound.Beep(500, 5000)
'''


def get_historic(request):
    app = TestAppGainer()
    app.connect('127.0.0.1', 7497, 0)

    contracts = []
    # Read the csv file for Contract Symbols
    stocklist = pd.read_csv("C://interactive_brokers//media//UpstoxList_marketwatch.csv")

    for i in range(len(stocklist)):
        print(stocklist['ContractSymbol'].iloc[i])
        c = Contract()
        c.symbol = stocklist['ContractSymbol'].iloc[i]
        c.secType = 'STK'
        c.exchange = stocklist['ExchangeSymbol'].iloc[i]
        c.currency = 'INR'
        contracts.append(c)

    app.contracts = contracts

    df_timeframe = pd.read_csv("C://interactive_brokers//media//Upstox_stocklist.csv")
    timeframe = str(int(df_timeframe['Timeframe'].iloc[0])) + " mins"

    for i in range(len(contracts)):
        app.reqHistoricalData(i, contracts[i], "", "2 D", timeframe, "TRADES", 1, 1, False, [])

    app.my_reqAccountSummary1(8003, "All", "TotalCashValue")

    app.run()
    return HttpResponse("Get Historic Data")


class TestApp(EWrapper, EClient):

    def __init__(self):
        EClient.__init__(self, self)

        self.contracts = []
        self.stocklist_marketwatch = pd.read_csv("C://interactive_brokers//media//UpstoxList_marketwatch.csv")
        self.stocklist = pd.read_csv("C://interactive_brokers//media//Upstox_stocklist.csv")

        try:
            self.df_signal = pd.read_csv('C://interactive_brokers//media//Upstox_Tradesheet//' + datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y") + '_signal_Upstox.csv')
        except:
            self.df_signal = pd.DataFrame()

        # self.exit_with_condition = pd.DataFrame(columns=["Symbol", "timestamp", "ExitSignal", "ExitCondition", "ClosePrice", "PreviousCandle_SMALow_as_stoploss", "PreviousCandle_SMAHigh_as_stoploss", "Low_as_stoploss", "High_as_stoploss"])
        self.exit_with_condition = pd.DataFrame()
        self.low_high_updated_as_mid_of_candle = pd.DataFrame()
        self.bar_open = dict.fromkeys(self.stocklist['ContractSymbol'], 0)
        self.bar_high = dict.fromkeys(self.stocklist['ContractSymbol'], 0)
        self.bar_low = dict.fromkeys(self.stocklist['ContractSymbol'], 0)
        self.bar_close = dict.fromkeys(self.stocklist['ContractSymbol'], 0)
        self.bar_written = dict.fromkeys(self.stocklist['ContractSymbol'], 0)

        self.trade_happen = dict.fromkeys(self.stocklist['ContractSymbol'], 0)

        self.high_capture = dict.fromkeys(self.stocklist['ContractSymbol'], 0)
        self.low_capture = dict.fromkeys(self.stocklist['ContractSymbol'], 0)
        self.high_low_capture_mid_candle = dict.fromkeys(self.stocklist['ContractSymbol'], 0)

        self.risk_based_capital = dict.fromkeys(self.stocklist['ContractSymbol'], 0)
        self.stoploss_in_percentage = dict.fromkeys(self.stocklist['ContractSymbol'], 0)
        self.low_high_capture = dict.fromkeys(self.stocklist['ContractSymbol'], 0)

        self.initial_capital = pd.read_csv("C://interactive_brokers//media//Account.csv")
        self.risk_param = pd.read_csv("C://interactive_brokers//media//Initial_Capital.csv")
        self.Quantity = dict.fromkeys(self.stocklist['ContractSymbol'], 0)

        self.dfdatabase = pd.read_csv("C://interactive_brokers//media//Signal_DataBase.csv")
        self.entry_price_captured_at_fresh_long_position = dict.fromkeys(self.stocklist['ContractSymbol'], 0)
        self.entry_price_captured_at_fresh_short_position = dict.fromkeys(self.stocklist['ContractSymbol'], 0)

        self.ema_low_captured_at_fresh_long_position = dict.fromkeys(self.stocklist['ContractSymbol'], 0)
        self.ema_high_captured_at_fresh_short_position = dict.fromkeys(self.stocklist['ContractSymbol'], 0)

    def tickPrice(self, reqId: TickerId, tickType, price: float, attrib):
        super().tickPrice(reqId, tickType, price, attrib)
        c = self.contracts[reqId]
        # This is for LTP
        if tickType == 4:

            time = datetime.now(pytz.timezone(tz)).strftime("%H:%M:%S")
            if "09:15:00" <= time < "15:30:00":
                try:

                    # print(str(c.symbol) + "->", price)
                    dict_out.update({c.symbol: price})

                    if int(str(time).split(':')[1]) % int(self.stocklist.loc[self.stocklist['ContractSymbol'] == str(c.symbol), 'Timeframe'].iloc[0]) != 0 and self.bar_written[c.symbol] == 1:
                        self.bar_written[c.symbol] = 0

                    #if self.trade_happen[c.symbol] == 0 and (str(c.symbol) in str(self.dfdatabase['Symbol'])):
                        #self.trade_happen[c.symbol] = 1

                    if self.bar_open[c.symbol] == 0:
                        self.bar_open[c.symbol] = price
                    if self.bar_high[c.symbol] == 0 or price > self.bar_high[c.symbol]:
                        self.bar_high[c.symbol] = price
                    if self.bar_low[c.symbol] == 0 or price < self.bar_low[c.symbol]:
                        self.bar_low[c.symbol] = price

                    # print("Timeframe = {}".format(int(self.stocklist.loc[self.stocklist['ContractSymbol'] == str(c.symbol), 'Timeframe'].iloc[0])))
                    if int(str(time).split(':')[1]) % int(self.stocklist.loc[self.stocklist['ContractSymbol'] == str(c.symbol), 'Timeframe'].iloc[0]) == 0 and self.bar_written[c.symbol] == 0 and time > "09:16:00":
                        stock_data = pd.read_csv('C://interactive_brokers//media//Stock_Data//' + c.symbol + '.csv')
                        self.bar_close[c.symbol] = price

                        print('******************************************************')

                        idx = len(stock_data)
                        stock_data.set_value(idx, 'timestamp', datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"))
                        stock_data.set_value(idx, 'Open', self.bar_open[c.symbol])
                        stock_data.set_value(idx, 'High', self.bar_high[c.symbol])
                        stock_data.set_value(idx, 'Low', self.bar_low[c.symbol])
                        stock_data.set_value(idx, 'Close', self.bar_close[c.symbol])

                        if int(self.stocklist.loc[self.stocklist['ContractSymbol'] == str(c.symbol), 'Timeframe'].iloc[0]) == 5:
                            # if time >= '09:20:00' and time < '09:25:00':
                            if time >= '09:20:00' and time < '09:25:00' and self.low_high_capture[c.symbol] != 1:
                                print("High Low Capture begins")
                                self.high_capture[c.symbol] = self.bar_high[c.symbol]
                                self.low_capture[c.symbol] = self.bar_low[c.symbol]

                                self.low_high_capture[c.symbol] = 1



                        if int(self.stocklist.loc[self.stocklist['ContractSymbol'] == str(c.symbol), 'Timeframe'].iloc[0]) == 15:
                            if time >= '09:30:00' and time < '09:45:00' and self.low_high_capture[c.symbol] != 1:
                                self.high_capture[c.symbol] = self.bar_high[c.symbol]
                                self.low_capture[c.symbol] = self.bar_low[c.symbol]
                                self.low_high_capture[c.symbol] = 1

                        stock_data['EMA_High'] = talib.EMA(stock_data["High"], 12)
                        stock_data['EMA_Low'] = talib.EMA(stock_data["Low"], 12)

                        stock_data.to_csv('C://interactive_brokers//media//Stock_Data//' + c.symbol + '.csv',
                                          index=False)

                        self.bar_open[c.symbol] = 0
                        self.bar_high[c.symbol] = 0
                        self.bar_low[c.symbol] = 0
                        self.bar_close[c.symbol] = 0
                        self.bar_written[c.symbol] = 1

                    df_stock = pd.read_csv('C://interactive_brokers//media//Stock_Data//' + c.symbol + '.csv')

                    i = len(df_stock) - 1

                    # New Trade should happen only between 9:20 to 12:00
                    if (time >= '09:20:00') and (time < '12:00:00') and self.low_high_capture[c.symbol] == 1:
                        # if (time >= '13:15:00') and (time < '14:15:00') and self.trade_happen[c.symbol] == 0 and self.trade_count[c.symbol] < 2:

                        # For LONG Position
                        if price > self.high_capture[c.symbol] and self.trade_happen[c.symbol] == 0 and self.high_capture[c.symbol] != 0:
                            nu_of_lot = int(self.stocklist.loc[self.stocklist['ContractSymbol'] == str(c.symbol), 'no_of_lot'].iloc[0])
                            # Quantity = int(self.stocklist.loc[self.stocklist['ContractSymbol'] == str(c.symbol), 'Quantity'].iloc[0])

                            if abs(self.high_capture[c.symbol] - self.low_capture[c.symbol]) > (0.02 * self.low_capture[c.symbol]):
                                self.high_low_capture_mid_candle[c.symbol] = (self.high_capture[c.symbol] + self.low_capture[c.symbol]) * 0.5
                            else:
                                self.high_low_capture_mid_candle[c.symbol] = self.low_capture[c.symbol]


                            self.stoploss_in_percentage[c.symbol] = (abs(price - self.low_capture[c.symbol]) / price) * 100
                            self.risk_based_capital[c.symbol] = ((self.initial_capital["Capital"].iloc[0] * self.risk_param["Risk_Percentage"].iloc[0] * 0.01) * 100) / self.stoploss_in_percentage[c.symbol]
                            # risk_based_capital = (940160 * 1 * 0.01) * 100/ 1.5
                            if self.risk_based_capital[c.symbol] > 300000:
                                self.risk_based_capital[c.symbol] = 300000
                            self.Quantity[c.symbol] = int(self.risk_based_capital[c.symbol] / price)  # Here Quantity = risk_based_capital / close price
                            capital_used_for_trade = price * self.Quantity[c.symbol]

                            if capital_used_for_trade <= self.initial_capital["Capital"].iloc[0]:
                                self.initial_capital["Capital"].iloc[0] = self.initial_capital["Capital"].iloc[0] - capital_used_for_trade

                                self.initial_capital.to_csv("C://interactive_brokers//media//Account.csv", index=False)

                                self.entry_price_captured_at_fresh_long_position[c.symbol] = price
                                self.ema_low_captured_at_fresh_long_position[c.symbol] = df_stock["EMA_Low"].iloc[i-1]

                                df1 = pd.DataFrame([[c.symbol,
                                                     datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"),
                                                     "LONG",
                                                     price, nu_of_lot, self.Quantity[c.symbol]]],
                                                   columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                                self.trade_happen[c.symbol] = 1

                                self.df_signal = pd.concat([self.df_signal, df1])
                                self.df_signal.to_csv('C://interactive_brokers//media//Upstox_Tradesheet//' + datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y") + '_signal_Upstox.csv', index=False)

                                self.dfdatabase = self.dfdatabase.drop_duplicates()
                                self.dfdatabase = pd.concat([self.dfdatabase, df1])
                                self.dfdatabase = self.dfdatabase.drop_duplicates()
                                self.dfdatabase.to_csv("C://interactive_brokers//media//Signal_DataBase.csv",index=False)

                                winsound.Beep(2500, 1000)

                        # For Short Position
                        if price < self.low_capture[c.symbol] and self.trade_happen[c.symbol] == 0 and self.low_capture[c.symbol] != 0:
                            nu_of_lot = int(self.stocklist.loc[self.stocklist['ContractSymbol'] == str(c.symbol), 'no_of_lot'].iloc[0])
                            # Quantity = int(self.stocklist.loc[self.stocklist['ContractSymbol'] == str(c.symbol), 'Quantity'].iloc[0])

                            if abs(self.high_capture[c.symbol] - self.low_capture[c.symbol]) > (0.02 * self.low_capture[c.symbol]):
                                self.high_low_capture_mid_candle[c.symbol] = (self.high_capture[c.symbol] + self.low_capture[c.symbol]) * 0.5
                            else:
                                self.high_low_capture_mid_candle[c.symbol] = self.high_capture[c.symbol]

                            self.stoploss_in_percentage[c.symbol] = (abs(self.high_capture[c.symbol] - price) / price) * 100
                            self.risk_based_capital[c.symbol] = ((self.initial_capital["Capital"].iloc[0] * self.risk_param["Risk_Percentage"].iloc[0] * 0.01) * 100) / self.stoploss_in_percentage[c.symbol]
                            if self.risk_based_capital[c.symbol] > 300000:
                                self.risk_based_capital[c.symbol] = 300000

                            self.Quantity[c.symbol] = int(self.risk_based_capital[c.symbol] / price)  # Here Quantity = risk_based_capital / close price
                            capital_used_for_trade = price * self.Quantity[c.symbol]

                            if capital_used_for_trade <= self.initial_capital["Capital"].iloc[0]:
                                self.initial_capital["Capital"].iloc[0] = self.initial_capital["Capital"].iloc[0] - capital_used_for_trade

                                self.initial_capital.to_csv("C://interactive_brokers//media//Account.csv", index=False)

                                self.entry_price_captured_at_fresh_short_position[c.symbol] = price
                                self.ema_high_captured_at_fresh_short_position[c.symbol] = df_stock["EMA_High"].iloc[i-1]

                                df1 = pd.DataFrame([[c.symbol,
                                                     datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"),
                                                     "SHORT",
                                                     price, nu_of_lot, self.Quantity[c.symbol]]],
                                                   columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                                self.trade_happen[c.symbol] = 1

                                self.df_signal = pd.concat([self.df_signal, df1])
                                self.df_signal.to_csv(
                                    'C://interactive_brokers//media//Upstox_Tradesheet//' + datetime.now(
                                        pytz.timezone(tz)).strftime("%d-%m-%y") + '_signal_Upstox.csv', index=False)

                                self.dfdatabase = self.dfdatabase.drop_duplicates()
                                self.dfdatabase = pd.concat([self.dfdatabase, df1])
                                self.dfdatabase = self.dfdatabase.drop_duplicates()
                                self.dfdatabase.to_csv("C://interactive_brokers//media//Signal_DataBase.csv",
                                                       index=False)

                                winsound.Beep(2500, 1000)

                    # if entry price captured at fresh long position is greater than ema low , then only take EMA_Low as a stop loss into consideration otherwise ignore it and consider Low Capture as a stop Loss
                    if self.entry_price_captured_at_fresh_long_position[c.symbol] > self.ema_low_captured_at_fresh_long_position[c.symbol]:
                        # FOR LONG EXIT DUE To price < df_stock["EMA_Low"].iloc[i - 1]
                        if self.trade_happen[c.symbol] == 1 and str(self.dfdatabase.loc[self.dfdatabase['Symbol'] == str(c.symbol), 'Signal'].iloc[0]) == "LONG" and (price < df_stock["EMA_Low"].iloc[i - 1]):
                            nu_of_lot = int(self.stocklist.loc[self.stocklist['ContractSymbol'] == str(c.symbol), 'no_of_lot'].iloc[0])

                            df1 = pd.DataFrame([[c.symbol,
                                                 datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), "LONGEXIT",
                                                 price, nu_of_lot, self.Quantity[c.symbol]]],
                                               columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                            trade_log = pd.DataFrame([[c.symbol,
                                                       datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"),
                                                       "LONGEXIT",
                                                       "Long Exit Due to closing price breaching the SMA Low",
                                                       price,
                                                       df_stock["EMA_Low"].iloc[i - 1],
                                                       df_stock["EMA_High"].iloc[i - 1],
                                                       self.low_capture[c.symbol],
                                                       self.high_capture[c.symbol]
                                                       ]],
                                                     columns=["Symbol", "timestamp", "ExitSignal", "ExitCondition",
                                                              "Price", "PreviousCandle_SMALow_as_stoploss",
                                                              "PreviousCandle_SMAHigh_as_stoploss", "Low_as_stoploss",
                                                              "High_as_stoploss"])
                            self.trade_happen[c.symbol] = 0

                            self.exit_with_condition = pd.concat([self.exit_with_condition, trade_log])
                            self.exit_with_condition.to_csv('C://interactive_brokers//media//Logs//' + datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y") + '_signal_logs.csv', index=False)
                            self.df_signal = pd.concat([self.df_signal, df1])
                            self.df_signal.to_csv(
                                'C://interactive_brokers//media//Upstox_Tradesheet//' + datetime.now(
                                    pytz.timezone(tz)).strftime(
                                    "%d-%m-%y") + '_signal_Upstox.csv', index=False)

                            self.dfdatabase = self.dfdatabase.drop_duplicates()
                            self.dfdatabase = self.dfdatabase[self.dfdatabase.Symbol != str(c.symbol)]  # delete the exit position symbol
                            self.dfdatabase = self.dfdatabase.drop_duplicates()

                            self.dfdatabase.to_csv("C://interactive_brokers//media//Signal_DataBase.csv", index=False)

                            winsound.Beep(2500, 1000)

                    # FOR LONG EXIT Due to  price < self.low_capture[c.symbol]
                    if self.trade_happen[c.symbol] == 1 and str(self.dfdatabase.loc[self.dfdatabase['Symbol'] == str(c.symbol), 'Signal'].iloc[0]) == "LONG" and (price < self.high_low_capture_mid_candle[c.symbol]):
                        nu_of_lot = int(self.stocklist.loc[self.stocklist['ContractSymbol'] == str(c.symbol), 'no_of_lot'].iloc[0])

                        df1 = pd.DataFrame([[c.symbol,
                                             datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"),
                                             "LONGEXIT",
                                             price, nu_of_lot, self.Quantity[c.symbol]]],
                                           columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])
                        trade_log = pd.DataFrame([[c.symbol,
                                                   datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"),
                                                   "LONGEXIT",
                                                   "Long Exit Due to closing price breaching the Low captured candle",
                                                   price,
                                                   df_stock["EMA_Low"].iloc[i - 1],
                                                   df_stock["EMA_High"].iloc[i - 1],
                                                   self.low_capture[c.symbol],
                                                   self.high_capture[c.symbol]
                                                   ]],
                                                 columns=["Symbol", "timestamp", "ExitSignal", "ExitCondition",
                                                          "Price", "PreviousCandle_SMALow_as_stoploss",
                                                          "PreviousCandle_SMAHigh_as_stoploss", "Low_as_stoploss",
                                                          "High_as_stoploss"])
                        self.trade_happen[c.symbol] = 0

                        self.exit_with_condition = pd.concat([self.exit_with_condition, trade_log])
                        self.exit_with_condition.to_csv('C://interactive_brokers//media//Logs//' + datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y") + '_signal_logs.csv', index=False)

                        self.df_signal = pd.concat([self.df_signal, df1])
                        self.df_signal.to_csv(
                            'C://interactive_brokers//media//Upstox_Tradesheet//' + datetime.now(
                                pytz.timezone(tz)).strftime(
                                "%d-%m-%y") + '_signal_Upstox.csv', index=False)

                        self.dfdatabase = self.dfdatabase.drop_duplicates()
                        self.dfdatabase = self.dfdatabase[self.dfdatabase.Symbol != str(c.symbol)]  # delete the exit position symbol
                        self.dfdatabase = self.dfdatabase.drop_duplicates()

                        self.dfdatabase.to_csv("C://interactive_brokers//media//Signal_DataBase.csv", index=False)

                        winsound.Beep(2500, 1000)

                    # if entry price captured at fresh short position is less than ema high, then only take EMA_High as a stop loss into consideration otherwise ignore it and consider high Capture as a stop Loss
                    if self.entry_price_captured_at_fresh_short_position[c.symbol] < self.ema_high_captured_at_fresh_short_position[c.symbol]:
                        # FOR SHORT EXIT due to price > df_stock["EMA_High"].iloc[i - 1]
                        if self.trade_happen[c.symbol] == 1 and str(self.dfdatabase.loc[self.dfdatabase['Symbol'] == str(c.symbol), 'Signal'].iloc[0]) == "SHORT" and (price > df_stock["EMA_High"].iloc[i - 1]):
                            nu_of_lot = int(self.stocklist.loc[self.stocklist['ContractSymbol'] == str(c.symbol), 'no_of_lot'].iloc[0])

                            df1 = pd.DataFrame([[c.symbol,
                                                 datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), "SHORTEXIT",
                                                 price, nu_of_lot, self.Quantity[c.symbol]]],
                                               columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                            trade_log = pd.DataFrame([[c.symbol,
                                                       datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"),
                                                       "SHORTEXIT",
                                                       "Short Exit Due to closing price breaching the SMA High",
                                                       price,
                                                       df_stock["EMA_Low"].iloc[i - 1],
                                                       df_stock["EMA_High"].iloc[i - 1],
                                                       self.low_capture[c.symbol],
                                                       self.high_capture[c.symbol]
                                                       ]],
                                                     columns=["Symbol", "timestamp", "ExitSignal", "ExitCondition",
                                                              "Price", "PreviousCandle_SMALow_as_stoploss",
                                                              "PreviousCandle_SMAHigh_as_stoploss", "Low_as_stoploss",
                                                              "High_as_stoploss"])
                            self.trade_happen[c.symbol] = 0

                            self.exit_with_condition = pd.concat([self.exit_with_condition, trade_log])
                            self.exit_with_condition.to_csv('C://interactive_brokers//media//Logs//' + datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y") + '_signal_logs.csv', index=False)
                            self.df_signal = pd.concat([self.df_signal, df1])
                            self.df_signal.to_csv(
                                'C://interactive_brokers//media//Upstox_Tradesheet//' + datetime.now(
                                    pytz.timezone(tz)).strftime(
                                    "%d-%m-%y") + '_signal_Upstox.csv', index=False)

                            self.dfdatabase = self.dfdatabase.drop_duplicates()
                            self.dfdatabase = self.dfdatabase[self.dfdatabase.Symbol != str(c.symbol)]  # delete the exit position symbol
                            self.dfdatabase = self.dfdatabase.drop_duplicates()

                            self.dfdatabase.to_csv("C://interactive_brokers//media//Signal_DataBase.csv", index=False)

                            winsound.Beep(2500, 1000)

                    # FOR SHORT EXIT due to price > self.high_capture[c.symbol]
                    if self.trade_happen[c.symbol] == 1 and str(self.dfdatabase.loc[self.dfdatabase['Symbol'] == str(c.symbol), 'Signal'].iloc[0]) == "SHORT" and (price > self.high_low_capture_mid_candle[c.symbol]):
                        nu_of_lot = int(self.stocklist.loc[self.stocklist['ContractSymbol'] == str(c.symbol), 'no_of_lot'].iloc[0])

                        df1 = pd.DataFrame([[c.symbol,
                                             datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), "SHORTEXIT",
                                             price, nu_of_lot, self.Quantity[c.symbol]]],
                                           columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                        trade_log = pd.DataFrame([[c.symbol,
                                                   datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"),
                                                   "SHORTEXIT",
                                                   "Short Exit Due to closing price breaching the High captured candle",
                                                   price,
                                                   df_stock["EMA_Low"].iloc[i - 1],
                                                   df_stock["EMA_High"].iloc[i - 1],
                                                   self.low_capture[c.symbol],
                                                   self.high_capture[c.symbol]
                                                   ]],
                                                 columns=["Symbol", "timestamp", "ExitSignal", "ExitCondition",
                                                          "Price", "PreviousCandle_SMALow_as_stoploss",
                                                          "PreviousCandle_SMAHigh_as_stoploss", "Low_as_stoploss",
                                                          "High_as_stoploss"])

                        self.trade_happen[c.symbol] = 0

                        self.exit_with_condition = pd.concat([self.exit_with_condition, trade_log])
                        self.exit_with_condition.to_csv('C://interactive_brokers//media//Logs//' + datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y") + '_signal_logs.csv', index=False)
                        self.df_signal = pd.concat([self.df_signal, df1])
                        self.df_signal.to_csv(
                            'C://interactive_brokers//media//Upstox_Tradesheet//' + datetime.now(
                                pytz.timezone(tz)).strftime(
                                "%d-%m-%y") + '_signal_Upstox.csv', index=False)

                        self.dfdatabase = self.dfdatabase.drop_duplicates()
                        self.dfdatabase = self.dfdatabase[self.dfdatabase.Symbol != str(c.symbol)]  # delete the exit position symbol
                        self.dfdatabase = self.dfdatabase.drop_duplicates()

                        self.dfdatabase.to_csv("C://interactive_brokers//media//Signal_DataBase.csv", index=False)

                        winsound.Beep(2500, 1000)

                    # SQUARE OFF LONG AND SHORT POSITION
                    if time >= '15:10:00':

                        shutil.rmtree("C://interactive_brokers//media//market_watchlist//")
                        os.mkdir("C://interactive_brokers//media//market_watchlist")

                        if self.trade_happen[c.symbol] == 1 and str(self.dfdatabase.loc[self.dfdatabase['Symbol'] == str(c.symbol), 'Signal'].iloc[0]) == "LONG":
                            nu_of_lot = int(self.stocklist.loc[self.stocklist['ContractSymbol'] == str(c.symbol), 'no_of_lot'].iloc[0])

                            df1 = pd.DataFrame([[c.symbol,
                                                 datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"),
                                                 "LONGSQOFF",
                                                 price, nu_of_lot, self.Quantity[c.symbol]]],
                                               columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                            self.trade_happen[c.symbol] = 0

                            self.df_signal = pd.concat([self.df_signal, df1])
                            self.df_signal.to_csv(
                                'C://interactive_brokers//media//Upstox_Tradesheet//' + datetime.now(
                                    pytz.timezone(tz)).strftime(
                                    "%d-%m-%y") + '_signal_Upstox.csv', index=False)

                            self.dfdatabase = self.dfdatabase.drop_duplicates()
                            self.dfdatabase = self.dfdatabase[self.dfdatabase.Symbol != str(c.symbol)]  # delete the exit position symbol
                            self.dfdatabase = self.dfdatabase.drop_duplicates()

                            self.dfdatabase.to_csv("C://interactive_brokers//media//Signal_DataBase.csv", index=False)

                            winsound.Beep(2500, 1000)

                        if self.trade_happen[c.symbol] == 1 and str(self.dfdatabase.loc[self.dfdatabase['Symbol'] == str(c.symbol), 'Signal'].iloc[0]) == "SHORT":
                            nu_of_lot = int(self.stocklist.loc[self.stocklist['ContractSymbol'] == str(c.symbol), 'no_of_lot'].iloc[0])

                            df1 = pd.DataFrame([[c.symbol,
                                                 datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"),
                                                 "SHORTSQOFF",
                                                 price, nu_of_lot, self.Quantity[c.symbol]]],
                                               columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                            self.trade_happen[c.symbol] = 0

                            self.df_signal = pd.concat([self.df_signal, df1])
                            self.df_signal.to_csv(
                                'C://interactive_brokers//media//Upstox_Tradesheet//' + datetime.now(
                                    pytz.timezone(tz)).strftime(
                                    "%d-%m-%y") + '_signal_Upstox.csv', index=False)

                            self.dfdatabase = self.dfdatabase.drop_duplicates()
                            self.dfdatabase = self.dfdatabase[
                                self.dfdatabase.Symbol != str(c.symbol)]  # delete the exit position symbol
                            self.dfdatabase = self.dfdatabase.drop_duplicates()

                            self.dfdatabase.to_csv("C://interactive_brokers//media//Signal_DataBase.csv", index=False)

                            winsound.Beep(2500, 1000)

                except:
                    pass


def get_started(request):
    url = request.get_full_path
    url = str(url)
    print(url)

    if url.find('_s') == -1:

        app = TestApp()
        app.connect('127.0.0.1', 7497, 1)

        contracts = []
        # Read the csv file for Contract Symbols
        stocklist = pd.read_csv("C://interactive_brokers//media//UpstoxList_marketwatch.csv")

        for i in range(len(stocklist)):
            print(stocklist['ContractSymbol'].iloc[i])

            c = Contract()
            c.symbol = stocklist['ContractSymbol'].iloc[i]
            c.secType = 'STK'
            c.exchange = 'NSE'
            c.currency = 'INR'
            contracts.append(c)

        app.contracts = contracts

        for i in range(len(contracts)):
            # Requesting tickPrice
            app.reqMktData(i, contracts[i], "", False, False, [])

        app.run()


    elif url.find('_s') != -1:
        os._exit(0)

    return HttpResponse("Algo started")


def get_log(request):
    results1 = ""

    df_new = pd.DataFrame(list(dict_out.items()), columns=['Symbol', 'Price'])

    df_old = dict_out_backup
    df_old = pd.DataFrame(list(df_old.items()), columns=['Symbol', 'Price'])

    the_table = """<table border="1" class="dataframe" style = " margin-left: 350px;">
    <thead>
    <tr style="text-align: right;">
      <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">Symbol</th>
      <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">Price</th>
    </tr>
    </thead>
    <tbody>"""
    if len(df_new) == 0:
        df_start_price_symbol = pd.read_csv('C://interactive_brokers//media//UpstoxList_marketwatch.csv')

        for k in range(0, len(df_start_price_symbol)):

            try:
                value1 = df_start_price_symbol['ContractSymbol'].iloc[k]

                value2 = "--"

                the_table += """<tr>
                                <td>%(value1)s</td>
                                <td><centre>%(value2)s</centre></td>
                            </tr>""" % {'value1': value1,
                                        'value2': value2,
                                        }
            except:
                pass

    else:
        for k in range(0, len(df_new)):

            try:
                value1 = df_new['Symbol'].iloc[k]
                value2 = df_new['Price'].iloc[k]
                value3 = df_old['Price'].iloc[k]

                the_table += """<tr>
                                <td>%(value1)s</td>
                                <td style="background-color: %(color1)s;"><font color="white">%(value2)s</font></td>
                            </tr>""" % {'value1': value1,
                                        'value2': round(value2, 2),
                                        'value3': round(value3, 2),
                                        'color1': get_color_for_ticker(value2, value3)
                                        }
            except:
                pass

    the_table += """</tbody>
                </table>"""

    results1 += the_table

    dict_out_backup.update(dict_out)

    try:
        stocks_signal = pd.read_csv(
            'C://interactive_brokers//media//Upstox_Tradesheet//' + datetime.now(pytz.timezone(tz)).strftime(
                "%d-%m-%y") + '_signal_Upstox.csv')
        stocks_signal = stocks_signal.to_html(index=False).replace('<th>',
                                                                   '<th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">')
        results1 += stocks_signal
    except:
        stocks_signal = pd.DataFrame(columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])
        stocks_signal = stocks_signal.to_html(index=False).replace('<th>',
                                                                   '<th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">')
        results1 += stocks_signal

    # P and L calculation computed here
    try:
        stocks_pos = pd.read_csv("C://interactive_brokers//media//Signal_DataBase.csv")
        stocklist_for_reversal = pd.read_csv("C://interactive_brokers//media//Upstox_stocklist.csv")

        if len(stocks_pos) == 0:
            stocks_pos = stocks_pos.to_html(index=False).replace('<th>',
                                                                 '<th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">')
            results1 += stocks_pos
        else:
            df_pos = pd.DataFrame()
            for i in range(len(stocks_pos)):

                try:
                    if len(df_new) != 0 and (str(stocks_pos['Symbol'].iloc[i]) in str(df_new['Symbol'])):
                        if str(stocks_pos['Signal'].iloc[i]) == "LONG":
                            df_bar = pd.DataFrame([[stocks_pos['Symbol'].iloc[i], stocks_pos['Date'].iloc[i],
                                                    stocks_pos['Signal'].iloc[i], \
                                                    stocks_pos['Price'].iloc[i], stocks_pos['Lots'].iloc[i],
                                                    stocks_pos['Qty'].iloc[i], \
                                                    round(((df_new.loc[df_new['Symbol'] == str(
                                                        stocks_pos['Symbol'].iloc[i]), 'Price'].iloc[0]) *
                                                           stocks_pos['Qty'].iloc[i]) \
                                                          - (stocks_pos['Price'].iloc[i] * stocks_pos['Qty'].iloc[i]),
                                                          2)]], \
                                                  columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty", "P&L"])
                        else:
                            df_bar = pd.DataFrame([[stocks_pos['Symbol'].iloc[i], stocks_pos['Date'].iloc[i],
                                                    stocks_pos['Signal'].iloc[i], \
                                                    stocks_pos['Price'].iloc[i], stocks_pos['Lots'].iloc[i],
                                                    stocks_pos['Qty'].iloc[i], \
                                                    round((stocks_pos['Price'].iloc[i] * stocks_pos['Qty'].iloc[i]) \
                                                          - ((df_new.loc[df_new['Symbol'] == str(
                                                        stocks_pos['Symbol'].iloc[i]), 'Price'].iloc[0]) *
                                                             stocks_pos['Qty'].iloc[i]), 2)]], \
                                                  columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty", "P&L"])
                    else:
                        if (str(stocks_pos['Signal'].iloc[i]) == "LONG"):
                            df_bar = pd.DataFrame([[stocks_pos['Symbol'].iloc[i], stocks_pos['Date'].iloc[i],
                                                    stocks_pos['Signal'].iloc[i], \
                                                    stocks_pos['Price'].iloc[i], stocks_pos['Lots'].iloc[i],
                                                    stocks_pos['Qty'].iloc[i], \
                                                    "--"]], \
                                                  columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty", "P&L"])
                        else:
                            df_bar = pd.DataFrame([[stocks_pos['Symbol'].iloc[i], stocks_pos['Date'].iloc[i],
                                                    stocks_pos['Signal'].iloc[i], \
                                                    stocks_pos['Price'].iloc[i], stocks_pos['Lots'].iloc[i],
                                                    stocks_pos['Qty'].iloc[i], \
                                                    "--"]], \
                                                  columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty", "P&L"])

                except:
                    continue
                df_pos = pd.concat([df_pos, df_bar])

            the_table_pos = """<table border="1" class="dataframe">
            <thead>
            <tr style="text-align: right;">
              <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">Symbol</th>
              <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">Date</th>
              <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">Signal</th>
              <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">Price</th>
              <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">Lots</th>
              <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">Qty</th>             
              <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">P&L</th>
            </tr>
            </thead>
            <tbody>"""

            for k in range(0, len(df_pos)):

                try:
                    value1 = df_pos['Symbol'].iloc[k]
                    value2 = df_pos['Date'].iloc[k]
                    value3 = df_pos['Signal'].iloc[k]
                    value4 = df_pos['Price'].iloc[k]
                    value5 = df_pos['Lots'].iloc[k]
                    value6 = df_pos['Qty'].iloc[k]

                    value7 = df_pos['P&L'].iloc[k]
                    the_table_pos += """<tr>
                                    <td>%(value1)s</td>
                                    <td>%(value2)s</td>
                                    <td>%(value3)s</td>
                                    <td>%(value4)s</td>
                                    <td>%(value5)s</td>
                                    <td>%(value6)s</td>
                                    <td>%(value7)s</td>


                                </tr>""" % {'value1': value1,
                                            'value2': value2,
                                            'value3': value3,
                                            'value4': value4,
                                            'value5': value5,
                                            'value6': value6,
                                            'value7': value7,

                                            }
                except:
                    pass

            the_table_pos += """</tbody>
                        </table>"""

            results1 += the_table_pos

    except:
        stocks_pos = pd.DataFrame(columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty", "P&L"])
        stocks_pos = stocks_pos.to_html(index=False).replace('<th>',
                                                             '<th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">')
        results1 += stocks_pos

    return HttpResponse(results1)


def get_color_for_ticker(value2, value3):
    if value2 > value3:
        return "green"
    elif value2 < value3:
        return "Red"
    else:
        return "#4d4d4d"


def updatemarketwatchstrike(request):
    url = request.get_full_path
    print(url)
    params = str(url)[:-3].split('?')[1]
    params = str(params).split('*%*')

    df1 = pd.read_csv("C://interactive_brokers//media//Upstox_stocklist.csv")

    idx = len(df1)

    df1.set_value(idx, 'S_no', int(idx))
    df1.set_value(idx, 'ContractSymbol', str(params[0]))
    df1.set_value(idx, 'ExchangeSymbol', str(params[1]))
    df1.set_value(idx, 'Timeframe', params[2])
    df1.set_value(idx, 'no_of_lot', params[3])
    df1.set_value(idx, 'Quantity', params[4])
    df1.drop_duplicates(subset="ContractSymbol", keep="first", inplace=True)

    df1.to_csv("C://interactive_brokers//media//Upstox_stocklist.csv", index=False)
    error = ""
    return JsonResponse({"error": error})


def update_maindatabase(request):
    url = request.get_full_path
    print(url)
    params = str(url)[:-3].split('?')[1]
    params = str(params).split('$$')[0]

    print(params)

    try:
        df_StockDetail = pd.read_csv('C://interactive_brokers//media//Upstox_stocklist.csv')

        df_stock_index = df_StockDetail.index[df_StockDetail['ContractSymbol'] == str(params).split('*')[0]].tolist()

        df_StockDetail['Timeframe'].iloc[df_stock_index[0]] = str(params).split('*')[1]
        df_StockDetail['no_of_lot'].iloc[df_stock_index[0]] = str(params).split('*')[2]
        df_StockDetail['Quantity'].iloc[df_stock_index[0]] = str(params).split('*')[3]

        df_StockDetail = df_StockDetail.drop_duplicates()
        df_StockDetail.to_csv('C://interactive_brokers//media//Upstox_stocklist.csv', index=False)

    except:
        print("error in updating")

    error = ""
    return JsonResponse({"error": error})


def get_stocklistmkt(request):
    url = request.get_full_path
    print(url)
    params = str(url)[:-3].split('?')[1]
    nameofmktwatch = params.split('***')[1]
    params = params.split('***')[0]
    df1 = pd.DataFrame([[params]], columns=["ContractSymbol"])
    df1.to_csv("C://interactive_brokers//media//market_watchlist//" + nameofmktwatch + ".csv", index=False)
    error = ""
    return JsonResponse({"error": error})


def scrip_master_updation(request):
    url = request.get_full_path
    print(url)
    params = str(url)[:-3].split('?')[1]
    stocklist123 = pd.read_csv("C://interactive_brokers//media//market_watchlist//" + params.split('*&*')[0] + ".csv")
    main_stocklist = pd.read_csv("C://interactive_brokers//media//Upstox_stocklist.csv")
    stocks_name = []
    df_stocks = pd.DataFrame()
    stocks_name = str(stocklist123["ContractSymbol"].iloc[0]).split(',')
    for i in range(len(stocks_name)):
        df1 = pd.DataFrame([[str(stocks_name[i]), str(params.split('*&*')[0]), main_stocklist.loc[
            main_stocklist['ContractSymbol'] == str(stocks_name[i]), 'ExchangeSymbol'].iloc[0]]],
                           columns=["ContractSymbol", "name_of_marketwatch", "ExchangeSymbol"])
        df_stocks = pd.concat([df_stocks, df1])

    df_stocks.to_csv("C://interactive_brokers//media//UpstoxList_marketwatch.csv", index=False)
    error = ""
    return JsonResponse({"error": error})


def MarketWatch(request):
    return render(request, "first/marketwatchpage.html", {})


def VolumeRatio(request):
    return render(request, "first/volumeratio.html", {})


def screener_only_topgainer(request):
    results1screener = ""

    print("************************************************************")
    bid_ask_return = pd.read_csv(
        "C://interactive_brokers//media//BidSize_AskSize_Return.csv")
    bid_ask_return = bid_ask_return.sort_values(by='BidAskSizeRatio', ascending=False)
    the_table_pos = """<table border="1" class="table table-striped">
                <thead>
                <tr style="text-align: right;">
                  <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">S No.</th>
                  <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">Stocks</th>
                  <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">Bid Size</th>              
                  <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">Ask Size</th>
                  <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">Volume Ratio</th>
                  <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">Return</th>              

                </tr>
                </thead>
                <tbody>"""

    for k in range(0, len(bid_ask_return)):

        try:
            value1 = k + 1
            value2 = bid_ask_return['Stocks'].iloc[k]
            value3 = bid_ask_return['BidSize'].iloc[k]
            value4 = bid_ask_return['AskSize'].iloc[k]
            value5 = bid_ask_return['BidAskSizeRatio'].iloc[k]
            value6 = bid_ask_return['Return'].iloc[k]

            the_table_pos += """<tr>
                                        <td>%(value1)s</td>
                                        <td>%(value2)s</td>
                                        <td>%(value3)s</td>
                                        <td>%(value4)s</td>
                                        <td>%(value5)s</td>
                                        <td>%(value6)s</td>                                                                        


                                    </tr>""" % {'value1': value1,
                                                'value2': value2,
                                                'value3': value3,
                                                'value4': value4,
                                                'value5': value5,
                                                'value6': value6,

                                                }
        except:
            pass

    the_table_pos += """</tbody>
                            </table>"""

    results1screener += the_table_pos

    return HttpResponse(results1screener)


def screener_only(request):
    results1screener = ""
    try:
        print("************************************************************")
        df_marketwatch = pd.read_csv('C://interactive_brokers//media//UpstoxList_marketwatch.csv')
        df_pos = pd.read_csv('C://interactive_brokers//media//Upstox_stocklist.csv')
        df_pos = df_pos.drop_duplicates()
        df_marketwatch = df_marketwatch.drop_duplicates()

        if len(df_marketwatch) == 0:
            results1screener += "No Stock"
        else:
            the_table_pos = """<table border="1" class="table table-striped">
            <thead>
            <tr style="text-align: right;">
              <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">S No.</th>
              <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">Contract Symbol</th>
              <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">Exchange Symbol</th>              
              <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">Timeframe</th>
              <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">No. of Lots</th>
              <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">Quantity</th>              
              <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;"></th>
              <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;"></th>
            </tr>
            </thead>
            <tbody>"""

            for k in range(0, len(df_marketwatch)):

                try:
                    value1 = k + 1
                    value2 = df_marketwatch['ContractSymbol'].iloc[k]
                    value3 = df_pos.loc[df_pos["ContractSymbol"] == str(
                        df_marketwatch['ContractSymbol'].iloc[k]), 'ExchangeSymbol'].iloc[0]

                    value4 = int(df_pos.loc[df_pos["ContractSymbol"] == str(
                        df_marketwatch['ContractSymbol'].iloc[k]), 'Timeframe'].iloc[0])
                    value5 = int(df_pos.loc[df_pos["ContractSymbol"] == str(
                        df_marketwatch['ContractSymbol'].iloc[k]), 'no_of_lot'].iloc[0])
                    value6 = int(df_pos.loc[df_pos["ContractSymbol"] == str(
                        df_marketwatch['ContractSymbol'].iloc[k]), 'Quantity'].iloc[0])

                    value7 = df_marketwatch['ContractSymbol'].iloc[k]
                    value8 = df_marketwatch['ContractSymbol'].iloc[k]

                    the_table_pos += """<tr>
                                    <td>%(value1)s</td>
                                    <td>%(value2)s</td>
                                    <td>%(value3)s</td>
                                    <td>%(value4)s</td>
                                    <td>%(value5)s</td>
                                    <td>%(value6)s</td>                                                                        
                                    <td id=%(value7)s onclick="mainDataBase(this.id)"><a href= "javascript:void(0)">Remove</a></td>
                                    <td id=%(value8)s onclick="updateDataBase(this.id)"><a href= "javascript:void(0)">UpdateParameter</a></td>

                                </tr>""" % {'value1': value1,
                                            'value2': value2,
                                            'value3': value3,
                                            'value4': value4,
                                            'value5': value5,
                                            'value6': value6,
                                            'value7': value7,
                                            'value8': value8

                                            }
                except:
                    pass

            the_table_pos += """</tbody>
                        </table>"""

            results1screener += the_table_pos

    except:
        results1screener += "No Stock"
    return HttpResponse(results1screener)


def removeStock_maindatabase(request):
    url = request.get_full_path
    print(url)
    params = str(url)[:-3].split('?')[1]
    params = str(params).split('$$')[0]

    print(params)

    try:
        df_marketwatch = pd.read_csv('C://interactive_brokers//media//UpstoxList_marketwatch.csv')
        df_frommarket = pd.read_csv(
            "C://interactive_brokers//media//market_watchlist//" + str(
                df_marketwatch['name_of_marketwatch'].iloc[0]) + ".csv")

        df_marketwatch = df_marketwatch.drop_duplicates()
        df_marketwatch = df_marketwatch.loc[df_marketwatch['ContractSymbol'] != str(params)]
        df_marketwatch = df_marketwatch.drop_duplicates()
        df_marketwatch.to_csv('C://interactive_brokers//media//UpstoxList_marketwatch.csv', index=False)

        string_params = params + ','

        if string_params in df_frommarket['ContractSymbol'].iloc[0]:
            df_frommarket['ContractSymbol'].iloc[0] = df_frommarket['ContractSymbol'].iloc[0].replace(string_params, '')
        else:
            string_params = ',' + params
            df_frommarket['ContractSymbol'].iloc[0] = df_frommarket['ContractSymbol'].iloc[0].replace(string_params, '')

        df_frommarket.to_csv(
            "C://interactive_brokers//media//market_watchlist//" + str(
                df_marketwatch['name_of_marketwatch'].iloc[0]) + ".csv",
            index=False)

    except:
        print("error in Removal")

    error = ""
    return JsonResponse({"error": error})


