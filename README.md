# Accra Dashboard

## Introduction

This project aim to provide a global insight of the transit system in Accra.
The dashboard is a visualisation of global indicators based mainly on the GTFS
data feed available at https://github.com/AFDLab4Dev/AccraMobility/tree/master/GTFS

## Installation
### To generate the indicators

* Install pipenv : `pip3 install pipenv`
* Create the virtual environnemnt with the required packages : `pipenv --python 3.5 install -r indicators_generation/requirements.txt`
* Activate the virtual environnemnt : `pipenv shell`
* Run the script : `python indicators_generation/indicators_generation.py`

The last command has to be launched periodically to update the dashboard informations. This can be done using crontab.

NB: Trends data are computed each time the script is called. 


## To install Superset

* Install [Docker CR](https://docs.docker.com/engine/installation/linux/docker-ce/ubuntu/) and [Docker compose](https://docs.docker.com/compose/install/)
* Run `docker-compose up -d` (the "-d" switch run in detached mode)
* Open a webbrowser to `http://0.0.0.0:8088/` (or using the IP address of your web server) and login with `admin` and pwd `admin`

## To make changes to the dashboard
The Superset dashboard configuration is stored in a SQLite database. Following changes
using GitHub is not easy, as the DB is also auto-updating it's data to provide a cache
for the web site.
To enable configuration revue within GitHub, the dashboard configuration is followed with CSV exports.

###  Change of the dashboard configuration in GitHub
* Use Superset web site to make modifications of the dashboard content or layout
* Export the dashboard configuration using the shell script `bash ./superset/dashboard_conf/db_to_csv.sh`
* Make a pull request with the CSV config files ( `superset.db` file is not mandatory)

###  Update the dashboard configuration after git pull
* Get the dashboard changes using `git pull`
* Run the script : `python indicators_generation/indicators_generation.py` (there could be modifications in the source database)
* Update the superset config database using `bash ./superset/dashboard_conf/csv_to_db.sh`
