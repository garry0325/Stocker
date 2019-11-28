import sys
import numpy as np
import matplotlib.pyplot as plt
import datetime
from dateutil.relativedelta import relativedelta
import stockInfo
from matplotlib.font_manager import FontProperties
font=FontProperties(fname='/users/garry0325/Library/Fonts/TaipeiSansTCBeta-Regular.ttf',size=20)


global stockDictionary
stockDict = []

class bband():
	def __init__(self, price, MA, upper, lower):
		self.price = price
		self.MA = MA
		self.upper = upper
		self.lower = lower

def calculateBBands(date=datetime.datetime.now(),
					trackbackDates=90,
					N=20,	# days to make MA
					K=2):	# amplitude of band in stdev
	
	latestDate = stockInfo.generateStockPricesDictionaryByDate(date)['2330'].date
	datesNeeded = trackbackDates + N - 1
	day = 1
	
	stockList = {}
	while day <= datesNeeded:
		stockPrices = stockInfo.generateStockPricesDictionaryByDate(date, autoCorrectDate=False)
		if(stockPrices != None):
			stockDict.append(stockPrices)
			for stockItem in stockPrices:
				if(stockItem in stockList):
					stockList[stockItem] = np.append(stockList[stockItem], stockPrices[stockItem].price)
				else:
					stockList[stockItem] = np.array(stockPrices[stockItem].price)
		
			day = day + 1
		date = date - relativedelta(days=1)

	bbandList = {}
	stockListCopy = stockList.copy()
	for stockItem in stockListCopy:
		try:
			if(len(stockList[stockItem]) != datesNeeded):
				del stockList[stockItem]
				continue
		except TypeError:	# raises TypeError when using len(ndarray) ndarray has len 1
			del stockList[stockItem]
			continue

		bbandList[stockItem] = []

		for i in range(0, trackbackDates):
			n = stockList[stockItem][i:i+N]
			mean = n.mean()
			s = n.std()
		
			bbandList[stockItem].append(bband(stockList[stockItem][i], mean, mean + K * s, mean - K * s))
	print("Latest date %d/%02d/%02d" % (latestDate.year, latestDate.month, latestDate.day))
	
	return bbandList

def filterPriceHigherThanUpper(bbandList):
	bbandListCopy = bbandList.copy()
	for stockItem in bbandListCopy:
		if(bbandList[stockItem][0].price <= bbandList[stockItem][0].upper):
			del bbandList[stockItem]

	print("%d stocks found after filtering out price lower than upper" % (len(bbandList)))

	return bbandList

def filterHighestPriceForDays(bbandList, days=20):
	bbandListCopy = bbandList.copy()
	for stockItem in bbandListCopy:
		highest = True
		for i in range(1, days):
			if(bbandList[stockItem][i].price >= bbandList[stockItem][0].price):
				highest = False
				break

		if(not highest):
			del bbandList[stockItem]

	print("%d stocks found after highest price filter" % (len(bbandList)))

	return bbandList

def filterByMAandVolume(bbandList, date, duration=5, ratio=2):
	bbandListCopy = bbandList.copy()
	for stockItem in bbandListCopy:
		
		# filter by volume
		volume = 0
		for i in range(0, duration):
			volume = volume + stockDict[i][stockItem].volume
		volume = volume / duration
		if((stockDict[0][stockItem].volume / volume) < ratio or stockDict[0][stockItem].volume <= 1000 or stockDict[0][stockItem].price <= 10.0):
			del bbandList[stockItem]
			continue

		# filter by MA order
		MA5 = 0
		MA10 = 0
		MA20 = 0
		for i in range(0, 20):
			if(i < 5):
				MA5 = MA5 + stockDict[i][stockItem].price
			if(i < 10):
				MA10 = MA10 + stockDict[i][stockItem].price
			if(i < 20):
				MA20 = MA20 + stockDict[i][stockItem].price
		if(not (MA5 < MA10 and MA10 < MA20)):
			del bbandList[stockItem]
			continue

	print("%d stocks found after MA & volume filter" % (len(bbandList)))
	return bbandList

def evaluation(bbandList, buyDate, sellDate):
	d1 = stockInfo.generateStockPricesDictionaryByDate(buyDate)
	d2 = stockInfo.generateStockPricesDictionaryByDate(sellDate)
	
	averageProfit = 0
	for stockItem in bbandList:
		profit = (d2[stockItem].price - d1[stockItem].price) * 100 / d1[stockItem].price
		averageProfit = averageProfit + profit
		print("%3d%% %s" % (profit, stockItem))

	print("Average profit: %3d%%" % (averageProfit/len(bbandList)))

