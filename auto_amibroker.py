"""
This is a master file that will do a lot of work. Work flow as below:

1. We need to write an initial strategy that we want to test either in this python or in another file.
2. This python will combine codes above with 51 filters to generate another 51 AFL files.
3. Then this python will use a template .apx file to generate multiple .apx files.
4. Then this python will run above .apx files in Amibroker. (After testing, we don't this anymore, instead we generate an ABB file and run in AB.)
5. Since each AFL has a unique name, we can distinguish which file is the final "out-of-sample" result file.
    We then copy the results into a folder for further use.

"""
import os
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
import win32com.client
import time
import configparser

CONFIG_FILE_PATH = 'S:\\Amibroker project\\Code\\run_config.ini'
config = configparser.ConfigParser()
config.read(CONFIG_FILE_PATH)

# ============================================================================
# Frequently used variables
# ============================================================================
STRATEGY_NAME = config['COMMON']['STRATEGY_NAME']
SYMBOL_NAME = config['COMMON']['SYMBOL_NAME']  # this is the name for the underlying in Amibroker
UNDERLYING_NAME = config['COMMON']['UNDERLYING_NAME']   # this is the name appeared in AFL/APX/ABB files
FREQUENCY = config['COMMON']['FREQUENCY']        # this will appear in AFL/APX/ABB files
AFL_PATH = config['COMMON']['AFL_PATH']        # file that contains only the main body of the strategy
AFL_HEAD_SETTINGS_PATH = config['COMMON']['AFL_HEAD_SETTINGS_PATH']

GEN_FILTER_OUTPUT_ROOT_PATH = config['COMMON']['GEN_FILTER_OUTPUT_ROOT_PATH']
APX_TEMPLATE_PATH = config['COMMON']['APX_TEMPLATE_PATH']
GEN_APX_OUTPUT_ROOT_PATH = GEN_FILTER_OUTPUT_ROOT_PATH
GEN_ABB_OUTPUT_ROOT_PATH = GEN_FILTER_OUTPUT_ROOT_PATH

AB_REPORTS_PATH = config['COMMON']['AB_REPORTS_PATH']
COPY_RESULTS_PATHS = config['COMMON']['COPY_RESULTS_PATHS']

# ============================================================================
# Variables for generating filters
# ============================================================================
NUM_FILTERS = int(config['GEN_AFL']['NUM_FILTERS'])
GEN_FILTER_OUTPUT_ROOT_PATH = GEN_FILTER_OUTPUT_ROOT_PATH

f = open(AFL_PATH, 'r')
AFL_MAINBODY = f.read()
f.close()
# sample AFL_MAINBODY below...
"""
//Optimize Var
FMAPeriod = Optimize("FMAPeriod",5,5,25,1);
SMAPeriod = Optimize("SMAPeriod",25,25,100,1);

//Formula
FMA = EMA(Close,FMAPeriod);
SMA = EMA(Close,SMAPeriod);

// BuySignal..
BuySignal = Cross(FMA,SMA);
SellSignal = Cross(SMA,FMA);
ShortSignal = Cross(SMA,FMA);
CoverSignal = Cross(FMA,SMA);
"""

f = open(AFL_HEAD_SETTINGS_PATH, 'r')
AFL_HEAD_SETTINGS = f.read()
f.close()
# sample AFL_HEAD_SETTINGS below...
"""
//Settings
noOfShares = 1;
SetPositionSize( noOfShares, spsShares );
SetTradeDelays(1,1,1,1);
OptimizerSetEngine("spso");
OptimizerSetOption("Runs", 3 );
OptimizerSetOption("MaxEval", 5000);
"""
# ============================================================================
# Variables for generating .apx files
# ============================================================================
APX_TEMPLATE_PATH = APX_TEMPLATE_PATH
GEN_APX_OUTPUT_ROOT_PATH = GEN_APX_OUTPUT_ROOT_PATH

