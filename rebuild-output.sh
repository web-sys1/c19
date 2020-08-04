#!/usr/bin/env bash

# exit if anything fails
set -e
# verbose execution
set -x

site_url="https://florinandrei.github.io/c19/"

for d in map_usa_per_capita map_usa_plain_numbers map_world_per_capita map_world_plain_numbers plot_world_per_capita plot_world_plain_numbers plot_usa_per_capita plot_usa_plain_numbers; do
  pushd $d
  #rm -f ../${d}.mp4
  cat frame-*.png | ffmpeg -framerate 4 -f image2pipe -i - -loglevel warning -f mp4 -pix_fmt yuv420p ../${d}.mp4
  popd
done

for scope in USA World; do
scope_lc=`echo $scope | tr A-Z a-z`
last_day=`cat last-day-${scope_lc}.txt`

tunit=""

if [ "$scope_lc" == "usa" ]; then
  tunit=" counties"
fi

if [ "$scope_lc" == "world" ]; then
  tunit=" countries"
fi

# Facebook says:
# The following required properties are missing: og:url, og:type, fb:app_id

html_header=$(cat <<'HEADER'
<!DOCTYPE html>
<html lang="en" dir="ltr">
  <head>
    <meta charset="utf-8">
    <meta property="og:description" content="Animated maps tracking the evolution of COVID-19 in time.">
    <meta name="twitter:description" content="Animated maps tracking the evolution of COVID-19 in time.">
    <meta name="twitter:card" content="summary_large_image">
    <meta property="og:site_name" content="covid-19-maps">
    <meta name="twitter:site" content="@florinandrei">
HEADER
)

echo "$html_header" > ${scope_lc}.html
cat << PAGE_TEMPLATE1 >> ${scope_lc}.html
    <meta property="og:image" content="${site_url}thumbnail.png">
    <meta name="twitter:image" content="${site_url}thumbnail.png">
    <meta property="og:title" content="${scope} COVID-19 daily cases">
    <meta name="twitter:title" content="${scope} COVID-19 daily cases">
    <title>${scope} COVID-19 daily cases</title>
  </head>
  <body style="font-family:'Helvetica'">
    <div align="center">
    <h1>Daily cases, per capita (fraction of population)</h1>
    <h2>Animated map (video)</h2>
    <video width="75%" loop video controls autoplay muted>
      <source src="map_${scope_lc}_per_capita.mp4" type="video/mp4">
      Your browser does not support the video tag.
    </video>
    <p>&nbsp;</p>
    <h2>Current top${tunit}, per capita</h2>
    <img src='${scope_lc}_per_capita_top.png' width="75%">
    <p>&nbsp;</p>
    <h2>Evolution of top${tunit}, per capita</h2>
    <video width="75%" loop video controls autoplay muted>
      <source src="plot_${scope_lc}_per_capita.mp4" type="video/mp4">
      Your browser does not support the video tag.
    </video>
PAGE_TEMPLATE1

if [ "$scope_lc" == "usa" ]; then
cat << PAGE_TEMPLATE2 >> ${scope_lc}.html
    <p>&nbsp;</p>
    <h2>Current top states, per capita</h2>
    <img src='usa_states_per_capita_top.png' width="75%">
PAGE_TEMPLATE2

cat << PAGE_TEMPLATE6 >> ${scope_lc}.html
    <p>&nbsp;</p>
    <h2>SF Bay Area counties, per capita</h2>
    <img src='bay_area_per_capita_top.png' width="75%">
PAGE_TEMPLATE6
fi