def plotBBand(bbandList, stockId):
	ma = []
	upper = []
	lower = []
	price = []
	
	for i in bbandList[stockId]:
		price.insert(0, i.price)
		ma.insert(0, i.MA)
		upper.insert(0, i.upper)
		lower.insert(0, i.lower)
	
	volume = []
	for i in range(len(price)-1, -1, -1):
		volume.append(stockDict[i][stockId].volume)
	volume = np.array(volume)
	lastDayVolume = volume[len(volume)-1]
	
	color = []
	for i in range(0, len(price)-1):
		if(price[i] < price[i+1]):
			color.append('r')
		elif(price[i] > price[i+1]):
			color.append('g')
		else:
			color.append('y')
	color.insert(0, 'r')
	
	l = range(0, len(ma))
	plt.figure(figsize=(10, 5))
	plt.plot(l, price, c='red', linewidth=2.0)
	plt.plot(l, ma, linewidth=1.5, alpha=0.5)
	plt.plot(l, upper, linewidth=1.5, alpha=0.5)
	plt.plot(l, lower, linewidth=1.5, alpha=0.5)

	ylim = plt.gca().get_ylim()
	ylim = [ylim[0], ylim[1]]
	ylim[0] = ylim[0] - ((ylim[1] - ylim[0]) * 0.3)
	volume = volume * (ylim[1] - ylim[0]) / 3 / max(volume) + ylim[0]
	plt.bar(l, volume, color=color, alpha=0.8)
	plt.ylim(ylim)

	plt.title(stockId + ' ' + stockDict[0][stockId].name, fontproperties=font)
	plt.ylabel('Price')
	plt.xlabel('Prc ' + str(price[0]) + ' (' + str(round((price[len(price)-1] - price[len(price)-2]) * 100 / price[len(price)-2], 2)) + '%)\nVol ' + str(lastDayVolume))

	plt.show()

def plotStocks(stockIds, untilDate, trackbackDates=180):
	if(type(stockIds) != list):
		stockIds = [stockIds]

	bband = calculateBBands(untilDate, trackbackDates=trackbackDates)
	for i in stockIds:
		plotBBand(bband, i)


def showFilteredStocksOnDate(date, trackbackDates=90):
	bband = calculateBBands(date, trackbackDates=trackbackDates)
	bband = filterPriceHigherThanUpper(bband)
	bband = filterHighestPriceForDays(bband)
	bband = filterByMAandVolume(bband, date)
	
	for i in bband:
		averageWidth = 0
		for j in range(30):
			averageWidth = averageWidth + (bband[i][j].upper - bband[i][j].MA) * 100 / bband[i][j].MA
		averageWidth = averageWidth / 30
		print("%s %.1f%%" % (i, averageWidth))
	
	c = input('show plot (y/n)?')
	if(c == 'y'):
		for i in bband:
			plotBBand(bband, i)

def evaluateFilteredStocksWithProfit(evaluateDate, sellDate, trackbackDates=90):
	bband = calculateBBands(evaluateDate, trackbackDates=trackbackDates)
	bband = filterPriceHigherThanUpper(bband)
	bband = filterHighestPriceForDays(bband)
	bband = filterByMAandVolume(bband, evaluateDate)

	buyDate = evaluateDate + relativedelta(days=1)
	d1 = stockInfo.generateStockPricesDictionaryByDate(buyDate)
	d2 = stockInfo.generateStockPricesDictionaryByDate(sellDate)

	for i in bband:
		profit = (d2[i].price - d1[i].price) * 100 / d1[i].price
		
		averageWidth = 0
		for j in range(30):
			averageWidth = averageWidth + (bband[i][j].upper - bband[i][j].MA) * 100 / bband[i][j].MA
		averageWidth = averageWidth / 30
		
		print("%3d%% %s %.1f%%" % (profit, i, averageWidth))
	
	c = input('show plot (y/n)?')
	if(c == 'y'):
		for i in bband:
			plotBBand(bband, i)


if(sys.argv[1] == '0'):
	showFilteredStocksOnDate(datetime.datetime(2019, 11, 26))

elif(sys.argv[1] == '1'):
	evaluateFilteredStocksWithProfit(datetime.datetime(2019, 11, 19), datetime.datetime(2019, 11, 28))


elif(sys.argv[1] == '2'):
	while True:
		c = input("id: ")
		if(c == 'end'):
			break
		try:
			plotStocks(c, datetime.datetime(2019, 11, 28), 90)
		except:
			continue