APPLY_TO = config['GEN_APX']['APPLY_TO']  # 0 - all symbols, 1 - current, 2 - filter
WATCHLIST_NUMBER = config['GEN_APX']['WATCHLIST_NUMBER']

FREQUENCY_PERIODICITY_dict = {'daily': 0, 'day/night': 1, 'hourly': 2, '15min': 3, '5min': 4,
                              '1min': 5, '60min': 2, 'tick': 9, '3min': 10, '30min': 11}
PERIODICITY = FREQUENCY_PERIODICITY_dict[FREQUENCY]
PERIODICITY_IND = int(config['GEN_APX']['PERIODICITY_IND'])

IS_ENABLED = config['GEN_APX']['IS_ENABLED']
IS_ENABLED_IND = int(config['GEN_APX']['IS_ENABLED_IND'])  # num under 'BacktestSettings'

IS_START_DATE = config['GEN_APX']['IS_START_DATE']
IS_START_DATE_IND = int(config['GEN_APX']['IS_START_DATE_IND'])

IS_END_DATE = config['GEN_APX']['IS_END_DATE']
IS_END_DATE_IND = int(config['GEN_APX']['IS_END_DATE_IND'])

IS_LAST_DATE = config['GEN_APX']['IS_LAST_DATE']
IS_LAST_DATE_IND = int(config['GEN_APX']['IS_LAST_DATE_IND'])

IS_STEP = config['GEN_APX']['IS_STEP']
IS_STEP_IND = int(config['GEN_APX']['IS_STEP_IND'])

IS_STEP_UNIT = config['GEN_APX']['IS_STEP_UNIT']  # 1 - year, 2 - month
IS_STEP_UNIT_IND = int(config['GEN_APX']['IS_STEP_UNIT_IND'])

IS_ANCHORED = config['GEN_APX']['IS_ANCHORED']
IS_ANCHORED_IND = int(config['GEN_APX']['IS_ANCHORED_IND'])

IS_LAST_USES_TODAY = config['GEN_APX']['IS_LAST_USES_TODAY']
IS_LAST_USES_TODAY_IND = int(config['GEN_APX']['IS_LAST_USES_TODAY_IND'])

OS_ENABLED = config['GEN_APX']['OS_ENABLED']
OS_ENABLED_IND = int(config['GEN_APX']['OS_ENABLED_IND'])

OS_START_DATE = config['GEN_APX']['OS_START_DATE']
OS_START_DATE_IND = int(config['GEN_APX']['OS_START_DATE_IND'])

OS_END_DATE = config['GEN_APX']['OS_END_DATE']
OS_END_DATE_IND = int(config['GEN_APX']['OS_END_DATE_IND'])

OS_LAST_DATE = config['GEN_APX']['OS_LAST_DATE']
OS_LAST_DATE_IND = int(config['GEN_APX']['OS_LAST_DATE_IND'])

OS_STEP = config['GEN_APX']['OS_STEP']
OS_STEP_IND = int(config['GEN_APX']['OS_STEP_IND'])

OS_STEP_UNIT = config['GEN_APX']['OS_STEP_UNIT']  # 1 - year, 2 - month
OS_STEP_UNIT_IND = int(config['GEN_APX']['OS_STEP_UNIT_IND'])

OS_ANCHORED = config['GEN_APX']['OS_ANCHORED']
OS_ANCHORED_IND = int(config['GEN_APX']['OS_ANCHORED_IND'])

OS_LAST_USES_TODAY = config['GEN_APX']['OS_LAST_USES_TODAY']
OS_LAST_USES_TODAY_IND = int(config['GEN_APX']['OS_LAST_USES_TODAY_IND'])


def get_num_str(num):
    to_return = ''
    #
    # if num < 10:
    #     to_return = '00' + str(num)
    # elif num < 100:
    #     to_return = '0' + str(num)
    # else:
    #     to_return = str(num)

    if num < 10:
        to_return = '0' + str(num)
    else:
        to_return = str(num)

    return to_return


