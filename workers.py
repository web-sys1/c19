import plotly.express as px
import os
import shutil
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import matplotlib._color_data as mcd
import plotly.io as pio
import time


def gamma(x, g, max):
  # apply gamma corrections to the data
  # boost visibility for low values
  # keep highest values unchanged
  return(max * (x / max) ** g)


def assign_colors(df):
  colors = {}
  colorPalette = list(mcd.CSS4_COLORS.keys())
  banned_colors = ['white', 'azure', 'aliceblue', 'floralwhite', 'ghostwhite', 'honeydew', 'ivory', 'lightcyan', 'snow', 'whitesmoke', 'seashell', 'mintcream', 'oldlace', 'linen', 'lightyellow', 'lightgoldenrodyellow', 'cornsilk', 'beige', 'antiquewhite', 'lemonchiffon', 'lavenderblush', 'papayawhip', 'blanchedalmond']
  for c in banned_colors:
    colorPalette.remove(c)
  for unit in df.columns:
    colors[unit] = colorPalette[df.columns.tolist().index(unit) % len(colorPalette)]
  return(colors)


def make_plots(df, plot_folder, area_unit, unit_colors, data_type, plot_scope, name_dict, do_all):
  max_value = df.values.max()
  N = 12
  last_file = None

  # replace area unit numeric codes with actual names
  # this is for USA counties only
  if isinstance(name_dict, pd.DataFrame):
    for c in df.columns:
      if c not in name_dict.index.tolist():
        # if FIPS codes are not in population data
        # we don't draw represent them on the map anyway
        # so let's delete them from the plots as well
        df.drop(columns=[c], inplace=True)
        continue
      name = name_dict.loc[c, 'name']
      df.rename(columns={c: name}, inplace=True)
      unit_colors[name] = unit_colors.pop(c)

  if do_all:
    day_list = df.index.tolist()
  else:
    day_list = df.index.tolist()[-1:]
  for day in day_list:
    # make it look like YYYY/MM/DD
    daystring = lfill_date(day)
    plot_file = 'frame-' + daystring.replace('/', '') + '.png'
    plot_full_path = os.path.join(plot_folder, plot_file)
    # if the file exists, skip this frame
    if os.path.exists(plot_full_path):
      continue

    plt.rcParams["figure.dpi"] = 192
    fig = plt.figure(figsize=(10, 5.625))
    plt.title(plot_scope + ' COVID-19 daily cases - ' + data_type + ' - linear scale - top ' + str(N) + ' ' + area_unit)
    # x ticks get too crowded, limit their number
    plt.gca().xaxis.set_major_locator(plt.MaxNLocator(nbins=7))
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['top'].set_visible(False)

    # extract one day from dataframe
    # put area units in one column
    # put values in the other column
    daydf = df.loc[day].to_frame()
    daydf.index.name = area_unit
    daydf.reset_index(inplace=True)
    topN = daydf.sort_values(by=[day], ascending=False).head(N)
    topNunits = topN[area_unit].tolist()
    all_champs = df.loc[:day, topNunits]
    #max_value = all_champs.values.max()
    plt.gca().set_ylim(bottom=0, top=max_value)
    for u in topNunits:
      champ = df.loc[:day, u].to_frame()
      p = plt.plot(champ.index.tolist(), champ[u].tolist(), color=unit_colors[u])
    leg = plt.legend(topNunits, loc='upper left', frameon=False)
    for line, text in zip(leg.get_lines(), leg.get_texts()):
      line.set_color(unit_colors[text.get_text()])

    fig.subplots_adjust(left = 0.07, right = 0.99, bottom = 0.065, top = 0.94)
    fig.savefig(plot_full_path)
    last_file = plot_full_path
    plt.close()

  curr_snap = plot_scope + '_' + data_type + '_top.png'
  curr_snap = curr_snap.replace(' ', '_')
  curr_snap = curr_snap.lower()
  if last_file != None:
    shutil.copyfile(last_file, curr_snap)


def make_folder_name(prefix, scope, data_type):
  fn = prefix + '_' + scope + '_' + data_type
  fn = fn.replace(' ', '_')
  fn = fn.lower()
  return fn


def lfill_date(date_in):
  # from 1/21/20 to 2020/01/21
  date_chunks = date_in.split('/')
  date_filled = '20' + date_chunks[2] + '/' + date_chunks[0].rjust(2, '0') + '/' + date_chunks[1].rjust(2, '0')
  return(date_filled)


