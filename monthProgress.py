import pandas as pd
import numpy as np
import datetime
from dateutil.relativedelta import relativedelta
import pickle
import os
import sys
import time
import stockInfo
import matplotlib.pyplot as plt

M = 3	# Take M latest months to make average
N = 4	# Filter stocks whose average revenue increase more than N months in a row

monthlyReportFolder = 'monthlyReport/'
monthlyReportFile = ['siireport', 'otcreport']

global revenue
revenue = {}
global startDate
global endDate

def generateMonthlyRevenueToDictionary(M, N, end=datetime.datetime.now()):
	
	now = end
	numberOfMonths = M + N - 1
	count = 0
	
	revenue = {}	# should be initialized in order to generate multiple rounds within an execution
	
	while count <= numberOfMonths:
		for reportFile in monthlyReportFile:
			filename = monthlyReportFolder + reportFile + '%d%02d.csv' % (now.year, now.month)
			print(filename)
			
			# determine if the report is intact
			if(os.stat(filename).st_size > 1000):
				df = pd.read_csv(filename)
				df = df[['公司代號', '公司名稱', '營業收入-當月營收', '產業別']]
				
				for i in range(0, len(df)):
					id = str(df.loc[i]['公司代號'])
					
					# filter out construction stocks
					if(df.loc[i]['產業別'] == '建材營造'):
						continue
					if(id in revenue):
						r = df.loc[i]['營業收入-當月營收']	# store the value first because there are two subsequent task regarding to that value(if & append), making it more efficient
						if(r != 0):
							revenue[id].append(r)
					else:
						r = df.loc[i]['營業收入-當月營收']
						if(r != 0):
							revenue[id] = [r]

			else:
				print("No content, breaking out. Duration to %d-%02d" % (end.year, end.month-1))
				break

		count = count + 1
		
		if(count == numberOfMonths):	# after extracting monthly revenue for the M&N, extract that from the previous year of the month for YoY calculation
			now = end - relativedelta(years=1)
		else:
			now = now - relativedelta(months=1)

				
	with open('monthProgress.pkl', 'wb') as f:
		pickle.dump([revenue, end, M, N], f)
		print("cache monthProgress.pkl generated")



def readMonthlyRevenueFromDictionary():
	global revenue
	global endDate
	
	with open('monthProgress.pkl', 'rb') as f:
		revenue, endDate, M, N = pickle.load(f)

	print("Revenue data until %d-%02d\nM = %d N = %d\n" % (endDate.year, endDate.month, M, N))

def constraintsOutput(price=0, volume=0, dyield=0, peratio=0, pbratio=0, revenue=0, YoY=0):
	output = ""
	if(price != 0):
		if(type(price) == tuple):
			output = output + 'Price\t' + str(price[0]) + '~' + str(price[1]) + '\n'
		else:
			output = output + 'Price\t ' + str(price) + '~\n'
	if(volume != 0):
		if(type(volume) == tuple):
			output = output + 'Volume\t' + str(volume[0]) + '~' + str(volume[1]) + '\n'
		else:
			output = output + 'Volume\t' + str(volume) + '~\n'
	if(dyield != 0):
		if(type(dyield) == tuple):
			output = output + 'Yield\t' + str(dyield[0]) + '~' + str(dyield[1]) + '\n'
		else:
			output = output + 'Yield\t' + str(dyield) + '~\n'
	if(peratio != 0):
		if(type(peratio) == tuple):
			output = output + 'P/E\t' + str(peratio[0]) + '~' + str(peratio[1]) + '\n'
		else:
			output = output + 'P/E\t ~' + str(peratio) + '\n'
	if(pbratio != 0):
		if(type(pbratio) == tuple):
			output = output + 'P/B\t ' + str(pbratio[0]) + '~' + str(pbratio[1]) + '\n'
		else:
			output = output + 'P/B\t ~' + str(pbratio) + '\n'
	if(revenue != 0):
		if(type(revenue) == tuple):
			output = output + 'Revenue\t' + str(revenue[0]) + '~' + str(revenue[1]) + '\n'
		else:
			output = output + 'Revenue\t' + str(revenue) + '~\n'
	if(YoY != 0):
		if(type(YoY) == tuple):
			output = output + 'YoY\t' + str(YoY[0]) + '~' + str(YoY[1]) + '\n'
		else:
			output = output + 'YoY\t' + str(YoY) + '~\n'

	print(output)