class GenFilter:
    def __init__(self, num_filters, underlying_name, freq_name, strategy_name, output_root_path,
                 main_body_code, headsettings):
        self.num_filters = num_filters
        self.underlying_name = str(underlying_name)
        self.freq_name = str(freq_name)
        self.strategy_name = str(strategy_name)
        self.output_root_path = output_root_path

        self.output_root_path = os.path.join(output_root_path, self.strategy_name)
        if not os.path.exists(self.output_root_path):
            os.mkdir(self.output_root_path)
        self.output_root_path = os.path.join(self.output_root_path, 'afl')
        if not os.path.exists(self.output_root_path):
            os.mkdir(self.output_root_path)

        self.main_body_code = main_body_code
        self.headsettings = headsettings

    def run(self):
        output_path_list = []
        for i in range(1, self.num_filters + 1):
            codes = self.gen_codes(i)
            output_path = os.path.join(
                self.output_root_path,
                self.underlying_name + ';' + self.freq_name + ';'
                + self.strategy_name + 'Test' + get_num_str(i) + '.afl'
            )
            with open(output_path, 'w') as f:
                f.write(codes)
            f.close()
            output_path_list.append(output_path)

        return output_path_list

    def gen_include_code(self, num):
        if not isinstance(num, int):
            raise TypeError('num must be an int! num=%s' % num)
        num_str = get_num_str(num)
        return "#include <Test" + num_str + ".afl>"

    def gen_codes(self, num):
        if not isinstance(num, int):
            raise TypeError('num must be an int! num=%s' % num)

        new_line = '\n'

        settings = self.headsettings

        mainbody = self.main_body_code
        include_line = self.gen_include_code(num)
        exploration = """
/*-------------------------------------
    Exploration
-------------------------------------*/
Filter = 1;
AddColumn( Buy, "Buy" );
AddColumn( Cover, "Cover" );
AddColumn( Sell, "Sell" );
AddColumn( Short, "Short" );"""

        share_control = """
/*-------------------------------------
    Shares Control
-------------------------------------*/
SetPositionSize( noOfShares, spsShares );"""

        optimizaiton_engine_control = """
/*-------------------------------------
    Optimization Engine Control
-------------------------------------*/
if(typeof(OptSteps) == "undefined"){
	OptSteps = 1;
}
if(OptSteps>100){
	OptimizerSetEngine("spso");
	OptimizerSetOption("Runs", 3 );
	OptimizerSetOption("MaxEval", 5000);
}"""
        codes = settings + new_line + \
                mainbody + new_line + \
                include_line + new_line + \
                exploration + new_line + \
                share_control + new_line + \
                optimizaiton_engine_control

        return codes


