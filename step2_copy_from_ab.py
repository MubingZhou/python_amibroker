import os
import configparser
import shutil
import pandas as pd

CONFIG_FILE_PATH = 'S:\\Amibroker project\\Code\\step2_run_config.ini'
config = configparser.ConfigParser()
config.read(CONFIG_FILE_PATH)

STRATEGY_NAME = config['COMMON']['STRATEGY_NAME']
SYMBOL_NAME = config['COMMON']['SYMBOL_NAME']  # this is the name for the underlying in Amibroker
UNDERLYING_NAME = config['COMMON']['UNDERLYING_NAME']   # this is the name appeared in AFL/APX/ABB files
FREQUENCY = config['COMMON']['FREQUENCY']        # this will appear in AFL/APX/ABB files

AB_REPORTS_PATH = config['COMMON']['AB_REPORTS_PATH']
COPY_RESULTS_PATHS = config['COMMON']['step2_reports_root_path']  # COPY_RESULTS_PATHS = GEN_FILTER_OUTPUT_ROOT_PATH
STEP2_AFL_APX_ABB_ROOT_PATH = config['COMMON']['step2_afl_apx_abb_root_path']


def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


class Step2ExtractReportsAB:
    def __init__(self, strategy_name, ab_reports_path, apx_path_list, output_root_path):
        self.ab_reports_path = ab_reports_path
        self.oos_dir_list = [os.path.basename(p).split('.')[0] for p in os.listdir(apx_path_list)]

        # the below method is not applicable when there are many files under the directory
        # file_list = os.listdir(self.ab_reports_path)
        # file_list = [os.path.join(self.ab_reports_path, f) for f in file_list]
        # file_modtime = ((os.stat(f)[8], f) for f in file_list)
        # file_modtime_sorted = sorted(file_modtime, key=lambda x: -x[0])  # sorted by time descendingly
        # self.file_list = [f[1] for f in file_modtime_sorted]
        # print(self.file_list)

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

        self.output_path = output_root_path
        # self.output_path = os.path.join(output_root_path, strategy_name)
        # if not os.path.exists(self.output_path):
        #     os.mkdir(self.output_path)

    def run(self):
        for oos_result in self.oos_dir_list:
            print('oos_results = %s' % oos_result)
            for f in self.file_list:
                bf = os.path.basename(f)
                if oos_result in bf:
                    if 'Out-of-Sample summary' in bf:
                        try:
                            folder_name = oos_result[0:oos_result.find("Test")+6]
                            if not os.path.exists(os.path.join(self.output_path, folder_name)):
                                os.mkdir(os.path.join(self.output_path, folder_name))
                            this_output_path = os.path.join(self.output_path, folder_name, oos_result)
                            if not os.path.exists(this_output_path):
                                os.mkdir(this_output_path)
                            copytree(os.path.join(self.ab_reports_path, bf), this_output_path)
                            print('dir=%s done!' % bf)
                        except:
                            pass
                        try:
                            shutil.rmtree(f)
                        except:
                            pass
                    else:
                        try:
                            shutil.rmtree(f)
                        except:
                            pass

    def recognize_testcase_from_filename(self, fname):
        fname = os.path.basename(fname)
        ind = fname.find('Test')
        return int(fname[ind+4:ind+6])


if __name__ == '__main__':
    # STEP2_AFL_APX_ABB_ROOT_PATH = 'S:\\Amibroker project\\Code\\Step2_AFL_APX_ABB_results'
    # STRATEGY_NAME = 'TrixCrossOver'
    # AB_REPORTS_PATH = 'S:\\temp_nouse\\AB_results'
    # COPY_RESULTS_PATHS = 'S:\\temp_nouse'
    apx_path_list = os.path.join(STEP2_AFL_APX_ABB_ROOT_PATH, STRATEGY_NAME, 'apx')
    print(apx_path_list)
    extract_ab = Step2ExtractReportsAB(STRATEGY_NAME, AB_REPORTS_PATH,
                                       apx_path_list,
                                       COPY_RESULTS_PATHS)
    extract_ab.run()
    print('Step2 - Extract ab done!')
