#               ---------TO DO --------------

#make system argv input enter 
#add gridsearch(pdq selection) to arima
#add plot labels
#data persentage between train and prediction
# 				--------- TO DO ------------


from pyzabbix import ZabbixAPI
import pandas as pd
import json
import csv
import matplotlib.pyplot as plt
from statsmodels.graphics.tsaplots import plot_acf
from statsmodels.tsa.arima_model import ARIMA
from sklearn.metrics import mean_squared_error
from math import sqrt
import os
import itertools
import warnings
from RegscorePy import *


# PART 1
#zabbix server url
zapi = ZabbixAPI("yourmachineip/zabbix") 
#zabbix creds
zapi.login("Admin", "zabbix")

#connection verify
print("Connected to Zabbix API Version %s" % zapi.api_version())

#we inclue iterator value to the file names to eliminate confusion
global bool_value
bool_value = True
global iterator
iterator = 0

#variables for arima parameters and aic function value
global param_temp
global aic_temp
global mse_temp


#while loop to check if filename allready exists
while bool_value:
	print(bool_value)
	filename = "zabbixdata_%d_.json" % iterator
	exists = os.path.isfile(filename)
	if exists:
		iterator = iterator + 1
		print(iterator)
	if exists == False:
		bool_value = False  
		print(bool_value)


filename = "zabbixdata_%d_.json" % iterator
#ForecastCPU values(float) sorted by clock,json data. (select itemid,key_,name from items where key_="anything";)
#select itemid,name,key_ form items; to display full list of items.
for h in zapi.history.get(history='0',itemids='23303', sortfield='clock', sortorder='DESC',limit=500):
	#convert dict data to json 
	h = json.dumps(dict(h))
	#write json data to file
	f = open(filename,"a+")
	f.write(h + "\r\n")
    
#open json with pandas

with open(filename) as f_input:
	filename = filename + ".csv"
	#read from json file and convert to csv
	df = pd.read_json(f_input, encoding = 'utf-8', lines = True)
	df.to_csv(filename, encoding = 'utf-8', index = False)

#-----------------------END-------------------------


# PART 2

# now we parse the csv data and  apply arima function to data.


#2.0
#read data from file and parse it
tseries = pd.read_csv(filename, index_col = 'clock')

# we only want clock and value colums to process
tseries_parsed = tseries[tseries.columns[2]]
print(tseries_parsed.head())

tseries_parsed.plot()


#2.1
#regression part

tseries_parsed_diff = tseries_parsed.diff(periods = 5)

#we extract NaN values out
tseries_parsed_diff = tseries_parsed_diff[5:]
tseries_parsed_diff.plot()



#2.2
#autocorrelation plots before and after diff,so we can observe data
plot_acf(tseries_parsed, color = 'gray')
plot_acf(tseries_parsed_diff, color= 'green')


#2.3
#train and prediction values will be set

X = tseries_parsed.values
#check how many values are there,which will be 499.
print("loaded data count: %d \n"% (X.size))

#train data is set to train variable
train = X[0:450] 
print("train data count : %d \n" % (train.size))

#test data is set to test variable
test = X[450:499]
print("test data count : %d \n" % (test.size))

#predictions variable
predictions = []


#----------------------- END ------------------------

#PART 3
#--------------------------------OPTIONAL-----------------------------------------
#now we are trying to find best combination of parameters for arima

warnings.filterwarnings('ignore')

#we can appends this range to find best combination if we havent yet.
p=d=q= range(0,6)

pdq = list(itertools.product(p,d,q))
print(pdq)

#now we make for loop to iterate over

for param in pdq:
	
	try:
		model_arima = ARIMA(train, order= param)
		model_arima_fit = model_arima.fit()
		print(mean_squared_error, param, model_arima_fit.aic)
		
		aic_temp = model_arima_fit.aic
		param_temp = param
		mse_temp = mean_squared_error

		if aic_temp < model_arima_fit.aic & model_arima_fit.aic > 0:
			
			mse_temp = mean_squared_error
			param_temp = param
			aic_temp = model_arima_fit.aic
			print("Better parameter combination found!")
		elif aic_temp > model_arima_fit.aic & model_arima_fit.aic < 0:
			mse_temp = mean_squared_error
			param_temp = param
			aic_temp = model_arima_fit.aic
	except:
		continue


#after determination of best parameter combination,we plot the graph

#----------------------END----------------------

#PART 4
#ARIMA Model First Part(Auto Regression(AR))

#p,d,q parameters correspond to AR,I,MA parameters.
#periods, order of diff, lag

#4.1

#we pass param_temp value which was fetched from aic trials
model_arima = ARIMA(train, order = param_temp)

#substract each value from the one that follows it. thus allows graph to be smoother.
model_arima_fit = model_arima.fit()

#4.2

#we apply forecast(in arima,we use forecast func instead of predict) and store it in predictions
predictions = model_arima_fit.forecast(steps = 49)[0]
#predictions = np.append(predictions)


#test as red,predictions as yellow color
plt.plot(test,color = 'red')
plt.plot(predictions, color ='blue')
plt.show()

#4.3

#mean square error
mse = mean_squared_error(test,predictions)
#sqrt mse is to evaluate performance of model
rmse = sqrt(mse)

print("Test result: {} ".format(mse))
print("RMSE : %3.f \n" % rmse)

plt.show()

#-----------------END-------------------