class GenAPX:
    def __init__(self, afl_path_list, apx_template_path, underlying_name, freq_name, strategy_name, apx_output_path):
        # afl path should be sth. like 'C:\\\\Program Files\\\\AmiBroker\\\\Formulas\\\\Custom\\\\'
        self.afl_path_list = afl_path_list
        self.apx_template_path = apx_template_path

        self.underlying_name = underlying_name
        self.freq_name = freq_name
        self.strategy_name = strategy_name
        self.apx_output_path = os.path.join(apx_output_path, self.strategy_name)
        if not os.path.exists(self.apx_output_path):
            os.mkdir(self.apx_output_path)
        self.apx_output_path = os.path.join(self.apx_output_path, 'apx')
        if not os.path.exists(self.apx_output_path):
            os.mkdir(self.apx_output_path)

    def run(self):
        # afl_path = 'C:\\\\Program Files\\\\AmiBroker\\\\Formulas\\\\Custom\\\\_test_no_use2.afl'
        output_path_list = []
        for afl_path in self.afl_path_list:
            num = os.path.basename(afl_path.split('.')[0])
            num = int(num[-2:])

            afl_path = self.format_path(afl_path)
            afl_codes = ''
            with open(afl_path, 'r') as afl:
                afl_codes = afl.read()
            afl_codes = afl_codes.replace('\n', '\\n')
            # afl_codes = afl_codes.replace('\n', '\r\n')

            # write back
            # afl_path = 'C:\\\\Program Files\\\\AmiBroker\\\\Formulas\\\\Custom\\\\_test_no_use3.afl'
            # with open(afl_path, 'w') as afl:
            #     afl.write(afl_codes)

            # apx_template_path = 'T:\\Amibroker project\\Code\\test_ole\\template.apx'
            root_element = ET.ElementTree(file=self.apx_template_path)
            root_element_tree = root_element.getroot()

            root_element_tree = self.general_settings(root_element_tree, wln=WATCHLIST_NUMBER, apply_to=APPLY_TO,
                                                      formula_content=afl_codes, formula_path=afl_path)
            root_element_tree = self.backtest_settings(root_element_tree)

            # apx_output_path = 'T:\\Amibroker project\\Code\\test_ole\\Analysis20.apx'
            output_path = os.path.join(
                self.apx_output_path,
                self.underlying_name + ';' + self.freq_name + ';'
                + self.strategy_name + 'Test' + get_num_str(num) + '.apx'
            )
            root_element.write(output_path)

            output_path_list.append(output_path)

        return output_path_list

    def format_path(self, p):
        return p.replace('\\', '\\\\')

    def general_settings(self, root_element_tree, apply_to=2, wln=64, formula_content='', formula_path=''):
        root_element_tree = self.set_watchlist_num(root_element_tree, wln)
        root_element_tree = self.set_formula_content(root_element_tree, formula_content)
        root_element_tree = self.set_formula_path(root_element_tree, formula_path)
        root_element_tree = self.set_apply_to(root_element_tree, apply_to)
        return root_element_tree

    def backtest_settings(self, root_element_tree):
        root_element_tree = self.set_value_under_btsetting(root_element_tree, PERIODICITY_IND, PERIODICITY)
        root_element_tree = self.set_value_under_btsetting(root_element_tree, IS_ENABLED_IND, IS_ENABLED)
        root_element_tree = self.set_value_under_btsetting(root_element_tree, IS_START_DATE_IND, IS_START_DATE)
        root_element_tree = self.set_value_under_btsetting(root_element_tree, IS_END_DATE_IND, IS_END_DATE)
        root_element_tree = self.set_value_under_btsetting(root_element_tree, IS_LAST_DATE_IND, IS_LAST_DATE)
        root_element_tree = self.set_value_under_btsetting(root_element_tree, IS_STEP_IND, IS_STEP)
        root_element_tree = self.set_value_under_btsetting(root_element_tree, IS_STEP_UNIT_IND, IS_STEP_UNIT)
        root_element_tree = self.set_value_under_btsetting(root_element_tree, IS_ANCHORED_IND, IS_ANCHORED)
        root_element_tree = self.set_value_under_btsetting(root_element_tree, IS_LAST_USES_TODAY_IND, IS_LAST_USES_TODAY)
        root_element_tree = self.set_value_under_btsetting(root_element_tree, OS_ENABLED_IND, OS_ENABLED)
        root_element_tree = self.set_value_under_btsetting(root_element_tree, OS_START_DATE_IND, OS_START_DATE)
        root_element_tree = self.set_value_under_btsetting(root_element_tree, OS_END_DATE_IND, OS_END_DATE)
        root_element_tree = self.set_value_under_btsetting(root_element_tree, OS_LAST_DATE_IND, OS_LAST_DATE)
        root_element_tree = self.set_value_under_btsetting(root_element_tree, OS_STEP_IND, OS_STEP)
        root_element_tree = self.set_value_under_btsetting(root_element_tree, OS_STEP_UNIT_IND, OS_STEP_UNIT)
        root_element_tree = self.set_value_under_btsetting(root_element_tree, OS_ANCHORED_IND, OS_ANCHORED)
        root_element_tree = self.set_value_under_btsetting(root_element_tree, OS_LAST_USES_TODAY_IND, OS_LAST_USES_TODAY)
        return root_element_tree

    def set_apply_to(self, root_element_tree, apply_to_num):
        general = root_element_tree[0]
        apply_to = general[4]
        apply_to.text = str(apply_to_num)
        return root_element_tree

    def set_watchlist_num(self, root_element_tree, wln):
        # root_element_tree should be a root element tree
        general = root_element_tree[0]
        include_filter = general[12]
        watchlist = include_filter[13]
        watchlist.text = str(wln)
        return root_element_tree

    def set_formula_content(self, root_element_tree, content):
        # root_element_tree should be a root element tree
        general = root_element_tree[0]
        formula_content = general[3]
        formula_content.text = content
        return root_element_tree

    def set_formula_path(self, root_element_tree, content):
        # root_element_tree should be a root element tree
        general = root_element_tree[0]
        formula_content = general[2]
        formula_content.text = content
        return root_element_tree

    def set_value_under_btsetting(self, root_element_tree, ind, content):
        bt_setting = root_element_tree[1]
        to_set = bt_setting[ind]
        to_set.text = str(content)
        return root_element_tree


