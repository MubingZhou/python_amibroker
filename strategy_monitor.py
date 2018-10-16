import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import datetime, os, configparser, time, math, calendar, warnings, sys
# from generate_html import GenerateHTML

pd.set_option('display.max_columns', 500)


class StrategyMonitory:
    FUTURES_LETTER_MONTH_MAP = {1: 'F', 2: 'G', 3: 'H', 4: 'J', 5: 'K', 6: 'M',
                                7: 'N', 8: 'Q', 9: 'U', 10: 'V', 11: 'X', 12: 'Z'}
    UNDERLYING_DICT = {'HSI': 'HI' +
                              FUTURES_LETTER_MONTH_MAP[datetime.datetime.now().month] +
                              str(datetime.datetime.now().year)[3]}

    def __init__(self, root_path, trades_root_path, today_date_list, source):
        self.root_path = root_path
        self.trades_root_path = trades_root_path
        self.today_date_list = today_date_list if isinstance(today_date_list, list) else [today_date_list]
        self.source = source

    def run(self):
        for today_date in self.today_date_list:
            self.generate_report(self.root_path, self.trades_root_path, today_date, source=self.source)

    def guess_underlying(self, today_date):
        year = today_date.year
        month = today_date.month
        month_end = pd.Timestamp(year=year, month=month, day=calendar.monthrange(year, month)[1])
        t_2 = month_end + pd.offsets.Day(1) - pd.offsets.BDay(2)
        for (index, underlying) in self.UNDERLYING_DICT.items():
            if today_date >= t_2:   # set to next month
                if month == 12:
                    month = 1
                    year = year + 1
                else:
                    month = month + 1
            prefix = ''
            if index == 'HSI':
                prefix = 'HI'
            elif index == 'HSCEI':
                prefix = 'HC'
            contract_code = prefix + self.FUTURES_LETTER_MONTH_MAP[month] + str(year)[3]
            if contract_code != underlying:
                msg = '\nContract code may be different for ' + str(index) + \
                    ' futures. Current code='+ str(underlying) + ', suggested code='+ str(contract_code) + '.\n' + \
                    'If you want to change code, press 1. If you want to proceed without change, press any key.'
                warnings.warn(msg)
                time.sleep(1)
                e = input('Input:')
                if e == '1' or e == 1:
                    self.UNDERLYING_DICT[index] = contract_code
                    print('Contract code changed for %s in month %d. New code=%s\n'%(
                        underlying, month, contract_code
                    ))

    def generate_report(self, root_path, trades_root_path, today_date, source=1):
        """
        source: 1 - Sharp Point, 2 - Multi Chart

        This acts as the main console to control other fuctions. Work flow as flow:
        1. We should start from the 1st trade file(s).
        2. Read the REPORT files and get their last day's positions and price (If such file not exits, create a new empty one)
        3. Read the TRADE files and calculate the pnl of every strategy.
        4. Update the REPORT file with latest pnl & holding positions. Generate graphs
        """
        self.guess_underlying(today_date)
        # time.sleep(1000000)
        today_date = pd.Timestamp(today_date)
        today_date_str_yyyymmdd = today_date.strftime('%Y%m%d')

        # ---------------------- the all strategies ----------------------
        all_strategies = []
        if source == 1:  # SP
            acc_strategy_map_path = os.path.join(root_path, "parameters", "acc_strategy_map_sp.csv")
            with open(acc_strategy_map_path) as f:
                acc_strategy_content = f.readlines()
            acc_strategy_map = {}
            for c in acc_strategy_content:
                carr = c.split(',')
                acc_strategy_map[carr[0]] = carr[1].replace('\n', '')
            all_strategies = list(acc_strategy_map.values())
        if source == 2:  # MC
            acc_strategy_map_path = os.path.join(root_path, "parameters", "all_strategy_list_mc.csv")
            with open(acc_strategy_map_path) as f:
                s = f.readline()
                all_strategies = s.split(',')
                all_strategies[len(all_strategies) - 1] = all_strategies[len(all_strategies) - 1].replace('\n', '')
                # print(all_strategies)

        # ---------------------- read initialization data by strategy ----------------------
        # two files for a strategy file: one is its data, .csv; the other is its config, .ini
        config_dict = {}
        strategy_data_dict = {}
        last_pos_data = pd.DataFrame({'Strategy': [], 'Qty': [], 'T. Price': []})
        all_strategies_file_exist = True
        for s in all_strategies:
            config_path = os.path.join(root_path, s + '.ini')
            if os.path.exists(config_path):
                config = configparser.ConfigParser()
                config.read(config_path)
                s_dict = {}
                s_dict['theo_pnl_per_day'] = float(config['COMMON']['theo_pnl_per_day'])
                s_dict['pnl_std'] = float(config['COMMON']['pnl_std'])
                s_dict['mode'] = config['COMMON']['mode']
                s_dict['underlying'] = config['COMMON']['underlying']
                s_dict['multiplier'] = float(config['COMMON']['multiplier'])
                s_dict['lot_size'] = float(config['COMMON']['lot_size'])
                s_dict['theo_trade_no_per_day'] = float(config['COMMON']['trade_no_per_day'])
                s_dict['theo_trade_no_long_per_day'] = float(config['COMMON']['trade_no_long_per_day'])
                s_dict['theo_trade_no_short_per_day'] = float(config['COMMON']['trade_no_short_per_day'])
                config_dict[s] = s_dict

                csv_path = os.path.join(root_path, s + '.csv')
                strategy_data = pd.read_csv(csv_path, parse_dates=['Date'])
                strategy_data_dict[s] = strategy_data
                # print(strategy_data)
                # time.sleep(100000)

                last_ind = len(strategy_data['Date']) - 1
                last_qty = strategy_data.iloc[last_ind]['Day End Pos'] if last_ind >= 0 else 0
                last_price = strategy_data.iloc[last_ind]['Day End Price'] if last_ind >= 0 else 0
                s_last_pos_data = pd.DataFrame({'Strategy': [s],
                                                'Qty': [last_qty],
                                                'T. Price': [last_price]})
                last_pos_data = last_pos_data.append(s_last_pos_data)
            else:   # if such config file not exists, will create an alert
                print("[generate_report] ERROR! No configure file for strategy %s. You should first calculate "
                      "the theoretical pnl & std. To do this, you will go to the backtesting result generated by AmiBroker "
                      " and convert the trade-by-trade pnl into day-by-day pnl and calculate the average daily pnl as "
                      "'theoretical pnl' and calculate the std as 'std' here." 
                      "But an empty .csv is generated with zero theo pnl & std!", s)
                config_data = configparser.ConfigParser()
                config_data['COMMON'] = {}
                config_data['COMMON']['theo_pnl_per_day'] = '0'
                config_data['COMMON']['pnl_std'] = '0'
                config_data['COMMON']['mode'] = 'point'
                config_data['COMMON']['underlying'] = 'HSI'
                config_data['COMMON']['multiplier'] = '50'
                config_data['COMMON']['lot_size'] = '1'
                config['COMMON']['trade_no_per_day'] = 0
                config['COMMON']['trade_no_long_per_day'] = 0
                config['COMMON']['trade_no_short_per_day'] = 0
                with open(config_path, 'w') as configfile:
                    config_data.write(configfile)

                strategy_data = pd.DataFrame({
                    'Date': [], 'Underlying': [], 'Theo PnL': [], 'Upper 1 STD': [], 'Lower 1 STD': [],
                    'Actual PnL': [], 'Actual PnL Cum': [], 'Day End Pos': [], 'Day End Price': [],
                    'Perfect PnL': [], 'Perfect PnL Cum': [],
                    'Buy': [], 'Sell': [], 'Short': [], 'Cover': [], 'Trade No': [], 'Trade No Cum': [],
                    'Theo Trade No Cum': [], 'Theo Trade No Cum - Long': [], 'Theo Trade No Cum - Short': []
                })
                strategy_data.to_csv(os.path.join(root_path, s + '.csv'), index=None)
                strategy_data_dict[s] = strategy_data
                all_strategies_file_exist = False
        if not all_strategies_file_exist:
            raise Exception("Strategy files not existing!")
        print('--------------- Init Data Read! --------------- ')
        # print(last_pos_data)
        # time.sleep(1000000)

        # ---------------------- get daily pnl ----------------------
        #  if we want to store last open position in csv
        # last_pos_path = os.path.join(root_path, "last_open_positions.csv")
        trades_path = os.path.join(trades_root_path, 'MC' + today_date_str_yyyymmdd +'.csv')
        end_of_day_price_path = os.path.join(root_path, "parameters", "underlying_price.csv")
        contract_multiplier_path = os.path.join(root_path, "parameters", "contract_multiplier.csv")
        commission_path = os.path.join(root_path, "parameters", "commission table.csv")
        output_path_parse_trades_pnl = os.path.join(root_path, "daily_pnl", today_date_str_yyyymmdd + "_pnl.csv")
        daily_trade_record_output_path = os.path.join(root_path, "trade_records")
        pnl = self.parse_trades_from_MC_records(acc_strategy_map_path, trades_path, last_pos_data,
                                                end_of_day_price_path, contract_multiplier_path, commission_path,
                                                strategy_config_dict=config_dict,
                                                today_date=today_date, daily_pnl_output_path=output_path_parse_trades_pnl,
                                                daily_trade_record_output_path=daily_trade_record_output_path,
                                                source=source)

        print(pnl)
        print('--------------- PnL Calculated! --------------- ')

        # ---------------- add record & draw equity curve ----------------
        for s in all_strategies:
            strategy_data = strategy_data_dict[s]
            l = len(strategy_data)+1
            theo_pnl = config_dict[s]['theo_pnl_per_day'] * l * config_dict[s]['multiplier'] * config_dict[s]['lot_size']
            theo_upper_band = theo_pnl + config_dict[s]['pnl_std'] * math.sqrt(l) \
                              * config_dict[s]['multiplier'] * config_dict[s]['lot_size']
            theo_lower_band = theo_pnl - config_dict[s]['pnl_std'] * math.sqrt(l) \
                              * config_dict[s]['multiplier'] * config_dict[s]['lot_size']
            actual_profit = 0
            day_end_pos = 0
            day_end_pos_price = 0
            buy_num = sell_num = short_num = cover_num = 0
            trade_no = 0
            theo_trade_no = config_dict[s]['theo_trade_no_per_day'] * l
            theo_trade_no_long = config_dict[s]['theo_trade_no_long_per_day'] * l
            theo_trade_no_short = config_dict[s]['theo_trade_no_short_per_day'] * l
            if s in list(pnl['Strategy']):
                actual_profit = list(pnl['Actual PnL'][pnl['Strategy'] == s])[0]
                day_end_pos = list(pnl['Day End Pos'][pnl['Strategy'] == s])[0]
                day_end_pos_price = list(pnl['Day End Price'][pnl['Strategy'] == s])[0]
                buy_num = list(pnl['Buy'][pnl['Strategy'] == s])[0]
                sell_num = list(pnl['Sell'][pnl['Strategy'] == s])[0]
                short_num = list(pnl['Short'][pnl['Strategy'] == s])[0]
                cover_num = list(pnl['Cover'][pnl['Strategy'] == s])[0]
                trade_no = list(pnl['Trade No'][pnl['Strategy'] == s])[0]
                print('%s %f' % (s, actual_profit))
            rec = pd.DataFrame({
                'Date': [today_date],
                'Underlying': [self.UNDERLYING_DICT[config_dict[s]['underlying']]],
                'Theo PnL': [theo_pnl],
                'Upper 1 STD': [theo_upper_band],
                'Lower 1 STD': [theo_lower_band],
                'Actual PnL': [actual_profit],
                'Perfect PnL': [0],
                'Day End Pos': [day_end_pos],
                'Day End Price': [day_end_pos_price],
                'Buy': [buy_num],
                'Sell': [sell_num],
                'Short': [short_num],
                'Cover': [cover_num],
                'Trade No': [trade_no],
                'Theo Trade No Cum': [theo_trade_no],
                'Theo Trade No Cum - Long': [theo_trade_no_long],
                'Theo Trade No Cum - Short': [theo_trade_no_short]
            })
            strategy_data = strategy_data.append(rec, sort=False)
            strategy_data['Actual PnL Cum'] = strategy_data['Actual PnL'].cumsum()
            strategy_data['Perfect PnL Cum'] = strategy_data['Perfect PnL'].cumsum()
            strategy_data['Trade No Cum'] = strategy_data['Trade No'].cumsum()
            strategy_data = strategy_data[[
                'Date', 'Underlying', 'Theo PnL', 'Upper 1 STD', 'Lower 1 STD', 'Actual PnL', 'Actual PnL Cum',
                'Day End Pos', 'Day End Price', 'Perfect PnL', 'Perfect PnL Cum',
                'Buy', 'Sell', 'Short', 'Cover', 'Trade No', 'Trade No Cum',
                'Theo Trade No Cum', 'Theo Trade No Cum - Long', 'Theo Trade No Cum - Short'
            ]]
            strategy_data.to_csv(os.path.join(root_path, s + '.csv'), index=None, float_format='%.2f')
            # print(strategy_data)

            title = today_date_str_yyyymmdd + "_" + s
            plt = self.equity_curve_draw(
                profit_avg=config_dict[s]['theo_pnl_per_day'] * config_dict[s]['multiplier'] * config_dict[s]['lot_size'],
                profit_std=config_dict[s]['pnl_std'] * config_dict[s]['multiplier'] * config_dict[s]['lot_size'],
                actual_profit=strategy_data['Actual PnL Cum'],
                perfect_profit=None, std_multiple=1, mode=1, title=title
            )
            plt.savefig(os.path.join(root_path, 'daily_pnl', title+'.png'))

        print('--------------- PnL Updated & Figure saved! Date=' + today_date_str_yyyymmdd + ' --------------- ')


    def parse_trades_from_MC_records(self, acc_strategy_map_path, trades_path, last_pos_path_or_data,
                                     end_of_day_price_path, contract_multiplier_path, commission_path,
                                     strategy_config_dict,
                                     today_date, daily_pnl_output_path=None, daily_trade_record_output_path=None,
                                     source=1):
        """
        This function parses trade data from SP or Multi-Chart and calculates pnl.
        Assumptions:
            1. You will need to provide initial positions for each strategy.
                This function will add one trade representing the initial position for each strategy.
            2. You will need to provide closing price of the underlying for today.
                This function will add one trade representing the cloing position for each strategy.

        source: 1 - Sharp Point, 2 - Multi Chart
        :param acc_strategy_map_path:
            If source=1:
                We don't know which SP account relates to which strategy. So we need this map.
                For a sample file, see S:\\Amibroker project\\MCReport\\daily_monitor\\acc_strategy_map_sp.csv
            If source=2:
                We don't need a map between account & strategy. We just need a list of strategy.
                For a sample file, see S:\\Amibroker project\\MCReport\\daily_monitor\\acc_strategy_map_mc.csv
        :param trades_path:
        :param last_pos_path_or_data:
        :param end_of_day_price_path:
        :param contract_multiplier_path:
        :param commission_path:
        :param daily_pnl_output_path:
        :param source:
        :return:
        """
        today_date = pd.Timestamp(today_date)
        # ---------------------- the all strategies ----------------------
        all_strategies = []
        if source == 1:
            with open(acc_strategy_map_path) as f:
                acc_strategy_content = f.readlines()
            acc_strategy_map = {}
            for c in acc_strategy_content:
                carr = c.split(',')
                acc_strategy_map[carr[0]] = carr[1].replace('\n', '')
            all_strategies = list(acc_strategy_map.values())
        if source == 2:
            with open(acc_strategy_map_path) as f:
                s = f.readline()
                all_strategies = s.split(',')
                all_strategies[len(all_strategies) - 1] = all_strategies[len(all_strategies)-1].replace('\n', '')
                # print(all_strategies)

        # ----------------------  read contract multiplier data ----------------------
        contract_multiplier = {}
        with open(contract_multiplier_path) as f:
            contract_multiplier_content = f.readlines()
        for c in contract_multiplier_content:
            carr = c.split(',')
            contract_multiplier[carr[0]] = float(carr[1])

        # -------------------- read commission_table_path -------------------
        commission = {}
        with open(commission_path) as f:
            commission_content = f.readlines()
        for c in commission_content:
            carr = c.split(',')
            commission[carr[0]] = float(carr[1])
        # print(commission)

        # -------------------- read end-of-day price -------------------
        end_of_day_price = {}  # date -> underlying -> price
        with open(end_of_day_price_path) as f:
            end_of_day_content = f.readlines()
        for e in end_of_day_content:
            earr = e.split(',')
            e_date = pd.Timestamp(datetime.datetime.strptime(earr[0], '%d/%m/%Y'))  # pandas.Timestamp
            if e_date not in end_of_day_price:
                end_of_day_price[e_date] = {}
            end_of_day_price[e_date][earr[1]] = float(earr[2])
        # print(end_of_day_price)

        # ----------------------  read trades data ----------------------
        data = pd.DataFrame()
        if source == 1:
            data = pd.read_csv(trades_path)
            data = data.dropna(axis=0, how='any')
            data_len = len(data)

            data['Trade Time2'] = data.apply(lambda x: pd.datetime.strptime(x['Trade Time'], '%d/%m/%Y %H:%M'), axis=1)
            data = data.drop(['Trade Time'], axis=1)
            data = data.rename({'Trade Time2':'Trade Time'}, axis=1)
            data['Trade Time'] = data['Trade Time'].astype('datetime64')
            # print(data)

            def judge_float(num):
                try:
                    f = float(num)
                    return f
                except ValueError:
                    return None

            def judge_qty_sp(row):
                bqty = judge_float(row['BQty'])
                if bqty is not None:
                    return bqty
                else:
                    return judge_float(row['SQty']) * -1

            data['Qty'] = data.apply(judge_qty_sp, axis=1)
            data = data[
                data['Account'].apply(
                    lambda x: x in list(acc_strategy_map.keys())
                )
            ]
            data['Strategy'] = data.apply(lambda x: acc_strategy_map[x['Account']], axis=1)
            to_del_cols = ['BQty', 'SQty', 'Trade#', 'Order#', 'Gateway Code', 'Initiator', 'Ext.Order#', 'Reference', 'Account']
            for c in to_del_cols:
                if c in list(data.columns):
                    data = data.drop(c, axis=1)
            data = data[['ID', 'T. Price', 'Trade Time', 'Qty', 'Strategy']]
            # print(data)
            #       ID  T. Price          Trade Time  Qty Strategy
            # 0  HSIU8   26596.0 2018-09-11 09:15:00  1.0  Model01
            # 1  HSIU8   26597.0 2018-09-11 09:15:00  1.0  Model01
            # 2  HSIU8   26475.0 2018-09-11 09:31:00 -2.0  Model01
            # 3  HSIU8   26475.0 2018-09-11 09:31:00 -2.0  Model01
            # 4  HSIU8   26625.0 2018-09-11 09:36:00  2.0  Model01
            # 5  HSIU8   26391.0 2018-09-11 15:22:00 -2.0  Model01
            # 6  HSIU8   26121.0 2018-09-11 21:08:00  2.0  Model01
            # 7  HSIU8   26215.0 2018-09-11 22:00:00  2.0  Model01

        if source == 2:
            def dateparser(d, t):
                return pd.datetime.strptime(d + ' ' + t, '%Y/%m/%d %H:%M:%S')
            data = pd.read_csv(trades_path, parse_dates={'Trade Time': ['日期', '时间']}, date_parser=dateparser)
            data = data.drop(data.columns[1], axis=1)
            # print(data)
            data_len = len(data)

            if data_len > 0:
                def MC_ID_converter(row):
                    # e.g. "HSI 1809" -> "HIU8"
                    sarr = row['合约'].split(' ')  # e.g. sarr = ['HSI', '1810']
                    str1 = 'HI' if sarr[0] == 'HSI' else 'HC'   # either HSI or HSCEI

                    d = self.FUTURES_LETTER_MONTH_MAP
                    return str1 + d[int(sarr[1][2:4])] + sarr[1][1]
                data['ID'] = data.apply(MC_ID_converter, axis=1)

                def MC_qty(row):
                    qty = row['成交手数'] if '买' in row['买/卖'] else -row['成交手数']
                    return qty
                data['Qty'] = data.apply(MC_qty, axis=1)

                to_del_cols = ['投资者', '合约', '买/卖', '开/平', '委托种类', '成交手数', '报单编号', '日期',
                               '时间', '备注', '合约名称', '触发条件', '报单手数', '策略ID']
                for c in to_del_cols:
                    if c in list(data.columns):
                        data = data.drop(c, axis=1)
                data = data.rename({'成交均价': 'T. Price', '策略名称': 'Strategy'}, axis=1)
                data = data[['ID', 'T. Price', 'Trade Time', 'Qty', 'Strategy']]

                data['Multiplier'] = data.apply(lambda x: contract_multiplier[x['ID']], axis=1)
                def get_gross_amount(row):
                    if row['Qty'] > 0:
                        return -(row['T. Price'] * row['Qty'] * row['Multiplier'] + commission[row['ID']] * row['Qty'])
                    if row['Qty'] < 0:
                        return -(row['T. Price'] * row['Qty'] * row['Multiplier'] - commission[row['ID']] * row['Qty'])

                data['Value'] = data.apply(get_gross_amount, axis=1)
            else:
                data['ID'] = []
                data['T. Price'] = []
                data['Trade Time'] = []
                data['Qty'] = []
                data['Strategy'] = []
                data['Multiplier'] = []
                data['Value'] = []

            data = data[['ID', 'T. Price', 'Trade Time', 'Qty', 'Strategy', 'Multiplier', 'Value']]
        if daily_trade_record_output_path is not None:
            today_date_str_yyyymmdd = today_date.strftime('%Y%m%d')
            for s in all_strategies:
                recs = data[data['Strategy'] == s]
                p = os.path.join(daily_trade_record_output_path, s)
                if not os.path.exists(p):
                    os.mkdir(p)
                p = os.path.join(p, today_date_str_yyyymmdd+'.csv')
                if recs is None or len(recs) == 0:
                    pd.DataFrame().to_csv(p)
                    continue
                dt_format = '%d/%m/%Y %H:%M:%S'
                recs.to_csv(p, index=None, date_format=dt_format)

        new_time = pd.Timestamp(year=today_date.year, month=today_date.month, day=today_date.day, hour=3)
        if data_len > 0:
            data['Trade Time'] = data.apply(lambda x: x['Trade Time'] if x['Trade Time'] > today_date else new_time, axis=1)
        # data = data.sort_values(by=['Trade Time'], ascending=True)
        # print(data)

        # ----------------------  read previous positions and append it to 'data' ----------------------
        if isinstance(last_pos_path_or_data, str):
            data_init = pd.read_csv(last_pos_path_or_data)
        elif isinstance(last_pos_path_or_data, pd.DataFrame):
            data_init = last_pos_path_or_data
        else:
            raise TypeError("'last_pos_path_or_data' should be a path or DataFrame")

        data_init = data_init[data_init['Qty'] != 0]
        for s in all_strategies:
            rec = data_init[data_init['Strategy'] == s].copy()
            # data_this_strategy = data[data['Strategy'] == s]
            # print(rec)
            if len(rec) > 0:
                # if len(data_this_strategy) > 0:
                rec.loc[:, 'Trade Time'] = today_date   # actually the time is not very important
                rec.loc[:, 'ID'] = self.UNDERLYING_DICT[strategy_config_dict[s]['underlying']]
                rec.loc[:, 'Multiplier'] = contract_multiplier[
                    self.UNDERLYING_DICT[strategy_config_dict[s]['underlying']]
                ]
                rec.loc[:, 'Value'] = -(rec['T. Price'] * rec['Qty'] * rec['Multiplier'])   # no commission
                rec = rec[list(data.columns)]
                data = data.append(rec, ignore_index=True)
        # print(data)
        data = data.sort_values(by=['Trade Time'], ascending=True)
        # time.sleep(100000)

        # ------------------- calculate day end positions --------------------
        day_end_pos = data.groupby(by='Strategy')['Qty'].sum()
        # print('Today day_end pos-> \n%s' % day_end_pos)
        day_end_pos_price = day_end_pos.copy()
        for s in day_end_pos.index:
            if day_end_pos[s] == 0:
                day_end_pos_price[s] = 0
            else:
                day_end_pos_price[s] = end_of_day_price[today_date][
                    self.UNDERLYING_DICT[strategy_config_dict[s]['underlying']]
                ]
        day_end_pos = pd.DataFrame({'Strategy':day_end_pos.index, 'Day End Pos':day_end_pos.values})
        day_end_pos_price = pd.DataFrame({'Strategy': day_end_pos_price.index, 'Day End Price': day_end_pos_price.values})
        # print('Today day_end pos price-> \n%s' % day_end_pos_price)
        # print('Today day_end pos -> \n%s' % day_end_pos)

        # -------------------- calculate trade No -------------
        day_end_trade_no = pd.DataFrame({
            'Buy': [0] * len(all_strategies),
            'Sell': [0] * len(all_strategies),
            'Short': [0] * len(all_strategies),
            'Cover': [0] * len(all_strategies),
            'Trade No': [0] * len(all_strategies)
        }, index=all_strategies)
        # print(day_end_trade_no)

        for s in all_strategies:
            data_s = data[data['Strategy'] == s]
            if len(data_s) == 0:
                continue
            data_s.loc[:, 'CumQty'] = data_s['Qty'].cumsum()
            # print(111)
            buy_num = len(data_s[data_s['CumQty'] == 1])
            short_num = len(data_s[data_s['CumQty'] == -1])
            prev_init = data_init[data_init['Strategy'] == s]
            if len(prev_init) > 0:
                if prev_init['Qty'][0] == 1:
                    buy_num = buy_num - 1
                if prev_init['Qty'][0] == -1:
                    short_num = short_num - 1
            sell_num = 0
            cover_num = 0
            for i in range(1, len(data_s)):  # skip the first element
                if data_s.iloc[i]['CumQty'] != 0:
                    continue
                if data_s.iloc[i-1]['CumQty'] == 1:
                    sell_num = sell_num + 1
                if data_s.iloc[i-1]['CumQty'] == -1:
                    cover_num = cover_num + 1
            day_end_trade_no.loc[s, 'Buy'] = buy_num
            day_end_trade_no.loc[s, 'Sell'] = sell_num
            day_end_trade_no.loc[s, 'Short'] = short_num
            day_end_trade_no.loc[s, 'Cover'] = cover_num
            day_end_trade_no.loc[s, 'Trade No'] = cover_num + sell_num
        day_end_trade_no = day_end_trade_no.reset_index()
        day_end_trade_no = day_end_trade_no.rename({'index': 'Strategy'}, axis=1)
        # print('Today day_end_trade_no -> \n%s' % day_end_trade_no)


        # ---------------------- append an imaginary closing trade for all open positions ----------------------
        open_pos = data.groupby(by='Strategy')['Qty'].sum()
        # print(list(open_pos.index))
        for s in all_strategies:
            this_open_pos = open_pos[open_pos.index == s]
            # print("%s \n s=%s" % (this_open_pos, s))
            if len(this_open_pos) > 0 and this_open_pos[0] != 0:
                data_this_strategy = data[data['Strategy'] == s]
                underlying_id = data_this_strategy.iloc[-1]['ID']

                price = end_of_day_price[today_date][underlying_id]
                qty = -this_open_pos[0]
                multiplier = contract_multiplier[underlying_id]
                rec = pd.DataFrame({'Trade Time': [max(data_this_strategy['Trade Time'])],
                                    'ID': [underlying_id], 'T. Price': [price], 'Qty': [qty],
                                    'Strategy': [s], 'Multiplier': [multiplier], 'Value': [-price * qty * multiplier]
                                    })
                data = data.append(rec, sort=True)

        # ---------------------- now calculate the pnl ----------------------
        data = data.sort_values(by=['Trade Time'], ascending=True)
        # print(data)
        pnl = data.groupby(by=['Strategy'])['Value'].sum()
        pnl = pd.DataFrame({'Strategy': pnl.index, 'Actual PnL': pnl.values})

        pnl = pnl.merge(day_end_pos, on='Strategy', how='outer')
        pnl = pnl.merge(day_end_pos_price, on='Strategy', how='outer')
        pnl = pnl.merge(day_end_trade_no, on='Strategy', how='outer')
        pnl = pnl.fillna(0)
        # print('Today P&L ->')
        # print(pnl)

        if daily_pnl_output_path is not None:
            # pass
            pnl.to_csv(daily_pnl_output_path)
        return pnl


    def equity_curve_draw(self, profit_avg, profit_std, actual_profit, perfect_profit=None,
                          std_multiple=1, mode=1, title='', x_axis=None):
        """
        This will plot actual equity curve vs. expected equity curve.
        Reference: Building Winning Algorithmic Trading Systems, page 212
        :param profit_avg:       expected avg profit per day/trade
        :param profit_std:        std of the profits
        :param actual_profit:   executed profit
        :param perfect_profit:  the profit assuming no execution errors
        :param std_multiple:    num of std
        :param mode:              1 - by day; 2 - by trade
        :return:
        """
        if not isinstance(actual_profit, (list, np.ndarray, pd.Series)):
            raise TypeError('Actual profit should be one of list, numpy.ndarray, pandas.Series. Type=%s'
                            % type(actual_profit))
        # add 0 to the beginning of the array
        actual_profit = np.append(np.array([0]), np.array(actual_profit))
        if perfect_profit is not None:
            perfect_profit = np.append(np.array([0]), np.array(perfect_profit))

        actual_profit_len = len(actual_profit)
        total_len = int(actual_profit_len * 1.5)

        x = np.linspace(0, total_len, total_len+1)
        if x_axis is None:
            x_axis = x
        zero_line = 0 * x

        mid_curve = x * profit_avg
        upper_curve = mid_curve + std_multiple * np.sqrt(x) * profit_std
        lower_curve = mid_curve - std_multiple * np.sqrt(x) * profit_std
        upper_curve2 = mid_curve + std_multiple * np.sqrt(x) * profit_std * 2
        lower_curve2 = mid_curve - std_multiple * np.sqrt(x) * profit_std * 2

        plt.figure()
        plt.rc('grid', linestyle='--', color='grey', linewidth=0.8)
        plt.grid(True)
        plt.plot(x, zero_line, color='grey', linestyle='--', linewidth=1)
        plt.plot(x, mid_curve, color='black', label='Expected P&L', linewidth=1)
        plt.plot(x, upper_curve, color='green', label='+' + str(std_multiple) + ' std', linewidth=1)
        plt.plot(x, lower_curve, color='red', label='-' + str(std_multiple) + ' std', linewidth=1)
        plt.plot(x, upper_curve2, color='green', label='+' + str(std_multiple*2) + ' std', linewidth=1, linestyle='--')
        plt.plot(x, lower_curve2, color='red', label='-' + str(std_multiple*2) + ' std', linewidth=1, linestyle='--')

        plt.plot(x[0:len(actual_profit)], actual_profit, '-o', linewidth=1,
                 color='#00008b', label='Actual P&L', markersize=3)
        if perfect_profit is not None:
            plt.plot(x[0:len(actual_profit)], perfect_profit, '-o', linewidth=1,
                     color='#008081', label='Perfect P&L', markersize=3)

        plt.legend(loc='upper left')
        x_label = 'days' if mode == 1 else 'trades'
        plt.xlabel('# of ' + x_label)
        plt.ylabel('$')
        by_day_trade = 'date' if mode == 1 else 'trade'
        plt.title(title + '_by' + by_day_trade)
        # plt.show()

        return plt


