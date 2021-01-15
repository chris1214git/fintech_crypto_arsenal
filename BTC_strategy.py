class Strategy():
    # option setting needed
    def __setitem__(self, key, value):
        self.options[key] = value

    # option setting needed
    def __getitem__(self, key):
        return self.options.get(key, '')

    def __init__(self):
        # strategy property
        self.subscribedBooks = {
            'Binance': {
                'pairs': ['BTC-USDT'],
            },
        }
        self.period =  10 * 60 # 10m k bar
        self.options = {}

        # user defined class attribute
        self.last_type = 'sell'
        self.last_cross_status = None
        self.close_price_trace = np.array([])
        self.median_trace = np.array([])
        # self.close_price_trace = np.array([20800]*320)
        # self.median_trace = np.array([20800]*320)
        self.mmi_period = 25 * 6
        self.ma_long = 160 * 6
        self.ma_short = 120 * 6
        self.ma_long = 80 * 6
        self.ma_short = 35 * 6
        self.stop_loss = 0.07
        self.UP = 1
        self.DOWN = -1
        self.cur_maximum = -1
        self.cur_minimum = 10**10
        self.buy_price = -1
        self.first_day = True
        self.first_sell = True
        

    def get_current_ma_cross(self):
        s_ma = talib.SMA(self.close_price_trace, int(self.ma_short))[-1]
        l_ma = talib.SMA(self.close_price_trace, int(self.ma_long))[-1]
        if np.isnan(s_ma) or np.isnan(l_ma):
            return None
        if s_ma > l_ma:
            return self.UP
        return self.DOWN
    
    def cross_over(self, s, l):
        if len(s) < 2:
            return 0
        if s[-2] < l[-2] and s[-1] >= l[-1]:
            return self.UP
        if s[-2] > l[-2] and s[-1] <= l[-1]:
            return self.DOWN
        return 0
    def get_cross_over(self):
        s = talib.SMA(self.close_price_trace, self.ma_short)
        l = talib.SMA(self.close_price_trace, self.ma_long)
        self.s = s
        self.l = l
        if len(s) < 2:
            return 0
        if s[-2] <= l[-2] and s[-1] > l[-1]:
            return self.UP
        if s[-2] >= l[-2] and s[-1] < l[-1]:
            return self.DOWN
        return 0
    def get_MMI(self, period=20):
        p1 = self.close_price_trace >  self.median_trace
        p2 = np.append(np.array([np.nan]), self.close_price_trace[:-1]) > self.median_trace

        mmi = np.mean((p1 & p2).astype(int)[-period:])
        # mmi = (p1 & p2).astype(int).rolling(period).mean()
        return mmi

    # called every self.period
    def trade(self, information):

        exchange = list(information['candles'])[0]
        pair = list(information['candles'][exchange])[0]
        close_price = information['candles'][exchange][pair][0]['close']
        open_price = information['candles'][exchange][pair][0]['open']
        # update price
        
        if self.first_day:
            self.close_price_trace = np.array( [float(close_price) - 100]* self.ma_long)
            self.median_trace = np.array( [float(close_price) - 100]* self.ma_long)
            # self.first_day = False
        else:
            self.close_price_trace = np.append(self.close_price_trace, [float(close_price)])
            self.close_price_trace = self.close_price_trace[-int(self.ma_long)*2:]
            self.median_trace = np.append(self.median_trace, np.median(self.close_price_trace[-self.mmi_period:]))
            self.median_trace = self.median_trace[-int(self.ma_long)*2:]

        # get asset info
        pair = list(information['candles'][exchange])[0] #BTC-USDT
        targetCurrency = pair.split('-')[0]  #BTC
        baseCurrency = pair.split('-')[1]  #USDT
        targetCurrency_amount = self['assets'][exchange][targetCurrency] 
        baseCurrency_amount = self['assets'][exchange][baseCurrency] 

        # time
        year = (information['candles'][exchange][pair][0]['time'])[:4]
        month = (information['candles'][exchange][pair][0]['time'])[5:7]
        day = (information['candles'][exchange][pair][0]['time'])[8:10]
        hour = (information['candles'][exchange][pair][0]['time'])[11:13]
        minute = (information['candles'][exchange][pair][0]['time'])[14:16]
        
        # action amount
        long_amount = float(baseCurrency_amount) / float(close_price) * 0.95
        # close_position_amount = -float(targetCurrency_amount)*0.9
        # short_amount = - float(baseCurrency_amount) / float(close_price) * 0.9
        short_amount = -float(targetCurrency_amount) * 1#*2

        cur_cross = self.get_cross_over()
        filter_mmi = self.get_MMI(period=self.mmi_period)

        if self.last_type == 'buy':
            self.cur_maximum = close_price if close_price > self.cur_maximum else self.cur_maximum
        drop_down = (self.cur_maximum - close_price) / self.cur_maximum

        # if hour == '00' and minute == '00' and int(day)%5==0: #day == '29' and 
        if hour == '00' and minute == '00' and day[-1] == '1': #day == '29' and 
            Log('{}-{}-{}, {}:{}'.format(year, month, day, hour, minute))
            Log('Asset {}: {}'.format(str(targetCurrency), str(targetCurrency_amount)))
            Log('Asset {}: {}'.format(str(baseCurrency), str(baseCurrency_amount)))
            
            # Log('{} {} {}, {}:{}'.format(cur_cross, cur_cross == self.UP, 9, hour, minute))
            # Log('close {} {} '.format(len(self.close_price_trace), self.close_price_trace))
            # Log('short {} {} '.format(len(self.s), self.s))
            # Log('{} '.format(s_ma))
            
            # Log( 'close_price' + str(close_price))
            # Log( 'buy_amount' + str(buy_amount))
            # Log( 'sell_amount' + str(sell_amount))
        if self.first_day:
            self.first_day = False
            self.last_type = 'buy'
            self.buy_price = close_price
            return [
                {
                    'exchange': exchange,
                    'amount': long_amount,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        # cross up
        if self.last_type == 'sell' and cur_cross == self.UP and filter_mmi>0.5:            
            Log('buying:' + str(long_amount))    # self['opt1']
            self.last_type = 'buy'
            self.buy_price = close_price
            return [
                {
                    'exchange': exchange,
                    'amount': long_amount,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        # cross down / rolling stop loss
        # elif self.last_type == 'buy'  and ((cur_cross == self.DOWN and self.first_sell == False) or drop_down > self.stop_loss):
        elif self.last_type == 'buy'  and ((cur_cross == self.DOWN and self.first_sell == False) or drop_down > self.stop_loss):
            Log('drop donw, cur_cross:' + str(cur_cross) + ', '+ str(drop_down))  # Log('selling, ' + exchange + ':' + pair)
            
            Log('selling:' + str(short_amount))  # Log('selling, ' + exchange + ':' + pair)
            self.first_sell = False
            self.last_type = 'sell'
            self.buy_price = -1
            self.cur_maximum = -1

            return [
                {
                    'exchange': exchange,
                    'amount': short_amount,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        return []
