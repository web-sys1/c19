#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np
import requests
import os
import json
import copy
import multiprocessing as mp
from multiprocessing import Pool
import psutil
from fuzzyset import FuzzySet
from matplotlib import pyplot as plt

from workers import *


# In[2]:


# how many ticks on the map color bar
cbarticks = 10
# coefficient for gamma
gexp = 0.2


# In[3]:


# get GeoJSON for counties
# https://eric.clst.org/tech/usgeojson/
geofile = 'gz_2010_us_050_00_20m.json'
geourl = 'https://eric.clst.org/assets/wiki/uploads/Stuff/' + geofile
if not os.path.exists(geofile):
    req = requests.get(geourl)
    with open(geofile, 'wb') as f:
        f.write(req.content)

with open(geofile, encoding='ISO-8859-1') as f:
    counties = json.load(f)

# add geo id field compatible with the data format
for c in counties['features']:
    c['id'] = c['properties']['GEO_ID'][-5:]


# In[4]:


# get GeoJSON data for states
# https://eric.clst.org/tech/usgeojson/
geostatefile = 'gz_2010_us_040_00_20m.json'
geostateurl = 'https://eric.clst.org/assets/wiki/uploads/Stuff/' + geostatefile
if not os.path.exists(geostatefile):
    req = requests.get(geostateurl)
    with open(geostatefile, 'wb') as f:
        f.write(req.content)

with open(geostatefile) as f:
    jstates = json.load(f)
#jstates


# In[5]:


# convert states from Polygon to LineString
states = copy.deepcopy(jstates)
for k, feat in enumerate(jstates['features']):
    if feat['geometry']['type']=='Polygon':
        states['features'][k]['geometry']['type']='LineString'
        states['features'][k]['geometry']['coordinates']=feat['geometry']['coordinates'][0]
    elif  feat['geometry']['type']=='MultiPolygon':
        states['features'][k]['geometry']['type']='MultiLineString' 
        states['features'][k]['geometry']['coordinates']=[linea[0] 
                                                           for linea in feat['geometry']['coordinates']]
    else: 
        raise ValueError('geom-type is not polygon or multipolygon')
#states


# In[6]:


# get population data
# this should rarely be updated, if ever
# https://www.ers.usda.gov/data-products/county-level-data-sets/download-data/
popxl = 'PopulationEstimates.xls'
popurl = 'https://www.ers.usda.gov/webdocs/DataFiles/48747/' + popxl
if not os.path.exists(popxl):
    req = requests.get(popurl)
    with open(popxl, 'wb') as f:
        f.write(req.content)

popdf = pd.read_excel(popxl, sheet_name='Population Estimates 2010-19', usecols=[0, 19, 2, 1], header=2)

# first line is the whole country, don't need it
popdf.drop([0], inplace=True)

# merge names into single columns, set FIPS as index
popdf.rename(columns={'FIPStxt': 'FIPS', 'POP_ESTIMATE_2019': 'pop'}, inplace=True)

popdf.set_index('FIPS', inplace=True)
popdf.index.name = None
popdf['name'] = popdf['Area_Name'] + ', ' + popdf['State']
popdf.drop(columns=['State', 'Area_Name'], inplace=True)
popdf


# In[7]:


# get COVID-19 data
# this should be updated daily
# https://github.com/CSSEGISandData/COVID-19
tsfile = 'time_series_covid19_confirmed_US.csv'
tsurl = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/' + tsfile
if not os.path.exists(tsfile):
    req = requests.get(tsurl)
    with open(tsfile, 'wb') as f:
        f.write(req.content)

t = pd.read_csv(tsfile)

# no FIPS, no play
t = t[t['FIPS'].notna()].copy(deep=True)
t


# In[8]:


# https://www.census.gov/data/tables/time-series/demo/popest/2010s-state-total.html
st_pop_file = 'nst-est2019-alldata.csv'
st_pop_url = 'http://www2.census.gov/programs-surveys/popest/datasets/2010-2019/national/totals/' + st_pop_file
if not os.path.exists(st_pop_file):
    req = requests.get(st_pop_url)
    with open(st_pop_file, 'wb') as f:
        f.write(req.content)

st1 = t[['Province_State'] + list(t.columns[11:])].copy(deep=True)
st2 = st1.groupby(['Province_State']).sum()
not_states = ['Diamond Princess', 'Grand Princess', 'American Samoa', 'Virgin Islands', 'Guam', 'Northern Mariana Islands', 'Puerto Rico']
st2.drop(not_states, inplace=True)

st_pop_init = pd.read_csv(st_pop_file)
st_pop = st_pop_init[['NAME', 'POPESTIMATE2019']].iloc[5:]
st_pop.set_index('NAME', inplace=True)
st_pop


