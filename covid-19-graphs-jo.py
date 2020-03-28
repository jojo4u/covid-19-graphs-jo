#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: jo
"""

import argparse

parser = argparse.ArgumentParser(description='COVID-19 graphs.')
parser.add_argument('mode', choices=['per_capita', 'pct_change'], help="Mode of calculation: per capita or percent change")
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

if (indicator_name == "Confirmed"):
    # for per_capita plot:
    start_from = 50     #starting plot from nths case
    capita =  10000     #divisor on confirmed cases
    min_percapita = 3   #minimum ratio of confirmed cases
    indicator_stringoutput_plural = "confirmed cases" 
    indicator_stringoutput_singular = "confirmed case"
    
    # for confirmed and pct_change plot
    min_cases = 1000    #only most affected countries 

elif (indicator_name == "Deaths"):
    # for per_capita plot:
    start_from = 3      #starting plot from nths death
    capita =  100000    #divisor on deaths
    min_percapita = 1   #minimum ratio of deaths
    indicator_stringoutput_plural = "deaths" 
    indicator_stringoutput_singular = "death"

    # for confirmed and pct_change plot:
    min_cases = 20       #only most affected countries 

pop_year = '2018'       #column from World Bank data,
# for pct_change plot
moving_average = 9      #smoothing 

# Do not show all days from following countries
ignore_on_x_axis = ['China','Singapore','Korea, South','Singapore','Japan']
# Cruise Ship has extreme numbers and skews graph
ignore_countries = ['Diamond Princess']
# San Marino has extreme numbers and skews graph
ignore_countries_percapita = ['San Marino']
# Always add following countries
force_countries = ['Germany','Austria','Switzerland','France','US','United Kingdom','Italy','Spain','Korea, South','Japan','Singapore']
#force_countries = ['US']
only_forced_countries = False

skip_US_counties = True

limit_x = 0  # limiting x-axis (depending on ignore_on_x_axis) 
indicator_name_percapita = indicator_name + " (percapita)"
indicator_name_percapita_max = indicator_name + " (percapita) max"

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import numpy as np
import math
import warnings
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

# removing all entries lower than start_from
df_source = df_source[df_source[indicator_name] >= start_from] 

#removing ignored countries
df_source = df_source[~df_source['Country_Region'].isin(ignore_countries)]

#df_result is used for filtered/processed data
df_result = pd.DataFrame()

data_date = df_source.Date.max()
print(f"Using {csv_file}, latest data from",data_date)


actually_forced_countries = []
actually_ignored_on_x_axis = []

if (mode == "per_capita"):
    
    lines = 0 #for color computation
    
    #per_capita provinces
    dftemp_provinces = df_source.copy()
    dftemp_capita_rows = pd.DataFrame()
    for country_province_nametpl,df_countrystate in dftemp_provinces.groupby(['Country_Region','Province_State'],sort=False):
        if has_duplicates(country_province_nametpl): # skip mainlands (covered by countries)
            continue
        if skip_US_counties:
            if (country_province_nametpl[0] == "US" and "," in country_province_nametpl[1]): # US counties have comma in name
                continue
        if (country_province_nametpl in df_pop_provinces.index):
            population = df_pop_provinces.loc[country_province_nametpl]['Population']
        else:
            population = np.nan
            warnings.warn(f"Population for {country_province_nametpl} not found in {csv_pop_provinces_file}", stacklevel=2)
        #print(nametuple,population)
        dftemp = pd.DataFrame()
        dftemp[indicator_name_percapita] = df_countrystate[indicator_name] / (population/capita)
        dftemp['name'] = country_province_nametpl[0] + " - " + country_province_nametpl[1]
        per_capita_max = dftemp[indicator_name_percapita].max()
        if (per_capita_max >= min_percapita):
            dftemp_capita_rows = dftemp_capita_rows.append(dftemp)
            lines += 1
            if not country_province_nametpl[0] in ignore_on_x_axis:
                limit_x = len(dftemp) if len(dftemp) > limit_x else limit_x
    
    dftemp_provinces = pd.merge(dftemp_provinces,dftemp_capita_rows,left_index=True,right_index=True)
    df_result = df_result.append(dftemp_provinces)
    
    #per_capita countries
    dftemp_countries = df_source.copy()
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
            warnings.warn(f"Population for {name} not found in {csv_pop_countries_file}", stacklevel=2)
        dftemp = pd.DataFrame()
        dftemp[indicator_name_percapita] = df_country[indicator_name] / (population/capita)
        dftemp['name'] = name
        per_capita_max = dftemp[indicator_name_percapita].max()
        if (only_forced_countries):
            if (name not in force_countries):
                print("Skipping unforced ", name)
                continue
        if (per_capita_max < min_percapita and name in force_countries):
            actually_forced_countries.append(name)
            print("Forcing", name)
        if (per_capita_max >= min_percapita or name in force_countries):
            dftemp_capita_rows = dftemp_capita_rows.append(dftemp)
            lines += 1
            if not name in ignore_on_x_axis:
                limit_x = len(dftemp) if len(dftemp) > limit_x else limit_x
    
    # inner join with results from per capita calculation
    dftemp_countries = pd.merge(dftemp_countries,dftemp_capita_rows,left_index=True,right_index=True)
    df_result = df_result.append(dftemp_countries)
    
    # need to limiting data to limit_x before sorting
    dftemp_limit = pd.DataFrame()
    for name,df_country in df_result.groupby('name',sort=False):
         # copy to avoid SettingWithCopyWarning
         df_country = df_country.copy()
         # limit x-axis
         if (len(df_country) > limit_x):
             df_country = df_country.head(limit_x)
             actually_ignored_on_x_axis.append(name)
         #recalulate percapita max for better order in legend
         df_country[indicator_name_percapita_max] = df_country[indicator_name_percapita].max()
         dftemp_limit = dftemp_limit.append(df_country)
    
    df_result = dftemp_limit            
    # sort by maximum ratio for a sorted legend
    df_result = df_result.sort_values(by=[indicator_name_percapita_max,'name','Date'],ascending=[False,True,True],ignore_index=True)
    
    # plot combined country/province data
    # palettes recommendations:
    #   YlOrBr_d OrRd_d Oranges_d copper RdPu_d magma viridis plasma spring 
    sns.set_palette(sns.color_palette('YlOrBr_d', lines))
    sns.set_style('ticks') 
    fig, ax = plt.subplots(1,1) 
    if (do_output):
        fig = plt.figure(figsize=(12,7))
    
    for name,df_country in df_result.groupby('name',sort=False):
        #print(name,df_country['Confirmed (percapita)'].max())
        #lines += 1
        length = len(df_country)
        x = np.arange(length)
        y = df_country[indicator_name_percapita]
    
        # annotate last date (index 0), move 0.1 to avoid clipping marker
        annotate_x=length-1+0.1 
        annotate_y=df_country[indicator_name_percapita].iloc[-1] 
        plt.annotate(name, xy=(annotate_x, annotate_y))
        
        # plot and put marker on last point
        plt.plot(x, y,label=name,marker='o',markevery=[length-1])
        
    #plt.tight_layout()
    plt.title(f"COVID-19 {indicator_stringoutput_plural} per capita by country/province (data {data_date})")
    plt.xlabel(f"Days since {start_from}th {indicator_stringoutput_singular}\nNot all days shown: " + ", ".join(actually_ignored_on_x_axis),wrap=True)

    ytext=indicator_stringoutput_plural.capitalize() + f" per {capita} capita\n"
    ytext += fill(f"Mininum: {min_percapita} - ignored for " + ", ".join(actually_forced_countries),100)
    plt.ylabel(ytext)

    plt.xticks(np.arange(limit_x))
    if (indicator_name == 'Confirmed'):
        ax.yaxis.set_major_locator(ticker.MultipleLocator(1))
        ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.5))
    if (indicator_name == "Confirmed"):
        plt.legend(bbox_to_anchor=(1.04,1), loc="upper left")
    else:
        plt.legend(loc='upper left',ncol=2,framealpha=0.6)
    plt.grid()
    if (do_output):
        output_file = "./output/" + mode + "-" + indicator_name.lower() + "-" + data_date
        print(f"Writing png file to " + output_file)
        fig.savefig(output_file, dpi=200, bbox_inches='tight')
    else:
        plt.show()

elif (mode == "pct_change"):
    #lines = 0 # for color computation
    limit_x = 26
    # sum up states 
    dftemp_pct = df_source.groupby(['Country_Region','Date'],sort='Date',as_index=False).sum()
    
    #sns.set_palette(sns.color_palette('YlOrBr_d', 10))
    #sns.set_style('ticks') 
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
        x = np.arange(len(df_country))
        y = df_country[indicator_name].pct_change() * 100
        y = smooth(y,moving_average)[:len(df_country)]
    
        annotate_x=max(x) #last one (index 0)
        annotate_y=y[-1] #last one
        plt.annotate(name, xy=(annotate_x, annotate_y))
        plt.plot(x, y,label=name,markevery=[len(df_country)-1])
        
    plt.title(f"COVID-19 {indicator_stringoutput_plural} percent change by country/province (data {data_date})")
    plt.xlabel(f"Days since {start_from}th {indicator_stringoutput_singular}")
    plt.ylabel(f"Percent daily grow of {indicator_stringoutput_plural} (moving average {moving_average})") 
    plt.xticks(np.arange(math.ceil(moving_average/2),limit_x))
    plt.legend(bbox_to_anchor=(1.04,1), ncol=2, loc="upper left")
    plt.grid()
    if (do_output):
        output_file = "./output/" + mode + "-" + indicator_name.lower() + "-" + data_date
        print(f"Writing png file to " + output_file)
        fig.savefig(output_file, dpi=200, bbox_inches='tight')
    else:
        plt.show()

"""
#confirmed
for name,df_country in df_grouped:
    if (df_country.Confirmed.max() > min_cases): # removing all countries with fewer than min_cases
        df_country = df_country.head(limit_x) # limiting data to limit_x
        x = np.arange(len(df_country))
        y = df_country.Confirmed
        plt.plot(x, y,label=name)

plt.limit_x(right=limit_x)
plt.xlabel("Days since 100th case")
plt.ylabel("Confirmed COVID-19 cases") 
plt.xticks(np.arange(limit_x))
plt.legend()
plt.show()
"""