def findStocksWithStrictlyIncreasingMonthlyAveragedRevenue(m, n):

	result = []
	
	for stockId in range(0, 10000):
		stockIdStr = "%04d" % (stockId)
	
		if(not(stockIdStr in revenue)):
			continue
		
		l = len(revenue[stockIdStr])
		if(l < (m+n)):	# filter out no enough data to be averaged
			continue
		
		# calculate average
		monthRevenue = revenue[stockIdStr]
		monthRevenue = np.array(monthRevenue)
		averagedRevenue = []
		for i in range(0, n):
			averagedRevenue.append(monthRevenue[i:i+m].mean())
		

		# identify strictly increasing
		strictlyIncreasing = all(averagedRevenue[i] >= averagedRevenue[i+1] for i in range(0, len(averagedRevenue)-1))
		
		# identify positive YoY
		positiveYoY = monthRevenue[0] > monthRevenue[len(monthRevenue)-1]
		
		# identify MoM
		positiveMoM = monthRevenue[0] > monthRevenue[1]
		
		
		if(strictlyIncreasing and positiveYoY and averagedRevenue[0] != 0):
			progress = (averagedRevenue[0] - averagedRevenue[n-1]) * 100 / averagedRevenue[n-1]
			progressYoY = (monthRevenue[0] - monthRevenue[len(monthRevenue)-1]) * 100 / monthRevenue[len(monthRevenue)-1]
			progressMoM = (monthRevenue[0] - monthRevenue[1]) * 100 / monthRevenue[1]
			
			result.append([stockIdStr, progress, progressYoY, progressMoM])

	print("%d stocks found with strictly increasing revenue with M=%d, N=%d" % (len(result), m, n))
	return result	# list of ['2330', '23.332', YoY, MoM]

def filtering(stockList, stockDictByDate, price=0, volume=0, dyield=0, peratio=0, pbratio=0, revenue=0, YoY=0):
	
	constraintsOutput(price, volume, dyield, peratio, pbratio, revenue, YoY)
	
	stockListCopy = stockList.copy()
	for stock in stockListCopy:
		if(stock[0] not in stockDictByDate or stockDictByDate[stock[0]].price == 0):
			stockList.remove(stock)


	if(price != 0):
		stockListCopy = stockList.copy()
		if(type(price) == tuple or type(price) == list):
			for stock in stockListCopy:
				if(not(price[0] <= stockDictByDate[stock[0]].price and stockDictByDate[stock[0]].price <= price[1])):
					stockList.remove(stock)
		else:
			for stock in stockListCopy:
				if(stockDictByDate[stock[0]].price < price):
					stockList.remove(stock)

	if(volume != 0):
		stockListCopy = stockList.copy()
		if(type(volume) == tuple or type(volume) == list):
			for stock in stockListCopy:
				if(not(volume[0] <= stockDictByDate[stock[0]].volume and stockDictByDate[stock[0]].volume <= volume[1])):
					stockList.remove(stock)
		else:
			for stock in stockListCopy:
				if(stockDictByDate[stock[0]].volume < volume):
					stockList.remove(stock)

	if(dyield != 0):
		stockListCopy = stockList.copy()
		if(type(dyield) == tuple or type(dyield) == list):
			for stock in stockListCopy:
				if(not(dyield[0] <= stockDictByDate[stock[0]].dyield and stockDictByDate[stock[0]].dyield <= dyield[1])):
					stockList.remove(stock)
		else:
			for stock in stockListCopy:
				if(stockDictByDate[stock[0]].dyield < dyield):
					stockList.remove(stock)

	if(peratio != 0):
		stockListCopy = stockList.copy()
		if(type(peratio) == tuple or type(peratio) == list):
			for stock in stockListCopy:
				if(not(peratio[0] <= stockDictByDate[stock[0]].peratio and stockDictByDate[stock[0]].peratio <= peratio[1])):
					stockList.remove(stock)
		else:
			for stock in stockListCopy:
				if(stockDictByDate[stock[0]].peratio > peratio):
					stockList.remove(stock)

	if(pbratio != 0):
		stockListCopy = stockList.copy()
		if(type(pbratio) == tuple or type(pbratio) == list):
			for stock in stockListCopy:
				if(not(pbratio[0] <= stockDictByDate[stock[0]].pbratio and stockDictByDate[stock[0]].pbratio <= pbratio[1])):
					stockList.remove(stock)
		else:
			for stock in stockListCopy:
				if(stockDictByDate[stock[0]].pbratio > pbratio):
					stockList.remove(stock)
	if(revenue != 0):
		stockListCopy = stockList.copy()
		if(type(revenue) == tuple or type(revenue) == list):
			for stock in stockListCopy:
				if(not(revenue[0] <= stock[1] and stock[1] <= revenue[1])):
					stockList.remove(stock)
		else:
			for stock in stockListCopy:
				if(revenue < stock[1]):
					stockList.remove(stock)

	if(YoY != 0):
		stockListCopy = stockList.copy()
		if(type(YoY) == tuple or type(YoY) == list):
			for stock in stockListCopy:
				if(not(YoY[0] <= stock[2] and stock[2] <= YoY[1])):
					stockList.remove(stock)
		else:
			for stock in stockListCopy:
				if(stock[2] < YoY):
					stockList.remove(stock)

	print("%d stocks found after filtering" % (len(stockList)))

	return stockList

