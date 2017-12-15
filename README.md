Accra Dashboard
===============

This project aim to provide a global insight of the transit system in Accra.
The dashboard is a visualisation of global indicators based mainly on the GTFS
data feed available at https://github.com/AFDLab4Dev/AccraMobility/tree/master/GTFS

To generate the indicators
--------------------------
* Install pipenv : `pip3 install pipenv`
* Create the virtual environnemnt with the required packages : `pipenv --python 3.5 install -r indicators_generation/requirements.txt`
* Activate the virtual environnemnt : `pipenv shell`
* Run the scipt : `python indicators_generation/indicators_generation.py`

To install Superset
-------------------
* Install [Docker CR](https://docs.docker.com/engine/installation/linux/docker-ce/ubuntu/) and [Docker compose](https://docs.docker.com/compose/install/)
* Run `docker-compose up -d` (the "-d" switch run in detached mode)
* Open a webbrowser to `http://0.0.0.0:8088/` and login with `admin` and pwd `admin`
