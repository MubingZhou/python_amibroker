import os
import configparser
import pandas as pd
import shutil

CONFIG_FILE_PATH = 'T:\\Amibroker project\\Code\\run_config.ini'
config = configparser.ConfigParser()
config.read(CONFIG_FILE_PATH)

STRATEGY_NAME = config['COMMON']['STRATEGY_NAME']
SYMBOL_NAME = config['COMMON']['SYMBOL_NAME']  # this is the name for the underlying in Amibroker
UNDERLYING_NAME = config['COMMON']['UNDERLYING_NAME']   # this is the name appeared in AFL/APX/ABB files
FREQUENCY = config['COMMON']['FREQUENCY']        # this will appear in AFL/APX/ABB files

AB_REPORTS_PATH = config['COMMON']['AB_REPORTS_PATH']
COPY_RESULTS_PATHS = config['COMMON']['GEN_FILTER_OUTPUT_ROOT_PATH']  # COPY_RESULTS_PATHS = GEN_FILTER_OUTPUT_ROOT_PATH

NUM_FILTERS = int(config['GEN_AFL']['NUM_FILTERS'])
FILTER_LIST = list(range(1, NUM_FILTERS + 1))
# FILTER_LIST = [38, 39]


class ExtractReportsAB:
    def __init__(self, ab_reports_path, underlying_name, freq_name, strategy_name, output_root_path, filter_list=None):
        self.ab_reports_path = ab_reports_path
        self.underlying_name = underlying_name
        self.freq_name = freq_name
        self.strategy_name = strategy_name

        # the below method is not applicable when there are many files under the directory
        # print("wahaha1")
        # file_list = os.listdir(self.ab_reports_path)
        # print("wahaha2")
        # file_list = [os.path.join(self.ab_reports_path, f) for f in file_list]
        # print("wahaha3")
        # file_modtime = ((os.stat(f)[8], f) for f in file_list)
        # print("wahaha4")
        # file_modtime_sorted = sorted(file_modtime, key=lambda x: -x[0])  # sorted by time descendingly
        # print("wahaha5")
        # self.file_list = [f[1] for f in file_modtime_sorted]
        # print(self.file_list)
        # print("wahaha6")

        ##  To solve the above problem: read the .rlst file within Amibroker's path
        result_pd = pd.read_csv(os.path.join(self.ab_reports_path, 'results.rlst'),
                                sep='\t', header=None, usecols=[0, 1], parse_dates=[1])

        def d2str(row):
            str1 = pd.datetime.strftime(row[1], '%Y%m%d%H%M%S')
            str2 = str(int(row[1].time().microsecond / 1000)).zfill(3)
            return os.path.join(ab_reports_path, row[0] + '-' + str1 + str2)

        file_list = result_pd.apply(d2str, axis=1)
        self.file_list = list(file_list)
        ##  done

        self.output_path = os.path.join(output_root_path, strategy_name)
        if not os.path.exists(self.output_path):
            os.mkdir(self.output_path)
        self.output_path = os.path.join(self.output_path, 'results')
        if not os.path.exists(self.output_path):
            os.mkdir(self.output_path)

        self.filter_list = filter_list if filter_list is not None else FILTER_LIST

    def run(self):
        # we will copy the OOS files to a new directory and remove the old files as well as the IS files
        testcase_toremove = []
        for f in self.file_list:
            bf = os.path.basename(f)
            if (self.underlying_name+';') in bf and (';'+self.freq_name) in bf \
                    and (';'+self.strategy_name) in bf:
                num = self.recognize_testcase_from_filename(bf)
                print('num=%d, bf=%s, testcase_toremove=%s' % (num, bf, testcase_toremove))

                temp_is_delted = False
                if num in self.filter_list and 'Out-of-Sample summary' in bf:
                    line = 'xcopy \"' + f + '\" \"' + os.path.join(self.output_path, bf) + '\" /i'
                    # print(line)
                    os.system(line)
                    self.filter_list.remove(num)
                    testcase_toremove.append(num)

                    # remove redundant files
                    try:
                        shutil.rmtree(f)
                        temp_is_delted = True
                    except:
                        pass


                # remove associated IS files
                if num in FILTER_LIST and not temp_is_delted:
                    try:
                        shutil.rmtree(f)
                    except:
                        pass



    def recognize_testcase_from_filename(self, fname):
        fname = os.path.basename(fname)
        ind = fname.find('Test')
        return int(fname[ind+4:ind+6])


if __name__ == '__main__':
    AB_REPORTS_PATH = 'S:\\temp_nouse\\AB_results'
    UNDERLYING_NAME = "HSI"
    FREQUENCY = 'hourly'
    STRATEGY_NAME = 'MovingAvgOscillator'
    COPY_RESULTS_PATHS = 'S:\\temp_nouse'
    extract_ab = ExtractReportsAB(AB_REPORTS_PATH, UNDERLYING_NAME, FREQUENCY, STRATEGY_NAME, COPY_RESULTS_PATHS)
    extract_ab.run()
