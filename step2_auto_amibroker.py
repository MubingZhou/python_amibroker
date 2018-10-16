import os
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
import win32com.client
import time
import configparser
import shutil

CONFIG_FILE_PATH = 'T:\\Amibroker project\\Code\\step2_run_config.ini'
config = configparser.ConfigParser()
config.read(CONFIG_FILE_PATH)

# ============================================================================
# Frequently used variables
# ============================================================================
STRATEGY_NAME = config['COMMON']['STRATEGY_NAME']
TEST_CHOSEN = int(config['COMMON']['TEST_CHOSEN'])
SYMBOL_NAME = config['COMMON']['SYMBOL_NAME']  # this is the name for the underlying in Amibroker
UNDERLYING_NAME = config['COMMON']['UNDERLYING_NAME']   # this is the name appeared in AFL/APX/ABB files
FREQUENCY = config['COMMON']['FREQUENCY']
ORIGINAL_AFL_ROOT_PATH = config['COMMON']['orginal_afl_root_path']        # file that contains the chosen afl
STEP2_AFL_APX_ABB_ROOT_PATH = config['COMMON']['step2_afl_apx_abb_root_path']
STEP2_APX_TEMPLATES_PATH = config['COMMON']['step2_apx_templates_path']
AB_REPORTS_PATH = config['COMMON']['AB_REPORTS_PATH']

# ============================================================================
# Variables for generating .apx files
# ============================================================================
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


class Step2GenAPX:
    def __init__(self, underlying_name, frequency, strategy_name, test_chosen,
                 raw_afl_root_path, apx_templates_path, output_root_path):
        # get raw afl path
        self.underlying_name = underlying_name
        self.frequency = frequency
        self.strategy_name = strategy_name
        self.test_chosen = test_chosen
        raw_file_name = underlying_name+';'+frequency+';'+strategy_name+'Test'+get_num_str(test_chosen)+'.afl'
        self.raw_afl_path = os.path.join(raw_afl_root_path, strategy_name, 'afl', raw_file_name)

        # read the afl's content
        with open(self.raw_afl_path, 'r') as afl:
            self.afl_codes = afl.read()
        self.afl_codes = self.afl_codes.replace('\n', '\\n')

        self.apx_templates_path = apx_templates_path
        self.output_root_path = output_root_path

    def run(self):
        # create directories
        p_list = [os.path.join(self.output_root_path, self.strategy_name),
                  os.path.join(self.output_root_path, self.strategy_name, 'afl'),
                  os.path.join(self.output_root_path, self.strategy_name, 'apx')]
        for p in p_list:
            if not os.path.exists(p):
                os.mkdir(p)

        output_path_list = []
        for f in os.listdir(self.apx_templates_path):
            if '.apx' not in f:
                continue
            prefix = f[0:5]
            yyyy_find = f.find('(A)')
            yyyy = f[yyyy_find-4:yyyy_find]

            # copy raw afl and rename
            new_file_name = self.underlying_name + ';' + \
                            self.frequency + ';' + \
                            self.strategy_name + ';' + \
                            'Test' + get_num_str(self.test_chosen) + '-' + \
                            prefix + str(yyyy)
            new_file_name_afl = new_file_name + '.afl'
            new_afl_path = os.path.join(self.output_root_path, self.strategy_name, 'afl', new_file_name_afl)
            shutil.copyfile(self.raw_afl_path, new_afl_path)

            # generate apx
            template_path = os.path.join(self.apx_templates_path, f)

            root_element = ET.ElementTree(file=template_path)
            root_element_tree = root_element.getroot()
            root_element_tree = self.set_formula_path(root_element_tree, new_afl_path)
            root_element_tree = self.set_formula_content(root_element_tree, self.afl_codes)

            output_apx_path = os.path.join(
                self.output_root_path,
                self.strategy_name,
                'apx',
                new_file_name + '.apx'
            )
            root_element.write(output_apx_path)

            output_path_list.append(output_apx_path)
        return output_path_list

    def format_path(self, p):
        return p.replace('\\', '\\\\')

    def general_settings(self, root_element_tree, formula_content='', formula_path=''):
        root_element_tree = self.set_formula_content(root_element_tree, formula_content)
        root_element_tree = self.set_formula_path(root_element_tree, formula_path)
        return root_element_tree

    def set_formula_path(self, root_element_tree, content):
        # root_element_tree should be a root element tree
        general = root_element_tree[0]
        formula_content = general[2]
        formula_content.text = content
        return root_element_tree

    def set_formula_content(self, root_element_tree, content):
        # root_element_tree should be a root element tree
        general = root_element_tree[0]
        formula_content = general[3]
        formula_content.text = content
        return root_element_tree


class Step2GenABB:
    def __init__(self, apx_path_list, underlying_name, freq_name, strategy_name, test_chosen, output_root_path):
        self.apx_path_list = []
        for p in apx_path_list:
            if '\\\\' in apx_path_list:
                self.apx_path_list.append(p)
            else:
                self.apx_path_list.append(p.replace('\\', '\\\\'))

        self.underlying_name = underlying_name
        self.freq_name = freq_name
        self.strategy_name = strategy_name
        self.test_chosen = test_chosen
        self.output_root_path = output_root_path

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
            self.output_root_path,
            self.strategy_name,
            self.underlying_name + ';' + self.freq_name + ';'
            + self.strategy_name + 'Test' + get_num_str(self.test_chosen) + '-Step2.abb'
        )
        tree.write(output_path)

        return output_path


if __name__ == '__main__':
    step2_gen_apx = Step2GenAPX(UNDERLYING_NAME, FREQUENCY, STRATEGY_NAME, TEST_CHOSEN,
                                ORIGINAL_AFL_ROOT_PATH, STEP2_APX_TEMPLATES_PATH, STEP2_AFL_APX_ABB_ROOT_PATH)
    apx_path_list = step2_gen_apx.run()
    print('Step2 - generating APX done...')

    step2_gen_abb = Step2GenABB(apx_path_list, UNDERLYING_NAME, FREQUENCY, STRATEGY_NAME,
                                TEST_CHOSEN, STEP2_AFL_APX_ABB_ROOT_PATH)
    step2_gen_abb.run()
    print('Step2 - generating APX done...')






