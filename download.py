import pandas as pd
import requests
from io import StringIO
import os
import time
import datetime
from dateutil.relativedelta import relativedelta
import pickle

def monthly_report(year, month):
	
	# 假如是西元，轉成民國
	if year > 1990:
		year -= 1911
		
	url = 'https://mops.twse.com.tw/nas/t21/sii/t21sc03_'+str(year)+'_'+str(month)+'_0.html'
	if year <= 98:
		url = 'https://mops.twse.com.tw/nas/t21/sii/t21sc03_'+str(year)+'_'+str(month)+'.html'
	
	# 偽瀏覽器
	headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
		
	# 下載該年月的網站，並用pandas轉換成 dataframe
	r = requests.get(url, headers=headers)
	r.encoding = 'big5'

	print(r.text)

	dfs = pd.read_html(StringIO(r.text), encoding='big-5')

	df = pd.concat([df for df in dfs if df.shape[1] <= 11 and df.shape[1] > 5])
				
	if 'levels' in dir(df.columns):
		df.columns = df.columns.get_level_values(1)
	else:
		df = df[list(range(0,10))]
		column_index = df.index[(df[0] == '公司代號')][0]
		df.columns = df.iloc[column_index]
								
	df['當月營收'] = pd.to_numeric(df['當月營收'], 'coerce')
	df = df[~df['當月營收'].isnull()]
	df = df[df['公司代號'] != '合計']
							
	# 偽停頓
	time.sleep(5)
		
	return df

def downloadMonthlyReport(year, month):

	rocyear = year
	if rocyear > 1990:
		rocyear = rocyear - 1911
	
	# switch tse/otc stocks
	tseotc = ['sii', 'otc']
	for cat in tseotc:
		url = 'https://mops.twse.com.tw/nas/t21/' + cat + '/t21sc03_' + str(rocyear) + '_' + str(month) + '.csv'

		headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

		req = requests.get(url, headers=headers)
		req.encoding = 'utf-8'

		if(len(req.text) <= 500):
			print("error with " + str(year) + "-" + "%02d" % (month))
			return

		file = open("monthlyReport/" + cat + "report" + str(year) + "%02d" % (month) + ".csv", "w")
		file.write(req.text)
		file.close()

		print(cat + "report" + str(year) + "%02d" % (month) + ".csv written" + "(%d)" %(len(req.text)))

def downloadMonthlyReportUntil(year=2015):
	thistime = datetime.datetime.now()
	while thistime.year >= year:
		thistime = thistime - relativedelta(months=1)
		
		if(os.path.exists("monthlyReport/otcreport%d%02d.csv" % (thistime.year, thistime.month))):
		   continue
		downloadMonthlyReport(thistime.year, thistime.month)
		time.sleep(1.5)

def downloadStockIdList():
	tseotc = ['2', '4']
	
	print("downloading tse list")
	url = 'http://isin.twse.com.tw/isin/C_public.jsp?strMode=' + tseotc[0]
	req = requests.get(url)
	df = pd.read_html(req.text)[0]
	df.columns = df.iloc[0]
	df = df.iloc[1:]
	df = df.dropna(thresh=3, axis=0).dropna(thresh=3, axis=1)

	print("downloading otc list")
	url = 'http://isin.twse.com.tw/isin/C_public.jsp?strMode=' + tseotc[1]
	req = requests.get(url)
	df2 = pd.read_html(req.text)[0]
	df2.columns = df2.iloc[0]
	df2 = df2.iloc[1:]
	df2 = df2.dropna(thresh=3, axis=0).dropna(thresh=3, axis=1)

	df = df.append(df2, ignore_index=True)
	df['有價證券代號及名稱'] = df['有價證券代號及名稱'].str.split('　')
	df = df.drop(df.index[0])
	
	print("removing unnecessasry stock ids")
	stockList = {}
	i = 0
	while True:
		try:
			if(len(df['有價證券代號及名稱'].iat[i][0]) != 4):
				df = df.drop(df.index[i])
			else:
				stockList[df['有價證券代號及名稱'].iat[i][0]] = [df['有價證券代號及名稱'].iat[i][1], df['市場別'].iat[i], df['產業別'].iat[i]]
				i = i + 1
		except IndexError:
			break

	df.to_csv('StockIdList.csv')
	
	with open('stockList.pkl', 'wb') as f:
		pickle.dump(stockList, f)

	print("StockIdList.csv written")


downloadMonthlyReportUntil(2015)
