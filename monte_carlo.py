import pandas as pd
import datetime
import time
pd.set_option('display.max_columns', 500)

def monte_carlo_byday(trade_file_path, price_data_path, output_path):
        """
                This function will first read a file containing all trades (this file comes from the html produced by AmiBroker)
                Then it will  compute the day-end pnl each day (daily close data should be provided via price_data_path)
                It will finally produce a list of daily pnl.
                """
        trade_data = pd.read_csv(trade_file_path)

        # print(trade_data.columns)

        # deal with date & time
        # print(trade_data)
        def get_datetime(date_str):
            date_format = '%m/%d/%Y %I:%M:%S %p'
            parsed_date = pd.Timestamp(2000, 1, 1)
            try:
                parsed_date = pd.Timestamp(
                    datetime.datetime.strptime(date_str, date_format)
                )
                return parsed_date
            except Exception:
                pass

            date_format = '%m/%d/%Y %H:%M'
            parsed_date = pd.Timestamp(2000, 1, 1)
            try:
                parsed_date = pd.Timestamp(
                    datetime.datetime.strptime(date_str, date_format)
                )
                return parsed_date
            except Exception:
                pass

            date_format = '%d/%m/%Y %I:%M:%S %p'
            try:
                parsed_date = pd.Timestamp(
                    datetime.datetime.strptime(date_str, date_format)
                )
                return parsed_date
            except Exception:
                pass

            date_format = '%m/%d/%Y %H:%M:%S'
            try:
                parsed_date = pd.Timestamp(
                    datetime.datetime.strptime(date_str, date_format)
                )
                return parsed_date
            except Exception:
                pass

            date_format = '%d/%m/%Y %H:%M:%S'
            try:
                parsed_date = pd.Timestamp(
                    datetime.datetime.strptime(date_str, date_format)
                )
                return parsed_date
            except Exception:
                pass

            date_format = '%d/%m/%Y %I:%M:%S %p'
            try:
                parsed_date = pd.Timestamp(
                    datetime.datetime.strptime(date_str, date_format)
                )
                return parsed_date
            except Exception:
                pass

            date_format = '%Y-%m-%d %H:%M:%S'
            try:
                parsed_date = pd.Timestamp(
                    datetime.datetime.strptime(date_str, date_format)
                )
                return parsed_date
            except Exception:
                pass

            print("%s can't be converted!" % date_str)

        def judge_direction(row):
            if 'LONG' in row['Trade'].upper():
                return 1
            if 'SHORT' in row['Trade'].upper():
                return -1

        trade_data['Date'] = trade_data.apply(lambda x: get_datetime(x['Date']), axis=1)
        trade_data = trade_data.rename({'Ex. Date': 'Ex.Date'}, axis=1)
        # print(trade_data)
        trade_data['Ex.Date'] = trade_data.apply(lambda x: get_datetime(x['Ex.Date']), axis=1)
        trade_data['Trade'] = trade_data.apply(judge_direction, axis=1)
        trade_data = trade_data.sort_values(by=['Date'], ascending=True)
        trade_data = trade_data[['Trade', 'Date', 'Price', 'Ex.Date', 'Ex. Price', 'Profit', 'Shares']]
        # print(trade_data)

        # read index day-end data
        index_data = pd.read_csv(price_data_path,
                                 parse_dates=['Dates'],
                                 date_parser=lambda x: pd.datetime.strptime(x, '%d/%m/%Y'))
        index_data = index_data.sort_values(by=['Dates'], ascending=True)
        index_data = index_data.rename({'Dates': 'Date'}, axis=1)
        # index_data will have two columns: Date, PX_LAST

        # extract relevant data
        start_date = pd.Timestamp(trade_data['Date'][0].date())  # Timestamp('2015-01-06 00:00:00')
        end_date = pd.Timestamp(trade_data['Ex.Date'].iloc[-1].date())
        pnl_data = pd.DataFrame({'Date': [], 'PnL': []})

        for d in index_data['Date']:
            if d < start_date or d > end_date:
                continue
            yest_close = index_data.iloc[list(index_data[index_data['Date'] == d].index)[0] - 1][1]
            yest = index_data.iloc[list(index_data[index_data['Date'] == d].index)[0] - 1][0]
            today_close = list(index_data[index_data['Date'] == d]['PX_LAST'])[0]
            print('Today date = %s, yest=%s, yest_close=%.1f, today_close=%.1f' % (d, yest, yest_close, today_close))
            # e.g. d = 2018-09-16
            day_end = pd.Timestamp(
                datetime.datetime.strptime(
                    d.date().strftime('%Y-%m-%d') + " 16:30:01", '%Y-%m-%d %H:%M:%S'
                ))  # e.g.  2018-09-16 23:59:59
            day_start = pd.Timestamp(
                datetime.datetime.strptime(
                    yest.date().strftime('%Y-%m-%d') + " 16:30:01", '%Y-%m-%d %H:%M:%S'
                ))  # e.g.  2018-09-16 00:00:00
            # print('day_start=%s, day_end=%s' % (day_start, day_end))
            cond1 = trade_data['Date'] <= day_end
            cond2 = trade_data['Ex.Date'] >= day_start
            today_trade_data = trade_data[cond1 & cond2]
            print(today_trade_data)
            # time.sleep(10000)

            # print('today_trade_data (before) = \n%s\n' % today_trade_data)

            # find those with open date earlier than day_start and modify their open price to be yesterday's close

            def update_profit(row):
                if row['Ex.Date'] > day_end and row['Date'] < day_start:  # a trade crosses multiple days
                    pnl = row['Trade'] * (today_close - yest_close)
                    return pnl * row['Shares']
                elif row['Ex.Date'] > day_end:
                    pnl = row['Trade'] * (today_close - row['Price']) - \
                          0.5 * (row['Trade'] * (row['Ex. Price'] - row['Price']) - row['Profit'])
                    return pnl * row['Shares']
                elif row['Date'] < day_start:
                    pnl = row['Trade'] * (row['Ex. Price'] - yest_close) - \
                          0.5 * (row['Trade'] * (row['Ex. Price'] - row['Price']) - row['Profit'])
                    return pnl * row['Shares']
                else:
                    return row['Profit'] * row['Shares']

            # today_trade_data.loc[:, 'Profit'] = today_trade_data.apply(update_profit_from_open, axis=1)
            # today_trade_data.loc[:, 'Profit'] = today_trade_data.apply(update_profit_from_close, axis=1)
            today_trade_data.loc[:, 'Profit'] = today_trade_data.apply(update_profit, axis=1)
            # today_trade_data['Ex. Price'] = today_trade_data.apply(assign_close_price, axis=1)
            # print('today_trade_data (after) = \n%s\n' % today_trade_data)

            today_pnl = today_trade_data['Profit'].sum()
            pnl_data = pnl_data.append(pd.DataFrame({'Date': [d], 'PnL': [today_pnl]}))
            # print('today pnl = %.1f' % today_pnl)
            # print('----------------------------------------------------------------------')

            # time.sleep(2)
        pnl_data.to_csv(output_path, index=None)
        print(pnl_data)
        print(output_path)

if __name__ == "__main__":
    trade_file_path = "D:\\test\\HSI;15min;BBandBreakOut;Test42-3m_3m2013.csv"
    price_data_path = "HI1.csv"
    monte_carlo_byday(trade_file_path, price_data_path)