# In[34]:


states_abs = st2.transpose()
states_abs.columns.name = None

# smooth the graph
states_abs = states_abs.rolling(21, min_periods=1, center=True, win_type='blackmanharris').mean().copy(deep=True)

# Convert cumulative numbers into daily deltas.
states_abs = states_abs.diff(axis=0).copy(deep=True)
# fill back first row with 0, because diff nuked it into NaN
states_abs.loc['1/22/20'] = 0
# there can be no negative deltas
states_abs.clip(lower=0, inplace=True)

states_abs


# In[35]:


states_rel = states_abs.copy(deep=True)
for c in states_rel.columns.tolist():
    states_rel[c] = states_rel[c] / st_pop['POPESTIMATE2019'].loc[c]
states_rel


# In[11]:


# keep only FIPS and dates
ts = t[['FIPS'] + list(t.columns[11:])].copy(deep=True)
# FIPS is integer
ts['FIPS'] = ts['FIPS'].astype(int)
ts


# In[12]:


# if a FIPS is missing from the data, backfill it from GeoJSON
# or else the map will have holes in it
# extract all known FIPS from GeoJSON
allcodes = [int(c['id']) for c in counties['features']]
len(allcodes)


# In[13]:


# now look for missing FIPS codes in data, and backfill them in from GeoJSON
# data will be all 0 for the backfilled rows
for c in allcodes:
    if c not in ts['FIPS'].tolist():
        newrow = {}
        newrow.update({'FIPS': c})
        for col in ts.columns.tolist()[1:]:
            newrow.update({col: 0})
        ts = ts.append(newrow, ignore_index=True)


# In[14]:


# GeoJSON is king. We need to have as many FIPS codes from GeoJSON
# as possible in the map, or else there will be missing portions.

# set FIPS as index
ts.set_index('FIPS', inplace=True)
ts


# In[15]:


# transpose: dates are index, FIPS are columns
df = ts.transpose(copy=True)
# clean the dates header
df.columns.name = None
df


# In[16]:


# smooth the graph
df = df.rolling(21, min_periods=1, center=True, win_type='blackmanharris').mean().copy(deep=True)

# Original data has cumulative numbers - columns increment forever.
# Convert cumulative numbers into daily deltas.
df = df.diff(axis=0).copy(deep=True)
# fill back first row with 0, because diff nuked it into NaN
df.loc['1/22/20'] = 0
# there can be no negative deltas
df.clip(lower=0, inplace=True)

# what is the most recent day in the data?
#lday = df.index.tolist()[-1].split('/')
#last_day = '20' + lday[2] + '/' + lday[0].rjust(2, '0') + '/' + lday[1].rjust(2, '0')
last_day = lfill_date(df.index.tolist()[-1])


# In[17]:


# This is where we start processing absolute numbers (total count, simple count)

usabs = df.copy(deep=True)
# the *lin data has the values before gamma
usabslin = usabs.copy(deep=True)
# generate color bar ticks from linear data
usabsticks = makebarticks(usabslin, gexp, cbarticks)

# apply gamma to make everyone visible
usabs = usabs.apply(gamma, g=gexp, max=np.unique(usabs).tolist()[-1]).copy(deep=True)


# In[18]:


# distribution of values
plt.figure(figsize=(16, 9))
histvals = np.unique(usabs).tolist()
plt.xlim([0, histvals[-1]])
_ = plt.hist(histvals, bins=1000)


# In[19]:


# This is where we start processing relative numbers (per capita)

usrel = df.copy(deep=True)

# divide by population
for c in usrel.columns:
    if c in popdf.index.tolist():
        usrel[c] = usrel[c] / popdf.loc[c, 'pop']
    else:
        # could not find population for that FIPS, so set numbers to 0
        usrel[c] = 0
usrellin = usrel.copy(deep=True)
# generate color bar ticks from linear data
usrelticks = makebarticks(usrellin, gexp, cbarticks)

# apply gamma to make everyone visible
usrel = usrel.apply(gamma, g=gexp, max=np.unique(usrel).tolist()[-1]).copy(deep=True)


# In[20]:


# distribution of values
plt.figure(figsize=(16, 9))
histvals = np.unique(usrel).tolist()
plt.xlim([0, histvals[-1]])
_ = plt.hist(np.unique(usrel).tolist(), bins=1000)


# In[21]:


dfcopy = usabs.copy(deep=True)
colint = dfcopy.columns.tolist()
colstr = [str(_).rjust(5, '0') for _ in colint]
dfcopy.rename(columns=dict(zip(colint, colstr)), inplace=True)
dfcopy


# In[22]:


# multiprocessing

