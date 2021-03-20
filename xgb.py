import xgboost
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import stockInfo
import datetime
import sys
import pickle

stockId = '2330'
startTrainDate = datetime.date(2018, 1, 1)
endTrainDate = datetime.date(2019, 12, 31)
predictDays = 3
startPredictDate = datetime.date(2019, 9, 1)
endPredictDate = datetime.date(2020, 6, 30)

def loadTrainingData():
    print("Loading training data from {}/{}/{} to {}/{}/{}...".format(startTrainDate.year, startTrainDate.month, startTrainDate.day, endTrainDate.year, endTrainDate.month, endTrainDate.day))
    x = [] # price, open, high, low, volume, transactions, dyield, peratio, pbratio
    y = [] # the price after 'predictDays'
    
    incrementDay = datetime.timedelta(days=1)
    iterateDate = startTrainDate
    while iterateDate <= endTrainDate:
        d = stockInfo.generateStockPricesDictionaryByDate(iterateDate, False)
        
        if(d != None):
            tempX = [d[stockId].price, d[stockId].open, d[stockId].high, d[stockId].low, d[stockId].volume, d[stockId].transactions, d[stockId].dyield, d[stockId].peratio, d[stockId].pbratio]
        
            x.append(tempX)
            y.append(d[stockId].price)
    
        iterateDate += incrementDay
        
    x = x[:-1 * predictDays]
    y = y[predictDays:]
    
    return x, y

def train():
    x, y = loadTrainingData()
    print(len(x))
    print(len(y))
    
    print('Training starts at {}'.format(datetime.datetime.now()))
    model = xgboost.XGBRegressor(max_depth = 50)
    model.fit(np.array(x), np.array(y))
    print('Ended at {}'.format(datetime.datetime.now()))
    
    print('Saving model...')
    with open('xgbModel.pkl', 'wb') as f:
        pickle.dump(model, f)
    print('Saved')
    
    
def loadPredictData():
    print("Loading predict data from {}/{}/{} to {}/{}/{}...".format(startPredictDate.year, startPredictDate.month, startPredictDate.day, endPredictDate.year, endPredictDate.month, endPredictDate.day))
    x = [] # price, open, high, low, volume, transactions, dyield, peratio, pbratio
    y = [] # the price after 'predictDays'
    
    incrementDay = datetime.timedelta(days=1)
    iterateDate = startPredictDate
    while iterateDate <= endPredictDate:
        d = stockInfo.generateStockPricesDictionaryByDate(iterateDate, False)
        
        if(d != None):
            tempX = [d[stockId].price, d[stockId].open, d[stockId].high, d[stockId].low, d[stockId].volume, d[stockId].transactions, d[stockId].dyield, d[stockId].peratio, d[stockId].pbratio]
        
            x.append(tempX)
            y.append(d[stockId].price)
    
        iterateDate += incrementDay
    
    return x, y

def predict():
    pass
    
    

if __name__ == '__main__':
    
    if(sys.argv[1] == 't'):
        train()
        
        
        
        
    elif(sys.argv[1] == 'p'):
        x, y = loadPredictData()
        with open('xgbModel.pkl', 'rb') as f:
            model = pickle.load(f)
            
        yPredict = model.predict(np.array(x))
        y = y[predictDays:]
        yPredict = yPredict[:-1 * predictDays]
        
        print('y: {}'.format(len(y)))
        print('yPredict: {}'.format(len(yPredict)))
        
        plt.plot(y, label = "True", color = 'Blue', linewidth = 2)
        plt.plot(yPredict, label = "Predict", color = 'Red', linewidth = 2)
        plt.legend()
        plt.show()
