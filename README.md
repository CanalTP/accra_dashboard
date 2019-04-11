# Accra Dashboard

**This project is no more maintained, but feel free to reuse it !**

## Introduction

This project aim to provide a global insight of the transit system in Accra.
The dashboard is a visualisation of global indicators based mainly on the GTFS
data feed available at https://github.com/AFDLab4Dev/AccraMobility/tree/master/GTFS

## Installation
### To generate the indicators

* Install pipenv : `pip3 install pipenv`
* Create the virtual environnemnt with the required packages : `pipenv --python 3.6 install -r indicators_generation/requirements.txt`
* Activate the virtual environnemnt : `pipenv shell`
* Run the script : `python indicators_generation/indicators_generation.py`

The last command has to be launched periodically to update the dashboard informations. This can be done using crontab.

NB: Trends data are computed each time the script is called.


## To install Superset

* Install [Docker CR](https://docs.docker.com/engine/installation/linux/docker-ce/ubuntu/) and [Docker compose](https://docs.docker.com/compose/install/)
* Run `docker-compose up -d` (the "-d" switch run in detached mode)
* Open a webbrowser to `http://0.0.0.0:8088/` (or using the IP address of your web server) and login with `admin` and pwd `admin`

## To make changes to the dashboard
The Superset dashboard configuration is stored in a SQLite database. Be carefull,
the DB is also auto-updating it's data to provide a cache for the web site.