def filterUsingMA(stockList, dateOfMA, MA=20, extraDays=2, shouldBeStrictlyIncreasing=False, interval=0):
	maList = stockInfo.generateMovingAverageDictionaryForAllStocksByDate(date=dateOfMA, MA=MA, extraDays=extraDays)
	
	d =  stockInfo.generateStockPricesDictionaryByDate(dateOfMA)
	
	stockListCopy = stockList.copy()
	for stock in stockListCopy:
		strictlyIncreasing = True
		if(shouldBeStrictlyIncreasing):
			try:	# stocks not open in any workday should be lack in maList
				a = all(maList[stock[0]][i] >= maList[stock[0]][i+1] for i in range(0, extraDays-1))
				b = d[stock[0]].price >= maList[stock[0]][0]
				strictlyIncreasing = a and b
			
			except KeyError:
				stockList.remove(stock)
				continue
	
		if(not strictlyIncreasing):
			stockList.remove(stock)
			continue
		
	
		try:	# stocks not open in any workday should be lack in maList
			progress = (maList[stock[0]][0] - maList[stock[0]][extraDays-1]) * 100 / maList[stock[0]][extraDays-1]

		except KeyError:
			stockList.remove(stock)
			continue

		if(interval != 0):
			if(type(interval) == tuple or type(interval) == list):
				if(not(interval[0] <= progress and progress <= interval[1])):
					stockList.remove(stock)
			else:
				if(progress < interval):
					stockList.remove(stock)

		stock.append(maList[stock[0]][0])
		stock.append(progress)

	print("%d stocks found after MA filter" % (len(stockList)))
	return stockList	# ['2330', growth, YoY, MoM, MA on buy date, MA increase]


def evaluation(stockList, buyDate, sellDate):
	averageProfit = 0
	count = 0
	
	d1 = buyDate['2330'].date
	d2 = sellDate['2330'].date
	

	print("\n獲利\t殖利\t本益\t淨比\t營收\tYoY\tMoM\t代號\t公司\t股價%d/%02d/%02d\t股價%d/%02d/%02d\t成交量\tMA20\tMA20Progress" % (d1.year, d1.month, d1.day, d2.year, d2.month, d2.day))
	print("-----------------------------------------------------------------------")
	
	for stock in stockList:
		
		try:
			profit = (sellDate[stock[0]].price - buyDate[stock[0]].price) * 100 / buyDate[stock[0]].price
		except:
			continue
		
		averageProfit = averageProfit + profit
		count = count + 1
		print("%3d%%\t%3.2f%%\t%5.2f\t%4.2f\t%3d%%\t%3d%%\t%3d%%\t%s\t%6s\t%7.2f\t%7.2f\t%10d\t%.2f\t%.3f%%" % (profit, buyDate[stock[0]].dyield, buyDate[stock[0]].peratio, buyDate[stock[0]].pbratio, stock[1], stock[2], stock[3], stock[0], buyDate[stock[0]].name, buyDate[stock[0]].price, sellDate[stock[0]].price, buyDate[stock[0]].volume, stock[4], stock[5]))
	
	# 0050 evaluation
	print("%3d%%\t\t\t\t\t\t\t%s\t%6s\t%7.2f\t%7.2f\t%10d\t\t" % (((sellDate['0050'].price - buyDate['0050'].price) * 100 / buyDate['0050'].price), '0050', buyDate['0050'].name, buyDate['0050'].price, sellDate['0050'].price, buyDate['0050'].volume))
		  
		  
	averageProfit = averageProfit / count
	print("\n%d stocks found\nAverage Profit: %.1f%%\n" % (count, averageProfit))


