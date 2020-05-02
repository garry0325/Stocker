import pandas as pd
import datetime
from dateutil.relativedelta import relativedelta
import requests
import json
import os
import sys
import time
import pickle

global stockList
with open('stockList.pkl', 'rb') as f:
	stockList = pickle.load(f)


class Stock():
	def __init__(self, name="", price=0, open=0, high=0, low=0, offset=0, volume=0, amount=0, transactions=0, cat="", dyield=0, peratio=0, pbratio=0, date=None):
		self.name = name
		self.price = price
		self.open = open
		self.high = high
		self.low = low
		self.offset = offset
		self.volume = volume
		self.amount = amount
		self.transactions = transactions
		self.cat = cat
		self.dyield = dyield
		self.peratio = peratio
		self.pbratio = pbratio
		self.date = date

	def summerize(self):
		if(self.price == 0):
			print("No data")
			return
		print("%s %d/%02d/%02d %s" % (self.name, self.date.year, self.date.month, self.date.day, self.cat))
		if(self.offset >= 0):
			offsetOutput = "+%.2f" % (self.offset)
			progressOutput = "+%.2f%%" % (self.offset * 100 / (self.price - self.offset))
		else:
			offsetOutput = "%.2f" % (self.offset)
			progressOutput = "%.2f%%" % (self.offset * 100 / (self.price - self.offset))
		print("收盤: %10.2f  %s  %s" % (self.price, offsetOutput, progressOutput))
		print("開盤: %10.2f" % (self.open))
		print("最高: %10.2f" % (self.high))
		print("最低: %10.2f" % (self.low))
		print("成交: %10d" % (self.volume))
		print("筆數: %10d" % (self.transactions))
		print("金額: %10d" % (self.amount))
		print("殖利: %10.2f%%" % (self.dyield))
		print("本益: %10.2f" % (self.peratio))
		print("淨比: %10.2f" % (self.pbratio))


def generateMovingAverageDictionaryForAllStocksByDate(date, MA = 20, extraDays = 1):

	defaultUpdateDays = MA
	databasePath = 'stockPrices/'

	MADaysPrices = {}
	
	days = MA
	while days > (1 - extraDays):
		dataFile = "%s%d%02d%02dprice.json" % (databasePath, date.year, date.month, date.day)
		dataExists = os.path.exists(dataFile)
		if(not dataExists):
			print("database needs update")
			updateStockPricesDatabase(fromDate = (date - relativedelta(days=defaultUpdateDays)))
			continue

		if(os.stat(dataFile).st_size <= 100):
			date = date - relativedelta(days=1)
			continue

		with open(dataFile) as f:
			stockPrices = json.load(f)

		stockPrices = generateStockPricesDictionaryByDate(date)

		for stockItem in stockPrices:
			if(stockItem in MADaysPrices):
				MADaysPrices[stockItem].append(stockPrices[stockItem].price)
			else:
				MADaysPrices[stockItem] = [stockPrices[stockItem].price]
	
		date = date - relativedelta(days=1)
		days = days - 1
	
	MADaysPricesCopy = MADaysPrices.copy()
	for i in MADaysPricesCopy:
		if(len(MADaysPrices[i]) != (MA + extraDays - 1)):	# stocks not open in any workday should be lack in the list
			del MADaysPrices[i]
			continue
		
		try:
			for j in range(0, extraDays):
				MADaysPrices[i][j] = sum(MADaysPrices[i][j:j+MA]) / MA
		except TypeError:
			del MADaysPrices[i]
			continue

		MADaysPrices[i] = MADaysPrices[i][:extraDays]


	return MADaysPrices



