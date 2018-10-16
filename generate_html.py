import pandas as pd
import configparser
import os
import time
import datetime
import numpy as np
import xlrd


class GenerateHTML:
    def __init__(self, config_path):
        config = configparser.ConfigParser()
        config.read(config_path)

        # variables related to INDEX and global variables
        self.root_path = config['COMMON']['html_root_path']  # root path of the HTML report
        self.table_contents_nl = [
            ('Backtesting', '', [
                ('Pipeline', 'backtesting/pipeline.html', []),
                ('Step1', 'backtesting/step1.html', []),
                ('Step2', 'backtesting/step2.html', []),
                ('Step3', 'backtesting/step3.html', [])
            ]),
            ('Monitoring', 'monitoring/monitoring.html', []),
            ('Material', 'materials/materials.html', [])
        ]

        # variables related to BACKTESTING-STEP1
        self.bkt_root_path = os.path.join(self.root_path, 'backtesting')
        if not os.path.exists(self.bkt_root_path):
            os.mkdir(self.bkt_root_path)
        # path containing step1 backtesting results (should not be in the html file systems)
        self.bkt_result_step1_path = config['BACKTESTING_STEP1']['bkt_result_step1_path']
        self.bkt_pipeline_xls_path = config['BACKTESTING_STEP1']['pipeline_xls_path']
        self.bkt_step1_carmdd_1 = float(config['BACKTESTING_STEP1']['car_mdd_1'])
        self.bkt_step1_carmdd_21 = float(config['BACKTESTING_STEP1']['car_mdd_21'])
        self.bkt_step1_netprofit_22 = float(config['BACKTESTING_STEP1']['net_profit_22'])

        # variables related to BACKTESTING-STEP2
        self.step2_dir = os.path.join(self.bkt_root_path, "step2")
        if not os.path.exists(self.step2_dir):
            os.mkdir(self.step2_dir)
        self.bkt_result_step2_path = config['BACKTESTING_STEP2']['bkt_result_step2_path']
        self.bkt_step2_carmdd_1 = float(config['BACKTESTING_STEP2']['bkt_step2_carmdd_1'])
        self.bkt_step2_trade_no_2 = float(config['BACKTESTING_STEP2']['bkt_step2_trade_no_2'])
        self.bkt_step2_carmdd_3 = float(config['BACKTESTING_STEP2']['bkt_step2_carmdd_3'])
        self.bkt_step2_std_4 = float(config['BACKTESTING_STEP2']['bkt_step2_std_4'])
        self.bkt_step2_has_good_strategy_temp = False  # please use it only as a temp variable

        # variables related to BACKTESTING-STEP3
        self.step3_dir = os.path.join(self.bkt_root_path, "step3")
        if not os.path.exists(self.step3_dir):
            os.mkdir(self.step3_dir)
        self.bkt_result_step3_path = config['BACKTESTING_STEP3']['bkt_result_step3_path']

        # variables related to MONITORING
        self.monitoring_dir = os.path.join(self.root_path, 'monitoring')
        if not os.path.exists(self.monitoring_dir):
            os.mkdir(self.monitoring_dir)
        monitoring_strategy_df_path = config['MONITORING']['monitoring_strategy_df']
        self.monitoring_strategy_df = pd.read_csv(monitoring_strategy_df_path)
        self.monitoring_daily_path = config['MONITORING']['daily_monitor_path']    # abs path
        self.monitoring_daily_relative_path = '../../../Report/daily_monitor/daily_pnl/'  # relative path
        self.monitoring_strategy_dict = {}


        # variables related to MATERIALS
        self.material_dir = os.path.join(self.root_path, 'materials')  # the path containing html
        if not os.path.exists(self.material_dir):
            os.mkdir(self.material_dir)
        self.material_path = config['MATERIAL']['material_path']  # the path containing real materials

    def run(self):
        # ------------------ index page ------------------
        self.generate_index_html()
        print('**************** Generate index.html done! **************** ')

        self.run_backtesting()
        self.run_monitoring()
        # self.run_materials()

    def run_backtesting(self):
        #########################################
        #              BACKTESTING              #
        #########################################
        # ------------------ backtesting - pipeline ------------------
        self.generate_bkt_pipeline()
        print('**************** Generate pipeline.html done! **************** ')

        # ------------------ backtesting - step1 ------------------
        # self.generate_bkt_step1()
        print('**************** Generate step1.html done! **************** ')

        # ------------------ backtesting - step2 ------------------
        # self.generate_bkt_step2()
        print('**************** Generate step2.html done! **************** ')

        # ------------------ backtesting - step3 ------------------
        # self.generate_bkt_step3()
        print('**************** Generate step3.html done! **************** ')

    def run_monitoring(self):
        #########################################
        #              MONITORING               #
        #########################################
        # ------------------ monitoring - main ------------------
        self.generate_monitoring_main()
        print('**************** Generate monitoring.html done! **************** ')

        # ------------------ monitoring - by model ------------------
        self.generate_monitoring_bystrategy()
        print('**************** Generate monitoring_by_strategy done! **************** ')

    def run_materials(self):
        #########################################
        #              MATERIALS                #
        #########################################
        # ------------------ materials ------------------
        self.generate_material_list()
        print('**************** Generate material_list done! **************** ')

    def generate_index_html(self, file_name="index.html"):
        s_begin = """
    <html>
    <head>
    <style type="text/css">
    ol {
        counter-reset: item
    }
    li {
        display: block
    }
    li:before {
        content: counters(item, ".")" ";
        counter-increment: item
    }
    </style>
    </head>
    
    
    <body style="font-size:35px">
    
    """
        s_content = self.nested_list(self.table_contents_nl, '')

        s_end = """
        
    </body>
    </html>
        """
        s = s_begin + s_content + s_end
        with open(os.path.join(self.root_path, file_name), 'w') as f:
            f.write(s)

    def generate_bkt_pipeline(self):
        s_begin = """
<html>
<head>
<link rel="stylesheet" type="text/css" href="../mystyle.css">
</head>
<body>
<p><a href="../index.html"><-Homepage<a></p>
<script src="../myfunction.js"></script>
<h1>Backtesting - Pipeline</h1>
            """
        s_end = """</body>
        </html>
        """

        s_content = """
<div class="tab">
  <button class="tablinks" onclick="openStep_pipeline(event, 'tablinks', 'Step1')">Step1</button>
  <button class="tablinks" onclick="openStep_pipeline(event, 'tablinks', 'Step2')">Step2</button>
  <button class="tablinks" onclick="openStep_pipeline(event, 'tablinks', 'Step3')">Step3</button>
</div>
        """
        data = xlrd.open_workbook(self.bkt_pipeline_xls_path, formatting_info=True)

        # step1
        s_step1_table = """<table id="table_content">\n"""
        s1_sheet = data.sheet_by_name('step1')  # step1 sheet
        c = 0
        finished_num = 0
        finished_not_copy_num = 0
        not_finished_num = 0
        not_start_num = 0
        for i in range(s1_sheet.nrows):
            s_step1_table += "<tr>\n"
            for j in range(s1_sheet.ncols):
                if c == 0:
                    s_step1_table += "<th>" + s1_sheet.cell(i, j).value + "</th>\n"
                else:
                    s_step1_table += "<td"
                    cell_value = str(s1_sheet.cell(i, j).value)
                    if j >= 3:
                        if cell_value != '' and cell_value != 'Y':
                            xfx = s1_sheet.cell_xf_index(i, j)
                            xf = data.xf_list[xfx]
                            bgx = xf.background.pattern_colour_index
                            if bgx == 64:  # no bg color in Excel
                                s_step1_table += " bgcolor=\"lightgreen\""
                                cell_value += ";In Progress"
                                not_finished_num += 1
                            else:  # has bg color in Excel
                                s_step1_table += " bgcolor=\"yellow\""
                                cell_value += ";Finished; Not Copy"
                                finished_not_copy_num += 1
                        elif cell_value == 'Y':
                            cell_value = '<b>Finished</>'
                            finished_num += 1
                        elif cell_value == '':
                            not_start_num += 1
                    s_step1_table += ">" + cell_value + "</td>\n"
            c = c + 1 if c == 0 else c
            s_step1_table += "</tr>\n"
        s_step1_table += "</table>\n"

        total_num = (s1_sheet.nrows - 1) * 5
        finished_str = "{:.0f} / {:.1f}%".format(finished_num, finished_num / total_num * 100)
        not_finished_num_str = "{:.0f} / {:.1f}%".format(not_finished_num, not_finished_num / total_num * 100)
        not_start_str = "{:.0f} / {:.1f}%".format(not_start_num, not_start_num / total_num * 100)
        finished_not_copy_str = "{:.0f} / {:.1f}%".format(
            finished_not_copy_num, finished_not_copy_num / total_num * 100
        )
        s_step1_stat = "<p>Total: " + str(total_num) + "</p>\n"
        s_step1_stat += "<p>Finished: " + finished_str + "&emsp;|&emsp;Finished but not copy: " \
                        + finished_not_copy_str + "</p>\n"
        s_step1_stat += "<p>In Progress: " + not_finished_num_str + "&emsp;|&emsp;Not Start: " + not_start_str + "</p>\n"

        s_content += "<div id=\"Step1\" class=\"tabcontent_default\">\n" + s_step1_stat + s_step1_table + "</div>\n"

        # step2
        s_step2_table = """<table id="table_content">\n"""
        s2_sheet = data.sheet_by_name('step2')  # step2 sheet
        c = 0
        finished_num = 0
        finished_not_copy_num = 0
        not_finished_num = 0
        not_start_num = 0
        for i in range(s2_sheet.nrows):
            s_step2_table += "<tr>\n"
            for j in range(s2_sheet.ncols):
                if c == 0:
                    s_step2_table += "<th>" + s2_sheet.cell(i, j).value + "</th>\n"
                else:
                    s_step2_table += "<td"
                    cell_value = str(s2_sheet.cell(i, j).value)
                    if j >= 2:
                        if cell_value != '' and cell_value != 'Y':
                            xfx = s2_sheet.cell_xf_index(i, j)
                            xf = data.xf_list[xfx]
                            bgx = xf.background.pattern_colour_index
                            if bgx == 64:   # no bg color in Excel
                                s_step2_table += " bgcolor=\"lightgreen\""
                                cell_value += ";In Progress"
                                not_finished_num += 1
                            else:  # has bg color in Excel
                                s_step2_table += " bgcolor=\"yellow\""
                                cell_value += ";Finished; Not Copy"
                                finished_not_copy_num += 1
                        elif cell_value == 'Y':
                            cell_value = '<b>Finished</b>'
                            finished_num += 1
                        elif cell_value == '':
                            not_start_num += 1
                    s_step2_table += ">" + cell_value + "</td>\n"
            c = c + 1 if c == 0 else c
            s_step2_table += "</tr>\n"
        s_step2_table += "</table>\n"

        total_num = (s2_sheet.nrows - 1) * 1
        finished_str = "{:.0f} / {:.1f}%".format(finished_num, finished_num / total_num * 100)
        not_finished_num_str = "{:.0f} / {:.1f}%".format(not_finished_num, not_finished_num / total_num * 100)
        not_start_str = "{:.0f} / {:.1f}%".format(not_start_num, not_start_num / total_num * 100)
        finished_not_copy_str = "{:.0f} / {:.1f}%".format(
            finished_not_copy_num, finished_not_copy_num / total_num * 100
        )
        s_step2_stat = "<p>Total: " + str(total_num) + "</p>\n"
        s_step2_stat += "<p>Finished: " + finished_str + "&emsp;|&emsp;Finished but not copy: " \
                        + finished_not_copy_str + "</p>\n"
        s_step2_stat += "<p>In Progress: " + not_finished_num_str + "&emsp;|&emsp;Not Start: " + not_start_str + "</p>\n"

        s_content += "<div id=\"Step2\" class=\"tabcontent\">\n" + s_step2_stat + s_step2_table + "</div>\n"

        # step3
        s_step3_table = """<table id="table_content">\n"""
        s3_sheet = data.sheet_by_name('step3')  # step3 sheet
        c = 0
        finished_num = 0
        finished_not_copy_num = 0
        not_finished_num = 0
        not_start_num = 0
        for i in range(s3_sheet.nrows):
            s_step3_table += "<tr>\n"
            for j in range(s3_sheet.ncols):
                if c == 0:
                    s_step3_table += "<th>" + s3_sheet.cell(i, j).value + "</th>\n"
                else:
                    s_step3_table += "<td"
                    cell_value = str(s3_sheet.cell(i, j).value)
                    if j >= 3:
                        if cell_value != '' and cell_value != 'Y':
                            xfx = s3_sheet.cell_xf_index(i, j)
                            xf = data.xf_list[xfx]
                            bgx = xf.background.pattern_colour_index
                            if bgx == 64:  # no bg color in Excel
                                s_step3_table += " bgcolor=\"lightgreen\""
                                cell_value += ";In Progress"
                                not_finished_num += 1
                            else:  # has bg color in Excel
                                s_step3_table += " bgcolor=\"yellow\""
                                cell_value += ";Finished; Not Copy"
                                finished_not_copy_num += 1
                        elif cell_value == 'Y':
                            cell_value = '<b>Finished</b>'
                            finished_num += 1
                        elif cell_value == '':
                            not_start_num += 1
                    s_step3_table += ">" + cell_value + "</td>\n"
            c = c + 1 if c == 0 else c
            s_step3_table += "</tr>\n"
        s_step3_table += "</table>\n"

        total_num = (s3_sheet.nrows - 1) * 1
        finished_str = "{:.0f} / {:.1f}%".format(finished_num, finished_num / total_num * 100)
        not_finished_num_str = "{:.0f} / {:.1f}%".format(not_finished_num, not_finished_num / total_num * 100)
        not_start_str = "{:.0f} / {:.1f}%".format(not_start_num, not_start_num / total_num * 100)
        finished_not_copy_str = "{:.0f} / {:.1f}%".format(
            finished_not_copy_num, finished_not_copy_num / total_num * 100
        )
        s_step3_stat = "<p>Total: " + str(total_num) + "</p>\n"
        s_step3_stat += "<p>Finished: " + finished_str + "&emsp;|&emsp;Finished but not copy: " \
                        + finished_not_copy_str + "</p>\n"
        s_step3_stat += "<p>In Progress: " + not_finished_num_str + "&emsp;|&emsp;Not Start: " + not_start_str + "</p>\n"

        s_content += "<div id=\"Step3\" class=\"tabcontent\">\n" + s_step3_stat + s_step3_table + "</div>\n"

        with open(os.path.join(self.bkt_root_path, 'pipeline.html'), 'w') as f:
            f.write(s_begin + s_content + s_end)

    # generating step1.html under "backtesting"
    def generate_bkt_step1(self):
        s_begin = """
    <html>
    <head>
    <link rel="stylesheet" type="text/css" href="../mystyle.css">
    </head>
    <body>
    <p><a href="../index.html"><-Homepage<a></p>

    <h1>Backtesting - Step1: Results</h1>
        """
        s_end = """</body>
    </html>
    """
        s_content = ''
        # read step 1 files
        # ********* by underlying ***********
        # TODO: to update underlyinglist
        underlying_list = ['HSI']
        for underlying in underlying_list:
            s_content += "<h2>Underlying: " + str(underlying) + "</h2>\n"
            s_content += """<p>Highlight Criteria:</br>
            &emsp;Cond1: CAR/MDD > """ + str(self.bkt_step1_carmdd_1) + """</br>
            &emsp;<strong><em>OR</em></strong></br>
            &emsp;Cond2: CAR/MDD > """ + str(self.bkt_step1_carmdd_21) + \
                         """ <strong><em>AND</em></strong> NetProfit > """ + str(self.bkt_step1_netprofit_22) + """
            </p>
            """
            s_table = "<table id=\"table_content\">\n"

            uly_path = os.path.join(self.bkt_root_path, underlying)
            if not os.path.exists(uly_path):
                os.mkdir(uly_path)

            # ********* by strategy *********
            bkt_result_step1_uly_path = os.path.join(self.bkt_result_step1_path, underlying)
            step1_df = pd.DataFrame({'3min': [], '5min': [], '15min': [], '30min': [], '60min': [],
                                     'good_3min': [], 'good_5min': [], 'good_15min': [], 'good_30min': [],
                                     'good_60min': []
                                     })
            strategy_list = os.listdir(bkt_result_step1_uly_path)
            strategy_list = sorted(strategy_list)
            for strategy in strategy_list:
                print("------------- Step 1 - " + strategy + " ---------------")
                bkt_step1_uly_strgy_path = os.path.join(bkt_result_step1_uly_path, strategy)
                uly_strategy_path = os.path.join(uly_path, strategy)  # path for html
                if not os.path.exists(uly_strategy_path):
                    os.mkdir(uly_strategy_path)

                rec = pd.DataFrame()
                freq_list = os.listdir(bkt_step1_uly_strgy_path)
                for freq in freq_list:
                    # ********* by frequency *********
                    # read strategy summary data
                    bkt_step1_uly_strgy_freq_path = os.path.join(bkt_step1_uly_strgy_path, freq)
                    summary = pd.read_csv(os.path.join(bkt_step1_uly_strgy_freq_path, 'ModelTestCheckList.csv'))
                    # print(summary.columns)
                    if 'Name' in summary:
                        summary = summary.drop(['Name'], axis=1)
                    if 'Unnamed 1' in summary:
                        summary = summary.drop(['Unnamed 1'], axis=1)
                    summary = summary.rename({'Period': 'Name'}, axis=1)
                    summary = summary.fillna(0)

                    has_good_strategy = False
                    cond1 = summary['CAR / MDD'] > self.bkt_step1_carmdd_1
                    cond21 = summary['CAR / MDD'] > self.bkt_step1_carmdd_21
                    cond22 = summary['Net Profit'] > self.bkt_step1_netprofit_22
                    cond = cond1 | (cond21 & cond22)
                    if len(summary[cond]) > 0:
                        has_good_strategy = True
                    summary.loc[:, 'good'] = cond
                    rec['good_' + freq] = [has_good_strategy]
                    # write a html for the summary data
                    output_path_temp = os.path.join(uly_strategy_path,
                                                    str(underlying) + "_" + str(strategy) + "_" + str(
                                                        freq) + ".html")
                    with open(output_path_temp, 'w') as f:
                        f.write(
                            self.generate_bkt_step1_strategy_summary(
                                summary, underlying, freq, strategy
                            )
                        )

                for freq_col in step1_df.columns:
                    if 'good' in freq_col:
                        if freq_col not in rec.columns:
                            rec[freq_col] = [False]
                    else:
                        if freq_col in freq_list:
                            rec[freq_col] = [freq_col]
                        else:
                            rec[freq_col] = ['&nbsp;']
                rec.index = [strategy]
                # print(rec)
                rec = rec[step1_df.columns]
                step1_df = step1_df.append(rec)
                print("------------- Step 1 - " + strategy + " END ---------------")

            # convert the step1_df into html
            row_n = len(step1_df)
            col_n = int(len(step1_df.columns) / 2)
            # print("col_n*2 = %f, col_n = %f, col_n = %s" % (len(step1_df.columns), col_n, step1_df.columns))
            # print(step1_df)
            for i in range(row_n):
                strategy = step1_df.index[i]
                s_table += "<tr align=\"left\">\n"
                s_table += "  <th>" + strategy + "</th>\n"
                for j in range(col_n):
                    freq = step1_df.columns[j]
                    if step1_df['good_' + freq][i]:
                        td_begin = "  <td bgcolor=\"yellow\">"
                    else:
                        td_begin = "  <td>"
                    if step1_df[freq][i] == '&nbsp;':
                        td_content = '&nbsp;'
                    else:
                        td_content = self.html_a(freq,
                                                 "\"" + underlying + "/" + strategy + "/"
                                                 + underlying + "_" + strategy + "_" + freq + ".html" + "\"")
                        td_content += "</br>"
                        td_date_path = os.path.join(self.bkt_result_step1_path, underlying,
                                                    strategy, freq, 'ModelTestCheckList.xltm.xlsm')
                        td_date = datetime.datetime.fromtimestamp(os.path.getmtime(td_date_path)).strftime(
                            '%d/%m/%Y')
                        td_content += td_date
                    s_table += td_begin + td_content + "</td>\n"
                s_table += "</tr>\n"
            s_table += "</table></br>\n"
            s_content += s_table

        with open(os.path.join(self.bkt_root_path, 'step1.html'), 'w') as f:
            f.write(s_begin + s_content + s_end)

    def generate_bkt_step1_strategy_summary(self, summary, underlying, freq, strategy):
        s_begin = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="utf-8">
    <link rel="stylesheet" type="text/css" href="../../../mystyle.css">
    <script src="../../../myfunction.js"></script>
    </head>
    <body>
        """
        s_end = """</body>
    </html>"""
        s_content = "<p><a href=\"../../step1.html\"><-Step1<a></p>\n</br>"
        s_content += "<h2>Strategy: " + str(underlying) + " - " + str(freq) + " - " + str(strategy) + "</h2>\n"

        s_table_begin = "<table id=\"table_content\">"
        s_table_content = '<tr>\n'

        # drop unnecessary columns
        cols_to_drop = []
        for c in summary.columns:
            if 'unnamed' in str(c).lower():
                cols_to_drop.append(c)
        summary = summary.drop(cols_to_drop, axis=1)

        # insert one column
        cols = list(summary.columns)
        cols.insert(1, 'AFL')
        cols.insert(2, 'Step2')
        summary.loc[:, 'AFL'] = 'go'
        summary.loc[:, 'Step2'] = 'go'
        summary = summary[cols]

        # writ the header
        space = False
        row_n = len(summary)
        col_n = len(summary.columns)
        for jj in range(col_n-1):
            col = summary.columns[jj]
            if not space:
                s_table_content += "  "
                space = True
            # if 'unnamed' in str(col).lower():
            #     col = 'Chg'
            #     continue  # don't show it
            s_table_content += "<th onclick=\"sortTable(" + str(jj) + ")\">" + str(col) + "</th>\n"
        s_table_content += "</tr>\n"

        # write table body
        for i in range(row_n):
            if summary['good'][i]:
                s_table_content += "<tr style=\"background-color:yellow;\">\n"
            else:
                s_table_content += "<tr>\n"
            for j in range(col_n-1):
                # if 'unnamed' in str(summary.columns[j]).lower():
                #     continue
                to_write = ''
                temp = summary.iloc[i, j]
                if isinstance(temp, (np.float, np.int64, np.int)):
                    to_write = '%.2f' % temp
                else:
                    # print(type(temp))
                    temp2 = temp.replace('%', '')
                    try:
                        n = float(temp2)
                        to_write = '%.2f%%' %  n
                    except:
                        to_write = temp
                if j == 0:  # first element, link to the results
                    path = "../../../../Result/Step1/" \
                           + underlying + '/' + strategy + '/' + freq + '/' + temp + '/' + 'stats.html'
                    to_write = self.html_a(to_write, href="\"" + path + "\"", target="\"_blank\"")
                elif j == 1:  # AFL
                    path = "../../../../Code/Step1_AFL_APX_ABB_results/" \
                           + strategy + '/afl/' + summary.iloc[i, 0] + '.afl'
                    to_write = self.html_a(to_write, href="\"" + path + "\"", target="\"_blank\"")
                elif j == 2:
                    if summary['good'][i]:
                        name = summary.iloc[i, 0]
                        nn = name.find('Test')
                        name = name[:nn] + ';' + name[nn:]
                        path = "../../step2/" + strategy + '_' + freq + '/' + name + '.html'
                        to_write = self.html_a(to_write, href="\"" + path + "\"", target="\"_blank\"")
                    else:
                        to_write = '&nbsp;'
                s_table_content += "  <td>" + to_write + "</td>\n"
            s_table_content += "</tr>\n"
        s_table_end = '</table>'

        s_table = s_table_begin + s_table_content + s_table_end

        s_content += s_table

        return s_begin + s_content + s_end

    def generate_bkt_step2(self):
        s_begin = """
    <html>
    <head>
    <link rel="stylesheet" type="text/css" href="../mystyle.css">
    </head>
    <body>
    <p><a href="../index.html"><-Homepage<a></p>
    
    <h1>Backtesting - Step2: Results</h1>
            """
        s_end = """</body>
    </html>
        """
        s_content = ''
        file_list = os.listdir(self.bkt_result_step2_path)
        file_dict = {}
        # e.g HSI -> {BBandBreakOut_3min -> [HSI;3min;BBandBreakOut;Test29, HSI;3min;BBandBreakOut;Test41]
        #             BBandBreakOut_5min -> [HSI;5min;BBandBreakOut;Test15, HSI;5min;BBandBreakOut;Test02]
        #             }
        #     HSCEI -> ...
        max_potential_cols = 0
        for f in file_list:
            # print('file=%s' % f)
            arr = f.split(";")
            underlying = arr[0]
            freq = arr[1]
            strategy = arr[2]
            strategy_freq = strategy + "_" + freq
            if underlying not in file_dict:
                file_dict[underlying] = {}
            file_dict_uly = file_dict[underlying]
            if strategy_freq not in file_dict_uly:
                file_dict_uly[strategy_freq] = []
            file_dict_uly_stgy_freq = file_dict_uly[strategy_freq]
            file_dict_uly_stgy_freq.append(f)
            # print(file_dict_uly_stgy_freq)
            if len(file_dict_uly_stgy_freq) > max_potential_cols:
                max_potential_cols = len(file_dict_uly_stgy_freq)
        # print("file_dict=%s" % file_dict)
        max_col_each_line = 9  # max num of cols each line (excluding the first col)
        col_num = 0
        if max_potential_cols <= max_col_each_line:
            col_num = max_potential_cols
        else:
            col_num = max_col_each_line

        for underlying, underlying_dict in file_dict.items():
            s_content += "<h2>Underlying: " + str(underlying) + "</h2>\n"
            s_content += """<p>Highlight Criteria:</br>
                        &emsp;Cond1: CAR/MDD > """ + str(self.bkt_step2_carmdd_1) + """</br>
                        &emsp;<strong><em>AND</em></strong></br>
                        &emsp;Cond2: Trade No. > """ + str(self.bkt_step2_trade_no_2) + """</br>
                        &emsp;<strong><em>AND</em></strong></br>
                        &emsp;Cond3: # of [CAR/MDD > """ + str(self.bkt_step2_carmdd_3) + """] should more than half in all walk forward tests</br> 
                        &emsp;<strong><em>AND</em></strong></br>
                        &emsp;Cond4: Std Dev < """ + str(self.bkt_step2_std_4) + """</br>
                        </p>
                        """
            s_table = "<table id=\"table_content\">\n"

            for strategy_freq, test_list in underlying_dict.items():
                strategy_freq_path = os.path.join(self.bkt_root_path, 'step2', strategy_freq)
                if not os.path.exists(strategy_freq_path):
                    os.mkdir(strategy_freq_path)
                s_table += "<tr align=\"left\">\n"
                s_table += "<th>" + strategy_freq + "</th>\n"

                test_list_len = len(test_list)
                total_len = (int(test_list_len / (col_num+0.0001)) + 1) * col_num
                for i in range(total_len):
                    if i > 0 and i % col_num == 0:
                        s_table += "<tr align=\"left\">\n<th>&nbsp;</th>\n"
                    if i < test_list_len:
                        # print(test_list[i].split(";"))

                        self.bkt_step2_has_good_strategy_temp = False
                        # create a html for each selected test case
                        # if test_list[i] in ["HSI;3min;BBandBreakOut;Test03", "HSI;3min;BBandBreakOut;Test07",
                        #                     "HSI;3min;BBandBreakOut;Test08"]:
                        with open(
                                os.path.join(
                                    self.bkt_root_path, 'step2', strategy_freq, test_list[i]+".html"),
                                'w') as f:
                            f.write(self.generate_bkt_step2_test_summary(test_list[i]))

                        # write the cell in step.html
                        test_case = test_list[i].split(";")[-1]
                        test_case = self.html_a(test_case,
                                                href="\"step2/" + strategy_freq + "/" + test_list[i] + ".html\"")
                        test_case_date_path = os.path.join(
                            self.bkt_result_step2_path, test_list[i], 'ModelTestCheckList.xltm.xlsm')
                        td_date = datetime.datetime.fromtimestamp(
                            os.path.getmtime(test_case_date_path)).strftime('%d/%m/%Y')
                        if self.bkt_step2_has_good_strategy_temp:
                            s_table += "<td bgcolor=\"yellow\">"
                        else:
                            s_table += "<td>"
                        s_table += test_case + "</br>" + td_date + "</td>\n"

                    else:
                        s_table += "<td>&nbsp;</td>\n"
                s_table += "</tr>\n"

            s_table += "</table></br>\n"
            s_content += s_table

        with open(os.path.join(self.bkt_root_path, "step2.html"), 'w') as f:
            f.write(s_begin + s_content + s_end)

    def generate_bkt_step2_test_summary(self, uly_freq_stgy_test):
        s_begin = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="utf-8">
    <link rel="stylesheet" type="text/css" href="../../../mystyle.css">
    <script src="../../../myfunction.js"></script>
    </head>
    <body>
            """
        s_end = """</body>
        </html>"""
        s_content = "<p><a href=\"../../step2.html\"><-Step2<a></p>\n</br>"
        arr = uly_freq_stgy_test.split(';')
        underlying = arr[0]
        freq = arr[1]
        strategy = arr[2]
        test_case = arr[3]
        s_content += "<h2>Strategy: " + str(underlying) + " - " + str(freq) + \
                     " - " + str(strategy) + " - " + test_case + "</h2>\n"

        has_good_strategy = False
        # read dataframe
        test_case_summary = pd.read_csv(
            os.path.join(self.bkt_result_step2_path, uly_freq_stgy_test, "ModelTestCheckList.csv")
        )
        test_case_summary_cols = list(test_case_summary.columns)
        test_case_summary[test_case_summary_cols[2:]] = test_case_summary[test_case_summary_cols[2:]].fillna(0.0)
        test_case_summary = test_case_summary.fillna('')
        name_col = 'Name'
        if 'Period' in test_case_summary.columns:
            if 'Name' not in test_case_summary.columns:
                pass
            else:
                if test_case_summary['Name'][0] != '':
                    test_case_summary['Period'] = test_case_summary['Period'] + "_" + test_case_summary['Name']
                test_case_summary = test_case_summary.drop(['Name'], axis=1)
            test_case_summary = test_case_summary.rename({'Period': 'Name'}, axis=1)
        # test_case_summary = test_case_summary.drop(['Name'], axis=1)
        test_case_summary = test_case_summary.fillna(0)
        # print(test_case_summary)

        # drop unnecessary columns
        cols_to_drop = []
        for c in test_case_summary.columns:
            if 'unnamed' in str(c).lower():
                cols_to_drop.append(c)
        test_case_summary = test_case_summary.drop(cols_to_drop, axis=1)

        # insert one column
        cols = list(test_case_summary.columns)
        cols.insert(1, 'AFL')
        cols.insert(2, 'Step3')
        test_case_summary.loc[:, 'AFL'] = 'go'
        test_case_summary.loc[:, 'Step3'] = 'go'
        test_case_summary = test_case_summary[cols]

        #test if has good strategy
        car_mdd_name = 'CAR / MDD'
        if car_mdd_name not in test_case_summary.columns:
            car_mdd_name = 'CAR/MaxDD'
        cond1 = test_case_summary[car_mdd_name] > self.bkt_step2_carmdd_1
        cond2 = test_case_summary['Trade No.'] > self.bkt_step2_trade_no_2
        cond3 = len(test_case_summary[test_case_summary[car_mdd_name] > self.bkt_step2_carmdd_3]) \
                >= 0.5 * len(test_case_summary)
        cond4 = test_case_summary[car_mdd_name].std() < self.bkt_step2_std_4
        test_case_summary['good'] = cond1 & cond2
        max_carmdd_index = -100
        if len(test_case_summary[cond1]) > 0 and len(test_case_summary[cond2]) > 0 and cond3 and cond4:
            self.bkt_step2_has_good_strategy_temp = True
            c = cond1 & cond2
            max_carmdd_index = test_case_summary[c].sort_values(['good', car_mdd_name], ascending=[0, 0]).index[0]

        s_table_begin = "<table id=\"table_content\">"
        s_table_content = '<tr>\n'

        space = False
        row_n = len(test_case_summary)
        col_n = len(test_case_summary.columns)
        for jj in range(col_n - 1):
            col = test_case_summary.columns[jj]
            if not space:
                s_table_content += "  "
                space = True
            # if 'unnamed' in str(col).lower():
            #     col = 'Chg'
            #     continue
            s_table_content += "<th onclick=\"sortTable(" + str(jj) + ")\">" + str(col) + "</th>\n"

        for i in range(row_n):
            s_table_content += "<tr>\n"
            for j in range(col_n - 1):
                if 'unnamed' in str(test_case_summary.columns[j]).lower():
                    continue
                to_write = ''
                temp = test_case_summary.iloc[i, j]
                # print(temp)
                if isinstance(temp, (np.float, np.int64, np.int)):
                    to_write = '%.2f' % temp
                else:
                    temp2 = temp.replace('%', '')
                    try:
                        n = float(temp2)
                        to_write = '%.2f%%' % n
                    except:
                        to_write = temp
                if j == 0:  # first element, link to the results
                    path = "../../../../Result/Step2/" + uly_freq_stgy_test + '/' + str(temp) + '/' + 'stats.html'
                    to_write = self.html_a(to_write, href="\"" + path + "\"", target="\"_blank\"")
                elif j == 1:  # AFL
                    path = "../../../../Code/Step2_AFL_APX_ABB_results/" + strategy + \
                           '/afl/' + test_case_summary.iloc[i, 0] + '.afl'
                    to_write = self.html_a(to_write, href="\"" + path + "\"", target="\"_blank\"")
                elif j == 2:   # TODO: to finish Step3  button
                    path = "../../../../Result/Step2/" + uly_freq_stgy_test + '/' + str(temp) + '/' + 'stats.html'
                    # to_write = self.html_a(to_write, href="\"" + path + "\"", target="\"_blank\"")

                if self.bkt_step2_has_good_strategy_temp and test_case_summary.index[i] == max_carmdd_index:
                    s_table_content += "  <td bgcolor=\"yellow\">"
                else:
                    s_table_content += "  <td>"
                s_table_content += to_write + "</td>\n"
            s_table_content += "</tr>\n"
        s_table_end = '</table>'
        s_table = s_table_begin + s_table_content + s_table_end
        s_content += s_table

        return s_begin + s_content + s_end

    def generate_bkt_step3(self):
        strategy_list = []
        strategy_df = pd.DataFrame()
        for s in os.listdir(self.bkt_result_step3_path):
            s_path = os.path.join(self.bkt_result_step3_path, s)
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
                    stats_table.iloc[29, 0] = stats_table.iloc[29, 0] + ' Loss'
                    stats_table = stats_table.set_index(0)
                    stats_table = stats_table.dropna()
                    # time.sleep(1000000)
                    stats_table_new = pd.DataFrame({
                        s: list(stats_table.iloc[:, 0])
                    }, index=list(stats_table.index))
                    strategy_df = strategy_df.append(stats_table_new.transpose())

        to_show_list = ['CAR/MaxDD', 'Net Profit', 'All trades', 'Avg. Bars Held', 'Winners', 'Avg. Profit',
                        'Losers', 'Avg. Loss', 'Max. system drawdown', 'Max. trade drawdown']
        # print(list(strategy_df.columns))
        rest_list = [x for x in list(strategy_df.columns) if x not in to_show_list]
        to_show_list.extend(rest_list)
        strategy_df = strategy_df[to_show_list]
        strategy_df.to_csv(os.path.join(self.bkt_result_step3_path, 'summary.csv'))

    def generate_monitoring_main(self):
        s_begin = """
<html>
<head>
<link rel="stylesheet" type="text/css" href="../mystyle.css">
<script src="../myfunction.js"></script>
</head>
<body>
<p><a href="../index.html"><-Homepage<a></p>
<h1>Monitoring</h1>\n """
        s_end = """</body>
</html>"""
        s_content = "<h2>Real Strategies</h2>\n"

        self.monitoring_strategy_dict = {}
        strategy_lastest_overview = pd.DataFrame()
        col_list = [
                'Name', 'Type', 'Date', 'Underlying', 'Actual PnL Cum', 'Day End Pos', 'Day End Price',
                'Theo PnL', 'Upper 1 STD', 'Lower 1 STD',
                'Trade No Cum', 'Trade No', 'Buy', 'Sell', 'Short', 'Cover', 'Theo Trade No Cum',
                'Theo Trade No Cum - Long', 'Theo Trade No Cum - Short',
            ]
        for ind in self.monitoring_strategy_df.index:
            this_strategy = self.monitoring_strategy_df.loc[ind, 'Strategy']
            type = self.monitoring_strategy_df.loc[ind, 'Type']
            this_strategy_df = pd.read_csv(
                os.path.join(self.monitoring_daily_path, this_strategy+'.csv'),
                parse_dates=['Date']
            )
            # print(this_strategy_df)
            this_strategy_df = this_strategy_df.sort_values(['Date'], axis=0, ascending=[0])
            # print(this_strategy_df)
            this_strategy_df.loc[:, 'Name'] = this_strategy
            this_strategy_df.loc[:, 'Type'] = type
            this_strategy_df = this_strategy_df[col_list]
            self.monitoring_strategy_dict[this_strategy] = this_strategy_df
            strategy_lastest_overview = strategy_lastest_overview.append(this_strategy_df.iloc[0, :])

        strategy_lastest_overview = strategy_lastest_overview[col_list]
        demo_strategy = strategy_lastest_overview[strategy_lastest_overview['Type'] == 'Demo']
        real_strategy = strategy_lastest_overview[strategy_lastest_overview['Type'] == 'Real']
        # print(strategy_lastest_overview)
        # print('-------------------------------------')

        def display_monitoring_overview(df):
            if df is None or len(df) == 0:
                return '<p>No strategies.</p>'
            s = "<table id=\"table_content\">\n"

            row_n = len(df)
            col_n = len(df.columns)
            s += "<tr>\n"
            # display table head
            for j in range(col_n):
                col = df.columns[j]
                s += "  <th onclick=\"sortTable(" + str(j) + ")\">" + col + "</th>\n"
            s += "</tr>\n"

            # display table body
            for i in range(row_n):
                s += "<tr>\n"
                for j in range(col_n):
                    temp = df.iloc[i, j]
                    if df.columns[j] == 'Name':
                        to_write = GenerateHTML.html_a(temp, href="\"" + temp + "/" + temp + ".html\"")
                    elif df.columns[j] == 'Date':
                        to_write = pd.Timestamp.strftime(temp, '%d/%m/%Y')
                    elif df.columns[j] in ['Underlying', 'Type']:
                        to_write = temp
                    elif df.columns[j] in ['Actual PnL Cum', 'Day End Price', 'Theo PnL', 'Upper 1 STD', 'Lower 1 STD']:
                        to_write = '{:,.1f}'.format(temp)
                    else:
                        to_write = '{:,.0f}'.format(temp)
                    s += "  <td>" + to_write + "</td>\n"
                s += "</tr>\n"
            s += "</table>\n"
            return s

        s_content += display_monitoring_overview(real_strategy)
        s_content += "<h2>Demo Strategies</h2>\n"
        s_content += display_monitoring_overview(demo_strategy)

        with open(os.path.join(self.monitoring_dir, "monitoring.html"), 'w') as f:
            f.write(s_begin + s_content + s_end)

    def generate_monitoring_bystrategy(self):
        for strategy in self.monitoring_strategy_dict:
            # e.g strategy = "HSI;15min;BBandBreakOut;Test42-3m_3m2015"
            output_html_path = os.path.join(self.monitoring_dir, strategy)
            if not os.path.exists(output_html_path):
                os.mkdir(output_html_path)

            s_begin = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<link rel="stylesheet" type="text/css" href="../../mystyle.css">
