import numpy as np
import datetime
import stockInfo
import monthProgress

startDate = datetime.datetime(2019, 7, 1)
surpassDate = datetime.datetime(2020, 7, 1)
sellDate = datetime.datetime(2020, 7, 10)
durationFilter = datetime.timedelta(days=50)

class MDMP():
    def __init__(self, name, price, volume, date):
        self.name = name
        self.maxDate = None
        self.maxPrice = None
        self.surpassPrice = price
        self.surpassVolume = volume
        self.surpassDate = date

record = {}
traceDate = surpassDate


d = stockInfo.generateStockPricesDictionaryByDate(surpassDate, False)
for stockId in d:
    record[stockId] = MDMP(d[stockId].name, d[stockId].high, d[stockId].volume, d[stockId].date)
traceDate = traceDate - datetime.timedelta(days=1)

while startDate <= traceDate:
    d = stockInfo.generateStockPricesDictionaryByDate(traceDate, False)
    if(d != None):
        for stockId in d:
            try:
                if(d[stockId].high > record[stockId].surpassPrice and record[stockId].maxDate == None):
                    record[stockId].maxPrice = d[stockId].high
                    record[stockId].maxDate = d[stockId].date
            except KeyError:
                continue

    traceDate = traceDate - datetime.timedelta(days=1)


d = stockInfo.generateStockPricesDictionaryByDate(sellDate, False)
averageProfit = 0
profitCount = 0

for stockId in record:
    if(record[stockId].surpassPrice <= 10 or record[stockId].surpassVolume <= 500):
        continue

    try:
        profit = (d[stockId].price - record[stockId].surpassPrice) * 100 / record[stockId].surpassPrice
    except ZeroDivisionError:
        continue
    averageProfit = averageProfit + profit
    profitCount = profitCount + 1

    if(record[stockId].maxDate == None):
        print("%s%s\t%9.1f%%\t$%5d\t%7d\t" % (stockId, record[stockId].name, profit, record[stockId].surpassPrice, record[stockId].surpassVolume))
        continue

    duration = record[stockId].surpassDate - record[stockId].maxDate
    if(duration > durationFilter):
        print("%s%s\t%9.1f%%\t$%5d\t%7d\t%d-%02d-%02d" % (stockId, record[stockId].name, profit, record[stockId].surpassPrice, record[stockId].surpassVolume, record[stockId].maxDate.year, record[stockId].maxDate.month, record[stockId].maxDate.day))

print("\nAverage profit: %.1f%%" % (averageProfit/profitCount))