def updateStockPricesDatabase(fromDate=datetime.datetime(2013, 1, 1)):
	toDate = datetime.datetime.now()
	
	print("downloading stock prices back to %d/%02d/%02d" % (fromDate.year, fromDate.month, fromDate.day))
	
	databasePath = 'stockPrices/'
	urlPricetse = 'https://www.twse.com.tw/exchangeReport/MI_INDEX?response=json&date='
	urlPerformancetse = 'https://www.twse.com.tw/exchangeReport/BWIBBU_d?response=json&date='
	urlPriceotc = 'https://www.tpex.org.tw/web/stock/aftertrading/otc_quotes_no1430/stk_wn1430_result.php?l=zh-tw&d='
	urlPerformanceotc = 'https://www.tpex.org.tw/web/stock/aftertrading/peratio_analysis/pera_result.php?l=zh-tw&d='
	
	
	if(toDate.date() == datetime.datetime.now().date()):
		if(datetime.datetime.now().hour < 17):	# today's stock prices be released after 1600
			print("toDate changed")
			toDate = toDate - relativedelta(days=1)
	date = toDate
	

	while date >= fromDate:
		# check if data exist
		dateFormat = "%d%02d%02dprice.json" % (date.year, date.month, date.day)
		dataExists = os.path.exists(databasePath + dateFormat)
		if(dataExists):
			#print("%s exists" % (dateFormat))
			date = date - relativedelta(days=1)
			continue
		
		prices = {}
		errors = 0

		# tse stocks
		url = "%s%d%02d%02d&type=ALLBUT0999" % (urlPricetse, date.year, date.month, date.day)
		req = requests.get(url)
		
		if(len(req.text) < 500):
			print("%d/%02d/%02d off day" % (date.year, date.month, date.day))
			prices['0000'] = 'off day'
			# write file
		else:
			response = json.loads(req.text)
			
			for stockItem in response['data9']:
				if(len(stockItem[0]) != 4):	# filter out irregular stocks
					continue
				try:
					# name, close, open, high, low, volume, offset, amount, trades, yield, peratio, pbratio, cat
					prepare = list(stockItem[i] for i in [1, 8, 5, 6, 7, 10, 2, 4, 3])
					
					if(stockItem[9] == '<p style= color:green>-</p>'):
						offset = -1 * float(stockItem[10])
					else:
						offset = float(stockItem[10])
					prepare[5] = offset
					
					for i in [1, 2, 3, 4]:
						prepare[i] = float(prepare[i].replace(',', ''))
					for i in [6, 7, 8]:
						prepare[i] = int(prepare[i].replace(',', ''))

					prepare[6] = int(prepare[6] / 1000)

				except:
					#print("error %s %s %d/%02d/%02d tse stock price" % (stockItem[0], stockItem[1], date.year, date.month, date.day))
					prepare = [stockItem[1], 0, 0, 0, 0, 0, 0, 0, 0]
					errors = errors + 1
				
				prepare = prepare + [0, 0, 0, '上市']
				prices[stockItem[0]] = prepare

			# tse stock performance data
			url = "%s%d%02d%02d&selectType=ALL" % (urlPerformancetse, date.year, date.month, date.day)
			req = requests.get(url)
			response = json.loads(req.text)
			for stockItem in response['data']:
				
				# format difference occur before 2017/4/12
				if(date.date() <= datetime.datetime(2017, 4, 12).date()):
					if(stockItem[2] == '-'):
						prices[stockItem[0]][10] = 0
					else:
						prices[stockItem[0]][10] = float(stockItem[2].replace(',', ''))
					if(stockItem[3] == '-'):
						prices[stockItem[0]][9] = 0
					else:
						prices[stockItem[0]][9] = float(stockItem[3].replace(',', ''))
					if(stockItem[4] == '-'):
						prices[stockItem[0]][11] = 0
					else:
						prices[stockItem[0]][11] = float(stockItem[4].replace(',', ''))
					continue
				
				if(stockItem[2] == '-'):
					prices[stockItem[0]][9] = 0
				else:
					prices[stockItem[0]][9] = float(stockItem[2].replace(',', ''))
				if(stockItem[4] == '-'):
					prices[stockItem[0]][10] = 0
				else:
					prices[stockItem[0]][10] = float(stockItem[4].replace(',', ''))
				if(stockItem[5] == '-'):
					prices[stockItem[0]][11] = 0
				else:
					prices[stockItem[0]][11] = float(stockItem[5].replace(',', ''))
		
			# otc stocks
			url = "%s%d/%02d/%02d&se=EW" % (urlPriceotc, date.year-1911, date.month, date.day)
			req = requests.get(url)
			response = json.loads(req.text)

			for stockItem in response['aaData']:
				if(len(stockItem[0]) != 4):
					continue
				try:
					prepare = list(stockItem[i] for i in [1, 2, 4, 5, 6, 3, 7, 8, 9])
					prepare[5] = prepare[5].replace(' ', '')
					
					for i in [1, 2, 3, 4]:
						prepare[i] = float(prepare[i].replace(',', ''))
					for i in [6, 7, 8]:
						prepare[i] = int(prepare[i].replace(',', ''))
					prepare[6] = int(prepare[6] / 1000)
					prepare[5] = float(prepare[5])

				except:
					#print("error %s %s %d/%02d/%02d otc stock price" % (stockItem[0], stockItem[1], date.year, date.month, date.day))
					if((prepare[5] == '除權息' or prepare[5] == '除權' or prepare[5] == '除息') and prepare[1] != '----'):
						prepare = [stockItem[1], prepare[1], prepare[2], prepare[3], prepare[4], 0, prepare[6], prepare[7], prepare[8]]
					else:
						prepare = [stockItem[1], 0, 0, 0, 0, 0, 0, 0, 0]
					errors = errors + 1
				
				prepare = prepare + [0, 0, 0, '上櫃']
				prices[stockItem[0]] = prepare

			# otc stock performance data
			url = "%s%d/%02d/%02d" % (urlPerformanceotc, date.year-1911, date.month, date.day)
			req = requests.get(url)
			response = json.loads(req.text)

			for stockItem in response['aaData']:
				if(stockItem[5] == 'N/A' or stockItem[5] == None):
					prices[stockItem[0]][9] = 0
				else:
					prices[stockItem[0]][9] = float(stockItem[5].replace(',', ''))
				if(stockItem[2] == 'N/A'):
					prices[stockItem[0]][10] = 0
				else:
					prices[stockItem[0]][10] = float(stockItem[2].replace(',', ''))
				if(stockItem[6] == 'N/A'):
					prices[stockItem[0]][11] = 0
				else:
					prices[stockItem[0]][11] = float(stockItem[6].replace(',', ''))

		with open(databasePath + dateFormat, 'w') as f:
			json.dump(prices, f)
		print("%s written (%d stocks, %d errors)" % (dateFormat, len(prices), errors))


		date = date - relativedelta(days=1)
		time.sleep(5)

