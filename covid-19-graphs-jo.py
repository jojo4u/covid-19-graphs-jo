#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: jo
"""

start_from_confirmed = 50 #starting plot from nths case
start_from_deaths = 1 
#for per_capita plot
capita_confirmed = 100000      #divisor on confirmed cases
capita_deaths = 1000000    #divisor on deaths
min_percapita_confirmed = 5    #minimum ratio on confirmed cases
min_percapita_deaths = 1     #minimum ration on deaths
pop_year = '2018'    #column from World Bank data,
#for confirmed and pct_change plot
min_cases = 1000     #only most affected countries 
#for pct_change plot
moving_average = 5   #smoothing 

capita = capita_confirmed
min_percapita = min_percapita_confirmed
start_from = start_from_confirmed
row = "Confirmed"

# Do not show all days from following countries
ignore_on_x_axis = ["China","Singapore","Korea, South"]
# Cruise Ship has extreme numbers and skews graph
ignore_countries = ["Cruise Ship"]
# San Marino has extreme numbers and skews graph
ignore_countries_percapita = ["San Marino"]

skip_US_counties = True

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import warnings
import seaborn as sns

csv_pop_countries_file = './population/worldbank-population-2020-03-14.csv'
csv_pop_provinces_file = './population/province_state-population-2020-03-17.csv'
csv_file = './covid-19-data/time-series-19-covid-combined.csv'

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

df_pop_countries = pd.read_csv(csv_pop_countries_file,index_col=0,usecols=['Country Name (JHU CSSE)','2018'])
df_pop_provinces = pd.read_csv(csv_pop_provinces_file,index_col=[0,1])
df_source = pd.read_csv(csv_file)

# replace forward slash which cant referenced in column names 
cols = df_source.columns
cols = cols.map(lambda x: x.replace('/', '_')) 
df_source.columns = cols

# dop unused columns
df_source = df_source.drop(columns=['Lat', 'Long'])

# removing all entries lower than start_from
df_source = df_source.query(row + " >= @start_from") 

#removing ignored countries
df_source = df_source[~df_source['Country_Region'].isin(ignore_countries)]

#df_result is used for filtered/processed data
df_result = pd.DataFrame()

#statistics
print(f"Using {csv_file}, latest data from",df_source.Date.max())

#per_capita

limit_x = 0  # limiting x-axis (depending on ignore_on_x_axis) 
lines = 0 # for color compuation

#per_capita provinces
dftemp_provinces = df_source
dftemp_capita_rows = pd.DataFrame()
for nametuple,df_countrystate in dftemp_provinces.groupby(['Country_Region','Province_State'],sort=False):
    if has_duplicates(nametuple): # skip mainlands (covered by countries)
        continue
    if skip_US_counties:
        if (nametuple[0] == "US" and ',' in nametuple[1]): # US counties have comma in name
            continue
    if (nametuple in df_pop_provinces.index):
        population = df_pop_provinces.loc[nametuple]['Population']
    else:
        population = np.nan
        warnings.warn(f"Population for {nametuple} not found in {csv_pop_provinces_file}")
    #print(nametuple,population)
    dftemp = pd.DataFrame()
    dftemp[(row + " (percapita)")] = df_countrystate[row] / (population/capita)
    dftemp["name"] = nametuple[0] + ' - ' + nametuple[1]
    per_capita_max = dftemp[(row + " (percapita)")].max()
    if (per_capita_max >= min_percapita):
        dftemp_capita_rows = dftemp_capita_rows.append(dftemp)
        lines += 1
        if not nametuple[0] in ignore_on_x_axis:
            limit_x = dftemp.count()[0] if dftemp.count()[0] > limit_x else limit_x

dftemp_provinces = pd.merge(dftemp_provinces,dftemp_capita_rows,left_index=True,right_index=True)
df_result = df_result.append(dftemp_provinces)

#per_capita countries
dftemp_countries = df_source
dftemp_countries = dftemp_countries[~dftemp_countries['Country_Region'].isin(ignore_countries_percapita)]
# drop provinces/states column
dftemp_countries = dftemp_countries.drop(columns=['Province_State'])
# sum up states 
dftemp_countries = dftemp_countries.groupby(['Country_Region','Date'],sort=False,as_index=False).sum()

dftemp_capita_rows = pd.DataFrame()
for name,df_country in dftemp_countries.groupby('Country_Region',sort=False):
    if (name in df_pop_countries.index):
        population = df_pop_countries.loc[name][pop_year]
    else:
        population = np.nan
        warnings.warn(f"Population for {name} not found in {csv_pop_countries_file}")
    dftemp = pd.DataFrame()
    dftemp[(row + " (percapita)")] = df_country[row] / (population/capita)
    dftemp["name"] = name
    per_capita_max = dftemp[(row + " (percapita)")].max()
    if (per_capita_max >= min_percapita):
        dftemp_capita_rows = dftemp_capita_rows.append(dftemp)
        lines += 1
        if not name in ignore_on_x_axis:
            limit_x = dftemp.count()[0] if dftemp.count()[0] > limit_x else limit_x

# inner join with results from per capita calculation
dftemp_countries = pd.merge(dftemp_countries,dftemp_capita_rows,left_index=True,right_index=True)
df_result = df_result.append(dftemp_countries)

# need to limiting data to limit_x before sorting
dftemp_limit = pd.DataFrame()
for name,df_country in df_result.groupby('name',sort=False):
     df_country = df_country.head(limit_x)
     #recalulate percapita max for better order in legend
     df_country[(row + " (percapita max)")] = df_country[(row + " (percapita)")].max()
     dftemp_limit = dftemp_limit.append(df_country)

df_result = dftemp_limit            
# sort by maximum ratio for sorted legend
df_result = df_result.sort_values(by=[(row + " (percapita max)"),'name','Date'],ascending=[False,True,True],ignore_index=True)

# plot combined country/province data
# palettes recommendations:
#   YlOrBr_d OrRd_d Oranges_d copper RdPu_d magma viridis plasma spring 
sns.set_palette(sns.color_palette('YlOrBr_d', lines))
sns.set_style("ticks") 
fig, ax = plt.subplots(1,1) 

for name,df_country in df_result.groupby('name',sort=False):
    #print(name,df_country["Confirmed (percapita)"].max())
    lines += 1
    x = np.arange(df_country.Date.count())
    y = df_country[(row + " (percapita)")]

    annotate_x=df_country.Date.count()-1 #last one (index 0)
    annotate_y=df_country[(row + " (percapita)")].iloc[-1] #last one
    plt.annotate(name, xy=(annotate_x, annotate_y))

    plt.plot(x, y,label=name)

plt.xlabel(f'Days since {start_from}th {row}')
plt.ylabel(f'{row} per {capita} capita (mininum {min_percapita})') 
plt.xticks(np.arange(limit_x))
if (row == "Confirmed"):
    ax.yaxis.set_major_locator(ticker.MultipleLocator(10))
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(5))
plt.legend(loc='upper left',ncol=2,framealpha=1)
plt.grid(axis='y')
plt.show()

"""
#pct_change
for name,df_country in df_grouped:
    if (df_country.Confirmed.max() > min_cases): # removing all countries with fewer than min_cases
        df_country = df_country.head(limit_x) # limiting data to limit_x
        x = np.arange(df_country.Date.count())
        y = df_country.Confirmed.pct_change() * 100
        y = smooth(y,moving_average)
        #y = group.Confirmed
        plt.plot(x, y,label=name)

plt.limit_x(right=limit_x)
plt.xlabel('Days since 100th case')
plt.ylabel(f'Percent daily grow (moving average {moving_average})') 
plt.xticks(np.arange(limit_x))
plt.legend()
plt.show()
"""

"""
#confirmed
for name,df_country in df_grouped:
    if (df_country.Confirmed.max() > min_cases): # removing all countries with fewer than min_cases
        df_country = df_country.head(limit_x) # limiting data to limit_x
        x = np.arange(df_country.Date.count())
        y = df_country.Confirmed
        plt.plot(x, y,label=name)

plt.limit_x(right=limit_x)
plt.xlabel('Days since 100th case')
plt.ylabel('Confirmed COVID-19 cases') 
plt.xticks(np.arange(limit_x))
plt.legend()
plt.show()
"""