cat << PAGE_TEMPLATE3 >> ${scope_lc}.html
    <p>&nbsp;</p>
    <hr style="width:75%">
    <p>&nbsp;</p>
    <h1>Daily cases, absolute values (simple count)</h1>
    <h2>Animated map (video)</h2>
    <video width="75%" loop video controls autoplay muted>
      <source src="map_${scope_lc}_plain_numbers.mp4" type="video/mp4">
      Your browser does not support the video tag.
    </video>
    <p>&nbsp;</p>
    <h2>Current top${tunit}, absolute values</h2>
    <img src='${scope_lc}_plain_numbers_top.png' width="75%">
    <p>&nbsp;</p>
    <h2>Evolution of top${tunit}, absolute values</h2>
    <video width="75%" loop video controls autoplay muted>
      <source src="plot_${scope_lc}_plain_numbers.mp4" type="video/mp4">
      Your browser does not support the video tag.
    </video>
PAGE_TEMPLATE3

if [ "$scope_lc" == "usa" ]; then
cat << PAGE_TEMPLATE4 >> ${scope_lc}.html
    <p>&nbsp;</p>
    <h2>Current top states, absolute values</h2>
    <img src='usa_states_plain_numbers_top.png' width="75%">
PAGE_TEMPLATE4
fi

cat << PAGE_TEMPLATE5 >> ${scope_lc}.html
    </div>
    <br>
    <div align="right">Last updated: ${last_day}</div>
  </body>
</html>
PAGE_TEMPLATE5

done

echo "$html_header" > index.html
cat << INDEX_TEMPLATE >> index.html
    <meta property="og:image" content="${site_url}thumbnail.png">
    <meta name="twitter:image" content="${site_url}thumbnail.png">
    <meta property="og:title" content="COVID-19 daily cases">
    <meta name="twitter:title" content="COVID-19 daily cases">
    <title>COVID-19 daily cases</title>
  </head>
  <body style="font-family:'Helvetica'">
  <div align="center">
  <table border=0 width="75%">
    <tr>
      <td><h1>&nbsp;</h1></td>
      <td><h1>&nbsp;</h1></td>
    </tr>
    <tr>
      <td style="text-align:center;">
        <h1>
          <a href="world.html" target="_blank">World map</a>
        </h1>
      </td>
      <td style="text-align:center;">
        <h1>
          <a href="usa.html" target="_blank">USA map</a>
        </h1>
      </td>
    </tr>
    <tr>
      <td><h1>&nbsp;</h1></td>
      <td><h1>&nbsp;</h1></td>
    </tr>
  </table>
  <table border=0 width="75%">
    <tr>
      <td>
        <p>
        Code: <a href="https://github.com/FlorinAndrei/c19" target="_blank">https://github.com/FlorinAndrei/c19</a>
        </p>
        <p>
        COVID-19 data source: <a href="https://github.com/CSSEGISandData/COVID-19" target="_blank">https://github.com/CSSEGISandData/COVID-19</a>
        </p>
        <p>
        World population data: <a href="https://www.worldometers.info/world-population/population-by-country/" target="_blank">https://www.worldometers.info/world-population/population-by-country/</a>
        </p>
        <p>
        World GeoJSON data: <a href="https://github.com/johan/world.geo.json" target="_blank">https://github.com/johan/world.geo.json</a>
        </p>
        <p>
        USA population data: <a href="https://www.ers.usda.gov/data-products/county-level-data-sets/download-data/" target="_blank">https://www.ers.usda.gov/data-products/county-level-data-sets/download-data/</a>
        </p>
        <p>
        USA GeoJSON data: <a href="https://eric.clst.org/tech/usgeojson/" target="_blank">https://eric.clst.org/tech/usgeojson/</a>
        </p>
        <p>
        &nbsp;
        </p>
      </td>
    </tr>
  </table>
  </div>
  </body>
</html>
INDEX_TEMPLATE

# Run these commands once to cache git credentials in Linux.
#git config --global credential.helper store
#git config --global user.email your@email.com
#git config --global user.name yourUserName
#git add *; git commit -m "rebuild"; git push
# Enter the password once.
# After this, git will not ask for credentials again.

# Nuke all git history
# make orphan branch
git checkout --orphan rebuild
# If you have .gitignore, then "git add *" never exits cleanly.
git add * || true
git commit -m "rebuild"
# delete master
git branch -D master
# rename new branch
git branch -m master
git push -f origin master
