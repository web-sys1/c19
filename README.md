## Main website

See results on the website: [https://florinandrei.github.io/c19/](https://florinandrei.github.io/c19/)

## Tech stuff

The main code (main apps) is in two Jupyter notebooks - [world.ipynb](https://github.com/FlorinAndrei/c19/blob/master/world.ipynb) and [usa.ipynb](https://github.com/FlorinAndrei/c19/blob/master/usa.ipynb). There's a helper library in [workers.py](https://github.com/FlorinAndrei/c19/blob/master/workers.py), containing code shared by the main apps. Their main output is a lot of PNG frames, one per day, per scope, per map type (not included in the repo, as it would be pointless).

COVID-19 data is in two files called `time_series_covid19_confirmed_*.csv`. If these don't exist, the main apps will download them from [the source](https://github.com/CSSEGISandData/COVID-19), which is updated daily. To refresh / update this visualization on your local machine, simply delete these files and re-run the whole code.

Other data sources are used as well (GeoJSON, population, etc). The files are included in this repo. The apps will get them from their sources as well if they are missing, but there's no need to do that on purpose - new-enough data will work just fine. It's good enough as it is.

Plotly and Matplotlib are used to render everything. Multiprocessing is used in key points to speed up rendering - the code will take over the whole CPU. It will also use a lot of RAM. I would suggest 4 cores and 16 GB of RAM to keep it happy. More cores will make it go faster.

The code was developed in Jupyter on Win/Mac. The idea was to transfer it to Linux when it's ready and run it as a cron job. But I've wasted way too much time trying to make Orca work on Linux. It's not worth it. So I ended up running it on Windows. The control logic is weird, the `runall.bat` script is the entry point, but it launches Bash scripts.

The Bash scripts need WSL on Windows. Install Ubuntu 20.04 on WSL - that's where Bash actually will run. Within Ubuntu, install git, ffmpeg, and s-nail.

To install Plotly and dependencies, use Anaconda. It's probably best to install everything via Anaconda, `runall.bat` expects that (via `env.bat`). Especially Orca (a Plotly dependency) is hard to install otherwise, at least on Windows. fuzzyset, as an exception, can only be installed with pip.

The code is not elegant - it was written to explore data, that's all.