def prediction(M, N, buyDate=datetime.datetime.now(),
			   price=10,
			   volume=10,
			   dyield=(0.1, 3),
			   peratio=(0.1, 100),
			   pbratio=0,
			   revenue=(10, 100),
			   YoY=(10, 100),
			   MA=20,
			   extraDays=2,
			   shouldBeStrictlyIncreasing=True,
			   interval=(0.8, 20)):
	
	generateMonthlyRevenueToDictionary(M=M, N=N, end=buyDate-relativedelta(months=1))
	readMonthlyRevenueFromDictionary()
	
	result = findStocksWithStrictlyIncreasingMonthlyAveragedRevenue(M, N)

	
	while True:
		buyDatePrices = stockInfo.generateStockPricesDictionaryByDate(buyDate)
		if(buyDatePrices == None):	# specific date stock price report not released yet
			buyDate = buyDate - relativedelta(days=1)
		else:
			print("take %d/%02d/%02d in prediction" % (buyDate.year, buyDate.month, buyDate.day))
			break
	
	buyDate = buyDatePrices['2330'].date
	
	result = filtering(result, buyDatePrices, price=price, volume=volume, dyield=dyield, peratio=peratio, pbratio=pbratio, revenue=revenue, YoY=YoY)

	result = filterUsingMA(result, buyDate, MA=MA, extraDays=extraDays, shouldBeStrictlyIncreasing=shouldBeStrictlyIncreasing, interval=interval)
	
	
	# showing filtering result
	count = 0
	
	print("殖利\t本益\t淨比\t營收\tYoY\tMoM\t代號\t公司\t股價%d/%02d/%02d\t成交量\tMA20\tMA20Progress" % (buyDate.year, buyDate.month, buyDate.day))
	print("-----------------------------------------------------------------------")
	
	for stock in result:
		
		count = count + 1
		print("%3.2f%%\t%5.2f\t%4.2f\t%3d%%\t%3d%%\t%3d%%\t%s\t%6s\t%7.2f\t%10d\t%.2f\t%.3f%%" % (buyDatePrices[stock[0]].dyield, buyDatePrices[stock[0]].peratio, buyDatePrices[stock[0]].pbratio, stock[1], stock[2], stock[3], stock[0], buyDatePrices[stock[0]].name, buyDatePrices[stock[0]].price, buyDatePrices[stock[0]].volume, stock[4], stock[5]))

			
	print("\n%d stocks found\n" % (count))