<script src="../../myfunction.js"></script>
</head>
<body>\n"""
            s_end = """</body>\n</html>"""
            s_content = "<p><a href=\"../monitoring.html\"><-Monitoring<a></p>\n</br>"
            s_content += "<h2>Strategy: " + strategy + "</h2>\n"

            this_strategy_df = self.monitoring_strategy_dict[strategy]
            # this_strategy_df = this_strategy_df.sort_values(['Date'], ascending=[0])

            # ----------- insert the pic ---------------
            s_content += "</br>"
            img_name = pd.Timestamp.strftime(this_strategy_df['Date'].iloc[0], '%Y%m%d') + '_' + strategy + '.png'
            # img_path = os.path.join(self.monitoring_daily_path, 'daily_pnl', img_name)
            img_path = '../../../Report/daily_monitor/daily_pnl/' + str(img_name)
            s_content += "<img src=\"" + img_path + "\">\n"

            # ------------ insert the table -------------
            s_content += "<table id=\"table_content\">\n"

            row_n = len(this_strategy_df)
            col_n = len(this_strategy_df.columns)

            s_content += '<tr>\n'
            for j in range(col_n):
                col = this_strategy_df.columns[j]
                s_content += "  <th>" + col + "</th>\n"
            s_content += "</tr>\n"

            # display table body
            for i in range(row_n):
                s_content += "<tr>\n"
                for j in range(col_n):
                    temp = this_strategy_df.iloc[i, j]
                    if this_strategy_df.columns[j] == 'Name':
                        to_write = temp
                    elif this_strategy_df.columns[j] == 'Date':
                        temp_str1 = pd.Timestamp.strftime(temp, '%Y%m%d')
                        temp_str2 = pd.Timestamp.strftime(temp, '%d/%m/%Y')
                        ds = temp_str1 + '_' + strategy
                        to_write = GenerateHTML.html_a(temp_str2, href="\"" + ds + ".html\"")
                        self.generate_monitoring_bystrategy_bydate_traderecords(strategy, temp_str1)
                    elif this_strategy_df.columns[j] in ['Underlying', 'Type']:
                        to_write = temp
                    elif this_strategy_df.columns[j] in \
                            ['Actual PnL Cum', 'Day End Price', 'Theo PnL', 'Upper 1 STD', 'Lower 1 STD']:
                        to_write = "{:,.1f}".format(temp)
                    else:
                        to_write = '{:,.0f}'.format(temp)
                    s_content += "  <td>" + to_write + "</td>\n"
                s_content += "</tr>\n"
            s_content += "</table>"

            with open(os.path.join(output_html_path, strategy+'.html'), 'w') as f:
                f.write(s_begin + s_content + s_end)

    def generate_monitoring_bystrategy_bydate_traderecords(self, strategy, date):
        # date should be in the format: yyyymmdd
        s_begin = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<link rel="stylesheet" type="text/css" href="../../mystyle.css">
</head>
<body>
                    """
        s_end = """</body>\n</html>"""
        s_content = "<p><a href=\"" + strategy +".html\"><-Strategy<a></p>\n</br>"
        s_content += "<p style=\"font-size:30px;\">Trade records of strategy: <i>" + \
                     strategy + "</i> on Date:" + date + "</p>\n"

        trade_records = pd.DataFrame()
        try:
            dateparse = lambda x: pd.datetime.strptime(x, '%d/%m/%Y %H:%M:%S')
            trade_records = pd.read_csv(os.path.join(self.monitoring_daily_path, 'trade_records', strategy, date + '.csv'),
                                        parse_dates=['Trade Time'], date_parser=dateparse)
            trade_records = trade_records.sort_values(['Trade Time'], ascending=[1])
        except:
            pass

        if trade_records is None or len(trade_records) == 0:
            s_content += "<p>No trade records</p>"
        else:
            s_table_begin = "<table id=\"table_content\">\n"
            s_table_content = '<tr>\n'
            for col in trade_records.columns:
                s_table_content += '  <th>' + col + '</th>\n'

            row_n = len(trade_records)
            col_n = len(trade_records.columns)
            for i in range(row_n):
                s_table_content += "<tr>\n"
                for j in range(col_n):
                    to_write = ''
                    temp = trade_records.iloc[i, j]
                    if isinstance(temp, (np.float, np.float64, np.int64, float, int)):
                        to_write = '{:,.1f}'.format(temp)
                    elif isinstance(temp, pd.Timestamp):
                        to_write = temp.strftime('%d/%m/%Y %H:%M:%S')
                    else:
                        to_write = temp
                    s_table_content += "  <td>" + to_write + "</td>\n"
                s_table_content += "</tr>\n"
            s_table = s_table_begin + s_table_content + "</table>\n"

            s_content += s_table

        with open(os.path.join(self.monitoring_dir, strategy, date + '_' + strategy + '.html'), 'w') as f:
            f.write(s_begin + s_content + s_end)

    def generate_material_list(self):
        s_begin = """
<html>
<head>
<style type="text/css">
ol {
    counter-reset: item;
    font-size:20px;
}
li {
    display: block;
    font-size:20px;
    margin-top:10px;
}
li:before {
    content: counters(item, ".")" ";
    counter-increment: item;
}
</style>
<script src="../myfunction.js"></script>
</head>
<body>
<p><a href="../index.html"><-Homepage<a></p>\n """
        s_end = """</body>
        </html>"""
        s_content = "<h1>Study Materials:</h1>\n"
        s_content += self.generate_material_list_dir_html(self.material_path)

        with open(os.path.join(self.root_path, 'materials', 'materials.html') ,'w') as f:
            f.write(s_begin + s_content + s_end)

    def generate_material_list_file_html(self, f, blanks="  "):
        # genrate the html for viewing a file
        # f must be a file
        base_f = os.path.basename(f)
        base_f_no_extension = base_f.split('.')[0]
        html_path = os.path.join(self.root_path, 'materials', 'viewers', base_f_no_extension+".html")
        to_return = ''
        if f.endswith('.pdf'):
            to_return = "<li><a href=\"" + html_path + " \" target=\"_blank\">" + base_f + "</a></li>\n"
            to_write = "<iframe width=\"100%\" height=\"100%\" src=\"" + f + "\"></iframe>"
            with open(html_path, 'w') as fw:
                fw.write(to_write)
        elif f.endswith('.txt') or f.endswith('.afl') or f.endswith('.css') or f.endswith('.js') or \
            f.endswith('.c') or f.endswith('.cpp') or f.endswith('.py') or f.endswith('.php') or \
            f.endswith('.csv'):
            to_return = "<li><a href=\"" + f + " \" target=\"_blank\">" + base_f + "</a></li>\n"
        else:
            to_return = "<li>" + base_f + "</li>\n"
        return blanks + to_return

    def generate_material_list_dir_html(self, d, blanks="", layer=0):
        if os.path.isfile(d):
            return self.generate_material_list_file_html(d, blanks)
        to_return = ''
        if layer > 0:
            to_return += blanks + '  <li>' + os.path.basename(d) + '\n'
        to_return += blanks + '  <ol>\n'
        for d_f in os.listdir(d):
            d_f = os.path.join(d, d_f)
            if os.path.isfile(d_f):
                to_return += self.generate_material_list_file_html(d_f, "  "*(layer+1) + blanks)
            if os.path.isdir(d_f):
                to_return += self.generate_material_list_dir_html(d_f, blanks="  " + blanks, layer=layer+1)
        to_return += blanks + '  </ol>\n'
        if layer > 0:
            to_return += blanks + '  </li>\n'


        return to_return


    # -------------------- utility functions --------------------
    def nested_list(self, nl, out_str, layer=0):
        # nl - nested list
        if len(nl) == 0:
            return ''
        out_str = out_str + '<ol>\n'
        for item in nl:
            if item[1] != '':
                out_str = out_str + "<li><a href=\"" + item[1] + "\">" + item[0] + "</a>"
            else:
                out_str = out_str + "<li>" + item[0]
            out_str = out_str + self.nested_list(item[2], '', layer+1) + '</li>\n'
            if layer == 0:
                out_str = out_str + '</br>\n'

        out_str = out_str + '</ol>\n'
        return out_str

    @staticmethod
    def html_p(content):
        return "<p>" + content + "</p>"


    # e.g. href="\"../index.html\""  # Note: must include \"
    @staticmethod
    def html_a(content, href=None, target=None):
        a_attribute = ''
        if href is not None:
            a_attribute += " href="+href
        if target is not None:
            a_attribute += " target=" + target
        if a_attribute != '':
            # print(content)
            return "<a" + a_attribute + ">" + content + "</a>"
        else:
            return "<a>" + content + "</a>"


    # convert pandas to plain html (no format)
    # def pandas2html(self, df, header=None, index=None):
    #     if not isinstance(df, pd.DataFrame):
    #         raise TypeError("[pands2html] df must be a pandas.DataFrame! Input df type=" + type(df))
    #     s_begin = "<table>\n"
    #     s_table = ''
    #
    #     if header is not None:
    #         s_table += '<tr>\n'
    #         space = False
    #         if index is not None:
    #             s_table += "  <th>&nbsp;</th>"
    #             space = True
    #         for col in s_table.columns:
    #             if not space:
    #                 s_table += "  "
    #                 space = True
    #             s_table += "<th>" + str(col) + "</th>"
    #         s_table += "\n</tr>\n"
    #
    #     row_n = len(df)
    #     col_n = len(df.columns)
    #     for i in range(row_n):
    #         s_table += "<tr>\n"
    #         if index is not None:
    #             s_table += "  <th>" + str(df.index[i]) + "</th>\n"
    #         for j in range(col_n):
    #             s_table += "  <td>" + str(df.iloc[i, j]) + "</td>\n"
    #         s_table += "</tr>\n"
    #
    #     s_end = '</table>'
    #     return s_begin + s_table + s_end



if __name__ == "__main__":
    config_path = "S:\\Amibroker project\\HTML_Report\\html_config.ini"
    # root_path = "S:\\Amibroker project\\HTML_Report2"
    # bkt_result_step1_path = 'S:\\Amibroker project\\Result\\Step1'
    # bkt_result_step2_path = 'S:\\Amibroker project\\Result\\Step2'
    html_builder = GenerateHTML(config_path)

    # html_builder.run()
    html_builder.run_monitoring()
    # nl = [
    #     ('Backtesting', '', [
    #         ('Step1', 'backtesting/step1.html', []),
    #         ('Step2', 'backtesting/step2.html', []),
    #         ('Step3', 'backtesting/step3.html', [])
    #     ]),
    #     ('Monitoring', '', []),
    #     ('Material', '', [])
    # ]
    # # generate_index_html(root_path)
    # print(nested_list(nl, ''))

    # run in the morning
    # while True:
    #     now_time = datetime.datetime.now()
    #     print('Now time = %s' % now_time)
    #     if now_time.hour == 6:
    #         html_builder2 = GenerateHTML(config_path)
    #         html_builder2.generate_bkt_pipeline()
    #         print('Run pipeline done!')
    #     time.sleep(58 * 60)