# TODO: it has been proved that to run multiple AB using below codes is ineffective.... so don't use it. If you really want to use it, please use Python2
class RunAB:
    def __init__(self, apx_path_list, amibroker_results_path, backtest_mode=6):
        """
                        backtest_mode:
                        0 : Scan
                        1 : Exploration
                        2 : Portfolio Backtest
                        3 : Individual Backtest
                        4 : Portfolio Optimization
                        5 : Individual Optimization (supported starting from v5.69)
                        6 : Walk Forward Test
                    """
        self.apx_path_list = apx_path_list
        self.amibroker_results_path = amibroker_results_path
        self.backtest_mode = backtest_mode

    def run(self):
        bk_analysis_list = []
        ab = win32com.client.Dispatch("Broker.Application")
        for apx_file in self.apx_path_list:
            NewA = ab.analysisDocs.open(apx_file)
            NewA.run(6)
            bk_analysis_list.append(NewA)

        while True:
            un_done = False
            for NewA in bk_analysis_list:
                if NewA.IsBusy:
                    un_done = True
                    break
            if un_done:
                time.sleep(1)
            else:
                break
        print('Amibroker all walk-forward backtesting done!')


class GenABB:
    def __init__(self, apx_path_list, underlying_name, freq_name, strategy_name, abb_output_path):
        self.apx_path_list = []
        for p in apx_path_list:
            if '\\\\' in apx_path_list:
                self.apx_path_list.append(p)
            else:
                self.apx_path_list.append(p.replace('\\', '\\\\'))

        self.underlying_name = underlying_name
        self.freq_name = freq_name
        self.strategy_name = strategy_name

        self.abb_output_path = abb_output_path

    def run(self):
        root = ET.Element('AmiBroker-Batch')
        root.attrib = {'CompactMode': '0'}

        for apx_file in self.apx_path_list:
            step_lp = ET.SubElement(root, 'Step')
            step_lp_action = ET.SubElement(step_lp, 'Action')
            step_lp_action.text = 'LoadProject'
            step_lp_param = ET.SubElement(step_lp, 'Param')
            step_lp_param.text = apx_file

            step_wft = ET.SubElement(root, 'Step')
            step_wft_action = ET.SubElement(step_wft, 'Action')
            step_wft_action.text = 'WalkForward'
            step_wft_param = ET.SubElement(step_wft, 'Param')

        tree = ET.ElementTree(root)

        output_path = os.path.join(
            self.abb_output_path,
            self.strategy_name,
            self.underlying_name + ';' + self.freq_name + ';'
            + self.strategy_name + '.abb'
        )
        tree.write(output_path)

        return output_path