def evaluateCertainStock(stockIds, buyDate, sellDate=None):
	if(type(stockIds) != list):
		stockIds = [stockIds]
	
	now = buyDate
	
	revenue = {}	# should be initialized in order to generate multiple rounds within an execution
	for stockItem in stockIds:
		revenue[stockItem] = []
	
	for k in range(0, 3):
		for reportFile in monthlyReportFile:
			filename = monthlyReportFolder + reportFile + '%d%02d.csv' % (now.year, now.month)
			print(filename)
			
			# determine if the report is intact
			if(os.path.exists(filename)):
				df = pd.read_csv(filename)
				df = df[['公司代號', '公司名稱', '營業收入-當月營收', '產業別']]
				
				
				for i in range(0, len(df)):
					id = str(df.loc[i]['公司代號'])
					if(not(id in stockIds)):
						continue
					
					# not filtering out construction stocks
					
					r = df.loc[i]['營業收入-當月營收']
					revenue[id].append(r)
		
			else:
				now = now - relativedelta(months=1)
				print("Revenue report not published yet. Take %d%02d" % (now.year, now.month))
				continue


		if(k == 0):
			now = now - relativedelta(months=1)
		elif(k == 1):
			now = now - relativedelta(years=1)
			now = now + relativedelta(months=1)

	if(sellDate != None):
		buy = stockInfo.generateStockPricesDictionaryByDate(buyDate)
		sell = stockInfo.generateStockPricesDictionaryByDate(sellDate)
		buyMA = stockInfo.generateMovingAverageDictionaryForAllStocksByDate(buyDate, MA=20, extraDays=2)

		print("\n獲利\t殖利\t本益\t淨比\tYoY\tMoM\t代號\t公司\t股價%d/%02d/%02d\t股價%d/%02d/%02d\t成交量\tMA20\tMA20Progress" % (buyDate.year, buyDate.month, buyDate.day, sellDate.year, sellDate.month, sellDate.day))
		print("-----------------------------------------------------------------------")
		
		averageProfit = 0
		count = 0
		for stockItem in revenue:
			try:
				profit = (sell[stockItem].price - buy[stockItem].price) * 100 / buy[stockItem].price
				MoM = (revenue[stockItem][0] - revenue[stockItem][1]) * 100 / revenue[stockItem][1]
				YoY = (revenue[stockItem][0] - revenue[stockItem][2]) * 100 / revenue[stockItem][2]
				MA = buyMA[stockItem][0]
				MAProgress = (MA - buyMA[stockItem][1]) * 100 / buyMA[stockItem][1]
			except:
				continue
			
			averageProfit = averageProfit + profit
			count = count + 1
			print("%3d%%\t%3.2f%%\t%5.2f\t%4.2f\t%3d%%\t%3d%%\t%s\t%6s\t%7.2f\t%7.2f\t%10d\t%.2f\t%.3f%%" % (profit, buy[stockItem].dyield, buy[stockItem].peratio, buy[stockItem].pbratio, YoY, MoM, stockItem, buy[stockItem].name, buy[stockItem].price, sell[stockItem].price, buy[stockItem].volume, MA, MAProgress))

		averageProfit = averageProfit / count
		print("\n%d stocks found\nAverage Profit: %.1f%%\n" % (count, averageProfit))

	else:
		buy = stockInfo.generateStockPricesDictionaryByDate(buyDate)
		buyMA = stockInfo.generateMovingAverageDictionaryForAllStocksByDate(buyDate, MA=20, extraDays=2)
		print("\t殖利\t本益\t淨比\tYoY\tMoM\t代號\t公司\t股價%d/%02d/%02d\t成交量\tMA20\tMA20Progress" % (buyDate.year, buyDate.month, buyDate.day))
		print("-----------------------------------------------------------------------")

		count = 0
		for stockItem in revenue:
			try:
				MoM = (revenue[stockItem][0] - revenue[stockItem][1]) * 100 / revenue[stockItem][1]
				YoY = (revenue[stockItem][0] - revenue[stockItem][2]) * 100 / revenue[stockItem][2]
				MA = buyMA[stockItem][0]
				MAProgress = (MA - buyMA[stockItem][1]) * 100 / buyMA[stockItem][1]
			except:
				continue
				
			count = count + 1
			print("%3d%%\t%3.2f%%\t%5.2f\t%3d%%\t%3d%%\t%s\t%6s\t%7.2f\t%10d\t%.2f\t%.3f%%" % (buy[stockItem].dyield, buy[stockItem].peratio, buy[stockItem].pbratio, YoY, MoM, stockItem, buy[stockItem].name, buy[stockItem].price, buy[stockItem].volume, MA, MAProgress))

		print("%d stocks found\n" % (count))



