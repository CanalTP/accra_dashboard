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
