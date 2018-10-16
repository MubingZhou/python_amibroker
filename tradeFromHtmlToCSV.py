from bs4 import BeautifulSoup
import pandas as pd
import os
from tqdm import tqdm


def TradeFromHtmlToCsv(Path):
    pathOpen = open(Path + "\\trades.html",'r')
    s = pathOpen.read()
    testtest = BeautifulSoup(s,"lxml")

    x = 0
    data_list = []
    for tr in testtest.find_all('tr'):
        if x >= 2:
            tds = tr.find_all('td')
            abc = tr.find_all('br')

            data_list.append({
                'Symbol' : tds[0].contents[0],
                'Trade' : tds[1].contents[0],
                'Date' : tds[2].contents[0],
                'Price' : ''.join(abc[0].next_siblings),
                'Ex.Date' : tds[3].contents[0],
                'Ex. Price' : ''.join(abc[1].next_siblings),
                '% chg' : tds[4].contents[0],
                'Profit' : tds[5].contents[0],
                '% Profit' : ''.join(abc[2].next_siblings),
                'Shares' : tds[6].contents[0],
                'Position value' : tds[7].contents[0],
                'Cum.profit' : tds[8].contents[0],
                '# bars' : tds[9].contents[0],
                'Profit/bar' : tds[10].contents[0],
                'MAE' : tds[11].contents[0],
                'MFE' : ''.join(abc[3].next_siblings),
                'Scale In/Out' : tds[12].contents[0]
            })
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
    efg = efg[['Symbol','Trade','Date','Price','Ex.Date','Ex. Price','% chg','Profit','% Profit'
        ,'Shares','Position value','Cum.profit','# bars','Profit/bar','MAE','MFE','Scale In/Out']]
    efg.to_csv(Path + "\\trades.csv", index=None)


# path = 'Y:\\Amibroker project\\Result\\Step3\\'
# files = os.listdir(path)
# for name in tqdm(files):
#     efg = TradeFromHtmlToCsv(path + name)
s = 'S:\\Amibroker project\\Result\\Step1\\HSI\\TrixCrossOver(T)\\3min\\HSI;3min;TrixCrossOverTest08(T)'
TradeFromHtmlToCsv(s)
