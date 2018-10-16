import pandas as pd
import numpy as np
import os
import math
import time
from tqdm import tqdm
import datetime
from bs4 import BeautifulSoup
import multiprocessing
import re
import random
import statsmodels.tsa.stattools as ts
from matplotlib import pyplot as plt
from shutil import copyfile
pd.set_option('display.max_columns', 500)


class CalculateCustomMetrics:
    def __init__(self, strategy_root_path, HSI_price_path,
                 monte_carlo=False, run_monte_carlo=False):
        # strategy_root_path should contain a list of strategies. E.g.
        """
                strategy_root_path
                    strategy_result_1
                        trades.html
                        stats.html
                        ...
                    strategy_result_2
                        trades.html
                        stats.html
                        ...
                    strategy_result_3
                        trades.html
                        stats.html
                        ...
                """
        self.strategy_root_path = strategy_root_path
        self.daily_pnl_path = os.path.join(self.strategy_root_path, 'daily_pnl.csv')
        self.trades_path = os.path.join(self.strategy_root_path, 'trades.csv')

        self.HSI_price_path = HSI_price_path
        self.monte_carlo = monte_carlo  # if do the Monte Carlo
        self.run_monte_carlo = run_monte_carlo  # suppose to substitute the above one
        self.get_step1_summary = True

    def generate_my_metrics(self):
        """
        This serves as a comprehensive function that will put all our self-defined metrics into one sheet.
        Must ensure that "daily_pnl.csv" and "trades.csv" are in place
        :return:
        """
        # check if 'daily_pnl.csv' exists
        if not os.path.exists(os.path.join(self.strategy_root_path, 'daily_pnl.csv')):
            CalculateCustomMetrics.generate_trade_csv_from_html(self.strategy_root_path)
            CalculateCustomMetrics.generate_daily_pnl(os.path.join(self.strategy_root_path, 'trades.csv'),
                                                      self.HSI_price_path,
                                                      os.path.join(self.strategy_root_path, 'daily_pnl.csv')
                                                      )

        daily_pnl = pd.read_csv(self.daily_pnl_path, parse_dates=['Date'])
        trades = pd.read_csv(self.trades_path, parse_dates=['Date', 'Ex.Date'],
                             date_parser=lambda x: pd.datetime.strptime(x, '%m/%d/%Y %I:%M:%S %p'))
        equity_curve = daily_pnl['PnL'].cumsum()
        daily_pnl.loc[:, 'month'] = daily_pnl['Date'].apply(lambda x: x.month)
        daily_pnl.loc[:, 'year'] = daily_pnl['Date'].apply(lambda x: x.year)
        monthly_pnl = daily_pnl.groupby(by=['year', 'month']).sum()

        k_ratio = CalculateCustomMetrics.cal_k_ratio(equity_curve)
        slope = CalculateCustomMetrics.cal_slope(equity_curve)
        gpr = CalculateCustomMetrics.cal_GPR(daily_pnl, method=1)
        avg_hold_min = CalculateCustomMetrics.cal_avg_hold_min(trade_data=trades)
        hhi_daily_10, hhi_trade_10, hhi_daily_5, hhi_trade_5 = CalculateCustomMetrics.cal_pnl_hhi(daily_pnl, trades)
        _, max_dd_days = CalculateCustomMetrics.cal_mdd_n_mdd_period(equity_curve)
        expectancy = CalculateCustomMetrics.cal_expectancy(trades['Profit'])

        my_metrics = pd.DataFrame({'Name': [], 'Value': []})
        my_metrics = my_metrics.append(pd.DataFrame({'Name': ['K Ratio (Zephyr)'], 'Value': [k_ratio]}))
        my_metrics = my_metrics.append(pd.DataFrame({'Name': ['Slope'], 'Value': [slope]}))
        my_metrics = my_metrics.append(pd.DataFrame({'Name': ['GPR'], 'Value': [gpr]}))
        my_metrics = my_metrics.append(pd.DataFrame({'Name': ['Average Hold Minutes'], 'Value': [avg_hold_min]}))
        my_metrics = my_metrics.append(pd.DataFrame({'Name': ['HHI Trade 10'], 'Value': [hhi_trade_10]}))
        my_metrics = my_metrics.append(pd.DataFrame({'Name': ['HHI Trade 5'], 'Value': [hhi_trade_5]}))
        my_metrics = my_metrics.append(pd.DataFrame({'Name': ['HHI Daily 10'], 'Value': [hhi_daily_10]}))
        my_metrics = my_metrics.append(pd.DataFrame({'Name': ['HHI Daily 5'], 'Value': [hhi_daily_5]}))
        my_metrics = my_metrics.append(pd.DataFrame({'Name': ['Max. DD Days'], 'Value': [max_dd_days]}))
        my_metrics = my_metrics.append(pd.DataFrame({'Name': ['Expectancy'], 'Value': [expectancy]}))
        my_metrics.to_csv(os.path.join(self.strategy_root_path, 'my_metrics.csv'), index=None)

        # CalculateCustomMetrics.cal_monte_carlo_one_strategy(
        #     self.strategy_root_path, mc_times=20, use_daily_pnl=True, use_trade_pnl=True)
        acf_path = os.path.join(self.strategy_root_path, 'acf_pacf')
        [trades_acf, trades_pacf, trades_pass_adf] = \
            CalculateCustomMetrics.cal_acf_pacf(trades['Profit'], output_path=acf_path, output_file_prefix='trade')
        [daily_pnl_acf, daily_pnl_pacf, daily_pnl_pass_adf] = \
            CalculateCustomMetrics.cal_acf_pacf(daily_pnl['PnL'], output_path=acf_path, output_file_prefix='daily')
        [monthly_pnl_acf, monthly_pnl_pacf, monthly_pnl_pass_adf] = \
            CalculateCustomMetrics.cal_acf_pacf(monthly_pnl['PnL'], output_path=acf_path, output_file_prefix='monthly')

        # first make a copy
        html_raw_path = os.path.join(self.strategy_root_path, 'stats_raw.html')
        if not os.path.exists(html_raw_path):
            copyfile(os.path.join(self.strategy_root_path, 'stats.html'),
                     os.path.join(self.strategy_root_path, 'stats_raw.html'))

        # output the result
        # self-defined metrics
        def get_inside_table_line(title, name, content):
            return "<tr><TH TITLE='" + str(title) + "'>" + str(name) + "</TH><TD>" + str(content) + "</TD></tr>\n"
        inside_table_line = '<TR><TD COLSPAN=4><hr size=1></TD></TR>\n'
        inside_table_line += '<TR><TH><b>My Metrics</b></TH></TR>\n'
        inside_table_line += get_inside_table_line('K Ratio (Zephyr)', 'K Ratio (Zephyr)', "{:.2f}".format(k_ratio))
        inside_table_line += get_inside_table_line('Slope', 'Slope', "{:.2f}".format(slope))
        inside_table_line += get_inside_table_line('Gain-to-Pain Ratio (>1.5 good)', 'GPR', "{:.2f}".format(gpr))
        inside_table_line += get_inside_table_line(
            'Average Hold Minutes', 'Average Hold Minutes', "{:.1f}".format(avg_hold_min))
        inside_table_line += get_inside_table_line(
            'Herfindahl-Hirschman Index by first 10 trades', 'HHI Trade 10', "{:.2f}".format(hhi_trade_10))
        inside_table_line += get_inside_table_line(
            'Herfindahl-Hirschman Index by first 5 trades', 'HHI Trade 5', "{:.2f}".format(hhi_trade_5))
        inside_table_line += get_inside_table_line(
            'Herfindahl-Hirschman Index by first 10 days\' pnl', 'HHI Daily 10', "{:.2f}".format(hhi_daily_10))
        inside_table_line += get_inside_table_line(
            'Herfindahl-Hirschman Index by first 5 days\' pnl', 'HHI Daily 5', "{:.2f}".format(hhi_daily_5))
        inside_table_line += get_inside_table_line('Max Drawdown Days', 'Max. DD Days', "{:.2f}".format(max_dd_days))
        inside_table_line += get_inside_table_line('Expectancy (>0.1 good)', 'Expectancy', "{:.2f}".format(expectancy))

        # monte carlo results
        mc_daily_path = os.path.join(self.strategy_root_path, 'MonteCarlo2', 'daily.xls')
        mc_daily_data = pd.read_excel(mc_daily_path, sheet_name='All year')
        mc_trade_path = os.path.join(self.strategy_root_path, 'MonteCarlo2', 'trades.xls')
        mc_trade_data = pd.read_excel(mc_trade_path, sheet_name='All year')
        mc_table = '</br><hr size=1>My Monte Carlo Results (Daily)</br><TABLE  id="table_content">\n'

        use_trade_data = False
        for i in range(len(mc_daily_data.index) + 1):
            mc_table += '<tr>'
            for j in range(len(mc_daily_data.columns)):
                if i == 0:  # table head
                    if j == 0:
                        mc_table += '<td></td>'
                    mc_table += '<th>' + str(mc_daily_data.columns[j]) + '</th>'
                else:  # table body
                    if j == 0:
                        mc_table += '<th>' + mc_daily_data.index[i-1] + '(Daily)'
                        if mc_daily_data.index[i-1] in mc_trade_data.index:
                            mc_table += '</br>' + mc_daily_data.index[i-1] + '(Trade)'
                            use_trade_data = True
                        mc_table += '</th>'
                    mc_table += '<td>%.3f' % mc_daily_data.iloc[i-1, j]
                    if use_trade_data:
                        mc_table += '</br>%.3f' % mc_trade_data.loc[mc_daily_data.index[i-1], mc_daily_data.columns[j]]
                    mc_table += '</td>'
            mc_table += '</tr>\n'
            use_trade_data = False
        mc_table += '</table>\n'

        # acf & pacf
        new_table_acf = '</br><hr size=2>My ACF/PACF Results</br><TABLE id="table_content">\n'
        new_table_acf += '<tr><th></th><th>ADF</th>'
        for i in range(len(trades_acf)):
            new_table_acf += '<th>Lag' + str(i) + '</th>'
        new_table_acf += '</tr>\n'
        temp_dict = {
            'ACF (Trades)': trades_acf, 'PACF (Trades)': trades_pacf,
            'ACF (Daily)': daily_pnl_acf, 'PACF (Daily)': daily_pnl_pacf,
            'ACF (Monthly)': monthly_pnl_acf, 'PACF (Monthly)': monthly_pnl_pacf,
        }
        pass_adf_dict = {
            'ACF (Trades)': trades_pass_adf, 'PACF (Trades)': trades_pass_adf,
            'ACF (Daily)': daily_pnl_pass_adf, 'PACF (Daily)': daily_pnl_pass_adf,
            'ACF (Monthly)': monthly_pnl_pass_adf, 'PACF (Monthly)': monthly_pnl_pass_adf,
        }
        for name in ['ACF (Trades)', 'PACF (Trades)', 'ACF (Daily)', 'PACF (Daily)', 'ACF (Monthly)', 'PACF (Monthly)']:
            data = temp_dict[name]
            pass_adf = pass_adf_dict[name]
            new_table_acf += '<tr><th>' + name + '</th><td>' + ('Y' if pass_adf else 'N') + '</td>'
            for c in data:
                new_table_acf += '<td>' + '{:.3f}'.format(c) + '</td>'
            new_table_acf += '\n'
        new_table_acf += '</table>\n'

        # css style
        css = """
#table_content {
    font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;
    border-collapse: collapse;
    width: 100%;
}

#table_content td{
    border: 1px solid #ddd;
    padding: 2px;
}
#table_content tr{
    font-size: 16px;
}

#table_content tr:nth-child(even){background-color: #f2f2f2;}


#table_content th {
    padding-top: 5px;
    padding-bottom: 5px;
    text-align: left;
    background-color: #4CAF50;
    border: 1px solid #ddd;
    color: white;
}
"""

        # insert the new content into original html
        html_content = ''
        with open(html_raw_path, 'r') as f:
            html_content = f.read()
            html_content = html_content.lower()
        table_end = html_content.rfind('</table>')
        new_html = html_content[0:table_end] + inside_table_line + '</table>' + \
                   mc_table + new_table_acf + \
                   html_content[table_end + len('</table>'):]
        style_end = new_html.rfind('</style>')
        new_html = new_html[0:style_end] + css + new_html[style_end:]


        with open(os.path.join(self.strategy_root_path, 'stats.html'), 'w') as f:
            f.write(new_html)

    def generate_summary(self):
        strategy_list = []
        strategy_df = pd.DataFrame()
        for s in os.listdir(self.strategy_root_path):
            s_path = os.path.join(self.strategy_root_path, s)
            # print(s_path)
            if os.path.isdir(s_path):
                strategy_list.append(s)
                stats_str = ''
                with open(os.path.join(s_path, 'stats.html'), 'r') as f:
                    stats_str = f.read().replace('\n', '')
                temp = pd.read_html(stats_str)
                if temp is not None and len(temp) > 1:
                    stats_table = temp[1]
                    stats_table = stats_table.drop(0, axis=0)
                    # print(stats_table.iloc[20, :])
                    stats_table.iloc[20, 0] = stats_table.iloc[20, 0] + ' Win'
                    stats_table.iloc[19, 0] = stats_table.iloc[19, 0] + ' Win'
                    stats_table.iloc[29, 0] = stats_table.iloc[29, 0] + ' Loss'
                    stats_table.iloc[28, 0] = stats_table.iloc[28, 0] + ' Loss'
                    stats_table = stats_table.set_index(0)
                    stats_table = stats_table.dropna()
                    # print(stats_table)
                    stats_table_new = pd.DataFrame({
                        s: list(stats_table.iloc[:, 0])
                    }, index=list(stats_table.index))
                    # print(stats_table.loc['Net Profit', 2])
                    stats_table_new.loc['Net Profit (Long)'] = [stats_table.loc['Net Profit', 2]]
                    # print(stats_table_new)
                    stats_table_new.loc['Net Profit (Short)'] = [stats_table.loc['Net Profit', 3]]

                    # pattern = re.compile(r"\((\d+)\)")
                    # print(stats_table)
                    winners_str = stats_table.loc['Winners', 1]
                    winners_str = winners_str.replace(' ', '').replace('%', '')
                    stats_table_new.loc['Winners No'] = [int(winners_str.split('(')[0])]
                    stats_table_new.loc['Winners %'] = [float(winners_str.split('(')[1].replace(')', ''))]
                    losers_str = stats_table.loc['Losers', 1]
                    losers_str = losers_str.replace(' ', '').replace('%', '')
                    stats_table_new.loc['Losers No'] = [int(losers_str.split('(')[0])]
                    stats_table_new.loc['Losers %'] = [float(losers_str.split('(')[1].replace(')', ''))]

                    winners_long_str = stats_table.loc['Winners', 2]
                    winners_long_str = winners_long_str.replace(' ', '').replace('%', '')
                    stats_table_new.loc['Winners No (Long)'] = [int(winners_long_str.split('(')[0])]
                    stats_table_new.loc['Winners % (Long)'] = [float(winners_long_str.split('(')[1].replace(')', ''))]
                    losers_long_str = stats_table.loc['Losers', 2]
                    losers_long_str = losers_long_str.replace(' ', '').replace('%', '')
                    stats_table_new.loc['Losers No (Long)'] = [int(losers_long_str.split('(')[0])]
                    stats_table_new.loc['Losers % (Long)'] = [float(losers_long_str.split('(')[1].replace(')', ''))]

                    winners_short_str = stats_table.loc['Winners', 3]
                    winners_short_str = winners_short_str.replace(' ', '').replace('%', '')
                    stats_table_new.loc['Winners No (Short)'] = [int(winners_short_str.split('(')[0])]
                    stats_table_new.loc['Winners % (Short)'] = [float(winners_short_str.split('(')[1].replace(')', ''))]
                    losers_short_str = stats_table.loc['Losers', 3]
                    losers_short_str = losers_short_str.replace(' ', '').replace('%', '')
                    stats_table_new.loc['Losers No (Short)'] = [int(losers_short_str.split('(')[0])]
                    stats_table_new.loc['Losers % (Short)'] = [float(losers_short_str.split('(')[1].replace(')', ''))]

                    if self.get_step1_summary:
                        strategy_df = strategy_df.append(stats_table_new.transpose())
                        continue

                    avg_win_dollar = float(stats_table.loc['Avg. Profit', 1])
                    # print(stats_table_new)
                    avg_loss_dollar = float(stats_table.loc['Avg. Loss', 1])
                    stats_table_new.loc['Expectancy'] = [
                        (avg_win_dollar * stats_table_new.loc['Winners %', s]/100 +
                         avg_loss_dollar * stats_table_new.loc['Losers %', s]/100) /
                        (-avg_loss_dollar)
                    ]

                    daily_pnl = pd.read_csv(os.path.join(s_path, 'daily_pnl.csv'), parse_dates=['Date'])
                    total_pnl = daily_pnl['PnL'].sum()
                    # print(CalculateCustomMetrics.cal_k_ratio(daily_pnl['PnL'].cumsum()))

                    # win rate
                    weekly_winrate, monthly_winrate, yearly_winrate, weekly_pnl, monthly_pnl, yearly_pnl = \
                        CalculateCustomMetrics.cal_profit_calendar_matrix(daily_pnl, s_path)
                    daily_winrate = len(daily_pnl[daily_pnl['PnL'] > 0]) / (
                        len(daily_pnl[daily_pnl['PnL'] > 0]) + len(daily_pnl[daily_pnl['PnL'] < 0])
                    )
                    stats_table_new.loc['Daily WinRate'] = [daily_winrate]
                    stats_table_new.loc['Weekly WinRate'] = [weekly_winrate]
                    stats_table_new.loc['Monthly WinRate'] = [monthly_winrate]
                    stats_table_new.loc['Yearly WinRate'] = [yearly_winrate]

                    # Herfindahl-Hirschman Index (HHI)
                    hhi_daily_10 = 0
                    hhi_daily_5 = 0
                    if len(daily_pnl) > 10:
                        daily_pnl_sorted = daily_pnl['PnL'].sort_values(ascending=False) / total_pnl * 100
                        daily_pnl_sorted_sq = daily_pnl_sorted ** 2
                        hhi_daily_10 = daily_pnl_sorted_sq[0:10].sum()
                        hhi_daily_5 = daily_pnl_sorted_sq[0:5].sum()
                    stats_table_new.loc['HHI Daily 5'] = [hhi_daily_5]
                    stats_table_new.loc['HHI Daily 10'] = [hhi_daily_10]

                    trade_data = pd.read_csv(os.path.join(s_path, 'trades.csv'))
                    trade_pnl = trade_data['Profit']
                    hhi_trade_5 = hhi_trade_10 = 0
                    if len(trade_pnl) > 10:
                        trade_pnl_sorted_sq = (trade_pnl.sort_values(ascending=False) / total_pnl * 100) ** 2
                        hhi_trade_5 = trade_pnl_sorted_sq[0:5].sum()
                        hhi_trade_10 = trade_pnl_sorted_sq[0:10].sum()
                    stats_table_new.loc['HHI Trade 5'] = [hhi_trade_5]
                    stats_table_new.loc['HHI Trade 10'] = [hhi_trade_10]

                    # recovering period & slope
                    equity_curve = daily_pnl['PnL'].cumsum()
                    stats_table_new.loc['K Ratio'] = [CalculateCustomMetrics.cal_k_ratio(equity_curve)]
                    stats_table_new.loc['Max DD Period'] = [
                        CalculateCustomMetrics.cal_mdd_n_mdd_period(equity_curve)[1]]
                    stats_table_new.loc['Slope'] = [CalculateCustomMetrics.cal_slope(equity_curve)]

                    # monte carlo
                    if self.monte_carlo:
                        mc_data = pd.read_excel(
                            os.path.join(s_path, 'MonteCarlo', 'MonteCarloResultResultAllYear.xlsx'),
                            sheet_name='Summary')
                        index_list = ['CAR / MDD', 'MDD', 'Max Pool', 'Min Pool', 'End Pool']
                        col_list = ['90%', '70%', '50%', '30%', '10%']
                        for i in index_list:
                            for j in col_list:
                                stats_table_new.loc[i + '_' + j] = [mc_data.loc[i, j]]

                    if self.run_monte_carlo:
                        # print(monthly_pnl)
                        # print(isinstance(monthly_pnl, pd.Series))
                        res = CalculateCustomMetrics.cal_monte_carlo(monthly_pnl, freq='monthly')
                        stats_table_new.loc['MC_Monthly_MDD_90%'] = res[0][0]
                        stats_table_new.loc['MC_Monthly_MDD_Period_90%'] = res[0][1]
                        stats_table_new.loc['MC_Monthly_CAR_MDD_90%'] = res[0][4]
                        stats_table_new.loc['MC_Monthly_Max_Equity_90%'] = res[0][2]
                        stats_table_new.loc['MC_Monthly_Min_Equity_90%'] = res[0][3]

                    # print(stats_table.loc['Net Profit', 2])
                    # time.sleep(1000000)
                    strategy_df = strategy_df.append(stats_table_new.transpose())

        strategy_df = strategy_df.rename({'Total Profit': 'Profit (Winners)',
                                          'Total Loss': 'Profit (Losers)',
                                          'All trades': 'Trade No.', 'CAR/MaxDD': 'CAR / MDD'}, axis=1)
        # print(strategy_df)
        # to_show_list = ['CAR/MaxDD', 'Net Profit', 'All trades', 'Avg. Bars Held', 'Winners', 'Avg. Profit',
        #                 'Losers', 'Avg. Loss', 'Max. system drawdown', 'Max. trade drawdown']
        to_show_list = ['Net Profit', 'Net Profit (Long)', 'Net Profit (Short)',
                        'CAR / MDD', 'Max. system drawdown', 'Max DD Period', 'Trade No.', 'Avg. Profit/Loss',
                        'Daily WinRate', 'Weekly WinRate', 'Monthly WinRate', 'Yearly WinRate',
                        'Winners %', 'Losers %', 'Winners % (Long)', 'Losers % (Long)',
                        'Winners % (Short)', 'Losers % (Short)',
                        'Profit Factor', 'Avg. Bars Held',
                        'Expectancy', 'K Ratio', 'HHI Daily 5', 'HHI Daily 10', 'HHI Trade 5', 'HHI Trade 10'
                        ]
        if self.monte_carlo:
            to_show_list.extend([
                'CAR / MDD_90%', 'MDD_90%', 'Max Pool_90%', 'Min Pool_90%', 'End Pool_90%',
                'CAR / MDD_70%', 'MDD_70%', 'Max Pool_70%', 'Min Pool_70%', 'End Pool_70%',
                'CAR / MDD_50%', 'MDD_50%', 'Max Pool_50%', 'Min Pool_50%', 'End Pool_50%',
                'CAR / MDD_30%', 'MDD_30%', 'Max Pool_30%', 'Min Pool_30%', 'End Pool_30%',
                'CAR / MDD_10%', 'MDD_10%', 'Max Pool_10%', 'Min Pool_10%', 'End Pool_10%'
            ])
        if self.run_monte_carlo:
            to_show_list.extend([
                'MC_Monthly_MDD_90%', 'MC_Monthly_MDD_Period_90%',
                'MC_Monthly_CAR_MDD_90%', 'MC_Monthly_Max_Equity_90%', 'MC_Monthly_Min_Equity_90%'
            ])
        if self.get_step1_summary:
            to_show_list = ['Net Profit', 'Net Profit (Long)', 'Net Profit (Short)', 'Trade No.',
                            'Avg. Profit/Loss', 'Winners %', 'Profit Factor', 'CAR / MDD',
                            'Max. system drawdown', 'Avg. Bars Held', 'Sharpe Ratio of trades'
                            ]
        # print(list(strategy_df.columns))
        # rest_list = [x for x in list(strategy_df.columns) if x not in to_show_list]
        # to_show_list.extend(rest_list)
        strategy_df = strategy_df[to_show_list]
        strategy_df.index.name = 'Name'
        strategy_df.to_csv(os.path.join(self.strategy_root_path, 'Summary.csv'))

    def generate_trade_csv_strategy_root(self):
        for s in tqdm(os.listdir(self.strategy_root_path)):
            s_path = os.path.join(self.strategy_root_path, s)
            print(s_path)
            if os.path.isdir(s_path):
                CalculateCustomMetrics.generate_trade_csv_from_html(s_path)

    @staticmethod
    def generate_trade_csv_from_html(Path):
        pathOpen = open(os.path.join(Path, "trades.html"), 'r')
        s = pathOpen.read()
        pathOpen.close()
        testtest = BeautifulSoup(s, "lxml")

        x = 0
        data_list = []
        for tr in testtest.find_all('tr'):
            if x >= 2:
                tds = tr.find_all('td')
                abc = tr.find_all('br')

                data_list.append({
                    'Symbol': tds[0].contents[0],
                    'Trade': tds[1].contents[0],
                    'Date': tds[2].contents[0],
                    'Price': ''.join(abc[0].next_siblings),
                    'Ex.Date': tds[3].contents[0],
                    'Ex. Price': ''.join(abc[1].next_siblings),
                    '% chg': tds[4].contents[0],
                    'Profit': tds[5].contents[0],
                    '% Profit': ''.join(abc[2].next_siblings),
                    'Shares': tds[6].contents[0],
                    'Position value': tds[7].contents[0],
                    'Cum.profit': tds[8].contents[0],
                    '# bars': tds[9].contents[0],
                    'Profit/bar': tds[10].contents[0],
                    'MAE': tds[11].contents[0],
                    'MFE': ''.join(abc[3].next_siblings),
                    'Scale In/Out': tds[12].contents[0]
                })
                # print(tds[2].contents[0])
            x += 1
        if len(data_list) == 0:
            efg = pd.DataFrame({
                'Symbol': [], 'Trade': [], 'Date': [], 'Price': [], 'Ex.Date': [],
                'Ex. Price': [], '% chg': [], 'Profit': [], '% Profit': [], 'Shares': [],
                'Position value': [], 'Cum.profit': [], '# bars': [],
                'Profit/bar': [], 'MAE': [], 'MFE': [], 'Scale In/Out': []
            })
        else:
            efg = pd.DataFrame(data_list)

            def recog_date_format(date_str, date_format):
                if '00:00:00' in date_str:
                    date_format = date_format.replace(' %p', '').replace('%I', '%H')
                try:
                    parsed_date = pd.Timestamp(
                        datetime.datetime.strptime(date_str, date_format)
                    )
                    return 1
                except Exception:
                    return 0

            def convert_date_format(date_str, date_format):
                if '00:00:00' in date_str:
                    date_format = date_format.replace(' %p', '').replace('%I', '%H')
                # print(date_str)
                parsed_date = pd.Timestamp(
                    datetime.datetime.strptime(date_str, date_format)
                )
                return parsed_date.strftime('%m/%d/%Y %I:%M:%S %p')

            potential_date_format = ['%m/%d/%Y %I:%M:%S %p', '%m/%d/%Y %H:%M', '%m/%d/%Y %H:%M:%S',
                                     '%d/%m/%Y %H:%M:%S', '%d/%m/%Y %I:%M:%S %p', '%d/%m/%Y %H:%M']
            for date_format in potential_date_format:
                res = efg['Date'].apply(recog_date_format, args=(date_format,))
                if res.sum() == len(efg):
                    efg.loc[:, 'Date'] = efg['Date'].apply(convert_date_format, args=(date_format,))
                    efg.loc[:, 'Ex.Date'] = efg['Ex.Date'].apply(convert_date_format, args=(date_format,))
                    continue

        efg = efg[['Symbol', 'Trade', 'Date', 'Price', 'Ex.Date', 'Ex. Price', '% chg', 'Profit', '% Profit'
            , 'Shares', 'Position value', 'Cum.profit', '# bars', 'Profit/bar', 'MAE', 'MFE', 'Scale In/Out']]
        efg.to_csv(Path + "\\trades.csv", index=None)

    def generate_daily_pnl_strategy_root(self):
        for s in tqdm(os.listdir(self.strategy_root_path)):
            s_path = os.path.join(self.strategy_root_path, s)
            # print(s_path)
            if os.path.isdir(s_path):
                trade_file_path = os.path.join(s_path, 'trades.csv')
                price_data_path = self.HSI_price_path
                output_path = os.path.join(s_path, 'daily_pnl.csv')
                CalculateCustomMetrics.generate_daily_pnl(trade_file_path, price_data_path, output_path)

    @staticmethod
    def generate_daily_pnl(trade_file_path, price_data_path, output_path):
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

        IMAGINARY_TRADES = pd.DataFrame({'Symbol':[], 'Trade':[], 'Date':[], 'Price': [],
                                         'Ex.Date': [], 'Ex.Price':[], 'Profit':[]})
        for d in index_data['Date']:
            if d < start_date or d > end_date:
                continue
            yest_close = index_data.iloc[list(index_data[index_data['Date'] == d].index)[0] - 1][1]
            yest = index_data.iloc[list(index_data[index_data['Date'] == d].index)[0] - 1][0]
            today_close = list(index_data[index_data['Date'] == d]['PX_LAST'])[0]
            # print('Today date = %s, yest=%s, yest_close=%.1f, today_close=%.1f' % (d, yest, yest_close, today_close))
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
            # print(today_trade_data)
            # time.sleep(10000)

            # print('today_trade_data (before) = \n%s\n' % today_trade_data)

            # find those with open date earlier than day_start and modify their open price to be yesterday's close

            def update_profit(row):
                nonlocal IMAGINARY_TRADES
                if row['Ex.Date'] > day_end and row['Date'] < day_start:  # a trade crosses multiple days
                    pnl = row['Trade'] * (today_close - yest_close)
                    return pnl * row['Shares']
                elif row['Ex.Date'] > day_end:
                    pnl = row['Trade'] * (today_close - row['Price']) - \
                          0.5 * (row['Trade'] * (row['Ex. Price'] - row['Price']) - row['Profit'])
                    day_end_str = day_end.strftime('%Y-%m-%d %I:%M:%S %p')
                    rec = pd.DataFrame({'Symbol':[row['Symbol']], 'Trade':[row['Trade']], 'Date':[row['Date']], 'Price': [row['Price']],
                                         'Ex.Date': [day_end_str], 'Ex.Price':[today_close], 'Profit':[pnl]})
                    IMAGINARY_TRADES = IMAGINARY_TRADES.append(rec)
                    return pnl * row['Shares']
                elif row['Date'] < day_start:
                    pnl = row['Trade'] * (row['Ex. Price'] - yest_close) - \
                          0.5 * (row['Trade'] * (row['Ex. Price'] - row['Price']) - row['Profit'])
                    day_start_str = day_end.strftime('%Y-%m-%d %I:%M:%S %p')
                    rec = pd.DataFrame({'Symbol': [row['Symbol']], 'Trade': [row['Trade']], 'Date': [day_start_str],
                                        'Price': [yest_close],
                                        'Ex.Date': [row['Ex.Date']], 'Ex.Price': [today_close['Ex.Price']], 'Profit': [pnl]})
                    IMAGINARY_TRADES = IMAGINARY_TRADES.append(rec)
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
        # print(pnl_data)
        # print(output_path)

    @staticmethod
    def equity_curve_type_check(equity_curve, msg_head=''):
        if not isinstance(equity_curve, (list, pd.Series, np.ndarray)):
            if isinstance(equity_curve, pd.DataFrame):
                if len(equity_curve.columns) != 1:
                    raise TypeError(msg_head + " equity_curve should have only one column.")
                else:
                    equity_curve = np.array(equity_curve.iloc[:, 0])
            else:
                raise TypeError(msg_head +
                                " equity_curve must be a list or pandas.Series or pandas.DataFrame with one column.")
        return True

    @staticmethod
    def cal_profit_calendar_matrix(daily_pnl_data, current_path=None, ignore_zero_winrate=True, to_csv=True):
        # pnl_data should be a pandas.DataFrame from 'daily_pnl.csv'
        # pnl_data = pd.read_csv(pnl_path, parse_dates=['Date'],
        #                        date_parser=lambda x: pd.datetime.strptime(x, '%Y-%m-%d'))
        daily_pnl_data.loc[:, 'year'] = daily_pnl_data['Date'].apply(lambda x: x.year)
        daily_pnl_data.loc[:, 'month'] = daily_pnl_data['Date'].apply(lambda x: x.month)
        daily_pnl_data.loc[:, 'week'] = daily_pnl_data['Date'].apply(lambda x: x.week)

        pnl_data_year = daily_pnl_data.groupby(by=['year'])['PnL'].sum()
        pnl_data_year_month = daily_pnl_data.groupby(by=['year', 'month'])['PnL'].sum()
        pnl_data_year_week = daily_pnl_data.groupby(by=['year', 'week'])['PnL'].sum()

        if to_csv:
            if current_path is None:
                raise ValueError('[cal_profit_calendar_matrix] if to_csv=True, current_path must not be None')
            pnl_data_year.to_csv(os.path.join(current_path, 'yearly_pnl.csv'))
            pnl_data_year_month.to_csv(os.path.join(current_path, 'monthly_pnl.csv'))
            pnl_data_year_week.to_csv(os.path.join(current_path, 'weekly_pnl.csv'))

        if ignore_zero_winrate:
            weekly_win_rate = pnl_data_year_week.apply(lambda x: 1 if x > 0 else 0).sum() / \
                              len(pnl_data_year_week[pnl_data_year_week != 0])
            monthly_win_rate = pnl_data_year_month.apply(lambda x: 1 if x > 0 else 0).sum() / \
                               len(pnl_data_year_month[pnl_data_year_month != 0])
            yearly_win_rate = pnl_data_year.apply(lambda x: 1 if x > 0 else 0).sum() / \
                              len(pnl_data_year[pnl_data_year != 0])
        else:
            weekly_win_rate = pnl_data_year_week.apply(lambda x: 1 if x > 0 else 0).sum() / len(pnl_data_year_week)
            monthly_win_rate = pnl_data_year_month.apply(lambda x: 1 if x > 0 else 0).sum() / len(pnl_data_year_month)
            yearly_win_rate = pnl_data_year.apply(lambda x: 1 if x > 0 else 0).sum() / len(pnl_data_year)

        return weekly_win_rate, monthly_win_rate, yearly_win_rate, pnl_data_year_week, pnl_data_year_month, pnl_data_year

    @staticmethod
    def cal_slope(equity_curve):
        msg_head = '[cal_slope]'
        CalculateCustomMetrics.equity_curve_type_check(equity_curve, msg_head)

        equity_curve = np.array(equity_curve)
        y = equity_curve
        x = np.array(list(range(len(y)))) + 1

        x_bar = x.mean()
        y_bar = y.mean()

        v1 = ((x - x_bar) * (y - y_bar)).sum()
        v2 = ((x - x_bar) ** 2).sum()

        return v1 / v2

    @staticmethod
    def cal_k_ratio(equity_curve):
        """
        This will calculate Zephyr K-Ratio (slope/s.e. of slope)
        :param equity_curve: should be a list or pandas.Series or pandas.DataFrame with one one column
        :return:
        """
        msg_head = '[cal_k_ratio]'
        CalculateCustomMetrics.equity_curve_type_check(equity_curve, msg_head)

        equity_curve = np.array(equity_curve)
        y = equity_curve
        x = np.array(list(range(len(y)))) + 1

        x_bar = x.mean()
        y_bar = y.mean()

        v1 = (((x - x_bar) * (y - y_bar)).sum()) ** 2
        v2 = ((x - x_bar)**2).sum()
        v3 = ((y - y_bar)**2).sum()

        steyx_v1 = math.sqrt(
            1/(len(y) - 2) * (v3 - v1 / v2)
        )
        steyx_v2 = math.sqrt(v2)
        steyx = steyx_v1 / steyx_v2

        slope = math.sqrt(v1) / v2

        return slope / steyx

    @staticmethod
    def cal_GPR(daily_pnl, method=1):
        """
        Calculate Gai-toPain Ratio ( =  total sum of monthly % return / abs(total sum of monthly % loss))
        method =  1 -> use points pnl instead of % pnl
        :param daily_pnl:
        :return:
        """
        msg_head = '[cal_GPR]'

        if not isinstance(daily_pnl, pd.DataFrame):
            raise TypeError('%s daily_pnl must be a DataFrame.' % msg_head)
        if 'Date' not in daily_pnl.columns or 'PnL' not in daily_pnl.columns:
            raise ValueError('%s \"Date\" and \"PnL\" must be in the columns' % msg_head)

        if method == 1:
            daily_pnl.loc[:, 'month'] = daily_pnl['Date'].apply(lambda x: x.month)
            daily_pnl.loc[:, 'year'] = daily_pnl['Date'].apply(lambda x: x.year)
            monthly_pnl = daily_pnl.groupby(by=['year', 'month']).sum()
            # print(monthly_pnl)
            total_pnl = monthly_pnl['PnL'].sum()
            total_loss = monthly_pnl[monthly_pnl['PnL'] < 0]['PnL'].sum() * -1
            if total_loss == 0:
                return 99999
            else:
                return total_pnl / total_loss

    @staticmethod
    def cal_mdd_n_mdd_period(equity_curve):
        msg_head = '[cal_mdd_n_mdd_period]'
        CalculateCustomMetrics.equity_curve_type_check(equity_curve, msg_head)

        mdd = 0
        mdd_period = 0
        dd_period = 0
        peak = equity_curve[0]
        for x in equity_curve:
            if x > peak:
                peak = x
                dd_period = 0
            else:
                dd_period += 1
            if peak == 0:
                peak = 1
            dd = float(peak - x) / peak
            if dd > mdd:
                mdd = dd
            if dd_period > mdd_period:
                mdd_period = dd_period
        return mdd, mdd_period

    @staticmethod
    def cal_monte_carlo(pnl, initial_equity=50000, multiplier=10, times=10000, freq='daily',
                        use_tqdm=False):
        """
                Apply Monte Carlo method to a series of daily PnL and calculate the 90%, 70%, 50%, 30%, and 10% values for different metrics.
                """
        msg_head = '[cal_monte_carlo]'
        CalculateCustomMetrics.equity_curve_type_check(pnl, msg_head)

        one_year_period_dict = {'daily': 356, 'quarterly': 4, 'monthly': 12, 'weekly': 52, 'trades':1000}
        one_year_period = one_year_period_dict[freq.lower()]

        pnl = np.array(pnl)
        equity_curve_raw = pnl
        MDD = []
        MDD_PERIOD = []
        MAX_EQUITY = []
        MIN_EQUITY = []
        CAR_MDD = []
        END_EQUITY = []
        CAR = []
        INIT_EQUITY = []
        MONTHLY_WINRATE = []
        WEEKLY_WINRATE = []
        QUARTERLY_WINRATE = []

        ra = tqdm(range(times)) if use_tqdm else range(times)
        for i in ra:
            # print(i)
            random.shuffle(pnl)
            cum_pnl = pnl.cumsum()
            cum_pnl = initial_equity + multiplier * cum_pnl
            # print(type(cum_pnl))
            mdd, mdd_period = CalculateCustomMetrics.cal_mdd_n_mdd_period(cum_pnl)
            car = math.log(cum_pnl[-1] / initial_equity) / (len(pnl) / one_year_period)

            MDD.append(abs(mdd))
            MDD_PERIOD.append(mdd_period)
            MAX_EQUITY.append(max(cum_pnl))
            MIN_EQUITY.append(min(cum_pnl))
            CAR_MDD.append(car / abs(mdd) if mdd > 0 else 9999)
            END_EQUITY.append(cum_pnl[-1])
            CAR.append(car)
            INIT_EQUITY.append(initial_equity)

            temp_pnl = pd.DataFrame({'pnl': pnl, 'ind': list(range(len(pnl)))})
            temp_pnl.loc[:, 'week'] = temp_pnl['ind'].apply(lambda x: (x - x % 5) / 5)
            temp_pnl.loc[:, 'month'] = temp_pnl['ind'].apply(lambda x: (x - x % 20) / 20)
            temp_pnl.loc[:, 'quarter'] = temp_pnl['ind'].apply(lambda x: (x - x % 60) / 60)

            weekly_pnl = temp_pnl.groupby(by=['week']).sum()
            weekly_winrate = len(weekly_pnl[weekly_pnl['pnl'] > 0]) / len(weekly_pnl)
            monthly_pnl = temp_pnl.groupby(by=['month']).sum()
            monthly_winrate = len(monthly_pnl[monthly_pnl['pnl'] > 0]) / len(monthly_pnl)
            quarterly_pnl = temp_pnl.groupby(by=['quarter']).sum()
            quarterly_winrate = len(quarterly_pnl[quarterly_pnl['pnl'] > 0]) / len(quarterly_pnl)
            WEEKLY_WINRATE.append(weekly_winrate)
            MONTHLY_WINRATE.append(monthly_winrate)
            QUARTERLY_WINRATE.append(quarterly_winrate)

            # WEEKLY_WINRATE.append(0)
            # MONTHLY_WINRATE.append(0)

            pnl = equity_curve_raw

        MDD = sorted(MDD)  # ascending
        MDD_PERIOD = sorted(MDD_PERIOD)  # ascending
        MAX_EQUITY = sorted(MAX_EQUITY, reverse=True)  # descending
        MIN_EQUITY = sorted(MIN_EQUITY, reverse=True)  # descending
        CAR_MDD = sorted(CAR_MDD, reverse=True)  # descending
        WEEKLY_WINRATE = sorted(WEEKLY_WINRATE, reverse=True)  # descending
        MONTHLY_WINRATE = sorted(MONTHLY_WINRATE, reverse=True)  # descending
        QUARTERLY_WINRATE = sorted(QUARTERLY_WINRATE, reverse=True)  # descending

        n_90 = int(math.floor(len(MDD)*0.9))
        n_70 = int(math.floor(len(MDD)*0.7))
        n_50 = int(math.floor(len(MDD)*0.5))
        n_30 = int(math.floor(len(MDD)*0.3))
        n_10 = int(math.floor(len(MDD)*0.1))

        # print(MDD[0:10])
        # print(MDD_PERIOD[0:10])
        # print(MAX_EQUITY[0:10])
        # print(MIN_EQUITY[0:10])
        # print(CAR_MDD[0:10])

        return [
            [MDD[n_90], MDD_PERIOD[n_90], MAX_EQUITY[n_90], MIN_EQUITY[n_90], CAR_MDD[n_90],
             CAR[n_90], END_EQUITY[n_90], INIT_EQUITY[n_90],
             WEEKLY_WINRATE[n_90], MONTHLY_WINRATE[n_90], QUARTERLY_WINRATE[n_90]],
            [MDD[n_70], MDD_PERIOD[n_70], MAX_EQUITY[n_70], MIN_EQUITY[n_70], CAR_MDD[n_70],
             CAR[n_70], END_EQUITY[n_70], INIT_EQUITY[n_70],
             WEEKLY_WINRATE[n_70], MONTHLY_WINRATE[n_70], QUARTERLY_WINRATE[n_70]],
            [MDD[n_50], MDD_PERIOD[n_50], MAX_EQUITY[n_50], MIN_EQUITY[n_50], CAR_MDD[n_50],
             CAR[n_50], END_EQUITY[n_50], INIT_EQUITY[n_50],
             WEEKLY_WINRATE[n_50], MONTHLY_WINRATE[n_50], QUARTERLY_WINRATE[n_50]],
            [MDD[n_30], MDD_PERIOD[n_30], MAX_EQUITY[n_30], MIN_EQUITY[n_30], CAR_MDD[n_30],
             CAR[n_30], END_EQUITY[n_30], INIT_EQUITY[n_30],
             WEEKLY_WINRATE[n_30], MONTHLY_WINRATE[n_30], QUARTERLY_WINRATE[n_30]],
            [MDD[n_10], MDD_PERIOD[n_10], MAX_EQUITY[n_10], MIN_EQUITY[n_10], CAR_MDD[n_10],
             CAR[n_10], END_EQUITY[n_10], INIT_EQUITY[n_10],
             WEEKLY_WINRATE[n_10], MONTHLY_WINRATE[n_10], QUARTERLY_WINRATE[n_10]]
            ]

    @staticmethod
    def cal_monte_carlo_one_strategy(strategy_path, mc_times=10000, use_daily_pnl=True, use_trade_pnl=False):
        # ignore_zero_winrate - if to ignore zero when calculate win rate
        # must ensure that 'daily_pnl.csv' is in place
        mc_root = os.path.join(strategy_path, 'MonteCarlo2')
        if not os.path.exists(mc_root):
            os.mkdir(mc_root)

        year_list = None
        daily_pnl_data = None
        pnl_data_year_daily = None
        if use_daily_pnl:
            daily_pnl_data = pd.read_csv(os.path.join(strategy_path, 'daily_pnl.csv'), parse_dates=['Date'])
            daily_pnl_data.loc[:, 'year'] = daily_pnl_data['Date'].apply(lambda x: x.year)
            daily_pnl_data.loc[:, 'month'] = daily_pnl_data['Date'].apply(lambda x: x.month)
            daily_pnl_data.loc[:, 'week'] = daily_pnl_data['Date'].apply(lambda x: x.week)

            year_list = daily_pnl_data['Date'].apply(lambda x: x.year).unique()
            year_list = np.insert(year_list, 0, 0)

            pnl_data_year_daily = daily_pnl_data.groupby(by=['year', 'Date'])['PnL'].sum()
            pnl_data_year_month = daily_pnl_data.groupby(by=['year', 'month'])['PnL'].sum()
            pnl_data_year_week = daily_pnl_data.groupby(by=['year', 'week'])['PnL'].sum()

        trade_pnl_data = None
        trade_pnl_data_year_daily = None
        if use_trade_pnl:
            trade_pnl_data = pd.read_csv(os.path.join(strategy_path, 'trades.csv'), parse_dates=['Date'],
                                         date_parser=lambda x: pd.datetime.strptime(x, '%m/%d/%Y %I:%M:%S %p'))
            trade_pnl_data.loc[:, 'year'] = trade_pnl_data['Date'].apply(lambda x: x.year)
            trade_pnl_data.loc[:, 'month'] = trade_pnl_data['Date'].apply(lambda x: x.month)
            trade_pnl_data.loc[:, 'week'] = trade_pnl_data['Date'].apply(lambda x: x.week)

            trade_pnl_data_year_daily = trade_pnl_data.groupby(by=['year', 'Date'])['Profit'].sum()

            year_list = trade_pnl_data['Date'].apply(lambda x: x.year).unique()
            year_list = np.insert(year_list, 0, 0)

        pnl_data = {
            'daily': pnl_data_year_daily,
            'trades': trade_pnl_data_year_daily
            # 'weekly': pnl_data_year_week, 'monthly': pnl_data_year_month
        }
        # print(trade_pnl_data_year_daily)
        # method 1: e.g. weekly -> random
        initial_equity = 50000
        for freq, data in pnl_data.items():
            if data is None or len(data) == 0:
                continue
            excel_writer = pd.ExcelWriter(os.path.join(mc_root, freq + '.xls'))
            for year in year_list:
                print('%s: year = %d' % (freq, year))
                this_year_data = data.loc[(year, )] if year > 0 else data

                mc_res_this_year = CalculateCustomMetrics.cal_monte_carlo(
                    this_year_data, freq=freq, use_tqdm=True, initial_equity=initial_equity, times=mc_times
                )
                mc_res_this_year = pd.DataFrame(
                    mc_res_this_year,
                    columns=['MDD', 'MDD_Period', 'Max_Equity', 'Min_Equity', 'CAR/MDD', 'CAR', 'End_Equity',
                             'Init_Equity', 'Weekly_Win_Rate', 'Monthly_Win_Rate', 'Quarterly_Win_Rate'],
                    index=['90%', '70%', '50%', '30%', '10%'])
                winrate_ignore_zero = len(this_year_data[this_year_data > 0]) / (
                        len(this_year_data[this_year_data != 0])
                )
                winrate_consider_zero = len(this_year_data[this_year_data > 0]) / (len(this_year_data))
                mc_res_this_year.loc[:, 'Win_Rate_Ignore0'] = winrate_ignore_zero
                mc_res_this_year.loc[:, 'Win_Rate_Consider0'] = winrate_consider_zero
                # mc_res_this_year.loc[:, 'Initial_equity'] = initial_equity
                required_columns = ['MDD', 'MDD_Period', 'Init_Equity', 'Max_Equity', 'Min_Equity', 'End_Equity']
                if freq == 'daily':
                    required_columns.extend(['CAR/MDD', 'Win_Rate_Ignore0', 'Win_Rate_Consider0',
                                             'Weekly_Win_Rate', 'Monthly_Win_Rate', 'Quarterly_Win_Rate'])
                if freq == 'trades':
                    required_columns.extend(['Win_Rate_Ignore0', 'Win_Rate_Consider0'])
                mc_res_this_year = mc_res_this_year[required_columns]
                mc_res_this_year = mc_res_this_year.transpose()
                mc_res_this_year.to_excel(excel_writer, sheet_name=str(year) if year > 0 else 'All year')
            excel_writer.save()

        # method 2: e.g. random -> weekly sampling -> random
        for freq in []:
        # for freq in ['weekly', 'monthly']:
            excel_writer = pd.ExcelWriter(os.path.join(mc_root, freq + '_method2.xls'))
            unit_days = 5 if freq == 'weekly' else 20
            for year in year_list:
                this_year_data = pnl_data_year_daily.loc[(year, )] if year > 0 else pnl_data_year_daily
                random_data = this_year_data.sample(frac=1)
                random_data = random_data.reset_index(drop=True)
                random_data_df = pd.DataFrame({'PnL': random_data, 'ind':random_data.index})
                random_data_df.loc[:, 'ind2'] = random_data_df['ind'].apply(lambda x: (x - x % unit_days) / unit_days)

                this_year_data = random_data_df.groupby(by=['ind2'])['PnL'].sum()

                mc_res_this_year = CalculateCustomMetrics.cal_monte_carlo(
                    this_year_data, freq=freq, use_tqdm=True, initial_equity=initial_equity, times=mc_times
                )
                mc_res_this_year = pd.DataFrame(
                    mc_res_this_year,
                    columns=['MDD', 'MDD_Period', 'Max_Equity', 'Min_Equity', 'CAR/MDD', 'CAR', 'End_Equity',
                             'Init_Equity', 'Weekly_Win_Rate', 'Monthly_Win_Rate', 'Quarterly_Win_Rate'],
                    index=['90%', '70%', '50%', '30%', '10%'])
                winrate_ignore_zero = len(this_year_data[this_year_data > 0]) / (
                    len(this_year_data[this_year_data != 0])
                )
                winrate_consider_zero = len(this_year_data[this_year_data > 0]) / (len(this_year_data))
                mc_res_this_year.loc[:, 'Win_Rate_Ignore0'] = winrate_ignore_zero
                mc_res_this_year.loc[:, 'Win_Rate_Consider0'] = winrate_consider_zero
                # mc_res_this_year.loc[:, 'Initial_equity'] = initial_equity
                mc_res_this_year = mc_res_this_year[[
                    'MDD', 'MDD_Period', 'Init_Equity', 'Max_Equity', 'Min_Equity', 'End_Equity',
                    'CAR/MDD', 'Win_Rate_Ignore0', 'Win_Rate_Consider0',
                    'Weekly_Win_Rate', 'Monthly_Win_Rate', 'Quarterly_Win_Rate'
                ]]
                mc_res_this_year = mc_res_this_year.transpose()
                mc_res_this_year.to_excel(excel_writer, sheet_name=str(year) if year > 0 else 'All year')
            excel_writer.save()

    @staticmethod
    def cal_acf_pacf(time_series, lags=10, adf_p_max=0.05 ,
                     output_path='', output_file_prefix=''):
        # first need to do the ADF test
        res = ts.adfuller(time_series, lags)
        adf_p_value = res[1]
        pass_adf = True
        if adf_p_value >= adf_p_max:
            print('[cal_acf_pacf] The time series may have unit root. ADF p value=%f' %(adf_p_value))
            pass_adf = False

        time_series2 = (time_series - time_series.mean()) / time_series.std()
        acf_res = ts.acf(time_series2, nlags=lags)
        pacf_res = ts.pacf(time_series2, nlags=lags)

        if not os.path.exists(output_path):
            os.mkdir(output_path)

        col = np.array(range(lags + 1))
        res = pd.DataFrame({'ACF': acf_res, 'PACF': pacf_res}, index=col)
        res = res.transpose()
        csv_name = ((output_file_prefix + '_') if output_file_prefix != '' else '') + \
                   'acf_pacf' + ('_not_pass_adf' if not pass_adf else '') + '.csv'
        res.to_csv(os.path.join(output_path, csv_name))

        fig = plt.figure()
        plt.bar(range(len(acf_res)), acf_res)
        fig.savefig(os.path.join(output_path,
                                 ((output_file_prefix + '_') if output_file_prefix != '' else '') + 'acf.png'))
        plt.close()

        fig = plt.figure()
        plt.bar(range(len(pacf_res)), pacf_res)
        fig.savefig(os.path.join(output_path,
                                 ((output_file_prefix + '_') if output_file_prefix != '' else '') + 'pacf.png'))
        plt.close()

        return [acf_res, pacf_res, pass_adf]

    @staticmethod
    def cal_avg_hold_min(trade_file_path=None, trade_data=None):
        msg_head = '[cal_exposure]'
        if trade_file_path is None and trade_data is None:
            raise ValueError(msg_head + " trade_file_path and trade_data can't be both None")

        if trade_file_path is not None:
            trade_data = pd.read_csv(trade_file_path, parse_dates=['Date', 'Ex.Date'],
                                     date_parser=lambda x: pd.datetime.strptime(x, '%m/%d/%Y %I:%M:%S %p'))

        # get frequency
        arr = trade_data.iloc[0, 0].split('_')
        freq = 0
        for a in arr:
            if 'min' in a:
                freq = float(a.replace('min', ''))
                break
        if freq == 0:
            raise ValueError(msg_head + ' freq=0 should not be correct. Please check file or data.')

        return freq * trade_data['# bars'].mean()

    @staticmethod
    def cal_pnl_hhi(daily_pnl, trade_data):
        """
        Herfindahl-Hirschman Index (HHI)
        """
        total_pnl = daily_pnl['PnL'].sum()
        hhi_daily_10 = 0
        hhi_daily_5 = 0
        if len(daily_pnl) > 10:
            daily_pnl_sorted = daily_pnl['PnL'].sort_values(ascending=False) / total_pnl * 100
            daily_pnl_sorted_sq = daily_pnl_sorted ** 2
            hhi_daily_10 = daily_pnl_sorted_sq[0:10].sum()
            hhi_daily_5 = daily_pnl_sorted_sq[0:5].sum()

        trade_pnl = trade_data['Profit']
        hhi_trade_5 = hhi_trade_10 = 0
        if len(trade_pnl) > 10:
            trade_pnl_sorted_sq = (trade_pnl.sort_values(ascending=False) / total_pnl * 100) ** 2
            hhi_trade_5 = trade_pnl_sorted_sq[0:5].sum()
            hhi_trade_10 = trade_pnl_sorted_sq[0:10].sum()

        return [hhi_daily_10, hhi_trade_10, hhi_daily_5, hhi_trade_5]

    @staticmethod
    def cal_expectancy(pnl_data):
        """
        pnl_data: should be a list of pnl, e.g. daily pnl, per trade pnl. It should be a list/numpy array/pandas.Series/
        """
        CalculateCustomMetrics.equity_curve_type_check(pnl_data, '[cal_expectancy]')

        pnl_data = pd.Series(pnl_data)
        pos_pnl_data = pnl_data[pnl_data > 0]
        neg_pnl_data = pnl_data[pnl_data < 0]

        win_num = len(pos_pnl_data)
        avg_win_dollar = pos_pnl_data.sum() / win_num

        loss_num = len(neg_pnl_data)
        avg_loss_dollar = neg_pnl_data.sum() / loss_num

        win_rate = win_num / (win_num + loss_num)
        loss_rate = loss_num / (win_num + loss_num)

        expectancy = (avg_win_dollar * win_rate + avg_loss_dollar * loss_rate) / abs(avg_loss_dollar)

        return expectancy

