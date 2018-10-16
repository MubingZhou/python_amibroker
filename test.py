import pandas as pd
import configparser
import os
import numpy as np
import random
import matplotlib.pyplot as plt
from FunctionList import  max_drawdown
from FunctionList import  AvgPoverAvgL
from FunctionList import  ExpectedValue
from time import sleep
from tqdm import tqdm

import math

config = configparser.ConfigParser()
config.read('Config.txt')
StartPool = config.get('StartPool', 'Pool')
path = config.get('CSVpath', 'path')
PointPerMoney = float(config.get('PointMoney', 'PointPerMoney'))
Times = config.get('testTimes', 'Times')

files = os.listdir(path)
for file in files:
    if not os.path.isdir(file):
        df = pd.read_csv(path+"/"+file ,parse_dates=[0, 3])

StartDate = df['OpenDate']
EndDate = df['CloseDate']
OpenTime = df['OpenTime']
CloseTime = df['CloseTime']
OpenPrice = df['OpenPrice']
ClosePrice = df['ClosePrice']
abc = df['NetProfit']
NetProfit=[]
for asd in abc:
    NetProfit.append(asd)
def rollDice():
    random.shuffle(NetProfit)
    return NetProfit

rollDice()
totalDate = EndDate[len(EndDate)-1] - StartDate[0]
totalDate = (totalDate / np.timedelta64(1, 'D')).astype(int)

x = 0
MDD = []
SP = []
FS = []
AR = []
MN = []
MX = []
CM = []
EV = []
AA = []
aB = {}
for i in tqdm(range(0, int(Times))):
    funds = int(StartPool)
    wX = []
    sumX = []
    jkl = 0
    rollDice()
    for currentWager in NetProfit:
        funds = funds + currentWager * PointPerMoney
        sumX.append(int(funds))
        wX.append(jkl)
        jkl += 1
    plt.plot(wX, sumX)
    tg = float(funds) / int(StartPool)
    if tg >= 0:
        ige = 1
    else:
        ige = -1
    n = (abs(tg)) ** (float(365) / totalDate) * ige - 1
    mdd = max_drawdown(sumX)
    if mdd == 0:
        mdd = 100
    AR.append(n*100)
    MN.append(np.min(sumX))
    MX.append(np.max(sumX))
    MDD.append(mdd*100)
    SP.append(int(StartPool))
    FS.append(funds)
    CM.append(n/mdd)
    EV.append(ExpectedValue(NetProfit))
    AA.append(AvgPoverAvgL(NetProfit))

aB = pd.DataFrame({'MDD':MDD,
                   'AnnualReturn':AR,
                   'EndPool': FS,
                   'StartPool': SP,
                   'MinPool': MN,
                   'MaxPool':MX,
                   'CAR/MDD':CM,
                   'ExpectedValue':EV,
                   'AvgP/AvgL':AA})

plt.ylabel('Pool')
plt.xlabel('Trade Count')
plt.savefig('MonteCarloResultResultGraph.png')

mddSort = sorted(MDD)
arSort = sorted(AR)
fsSort = sorted(FS)
mnSort = sorted(MN)
mxSort = sorted(MX)
cmSort = sorted(CM)
evSort = sorted(EV)
aaSort = sorted(AA)

a10 = int(math.floor(float(Times) * 0.1)) - 1
a30 = int(math.floor(float(Times) * 0.3)) - 1
a50 = int(math.floor(float(Times) * 0.5)) - 1
a70 = int(math.floor(float(Times) * 0.7)) - 1
a90 = int(math.floor(float(Times) * 0.9)) - 1

Precent10 = int(Times) - a10
Precent30 = int(Times) - a30
Precent50 = int(Times) - a50
Precent70 = int(Times) - a70
Precent90 = int(Times) - a90

result = [{'Average' : np.mean(MDD) , 'SD' : np.std(MDD) , '90%' : mddSort[a90] , '70%' : mddSort[a70] , '50%' : mddSort[a50] , '30%' : mddSort[a30] , '10%' : mddSort[a10]},
          {'Average' : np.mean(AR) , 'SD' : np.std(AR) , '90%' : arSort[Precent90] , '70%' : arSort[Precent70] , '50%' : arSort[Precent50] , '30%' : arSort[Precent30] , '10%' : arSort[Precent10]},
          {'Average': np.mean(FS), 'SD': np.std(FS), '90%': fsSort[Precent90], '70%': fsSort[Precent70],
           '50%': fsSort[Precent50], '30%': fsSort[Precent30], '10%': fsSort[Precent10]},
          {'Average': np.mean(MN), 'SD': np.std(MN), '90%': mnSort[Precent90], '70%': mnSort[Precent70],
           '50%': mnSort[Precent50], '30%': mnSort[Precent30], '10%': mnSort[Precent10]},
          {'Average': np.mean(MX), 'SD': np.std(MX), '90%': mxSort[Precent90], '70%': mxSort[Precent70],
           '50%': mxSort[Precent50], '30%': mxSort[Precent30], '10%': mxSort[Precent10]},
          {'Average': np.mean(CM), 'SD': np.std(CM), '90%': cmSort[Precent90], '70%': cmSort[Precent70],
           '50%': cmSort[Precent50], '30%': cmSort[Precent30], '10%': cmSort[Precent10]},
          {'Average': np.mean(EV), 'SD': np.std(EV), '90%': evSort[Precent90], '70%': evSort[Precent70],
           '50%': evSort[Precent50], '30%': evSort[Precent30], '10%': evSort[Precent10]},
          {'Average': np.mean(AA), 'SD': np.std(AA), '90%': aaSort[Precent90], '70%': aaSort[Precent70],
           '50%': aaSort[Precent50], '30%': aaSort[Precent30], '10%': aaSort[Precent10]}]

gh = pd.DataFrame(result,index = ['MDD','Annual Return','End Pool','Min Pool','Max Pool','CAR / MDD','Expected Value','AvgP / AvgL'] , columns = ['Average','SD','90%','70%','50%','30%','10%'])

writer = pd.ExcelWriter('MonteCarloResultResult.xlsx', engine='xlsxwriter')
aB.to_excel(writer, sheet_name='Total Result')
gh.to_excel(writer, sheet_name='Summary')
writer.save()








