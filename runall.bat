REM in env.bat add the path to your Anaconda activate script, like this:
REM call C:\Users\username\Anaconda3\Scripts\activate.bat
call env.bat

REM orca never exits and processes keep accumulating.
REM It eats up RAM, it locks the log files.
REM You have to kill it once in a while.
REM But then the first attempt will fail - see below.
taskkill /im orca.exe /f

del *.log

REM This is actually run in WSL.
REM Install Ubuntu 20.04 in WSL.
bash -c "./prep.sh" > prep.log 2>&1 || goto :error

del time_series_covid19_confirmed_global.csv
rmdir /s /q map_world_per_capita
rmdir /s /q map_world_plain_numbers
rmdir /s /q plot_world_per_capita
rmdir /s /q plot_world_plain_numbers
python world.py > world.log 2>&1 || goto :tryagain
goto :keepgoing

:tryagain
REM Orca is pretty trashy, fails on first attempt if no orca.exe processes are running already.
REM The only way to make it work is to try again without killing orca.exe
REM So we simply ignore the first error.
REM Only if it fails again, then we go to error handling.
rmdir /s /q map_world_per_capita
rmdir /s /q map_world_plain_numbers
rmdir /s /q plot_world_per_capita
rmdir /s /q plot_world_plain_numbers
python world.py > world2.log 2>&1 || goto :error

:keepgoing
del time_series_covid19_confirmed_US.csv
rmdir /s /q map_usa_per_capita
rmdir /s /q map_usa_plain_numbers
rmdir /s /q plot_usa_per_capita
rmdir /s /q plot_usa_plain_numbers
rmdir /s /q plot_usa_states_per_capita
rmdir /s /q plot_usa_states_plain_numbers
rmdir /s /q plot_bay_area_per_capita
python usa.py > usa.log 2>&1 || goto :error

del *.mp4

REM This is actually run in WSL.
REM Install Ubuntu in WSL.
bash -c "./rebuild-output.sh" > rebuild.log 2>&1 || goto :error

taskkill /im orca.exe /f

goto :EOF
:error
bash -c "./error-handling.sh"