if __name__ == '__main__':
    # profit_avg = 13.15
    # profit_std = 160.6
    #
    # sim_len = 40
    # actual_profit = np.linspace(1, sim_len, sim_len) * profit_avg + np.random.randint(-100, 100, sim_len) / 100 * profit_std
    # # equity_curve_draw(profit_avg, profit_std, actual_profit, actual_profit+100)
    #
    # # ----------------------- calculate pnl demo --------------
    # acc_strategy_map_path = 'S:\\Amibroker project\\MCReport\\daily_monitor\\all_strategy_list_mc.csv'
    # mc_record_path = 'S:\\Amibroker project\\MCReport\\MC20180921.csv'
    # mc_init_path = 'S:\\Amibroker project\\MCReport\\daily_monitor\\last_open_positions.csv'
    # end_of_day_price_path = 'S:\\Amibroker project\\MCReport\\daily_monitor\\underlying_price.csv'
    # contract_multiplier_path = 'S:\\Amibroker project\\MCReport\\daily_monitor\\contract_multiplier.csv'
    # commission_path = 'S:\\Amibroker project\\MCReport\\daily_monitor\\commission table.csv'
    # parse_trades_from_MC_records(acc_strategy_map_path, mc_record_path, mc_init_path,
    #                              end_of_day_price_path,
    #                              contract_multiplier_path, commission_path,
    #                              'S:\\Amibroker project\\MCReport\\daily_monitor\\pnl_20180921.csv',
    #                              source=2)

    # ------------ run the console1 -----------
    root_path = 'S:\\Amibroker project\\Report\\daily_monitor'
    trades_root_path = 'S:\\Amibroker project\\MCReport'
    today_date_list = [pd.Timestamp('2018-10-08')]
    sm = StrategyMonitory(root_path, trades_root_path, today_date_list, source=2)
    sm.run()

    # config_path = "S:\\Amibroker project\\HTML_Report\\html_config.ini"
    # html_builder = GenerateHTML(config_path)
    # html_builder.generate_monitoring_main()