def generate_daily_pnl(strategy_path, HSI_price_path):
    for strategy_freq in os.listdir(strategy_path):
        print(strategy_path + ' ' + strategy_freq)
        p = os.path.join(strategy_path, strategy_freq)
        c = CalculateCustomMetrics(p, HSI_price_path)
        c.generate_trade_csv_strategy_root()
        c.generate_daily_pnl_strategy_root()


def temp_generate_my_metrics(strategy_path, HSI_price_path):
    print('-------------------- %s ----------------------' % strategy_path)
    c = CalculateCustomMetrics(strategy_path, HSI_price_path, monte_carlo=False)
    c.generate_my_metrics()


if __name__ == '__main__':
    p = 'S:\\Amibroker project\\Result\\Step3\\2013'
    hsi_path = 'S:\\Amibroker project\\Code\\python_amibroker\\HI1.csv'
    # pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
    # for strategy in os.listdir(p):
    #     if strategy != 'WilliamR2':
    #         pool.apply_async(generate_daily_pnl, args=(os.path.join(p, strategy), hsi_path, ))
    # pool.close()
    # pool.join()
    #

    # CalculateCustomMetrics.generate_trade_csv_from_html('S:\\Amibroker project\\Result\\Step3\\2013\\HSI;15min;BBandBreakOut;Test15-5m_3m2013')
    # c = CalculateCustomMetrics('S:\\Amibroker project\\Result\\Step3', hsi_path, monte_carlo=False, run_monte_carlo=True)
    # c = CalculateCustomMetrics('S:\\Amibroker project\\Result\\Step3\\2013\\HSI;15min;BBandBreakOut;Test15-5m_3m2013',
    #                            hsi_path, monte_carlo=False)
    # c.generate_my_metrics()
    # c.generate_trade_csv()
    # c.generate_daily_pnl()
    # c.generate_summary()

    # pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
    # for strategy in os.listdir(p):
    #     pool.apply_async(temp_generate_my_metrics, args=(os.path.join(p, strategy), hsi_path, ))
    # pool.close()
    # pool.join()

    # temp_generate_my_metrics('S:\\Amibroker project\\Result\\Step3\\2013\\HIS;15min;RSIDivergence;Test06-4m_1m2013',
    #                          hsi_path)

    # trade_file_path = 'S:\\Amibroker project\\Result\\Step3\\15min;RSIDivergenceTest04(Hsi)5m_3mStart2015\\trades.csv'
    # output_file_path = 'S:\\Amibroker project\\Result\\Step3\\15min;RSIDivergenceTest04(Hsi)5m_3mStart2015\\daily_pnl.csv'
    # CalculateCustomMetrics.daily_pnl(trade_file_path, hsi_path, output_file_path)


    # test acf & pacf
    # s = 'S:\\Amibroker project\\Result\\Step3\\15min;RSIDivergenceTest04(Hsi)5m_3mStart2015\\daily_pnl.csv'
    # data = pd.read_csv(s, parse_dates=['Date'])
    # CalculateCustomMetrics.cal_acf_pacf(data['PnL'],
    #                 output_path='S:\\Amibroker project\\Result\\Step3\\15min;RSIDivergenceTest04(Hsi)5m_3mStart2015\\auto_corr')

    # test Monte Carlo
    ss = 'S:\\Amibroker project\\Result\\Step3\\2013'
    for folder in os.listdir(ss):
        if os.path.isfile(os.path.join(ss, folder)):
            continue
        if folder == 'HIS;15min;RSIDivergence;Test06-4m_1m2013':
            continue
        print('------------------ %s ---------------' % folder)
        CalculateCustomMetrics.cal_monte_carlo_one_strategy(
            os.path.join(ss, folder), use_trade_pnl=True, use_daily_pnl=False,
            mc_times=10000
        )

    # test GPR
    # pnl = pd.read_csv('S:\\Amibroker project\\Result\\Step3\\15min;RSIDivergenceTest06(Hsi)4m_1mStart2015\\daily_pnl.csv',
    #                   parse_dates=['Date'])
    # print(CalculateCustomMetrics.cal_GPR(pnl))