def savelinefig(df, title, fname):
  # plot numbers for top 10 counties
  # aiming for close to 1920x1080 px
  plt.rcParams["figure.dpi"] = 100
  plot = df.plot(figsize=(16,9), title=title)
  plot.set_ylim(bottom=0)
  plot.spines['right'].set_visible(False)
  plot.spines['top'].set_visible(False)
  fig = plot.get_figure()
  fig.savefig(fname, bbox_inches = 'tight', pad_inches = 0.1)


def makebarticks(df, gexp, ticks):
  # the color bar in the legend shows color codes for values
  # but our data may be gamma-boosted, so the values on the bar will be wrong
  # make custom values for the color bar to compensate gamma
  # basically, apply reverse gamma
  values = list(np.linspace(0, np.unique(df).tolist()[-1], num=ticks))
  labels = [gamma(x, 1 / gexp, values[-1]) for x in values]
  # ugly hack using <b>
  # this should be a font attr in Plotly instead
  labels = ['<b>%s</b>' % f"{x:.{3}}" for x in labels]
  return((values, labels))


def make_map(arg_list):

  pio.orca.ensure_server()
  # Sleeping here doesn't help.
  # Orca just doesn't work right.
  #time.sleep(30)

  df, geos, fidkey, map_scope, area_unit, map_geom, data_type, title_geom, map_folder, gexp, bar_ticks, layer = arg_list
  # df: dataframe to draw, index is days, columns are territories
    # days don't need to be sequential, they will render in whatever order they are in
  # geos: JSON with geo data
  # fidkey: the JSON attribute with the name of each area unit
  # map_scope: US, World...
  # area_unit: counties, countries... (the mosaic tiles that make the map)
  # map_geom: (lat, lon, zoom, wpx, hpx)
  # data_type: plain numbers, per capita...
  # title_geom: (title_x, title_y, title_font_size)
  # map_folder: where to create the map frames
  # gexp: exponent for gamma
  # bar_ticks: labels and values for the map color bar
  # layer: optional mapbox layer to add to the map (like US state borders)

  for day in df.index.tolist():
    # make it look like YYYY/MM/DD
    #_ = day.split('/')
    #daystring = '20' + _[2] + '/' + _[0].rjust(2, '0') + '/' + _[1].rjust(2, '0')
    daystring = lfill_date(day)
    map_file = 'frame-' + daystring.replace('/', '') + '.png'
    map_full_path = os.path.join(map_folder, map_file)
    # if the map exists, skip it
    if os.path.exists(map_full_path):
      continue

    # extract one day from dataframe
    # put area units in one column
    # put values in the other column
    daydf = df.loc[day].to_frame()
    daydf.index.name = area_unit
    daydf.reset_index(inplace=True)

    fig = px.choropleth_mapbox(
        daydf,
        geojson=geos,
        featureidkey=fidkey,
        locations=area_unit,
        color=day,
        range_color=[bar_ticks[0][0], bar_ticks[0][-1]],
        color_continuous_scale="Inferno",
        center={'lat': map_geom[0], 'lon': map_geom[1] },
        zoom=map_geom[2],
        mapbox_style='carto-positron',
    )

    tt = '<b>'
    tt += map_scope + ' COVID-19 daily cases - ' + data_type
    tt += ' - non-linear scale (gamma=' + str(gexp) + ') - '
    tt += daystring + '</b>'
    fig.update_layout(
        title_text=tt,
        title_x=title_geom[0],
        title_y=title_geom[1],
        title_font_size=title_geom[2],
        width=map_geom[3],
        height=map_geom[4],
        coloraxis_colorbar = {
            'tickmode': 'array',
            'title': '<b>' + data_type + '</b><br>&nbsp;',
            'tickvals': bar_ticks[0],
            'ticktext': bar_ticks[1],
        },
        margin={"r":0,"t":0,"l":0,"b":0},
    )

    if layer != None:
      fig.update_layout(
        mapbox_layers = [dict(sourcetype = 'geojson',
                                    source = layer,
                                    color='#ffffff',
                                    type = 'line',
                                    line=dict(width=1)
                               )],
      )

    fig.write_image(map_full_path, scale=1.0)