class ExtractReportsAB:
    def __init__(self, ab_reports_path, underlying_name, freq_name, strategy_name, output_root_path):
        self.ab_reports_path = ab_reports_path
        self.underlying_name = underlying_name
        self.freq_name = freq_name
        self.strategy_name = strategy_name

        file_list = os.listdir(self.ab_reports_path)
        file_list = [os.path.join(self.ab_reports_path, f) for f in file_list]
        file_modtime = ((os.stat(f), f) for f in file_list)
        file_modtime_sorted = sorted(file_modtime, key=lambda x: -x[1])  # sorted by time descendingly
        self.file_list = [f[0] for f in file_modtime_sorted]

        self.output_path = os.path.join(output_root_path, strategy_name)
        if not os.path.exists(self.output_path):
            os.mkdir(self.output_path)
        self.output_path = os.path.join(self.output_path, 'results')
        if not os.path.exists(self.output_path):
            os.mkdir(self.output_path)

    def run(self):
        for f in self.file_list:
            bf = os.path.basename(f)
            if self.underlying_name in bf and self.freq_name in bf \
                and self.strategy_name in bf and 'Out-of-Sample summary' in bf:
                line = 'xcopy ' + bf + ' ' + os.path(self.output_path, bf) + ' /i'
                os.system(line)


if __name__ == '__main__':
    strategy_name_list = ['PsychologicalLine_trend', 'FearGreedRatio', 'AroonOscillator',
                          'FisherTransform', 'RelativeMomentumIndex_trend1',
                          'RelativeMomentumIndex_trend2', 'REX', 'UltimateOscillator',
                          'MaxMin', 'McGinley_Dynamic', 'McGinley_Dynamic_BB',
                          'STARC_Bands', 'ComdityChanelIndex1', 'ComdityChanelIndex2',
                          'PriceZoneOscillator_reverseal', 'RelativeMomentumIndex_reversal1',
                          'SpearmanIndicator_cond1', 'SpearmanIndicator_cond2',
                          'SpearmanIndicator_cond3', 'SpearmanIndicator_cond4',
                          'MovingLinearRegression'
                          ]
    frequency_list = ['3min', '5min', '15min', '30min', '60min']
    for strategy in strategy_name_list:
        for freq in frequency_list:
            STRATEGY_NAME = strategy
            FREQUENCY = freq
            print('----------- ' + strategy + ' ' + freq + ' ---------------')

            AFL_PATH = 'S:\\Amibroker project\\Code\\Base_AFL\\' + strategy + '.afl'

            gen_filter = GenFilter(NUM_FILTERS, UNDERLYING_NAME, FREQUENCY,
                                   STRATEGY_NAME, GEN_FILTER_OUTPUT_ROOT_PATH, AFL_MAINBODY, AFL_HEAD_SETTINGS)
            afl_path_list = gen_filter.run()
            print('Generating filters done! Symbol=%s' % (SYMBOL_NAME))

            get_apx = GenAPX(afl_path_list, APX_TEMPLATE_PATH, UNDERLYING_NAME, FREQUENCY,
                             STRATEGY_NAME, GEN_APX_OUTPUT_ROOT_PATH)
            apx_path_list = get_apx.run()
            print('Generating apx files done! Symbol=%s' % (SYMBOL_NAME))

            get_abb = GenABB(apx_path_list, UNDERLYING_NAME, FREQUENCY, STRATEGY_NAME, GEN_ABB_OUTPUT_ROOT_PATH)
            abb_path = get_abb.run()
            print('Generating abb files done! Symbol=%s' % (SYMBOL_NAME))

    # run_ab = RunAB(apx_path_list, AB_RESULTS_PATH, backtest_mode=6)
    # run_ab.run()
