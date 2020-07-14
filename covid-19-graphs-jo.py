#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: jo
"""

import argparse

parser = argparse.ArgumentParser(description='COVID-19 graphs.')
parser.add_argument('mode', choices=['weekly_capita','cumulative_capita', 'pct_change'], help="Mode of calculation: per capita weekly/cumulative or percent change")
parser.add_argument('indicator', choices=['confirmed','deaths','recovered'], help="Indicator to output")
parser.add_argument('--no-output',action='store_false', help="Do not save png file to output directory")

args = parser.parse_args()
mode = args.mode
indicator_name = args.indicator
print(f"Runnig mode '{mode}' and indicator '{indicator_name}'")

do_output = args.no_output

ignore_countries_extra = []

if (indicator_name == 'confirmed'):
    start_from_default = 10      #starting plot from nths cumulative case
    start_from_ratio = 1000000   #starting plot when one in this number is confirmed cumlative (if larger than start_from_default)
    start_from_ratio_text = "a million"
    capita =  10000     #divisor on confirmed cases
if (indicator_name == 'deaths'): 
    start_from_default = 3      #starting plot from nths cumulative death
    start_from_ratio = 10000000  #starting plot when one in this number is dead cumulative (if larger than start_from_default)
    start_from_ratio_text = "10 million"
    capita =  100000    #divisor on deaths
    
if (mode == 'weekly_capita'):
    timespan = "Weeks"
    steps = 1
    if (indicator_name == 'confirmed'):
        min_percapita = 12  #minimum ratio of confirmed cases per week
        ignore_countries_extra = []
        indicator_stringoutput = "confirmed weekly cases" 
    if (indicator_name == 'deaths'):
        min_percapita = 3   #minimum ratio of deaths per week
        ignore_countries_extra = ['San Marino']
        indicator_stringoutput = "weekly deaths" 
if (mode == 'cumulative_capita'):  
    timespan = "Days"
    steps = 5
    if (indicator_name == 'confirmed'):
        min_percapita = 50   #minimum ratio of confirmed cases
        ignore_countries_extra = []
        indicator_stringoutput = "confirmed cases"   
    if (indicator_name == 'deaths'):  
        min_percapita = 15   #minimum ratio of deaths
        ignore_countries_extra = ['San Marino']
        indicator_stringoutput = "deaths" 
if (mode == 'pct_change'):
    ignore_countries_extra = []
    if (indicator_name == 'confirmed'):
        moving_average = 12
        min_cases = 2000    #only most affected countries
        ignore_countries_extra = []
        indicator_stringoutput = "confirmed cases"        
    if (indicator_name == 'deaths'):
        moving_average = 9
        min_cases = 50       #only most affected countries 
        indicator_stringoutput = "deaths" 
        ignore_countries_extra = []
      
# Do not show all days from following countries
ignore_on_x_axis = ['China','China / Hubei','Korea, South','Japan','Taiwan','Japan']
# countries to ignore completely
ignore_countries = ['French Polynesia']
# Always add following countries and provinces
force_countries = ['Germany','United States','United Kingdom','Italy','Spain','Korea, South','Japan','Taiwan','China / Hubei','Brazil']
#force_countries = ['US']
# display only forced countries
only_forced_countries = False

limit_x = 0  # limiting x-axis (depending on ignore_on_x_axis) 
data_row_percapita = indicator_name + " (percapita)"
data_row_percapita_sort = indicator_name + " (percapita) sort"

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import math
import warnings
import sys
from textwrap import fill
import locale

locale.setlocale(locale.LC_ALL, '')

csv_file = "./covid19-datasets/exports/combined/v1/values.tsv"
csv_pop_provinces_file = "./population/province_state-population-2020-04-17.csv"

df_pop_provinces = pd.read_csv(csv_pop_provinces_file,index_col=['location_label'])
df_source = pd.read_csv(csv_file,delimiter='\t',parse_dates=['date'],low_memory=False,usecols=[0,3,4,5,6,7,13,23,24,25,26,35,36,37,38,39,40,41,42,52])
#index_col=['location_label','date']

# removing unneeded data
warnings.warn("Skipping provinces for now", stacklevel=2)
df_source = df_source[df_source['location_type'].isin(['total-country'])]
#df_source = df_source[df_source['location_type'].isin(['total-country','total-province'])]
df_source = df_source[df_source['dataset'] == 'jhu/daily']

# remove JHU idiosyncrasies
# total-province includes mainlands
df_source = df_source[~df_source['location_label'].str.contains('(mainland)',regex=False)]
# total-province includes some canadian cities, detected by comma
df_source = df_source[~((df_source['country'] == 'Canada') & (df_source['location_label'].str.contains(',', regex=False)))]

# removing ignored countries
ignore_countries = ignore_countries + ignore_countries_extra
df_source = df_source[~df_source['country'].isin(ignore_countries)]

# fill all NaN in data row with 0 - this is needed for daily series 
df_source['delta_confirmed'].fillna(0,inplace=True)
df_source['delta_deaths'].fillna(0,inplace=True)
df_source['delta_recovered'].fillna(0,inplace=True)
df_source['delta_infected'].fillna(0,inplace=True)

# df_result is used for filtered/processed data
df_result = pd.DataFrame()

data_date = df_source['date'].max().date()
print(f"Using {csv_file}, latest data from",data_date)

actually_forced_countries = []
actually_ignored_on_x_axis = []

if (mode == 'cumulative_capita' or mode == 'weekly_capita'):
    
    if (mode == 'cumulative_capita'):
        data_row = 'absolute_' + indicator_name 
        data_row_cumulative = data_row
        
    elif (mode == 'weekly_capita'):
        data_row = 'delta_' + indicator_name
        data_row_cumulative = 'absolute_' + indicator_name 

    for name,dftemp in df_source.groupby(['location_label'],sort=False):

        if (name in df_pop_provinces.index):
            population = df_pop_provinces.loc[name]['population']
        else:
            population = dftemp['factbook_population'].iloc[0]
             
        if (np.isnan(population)):
            warnings.warn(f"Population for province {name} not found in {csv_pop_provinces_file}. skipping", stacklevel=2)
            continue

        start_from = math.ceil(population / start_from_ratio)
        if (start_from < start_from_default):
            start_from = start_from_default
    
        # copy to avoid SettingWithCopyWarning
        dftemp = dftemp.copy()
        
        # aggregate weeks for weekly capita
        if (mode == 'weekly_capita'):
            old_index_start = dftemp.index[0]
            
            
            
            # reverse dftemp in order to get the last week as full bucket
            #dftemp = dftemp.sort_values('date',ascending=False)
            #print(dftemp['date'])
            
            dftemp = dftemp.resample('7D',on='date').agg({data_row:'sum',data_row_cumulative:'sum','dataset':'last','location_type':'last','location_label':'last','country_code':'last','country':'last','province':'last','factbook_population':'last'})
            
            #dftemp = dftemp.sort_values('date',ascending=True)
            #if (name == 'Zimbabwe'):
            #    sys.exit(2)
            
            dftemp['date'] = dftemp.index
            
            # apply old index in order to append this dataframe later
            # TODO this seems clumsy
            dftemp.index = np.arange(old_index_start,(old_index_start + len(dftemp)))
        
        dftemp[data_row_percapita] = dftemp[data_row] / (population/capita)
        # smooth here to match maxima calculation with plot
        #dftemp[data_row_percapita] = dftemp[data_row_percapita].rolling(window=moving_average).mean()
        percapita_max = dftemp[data_row_percapita].max()
        cumulative_max = dftemp[data_row_cumulative].max()
        
        if (name not in force_countries):
            if (only_forced_countries):
                print("Skipping unforced ", name)
                continue
            if (percapita_max < min_percapita):
                continue
            dftemp = dftemp[dftemp[data_row_cumulative] >= start_from]
        else:
            if (cumulative_max < start_from):
                actually_forced_countries.append(name)
                print("Forcing (start date):", name)
            if (percapita_max < min_percapita):
                actually_forced_countries.append(name)
                print("Forcing (capita ratio):", name)
                dftemp = dftemp[dftemp[data_row_cumulative] >= start_from]
      
        if (len(dftemp) == 0):
            continue
        df_result = df_result.append(dftemp)
        if not name in ignore_on_x_axis:
            limit_x = len(dftemp) if len(dftemp) > limit_x else limit_x

    # need to limit data to limit_x before sorting
    dftemp_limit = df_result.copy()
    df_result = pd.DataFrame()
    for name,dftemp in dftemp_limit.groupby('location_label',sort=False):
         # copy to avoid SettingWithCopyWarning
         dftemp = dftemp.copy()
         # limit x-axis
         if (len(dftemp) > limit_x):
             dftemp = dftemp.head(limit_x)
             actually_ignored_on_x_axis.append(name)
         if (mode == 'weekly_capita'): 
             # set sort value to latest value for order in legend
             legendtitle = "Legend - sorted descending by latest value"
             dftemp[data_row_percapita_sort] = dftemp[data_row_percapita].iloc[-1] 
         elif (mode == 'cumulative_capita'):
             # set sort value percapita max for order in legend, recalulate because of limiting of x-axis
             legendtitle = "Legend - sorted descending by max value"
             dftemp[data_row_percapita_sort] = dftemp[data_row_percapita].max()
         df_result = df_result.append(dftemp)

    # sort for a sorted legend
    df_result = df_result.sort_values(by=[data_row_percapita_sort,'location_label','date'],ascending=[False,True,True],ignore_index=True)
    
    # plot combined country/province data
    
    if (mode == 'weekly_capita'): 
        sns.set_palette(sns.color_palette('deep'))
    elif (mode == 'cumulative_capita'):
        lines = len(df_result['location_label'].drop_duplicates())
        sns.set_palette(sns.color_palette('YlOrBr_d', lines))
    sns.set_style('ticks') 
    fig, ax = plt.subplots(1,1) 

    if (do_output):
        fig = plt.figure(figsize=(12,8.5))
    
    for name,dftemp in df_result.groupby('location_label',sort=False):
        length = len(dftemp)
        x = np.arange(length)
        y = dftemp[data_row_percapita]

        if (mode == 'weekly_capita'):
            if (np.all(np.isnan(y))):
                continue
            # annotate max value, move 0.1 to avoid clipping marker
            annotate_y=np.nanmax(y)
            annotate_x=np.nanargmax(y) + 0.1

        elif (mode == 'cumulative_capita'):
            annotate_y=y.iloc[-1]
            # annotate last date (count from index 0), move 0.1 to avoid clipping marker
            annotate_x=length-1+0.1 
        
        if (np.any(dftemp['province'])):
            label = dftemp['province'].iloc[0]
            linestyle = 'dashed'
        else:
            label = name
            linestyle = 'solid'
        plt.annotate(label,xy=(annotate_x, annotate_y))
        
        # plot and put marker on last point
        plt.plot(x,y,linestyle=linestyle,label=name,marker='o',markevery=[int(annotate_x)])
        
    plt.title(f"COVID-19 {indicator_stringoutput} per capita by country/province for {data_date}")
    
    plt.xlabel(f"{timespan} since cumulative {indicator_name} reached one in {start_from_ratio_text} of population (minimum {start_from_default})\nNot all days shown: " + ", ".join(actually_ignored_on_x_axis),wrap=True)


    ytext=indicator_stringoutput.capitalize() + f" per {capita} capita"
    ytext += "\nIgnored countries: " + ", ".join(ignore_countries) + "\n"
    ytext += fill(f"Must reach at least: {min_percapita} - ignored for " + ", ".join(actually_forced_countries),90)
    plt.ylabel(ytext)

    plt.xticks(np.arange(limit_x,step=steps))
    # legend to the right of plot
    plt.legend(bbox_to_anchor=(1.04,1), loc="upper left",title=legendtitle)
    plt.grid()
    if (do_output):
        output_file = "./output/" + mode + "-" + indicator_name.lower() + "-" + str(data_date)
        print(f"Writing png file to " + output_file)
        fig.savefig(output_file, dpi=200, bbox_inches='tight')
    else:
        plt.show()

""" currently not developed further
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
        fig = plt.figure(figsize=(12,9))
        
    for name,df_country in dftemp_pct.groupby('Country_Region',sort=False):
        if (only_forced_countries):
            if (name not in force_countries):
                print("Skipping unforced ", name)
                continue
        elif (df_country[indicator_name].max() < min_cases):
            continue # removing all unforced countries with fewer than min_cases

        df_country = df_country.head(limit_x) # limiting data to limit_x
        length = len(df_country)
        
        
        #len(df_country) can be smaller than limit_x
        x = np.arange(len(df_country))
        
        y = df_country[indicator_name].pct_change() * 100
        y = smooth(y,moving_average)[:length]
    
        #annotate_x=max(x) #last one (index 0)
        #annotate_y=y[-1] #last one
        
        annotate_y=y[int(np.ceil(length*2/3))]
        annotate_x=int(np.ceil(length*2/3))
        
        plt.annotate(name, xy=(annotate_x, annotate_y))
        plt.plot(x, y,label=name,marker='o',markevery=[annotate_x])
     
    #TODO actually ignored countries
    plt.title(f"COVID-19 {indicator_stringoutput} percent change by country/province for {data_date}")
    #TODO Text
    plt.xlabel(f"Days since first (TODO TEXT)\nLimited to {limit_x}")
    ytext = f"Percent daily grow of {indicator_stringoutput}\nMinimum: {min_cases} - moving average: {moving_average}"
    ytext += f"\nIgnored countries: " + ", ".join(ignore_countries) + "\n"

    plt.ylabel(ytext) 
    plt.xticks(np.arange(10,limit_x,5))
    plt.legend(bbox_to_anchor=(1.04,1), ncol=2, loc="upper left")
    plt.grid()
    if (do_output):
        output_file = "./output/" + mode + "-" + indicator_name.lower() + "-" + data_date
        print(f"Writing png file to " + output_file)
        fig.savefig(output_file, dpi=200, bbox_inches='tight')
    else:
        plt.show()
"""