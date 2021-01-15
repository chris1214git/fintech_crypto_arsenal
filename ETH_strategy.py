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
                'pairs': ['ETH-USDT'],
            },
        }
        self.time_base = 30
        self.period = self.time_base * 60
        self.options = {}

        # user defined class attribute
        self.last_type = 'sell'
        self.last_cross_status = None
        self.close_price_trace = np.array([])
        self.ma_short_buy = 5
        self.ma_short_sell = 15

        self.buy_rate = 0.002
        self.sell_rate = 0.01
        self.stock_volume = 0
        self.stock_base = 12000
        self.last_price = float('inf')


    # called every self.period
    def trade(self, information):

        exchange = list(information['candles'])[0]
        pair = list(information['candles'][exchange])[0]
        close_price = information['candles'][exchange][pair][0]['close']
        present_price = information['candles'][exchange][pair][0]['close']
        high_price = information['candles'][exchange][pair][0]['high']

        # add latest price into trace
        self.close_price_trace = np.append(self.close_price_trace, [float(close_price)])

        # calculate current ma cross status
        s_ma_buy = talib.SMA(self.close_price_trace, self.ma_short_buy)[-1]
        s_ma_sell = talib.SMA(self.close_price_trace, self.ma_short_sell)[-1]
        Log('info: ' + str(information['candles'][exchange][pair][0]['time']) + ', ' + str(information['candles'][exchange][pair][0]['open']) + ', assets' + str(self['assets'][exchange]['ETH']) + ',USDT' + str(self['assets'][exchange]['USDT']))

       
        # below MA buy
        if (s_ma_buy - present_price)/s_ma_buy >= self.buy_rate and self['assets'][exchange]['USDT'] > 0 and self.last_price > present_price:
            Log('buying, opt1:' + self['opt1'])
            self.last_type = 'buy'
            buy_volume = int(self.stock_base * (s_ma_buy - present_price)/s_ma_buy)
            self.last_price = present_price

            self.stock_volume += buy_volume

            return [
                {
                    'exchange': exchange,
                    'amount':  buy_volume ,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        # beyond MA sell
        elif (present_price - s_ma_sell)/s_ma_sell >= self.sell_rate and self.stock_volume > 0 and self.last_price < present_price:
            Log('selling, ' + exchange + ':' + pair)
            self.last_type = 'sell'

            sell_volume = (int((self.stock_base * (present_price - s_ma_sell)/s_ma_sell + 0.25)))
            self.last_price = present_price

            if sell_volume <= self.stock_volume:
                sell = sell_volume
                self.stock_volume -= sell_volume
                return [
                    {
                        'exchange': exchange,
                        'amount': -sell,
                        'price': -1,
                        'type': 'MARKET',
                        'pair': pair,
                    }
                ]
            else:
                sell = self.stock_volume
                stock_volume = 0
                return [
                    {
                        'exchange': exchange,
                        'amount': -sell,
                        'price': -1,
                        'type': 'MARKET',
                        'pair': pair,
                    }
                ]
         # 15%°±·l
        elif present_price < high_price * 0.85 and self.stock_volume > 0:
            Log('selling, ' + exchange + ':' + pair)
            self.last_type = 'sell'

            sell_volume = self.stock_volume
            self.last_price = present_price

            sell = sell_volume
            self.stock_volume = 0
            return [
                {
                    'exchange': exchange,
                    'amount': -sell,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        
        return []