if __name__ == "__main__":

	if(sys.argv[1] == '0'):
		generateMonthlyRevenueToDictionary(M=M, N=N, end=datetime.datetime(year=2019, month=8, day=1))

	elif(sys.argv[1] == '1'):
		
		readMonthlyRevenueFromDictionary()
		
		result = findStocksWithStrictlyIncreasingMonthlyAveragedRevenue(M, N)
		
		buyDate = endDate + relativedelta(months=1)
		buyDate = datetime.datetime(buyDate.year, buyDate.month, 11)
		
		sellDate = endDate + relativedelta(months=2)
		sellDate = datetime.datetime(sellDate.year, sellDate.month, 5)

		buyDatePrices = stockInfo.generateStockPricesDictionaryByDate(buyDate)
		sellDatePrices = stockInfo.generateStockPricesDictionaryByDate(sellDate)

		
		result = filtering(result, buyDatePrices, 10.0, 1000, dyield=(0.1, 20), peratio=(0.1, 100), revenue=(10, 100), YoY=(10, 100)) # best from 2019-06 monthly revenue, M=3, N=4
		result = filterUsingMA(result, buyDate, 20, 2, True, interval=(0.6, 25))
		
		'''
		result = filtering(result, buyDatePrices, 10.0, 500, dyield=(0.01, 20), peratio=(0.01, 200), pbratio=(0.01, 100), revenue=(1, 300), YoY=(0.01, 400)) # best from 2019-06 monthly revenue, M=3, N=4
		result = filterUsingMA(result, buyDate, 20, 2, False)
		'''
		
		
		evaluation(result, buyDatePrices, sellDatePrices)

	elif(sys.argv[1] == '4'):
		
		file = open('data.csv', 'w')
		file.write("獲利,殖利,本益,淨比,營收,YoY,MoM,代號,公司,股價buy,股價sell,成交量,MA20,MA20Progress\n")
		file.close()
		
		date = datetime.datetime(2019, 8, 1)
		
		while date >= datetime.datetime(2014, 1, 1):
		
			generateMonthlyRevenueToDictionary(M=M, N=N, end=date)

			readMonthlyRevenueFromDictionary()
			result = findStocksWithStrictlyIncreasingMonthlyAveragedRevenue(M, N)
			
			buyDate = endDate + relativedelta(months=1)
			buyDate = datetime.datetime(buyDate.year, buyDate.month, 11)
			sellDate = endDate + relativedelta(months=2)
			sellDate = datetime.datetime(sellDate.year, sellDate.month, 5)

			buyDatePrices = stockInfo.generateStockPricesDictionaryByDate(buyDate)
			sellDatePrices = stockInfo.generateStockPricesDictionaryByDate(sellDate)

			
			result = filtering(result, buyDatePrices, 10.0, 500, dyield=(0.01, 20), peratio=(0.01, 200), pbratio=(0.01, 100), revenue=(1, 300), YoY=(0.01, 400)) # best from 2019-06 monthly revenue, M=3, N=4
			result = filterUsingMA(result, buyDate, 20, 2, False)
			
			'''
			result = filtering(result, buyDatePrices, 10.0, 1000, dyield=(0.1, 20), peratio=(0.1, 100), revenue=(10, 100), YoY=(10, 100)) # best from 2019-06 monthly revenue, M=3, N=4
			result = filterUsingMA(result, buyDate, 20, 2, True, interval=(0.6, 25))
			'''
			
			evaluation(result, buyDatePrices, sellDatePrices)

			print("%d%02d complete" % (date.year, date.month))
			date = date - relativedelta(months=1)


	# M=4, N=5, buy date 11, sell date 5, price > 10, volume > 1000, dyield 0.1-3,
	# peratio 0.1-100, revenue 10-100, YoY 10-100.
	# Rank by YoY, if MA20 progress > 0.8 (maybe just filter it), then take it.

	elif(sys.argv[1] == '3'):
		prediction(M, N,
				   price=10.0,
				   volume=1000,
				   dyield=(0.1, 20),
				   peratio=(0.1, 100),
				   revenue=(10, 100),
				   YoY=(10, 100),
				   MA=20,
				   extraDays=2,
				   shouldBeStrictlyIncreasing=True,
				   interval=(0.6, 25))

	elif(sys.argv[1] == '5'):
		evaluateCertainStock(['3483', '5876'], datetime.datetime.now())
