#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: jo
"""

import argparse

parser = argparse.ArgumentParser(description='COVID-19 graphs.')
parser.add_argument('mode', choices=['daily_capita','cumulative_capita', 'pct_change'], help="Mode of calculation: per capita or percent change")
parser.add_argument('indicator', choices=['Confirmed', 'Deaths'], help="Indicator to output")
parser.add_argument('--no-output',action='store_false', help="Do not save png file to output directory")

args = parser.parse_args()
mode = args.mode
indicator_name = args.indicator
print(f"Runnig mode '{mode}' and indicator '{indicator_name}'")
#if args.no_output is not None:
#    do_output = False
#else:
#    do_output = True

do_output = args.no_output

ignore_countries_extra = []
if (indicator_name == "Confirmed"):
    # for all plots:
    start_from_default = 10     #starting plot from nths cumulative case
    start_from_ratio = 1000000  #starting plot when one in this number is confirmed cumlative (if larger than start_from_default)

    if (mode == 'daily_capita'):
        moving_average = 5
        min_percapita = 1   #minimum ratio of confirmed cases
        capita =  10000     #divisor on confirmed cases
        indicator_stringoutput_plural = "confirmed daily cases" 
        indicator_stringoutput_singular = "confirmed daily case"
        ignore_countries_extra = ['San Marino','Holy See','Andorra']
    if (mode == 'cumulative_capita'):
        min_percapita = 1  #minimum ratio of confirmed cases
        capita =  1000     #divisor on confirmed cases
        indicator_stringoutput_plural = "confirmed cases" 
        indicator_stringoutput_singular = "confirmed case"
        ignore_countries_extra = ['San Marino','Holy See']
    if (mode == 'pct_change'):
        moving_average = 9
        min_cases = 2000    #only most affected countries
        indicator_stringoutput_plural = "confirmed cases" 
        indicator_stringoutput_singular = "confirmed case"
elif (indicator_name == "Deaths"):
    # for all plots:
    start_from_default = 3      #starting plot from nths cumulative death
    start_from_ratio = 10000000 #starting plot when one in this number is dead cumulative (if larger than start_from_default)
    
    if (mode == 'daily_capita'):
        moving_average = 2
        min_percapita = 1   #minimum ratio of deaths
        capita =  100000    #divisor on deaths
        indicator_stringoutput_plural = "daily deaths" 
        indicator_stringoutput_singular = "daily death"
        ignore_countries_extra = ['San Marino','Holy See','Andorra']
    if (mode == 'cumulative_capita'):
        min_percapita = 2    #minimum ratio of deaths
        capita =  100000    #divisor on deaths
        indicator_stringoutput_plural = "deaths" 
        indicator_stringoutput_singular = "death"
        ignore_countries_extra = ['San Marino','Holy See']
    if (mode == 'pct_change'):
        moving_average = 9
        min_cases = 50       #only most affected countries 
        indicator_stringoutput_plural = "deaths" 
        indicator_stringoutput_singular = "death"
        
pop_year = '2018'       #column from World Bank data,

# Do not show all days from following countries
ignore_on_x_axis = ['China','Korea, South','Japan']
# Cruise Ship has extreme numbers and skews graph
ignore_countries = ['Diamond Princess','MS Zaandam']
# Always add following countries
force_countries = ['Germany','Austria','Switzerland','France','US','United Kingdom','Italy','Spain','Korea, South','Japan','Taiwan*']
#force_countries = ['US']
only_forced_countries = False

limit_x = 0  # limiting x-axis (depending on ignore_on_x_axis) 
indicator_name_percapita = indicator_name + " (percapita)"
indicator_name_percapita_sort = indicator_name + " (percapita) sort"

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import numpy as np
import math
import warnings
import sys
from textwrap import fill


csv_pop_countries_file = "./population/worldbank-population-2020-03-14.csv"
csv_pop_provinces_file = "./population/province_state-population-2020-03-28.csv"
csv_file = "./covid-19-data/data/time-series-19-covid-combined.csv"

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
cols = cols.map(lambda x: x.replace("/", "_")) 
df_source.columns = cols

# dop unused columns
df_source = df_source.drop(columns=['Lat', 'Long'])

#removing ignored countries
ignore_countries = ignore_countries + ignore_countries_extra
df_source = df_source[~df_source['Country_Region'].isin(ignore_countries)]

#df_result is used for filtered/processed data
df_result = pd.DataFrame()

data_date = df_source.Date.max()
print(f"Using {csv_file}, latest data from",data_date)

 

actually_forced_countries = []
actually_ignored_on_x_axis = []

if (mode == "cumulative_capita" or mode == "daily_capita"):
    
    lines = 0 #for color computation
    
    #percapita provinces
    for country_province_nametpl,dftemp in df_source.groupby(['Country_Region','Province_State'],sort=False):
        if has_duplicates(country_province_nametpl): # skip mainlands (covered by countries)
            continue
        if (country_province_nametpl in df_pop_provinces.index):
            population = df_pop_provinces.loc[country_province_nametpl]['Population']
            start_from = math.ceil(population / start_from_ratio) # round up
            #TODO why limit to Confirmed?
            if (start_from < start_from_default and indicator_name == 'Confirmed'):
                start_from = start_from_default
        else:
            population = np.nan
            start_from = start_from_default
            warnings.warn(f"Population for {country_province_nametpl} not found in {csv_pop_provinces_file}. Start from {start_from_default}. case.", stacklevel=2)
        # copy to avoid SettingWithCopyWarning
        dftemp = dftemp.copy()
        dftemp = dftemp[dftemp[indicator_name] >= start_from] 
        if (mode == 'daily_capita'):
            dftemp[indicator_name_percapita] = dftemp[indicator_name].diff() / (population/capita)
        elif (mode == 'cumulative_capita'):
            dftemp[indicator_name_percapita] = dftemp[indicator_name] / (population/capita)
        dftemp['name'] = country_province_nametpl[0] + " - " + country_province_nametpl[1]
        percapita_max = dftemp[indicator_name_percapita].max()
        if (percapita_max >= min_percapita):
            df_result = df_result.append(dftemp)
            lines += 1
            if not country_province_nametpl[0] in ignore_on_x_axis:
                limit_x = len(dftemp) if len(dftemp) > limit_x else limit_x
    
    #percapita countries
    df_source_countries = df_source.copy()
    
    # sum up states 
    df_source_countries  = df_source_countries.groupby(['Country_Region','Date'],sort=False,as_index=False).sum()
    
    for name,dftemp in df_source_countries.groupby('Country_Region',sort=False):
        if (name in df_pop_countries.index):
            population = df_pop_countries.loc[name][pop_year]
            start_from = math.ceil(population / start_from_ratio) # round up
            if (start_from < start_from_default and indicator_name == 'Confirmed'):
                start_from = start_from_default
        else:
            warnings.warn(f"Population for {name} not found in {csv_pop_countries_file}. Start from {start_from_default}. case.", stacklevel=2)
            population = np.nan
            start_from = 10
        # copy to avoid SettingWithCopyWarning
        dftemp = dftemp.copy()
        dftemp = dftemp[dftemp[indicator_name] >= start_from]  
        if (mode == 'daily_capita'):
            dftemp[indicator_name_percapita] = dftemp[indicator_name].diff() / (population/capita)
        elif (mode == 'cumulative_capita'):
            dftemp[indicator_name_percapita] = dftemp[indicator_name] / (population/capita)
        dftemp['name'] = name
        percapita_max = dftemp[indicator_name_percapita].max()
        if (only_forced_countries):
            if (name not in force_countries):
                print("Skipping unforced ", name)
                continue
        if (percapita_max < min_percapita and name in force_countries):
            actually_forced_countries.append(name)
            print("Forcing", name)
        if (percapita_max >= min_percapita or name in force_countries):
            df_result = df_result.append(dftemp)
            lines += 1
            if not name in ignore_on_x_axis:
                limit_x = len(dftemp) if len(dftemp) > limit_x else limit_x
    
    # need to limit data to limit_x before sorting
    dftemp_limit = df_result.copy()
    df_result = pd.DataFrame()
    for name,dftemp in dftemp_limit.groupby('name',sort=False):
         # copy to avoid SettingWithCopyWarning
         dftemp = dftemp.copy()
         # limit x-axis
         if (len(dftemp) > limit_x):
             dftemp = dftemp.head(limit_x)
             actually_ignored_on_x_axis.append(name)
         if (mode == 'daily_capita'): 
             #set max as latest value for better order in legend
             dftemp[indicator_name_percapita_sort] = dftemp[indicator_name_percapita].iloc[-1] 
         elif (mode == 'cumulative_capita'):
             #recalulate percapita max for better order in legend
             dftemp[indicator_name_percapita_sort] = dftemp[indicator_name_percapita].max()
         df_result = df_result.append(dftemp)

    # sort for a sorted legend
    df_result = df_result.sort_values(by=[indicator_name_percapita_sort,'name','Date'],ascending=[False,True,True],ignore_index=True)
    
    # plot combined country/province data
    # palettes recommendations:
    sns.set_palette(sns.color_palette('YlOrBr_d', lines))
    sns.set_style('ticks') 
    fig, ax = plt.subplots(1,1) 
    if (do_output):
        fig = plt.figure(figsize=(12,7))
    
    for name,dftemp in df_result.groupby('name',sort=False):
        #print(name,df_country['Confirmed (percapita)'].max())
        #lines += 1
        length = len(dftemp)
        x = np.arange(length)
        if (mode == 'daily_capita'):
            y = smooth(dftemp[indicator_name_percapita],moving_average)
            #TODO unify annotate_y (here: numpy array)
            annotate_y=y[-1]
        elif (mode == 'cumulative_capita'):
            y = dftemp[indicator_name_percapita]
            #TODO unify annotate_y (here: PDSeries)
            annotate_y=y.iloc[-1]             
        # annotate last date (index 0), move 0.1 to avoid clipping marker
        annotate_x=length-1+0.1 
        
        plt.annotate(name, xy=(annotate_x, annotate_y))
        
        # plot and put marker on last point
        plt.plot(x, y,label=name,marker='o',markevery=[length-1])
        
    plt.title(f"COVID-19 {indicator_stringoutput_plural} per capita by country/province for {data_date}")
    plt.xlabel(f"Days since one in {start_from_ratio} {indicator_stringoutput_singular}\nNot all days shown: " + ", ".join(actually_ignored_on_x_axis),wrap=True)

    ytext=indicator_stringoutput_plural.capitalize() + f" per {capita} capita"
    if (mode == 'daily_capita'):
        ytext += f" (moving average: {moving_average})"
    ytext += f"\nIgnored countries: " + ",".join(ignore_countries_extra) + "\n"
    ytext += fill(f"Mininum: {min_percapita} - ignored for " + ", ".join(actually_forced_countries),100)
    plt.ylabel(ytext)

    plt.xticks(np.arange(limit_x))
    # legend to the right of plot
    plt.legend(bbox_to_anchor=(1.04,1), loc="upper left")
    # legend in plot upper left
    #plt.legend(loc='upper left',ncol=2,framealpha=0.6)
    plt.grid()
    if (do_output):
        output_file = "./output/" + mode + "-" + indicator_name.lower() + "-" + data_date
        print(f"Writing png file to " + output_file)
        fig.savefig(output_file, dpi=200, bbox_inches='tight')
    else:
        plt.show()


elif (mode == "pct_change"):
    # removing all entries lower than start_from
    df_source = df_source[df_source[indicator_name] >= start_from_default] 
    
    dftemp_pct = df_source.groupby(['Country_Region','Date'],sort='Date',as_index=False).sum()

    #TODO
    if (indicator_name == 'Confirmed'):
        limit_x = 75
    else:
        limit_x = 45
    
    #TODO
    sns.set_palette(sns.color_palette('nipy_spectral',25))
    sns.set_style('ticks') 
    fig, ax = plt.subplots(1,1) 
    if (do_output):
        fig = plt.figure(figsize=(12,7))
        
    for name,df_country in dftemp_pct.groupby('Country_Region',sort=False):
        if (only_forced_countries):
            if (name not in force_countries):
                print("Skipping unforced ", name)
                continue
        elif (df_country[indicator_name].max() < min_cases):
            continue # removing all unforced countries with fewer than min_cases

        df_country = df_country.head(limit_x) # limiting data to limit_x
        
        #len(df_country) can be smaller than limit_x
        x = np.arange(len(df_country))
        y = df_country[indicator_name].pct_change() * 100
        y = smooth(y,moving_average)[:len(df_country)]
    
        annotate_x=max(x) #last one (index 0)
        annotate_y=y[-1] #last one
        plt.annotate(name, xy=(annotate_x, annotate_y))
        plt.plot(x, y,label=name,marker='o',markevery=[len(df_country)-1])
     
    #TODO actually ignored countries
    plt.title(f"COVID-19 {indicator_stringoutput_plural} percent change by country/province for {data_date}")
    plt.xlabel(f"Days since first {indicator_stringoutput_singular}\nLimited to {limit_x}")
    plt.ylabel(f"Percent daily grow of {indicator_stringoutput_plural}\nMinimum: {min_cases} - moving average: {moving_average}") 
    plt.xticks(np.arange(10,limit_x,5))
    plt.legend(bbox_to_anchor=(1.04,1), ncol=2, loc="upper left")
    plt.grid()
    if (do_output):
        output_file = "./output/" + mode + "-" + indicator_name.lower() + "-" + data_date
        print(f"Writing png file to " + output_file)
        fig.savefig(output_file, dpi=200, bbox_inches='tight')
    else:
        plt.show()