def generateStockPricesDictionaryByDate(date, autoCorrectDate=True):
	databasePath = 'stockPrices/'
	dataFile = databasePath + "%d%02d%02dprice.json" % (date.year, date.month, date.day)
	
	dataExists = os.path.exists(dataFile)
	if(not dataExists):
		print("%s not found, consider updating the database" % (dataFile))
		return None

	if(os.stat(dataFile).st_size <= 100):
		print("error: %d/%02d/%02d is not weekday" % (date.year, date.month, date.day))
		if(autoCorrectDate):
			while os.stat(dataFile).st_size <= 100:
				date = date - relativedelta(days=1)
				dataFile = databasePath + "%d%02d%02dprice.json" % (date.year, date.month, date.day)
			print("take %d/%02d/%02d to generate dict" % (date.year, date.month, date.day))
		else:
			return None

	with open(dataFile, 'r') as f:
		prices = json.load(f)

	stockDict = {}
	for stockItem in prices:
		stockDict[stockItem] = Stock(prices[stockItem][0], prices[stockItem][1], prices[stockItem][2], prices[stockItem][3], prices[stockItem][4], prices[stockItem][5], prices[stockItem][6], prices[stockItem][7], prices[stockItem][8], prices[stockItem][12], prices[stockItem][9], prices[stockItem][10], prices[stockItem][11], date)


	return stockDict


def listAllStocksProfitsByDates(date1, date2, threshold=20):
	
	d1 = generateStockPricesDictionaryByDate(date1)
	d2 = generateStockPricesDictionaryByDate(date2)
	
	for i in range(0, 10000):
		stockId = "%04d" % (i)
		
		try:
			profit = (d2[stockId].price - d1[stockId].price) * 100 / d1[stockId].price
			if(profit >= threshold):
				print("%03d%%\t%s\t%s" % (profit, stockId, d1[stockId].name))

		except:
			continue


if __name__ == "__main__":
	
	if(sys.argv[1] == 'd'):
		updateStockPricesDatabase()

	elif(sys.argv[1] == '1'):
		d = generateStockPricesDictionaryByDate(datetime.datetime(2013, 11, 29))
		d['4137'].summerize()