def make_wargs(df, ticktuple, workers, map, data_type, scale, states, map_folder, gexp):
    # each worker needs data to work on
    # let's generate arguments for each worker
    
    # geo data has FIPS codes as strings, left-padded with 0
    # let's convert our columns to that
    colint = df.columns.tolist()
    colstr = [str(_).rjust(5, '0') for _ in colint]
    df.rename(columns=dict(zip(colint, colstr)), inplace=True)
    
    # distribute the list of dates equally among all workers (round-robin)
    wdlist = [[] for _ in range(workers)]
    for ind, val in enumerate(df.index.tolist()):
        wdlist[ind % workers].append(val)
    
    # build argument tuples for workers
    # (lat, lon, zoom, w, h)
    map_geom = (38.5, -96.1, 4.4, 1920, 1080)
    # (title_x, title_y, title_font_size)
    title_geom = (0.03, 0.97, 32)
    warglist = [(df.loc[wdlist[w]], counties, 'id', map_scope, 'counties', map_geom, data_type, title_geom, map_folder, gexp, ticktuple, states) for w in range(workers)]
    # each tuple in the list is the argument for one worker
    return(warglist)


# In[23]:


map_scope = 'USA'


# In[23]:


# With iPython and/or Windows you have to put the worker control in __main__
# and the worker function in a separate module. Fails otherwise.
# Linux / plain Python don't have this issue.
if __name__ == '__main__':
    # one worker per CPU
    workers = psutil.cpu_count(logical = False)
    # MP voodoo. spawn seems to work on Mac and Win.
    # Other methods fail in bizarre ways.
    mp.set_start_method('spawn')

    # Batch processing. We have several tasks:
    # - process absolute numbers
    # - process per capita numbers
    # Make a list and add all tasks to it. Each element is a task.
    # Each element contains all arguments for all workers for that task.
    food4workers = []
    data_type = 'plain numbers'
    food4workers.append(make_wargs(usabs, usabsticks, workers, map_scope, data_type, gexp, states, make_folder_name('map', map_scope, data_type), gexp))
    data_type = 'per capita'
    food4workers.append(make_wargs(usrel, usrelticks, workers, map_scope, data_type, gexp, states, make_folder_name('map', map_scope, data_type), gexp))
    
    # Run all tasks sequentially.
    for f in food4workers:
        # sd is the task name basically
        sd = f[0][8]
        if not os.path.exists(sd):
            os.makedirs(sd)
        # Start the pool, then break it down after each task.
        # Probably safer this way.
        p = Pool(processes = workers)
        work_out = p.map(make_map, f)
        p.close()


# In[24]:


bacs = [6041,
       6097,
       6055,
       6095,
       6013,
       6001,
       6085,
       6081,
       6075,
       6087,
       6067,
       6053]

barel = usrellin[bacs].copy(deep=True)

data_type = 'per capita'
plot_scope = 'bay area'
color_ba_rel = assign_colors(barel)
plot_folder = make_folder_name('plot', plot_scope, data_type)
if not os.path.exists(plot_folder):
    os.makedirs(plot_folder)
make_plots(barel, plot_folder, 'counties', color_ba_rel, data_type, plot_scope, popdf, False)


# In[25]:


color_abs = assign_colors(usabslin)
color_rel = assign_colors(usrellin)
plot_scope = map_scope


# In[26]:


data_type = 'plain numbers'
plot_folder = make_folder_name('plot', plot_scope, data_type)
if not os.path.exists(plot_folder):
    os.makedirs(plot_folder)
make_plots(usabslin, plot_folder, 'counties', color_abs, data_type, plot_scope, popdf, True)

data_type = 'per capita'
plot_folder = make_folder_name('plot', plot_scope, data_type)
if not os.path.exists(plot_folder):
    os.makedirs(plot_folder)
make_plots(usrellin, plot_folder, 'counties', color_rel, data_type, plot_scope, popdf, True)


# In[36]:


color_state_abs = assign_colors(states_abs)
plot_scope = 'usa states'
data_type = 'plain numbers'
plot_folder = make_folder_name('plot', plot_scope, data_type)
if not os.path.exists(plot_folder):
    os.makedirs(plot_folder)
make_plots(states_abs, plot_folder, 'states', color_state_abs, data_type, plot_scope, False, False)


# In[37]:


color_state_rel = assign_colors(states_rel)
plot_scope = 'usa states'
data_type = 'per capita'
plot_folder = make_folder_name('plot', plot_scope, data_type)
if not os.path.exists(plot_folder):
    os.makedirs(plot_folder)
make_plots(states_rel, plot_folder, 'states', color_state_rel, data_type, plot_scope, False, False)


# In[28]:


# if all went well, write the most recent timestamp in the data to a file
with open('last-day-usa.txt', 'w') as f:
    f.write(last_day)


# In[ ]:




