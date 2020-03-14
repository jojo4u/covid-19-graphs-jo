#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 13 18:38:35 2020

@author: jo
"""

startfromcase = 50  #starting plot from nths case
#for per_capita plot
capita = 100000     #divisor
minpercapita = 4   #minimum ratio
yearpop = '2018'    #column from World Bank data,
#for confirmed and pct_change plot
mincases = 1000     #only most affected countries 
#for pct_change plot
movingaverage = 5   #smoothing 

ignore_on_x_axis = "China"

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import warnings
import seaborn as sns

csvpopfile =       './population/worldbank-population-2020-03-14.csv'
csvpopstatesfile = './population/province_state-population-wikidata-2020-03-14.csv'
csvfile =          './covid-19/time-series-19-covid-combined.csv'

plt.clf()

def smooth(y, box_pts):
    box = np.ones(box_pts)/box_pts
    y_smooth = np.convolve(y, box, mode='same')
    return y_smooth

def has_duplicates(iterable):
    seen = set()
    for x in iterable:
        if x in seen:
            return True
        seen.add(x)
    return False

dfpop =       pd.read_csv(csvpopfile,index_col=0,usecols=['Country Name (JHU CSSE)','2018'])
dfpopstates = pd.read_csv(csvpopstatesfile,index_col=[0,1])
df =          pd.read_csv(csvfile)

# replace forward slash which cant referenced in column names 
cols = df.columns
cols = cols.map(lambda x: x.replace('/', '_')) 
df.columns = cols

# dop unused columns
df = df.drop(columns=['Lat', 'Long'])

# removing all entries lower than 100 cases
df = df.query('Confirmed >= @startfromcase') 

df_result = pd.DataFrame()

#per_capita
#per_capita provinces
xlim = 0  # limiting x-axis (depending on ignore_on_x_axis) 
lines = 0 # for color compuation
df_tempprovinces = df
df_capitarows = pd.DataFrame()
for nametuple,df_countrystate in df_tempprovinces.groupby(['Country_Region','Province_State'],sort=False):
    if has_duplicates(nametuple): # skip mainlands (covered by countries)
        continue
    if (nametuple[0] == "US" and ',' in nametuple[1]): # skip US counties (comma in name)
        continue
    if (nametuple in dfpopstates.index):
        population = dfpopstates.loc[nametuple]['Population']
    else:
        population = np.nan
        warnings.warn(f"Population for {nametuple} not found in {csvpopfile}")
    #print(nametuple,population)
    df_temp = pd.DataFrame()
    df_temp["Confirmed (percapita)"] = df_countrystate.Confirmed / (population/capita)
    per_capita_max = df_temp["Confirmed (percapita)"].max()
    df_temp["name"] = nametuple[0] + ' - ' + nametuple[1]
    if (per_capita_max >= minpercapita):
        df_capitarows = df_capitarows.append(df_temp)
        lines += 1
        if not nametuple[0] in ignore_on_x_axis:
            xlim = df_temp.count()[0] if df_temp.count()[0] > xlim else xlim

df_tempprovinces = pd.merge(df_tempprovinces,df_capitarows,left_index=True,right_index=True)
df_result = df_result.append(df_tempprovinces)

#per_capita countries
# drop provinces/states column
df_tempcountries = df.query('Country_Region != "San Marino"')
# sum up states 
df_tempcountries = df_tempcountries.drop(columns=['Province_State']).groupby(['Country_Region','Date'],sort=False,as_index=False).sum()

df_capitarows = pd.DataFrame()
for name,df_country in df_tempcountries.groupby('Country_Region',sort=False):
    if (name in dfpop.index):
        population = dfpop.loc[name][yearpop]
    else:
        population = np.nan
        warnings.warn(f"Population for {name} not found in {csvpopfile}")
    df_temp = pd.DataFrame()
    df_temp["Confirmed (percapita)"] = df_country.Confirmed / (population/capita)
    per_capita_max = df_temp["Confirmed (percapita)"].max()
    df_temp["name"] = name
    if (per_capita_max >= minpercapita):
        df_capitarows = df_capitarows.append(df_temp)
        lines += 1
        if not name in ignore_on_x_axis:
            xlim = df_temp.count()[0] if df_temp.count()[0] > xlim else xlim

# inner join with results from per capita calculation
df_tempcountries = pd.merge(df_tempcountries,df_capitarows,left_index=True,right_index=True)
df_result = df_result.append(df_tempcountries)

# need to limiting data to xlim before sorting
df_templimit = pd.DataFrame()
for name,df_country in df_result.groupby('name',sort=False):
     df_country = df_country.head(xlim)
     #recalulate percapita max for better order in legend
     df_country["Confirmed (percapita max)"] = df_country["Confirmed (percapita)"].max()
     df_templimit = df_templimit.append(df_country)

df_result = df_templimit            
# sort by maximum ratio for sorted legend
df_result = df_result.sort_values(by=["Confirmed (percapita max)",'name','Date'],ascending=[False,True,True],ignore_index=True)

# plot combined country/province data

#sns.set() 
#sns.axes_style("ticks")
#sns.set_palette(sns.color_palette('husl', lines+6))
sns.set_palette(sns.color_palette('Oranges_d', lines))
sns.set_style("ticks")
#copper spring copper

for name,df_country in df_result.groupby('name',sort=False):
    #print(name,df_country["Confirmed (percapita)"].max())
    lines += 1
    x = np.arange(df_country.Date.count())
    y = df_country["Confirmed (percapita)"]

    annotatex=df_country.Date.count()-1 #last one (index 0)
    annotatey=df_country["Confirmed (percapita)"].iloc[-1] #last one
    plt.annotate(name, xy=(annotatex, annotatey))

    ax = plt.plot(x, y,label=name)
    
 



plt.xlabel(f'Days since {startfromcase}th case')
plt.ylabel(f'Cases per {capita} capita (mininum {minpercapita})') 
plt.xticks(np.arange(xlim))
plt.legend(loc='upper left',ncol=2,framealpha=1)
plt.grid(axis='y')
plt.show()

"""
#pct_change
for name,df_country in df_grouped:
    if (df_country.Confirmed.max() > mincases): # removing all countries with fewer than mincases
        df_country = df_country.head(xlim) # limiting data to xlim
        x = np.arange(df_country.Date.count())
        y = df_country.Confirmed.pct_change() * 100
        y = smooth(y,movingaverage)
        #y = group.Confirmed
        plt.plot(x, y,label=name)

plt.xlim(right=xlim)
plt.xlabel('Days since 100th case')
plt.ylabel(f'Percent daily grow (moving average {movingaverage})') 
plt.xticks(np.arange(xlim))
plt.legend()
plt.show()
"""

"""
#confirmed
for name,df_country in df_grouped:
    if (df_country.Confirmed.max() > mincases): # removing all countries with fewer than mincases
        df_country = df_country.head(xlim) # limiting data to xlim
        x = np.arange(df_country.Date.count())
        y = df_country.Confirmed
        plt.plot(x, y,label=name)

plt.xlim(right=xlim)
plt.xlabel('Days since 100th case')
plt.ylabel('Confirmed COVID-19 cases') 
plt.xticks(np.arange(xlim))
plt.legend()
plt.show()
"""