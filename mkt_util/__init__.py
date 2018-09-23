import json
import numpy as np
import pandas as pd
import time
import urllib
# import av


access = 'RF20IXY356J04AWD'

def get_intraday_prices(ticker: str, interval: str='1min',
                        outputsize: str='full') -> pd.DataFrame:
    """
    Gets intraday prices fof the given ticker
    :param ticker: (str) in the form of 'AAPL' or 'CTC-A.TO' or '.SPX'
    :param interval: (str) choice of '1min', '5min', '15min', '30min', '60min'
    :param outputsize: 'compact' get 100 data points, 'full' get 5 days of
        intraday data at the interval specified
    :return: pandas DataFrame
    """
    x_col_head = 'Time Series (' + interval + ')'
    url = ('https://www.alphavantage.co/query?'
           + 'function=TIME_SERIES_INTRADAY'
           + '&symbol=' + ticker
           + '&interval=' + interval
           + '&outputsize=' + outputsize
           + '&apikey=' + access)
    req = urllib.request.urlopen(url)
    x = json.loads(req.read().decode('utf-8'))
    intraday = pd.DataFrame(x[x_col_head],
                            dtype=np.float64).transpose()
    intraday.index = pd.to_datetime(intraday.index, dayfirst=True)
    intraday.columns = ['open', 'high', 'low', 'close', 'volume']
    return intraday


def get_daily_prices(ticker: str, output='compact') ->pd.DataFrame:
    """
    Gets the daily prices from alphavantage.co. Wait at least 12s between data
    requests.
    :param ticker: (str) in the form of 'AAPL' or 'CTC-A.TO' or '.SPX'
    :param output: 'compact' is 100 datapoints, 'full' is 20 years
    :return: pandas DataFrame
    """
    url = ('https://www.alphavantage.co/query?'
           + 'function=TIME_SERIES_DAILY_ADJUSTED'
           + '&symbol=' + ticker
           + '&outputsize=' + output
           + '&apikey=' + access)
    req = urllib.request.urlopen(url)
    x = json.loads(req.read().decode('utf-8'))
    daily = pd.DataFrame(x['Time Series (Daily)'],
                         dtype=np.float64).transpose()
    daily.index = pd.to_datetime(daily.index)
    daily.columns = ['open', 'high', 'low', 'close', 'adjusted close', 'volume',
                     'dividend amount', 'split coeff']
    return daily


class Security(object):
    """ security with historical intraday and daily price data """
    def __init__(self, ticker: str, intraday_prices: pd.DataFrame=None,
                 daily_prices: pd.DataFrame=None, output: str='compact'):
        """ Takes in a pandas data frame for the historical prices"""
        self.ticker = ticker
        self.intraday_prices = intraday_prices
        self.daily_prices = daily_prices

    def get_intraday(self):
        return self.intraday_prices

    def get_daily(self):
        return self.daily_prices


def create_fix_sprd_rule(df: pd.DataFrame, short_hurdle: float = 1.15,
                         short_cover: float = 1.01,
                         long_hurdle: float = 0.85,
                         long_cover: float =0.99 ) -> pd.DataFrame:
    """ Create the trade rule based on the fixed entry trade rules (hurdles)
    and exit trade rules (cover). Unlike rolling averages or medians, the rules
    are tied to a single, fixed reference level, e.g. average spread over the
    last two years.
    :param df:
    :param short_hurdle:
    :param short_cover:
    :param long_hurdle:
    :param long_cover:
    :return:
    """
    go_short = df['spread'].mean() * short_hurdle
    cover_short = df['spread'].mean() * short_cover
    go_long = df['spread'].mean() * long_hurdle
    cover_long = df['spread'].mean() * long_cover
    print('Short above: {:.2f}; Cover at {:.2f}'.format(go_short, cover_short))
    print('Long below: {:.2f}; Cover at {:.2f}'.format(go_long, cover_long))
    trade = 'NoTrade'
    trade_list=[]
    trade_tf = []
    for row in df.itertuples():
        if trade == 'NoTrade':
            if row[3] >= go_short:
                trade = 'Short'
                trade_tf.append(trade)
                trade_list.append(-1)
            elif row[3] <= go_long:
                trade = 'Long'
                trade_tf.append(trade)
                trade_list.append(1)
            else:
                trade_list.append(0)
                trade_tf.append(trade)
        elif trade == 'Short':
            if row[3] > cover_short:
                trade_tf.append(trade)
                trade_list.append(-1)
            else:
                trade = 'NoTrade'
                trade_tf.append(trade)
                trade_list.append(0)
        elif trade == 'Long':
            if row[3] < cover_long:
                trade_tf.append(trade)
                trade_list.append(1)
            else:
                trade = 'NoTrade'
                trade_tf.append('NoTrade')
                trade_list.append(0)
    df['Trade'] = trade_list
    df['Trade Dir'] = trade_tf
    return df

if __name__ == '__main__':
    ticker = 'aapl'
    intraday = get_intraday_prices(ticker)
    time.sleep(12)
    daily = get_daily_prices(ticker)
    aapl = Security('aapl', intraday, daily)
