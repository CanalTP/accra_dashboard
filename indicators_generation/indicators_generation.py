# coding=utf8

import os
import sqlite3
import pandas as pd
import zipfile
import requests
import numpy as np
from io import BytesIO
from shapely.geometry import LineString

def get_lines_speed(gtfs_source):
    with zipfile.ZipFile(gtfs_source, 'r') as myzip:
        trips_file = myzip.open('trips.csv')
        trips_data = pd.read_csv(trips_file)


def get_lines_infos(gtfs_source, CO2_source, default_CO2_per_km):
    """
    from GTFS, collecting lines infos with corresponding agency,
    CO2 production per km, global commercial speed,
    total kilometers over a year, daily frequency
    """
    with zipfile.ZipFile(gtfs_source, 'r') as myzip:
        routes_file = myzip.open('routes.txt')
        routes_data = pd.read_csv(routes_file)
        agency_file = myzip.open('agency.txt')
        agency_data = pd.read_csv(agency_file)
        routes_data = routes_data.merge(agency_data, on="agency_id")
        co2_data = pd.read_csv(CO2_source)
        routes_data = routes_data.merge(co2_data, how="left", left_on="route_short_name", right_on="gtfs_route_short_name")
        routes_data = routes_data.drop("gtfs_route_short_name", 1).drop("agency_timezone", 1).drop("agency_lang", 1)
        routes_data = routes_data.fillna(value={"co2_per_km": default_CO2_per_km})
    return routes_data

from geopy.distance import vincenty
import pyproj
wgs84 = pyproj.Proj("+init=EPSG:4326")
epsg_2136 = pyproj.Proj("+init=EPSG:2136")
foot_in_meter = 0.3047997101815088


def get_shape_infos(gtfs_source):
    with zipfile.ZipFile(gtfs_source, 'r') as myzip:
        shapes_file = myzip.open('shapes.txt')
        shapes_data = pd.read_csv(shapes_file)
    grouped_shapes = shapes_data.groupby('shape_id')
    shape_infos = []
    for shape_id in grouped_shapes.groups:
        shape_points = grouped_shapes.get_group(shape_id)
        shape_points = shape_points.sort_values('shape_pt_sequence')
        # First method of computation
        # previous_coord = ""
        # line_length_km = 0
        # for coord in zip(shape_points["shape_pt_lon"].data, shape_points["shape_pt_lat"].data):
        #     reproj_coords.append(pyproj.transform(wgs84, epsg_2136, coord[0], coord[1]))
        #     if previous_coord:
        #         line_length_km = line_length_km + vincenty((previous_coord[0],previous_coord[1]), (coord[0], coord[1])).kilometers
        #     previous_coord = coord
        # shape_length_in_meter = line_length_km * 1000

        # Second method of computation
        reproj_coords = []
        for coord in zip(shape_points["shape_pt_lon"].data, shape_points["shape_pt_lat"].data):
            reproj_coords.append(pyproj.transform(wgs84, epsg_2136, coord[0], coord[1]))
        line = LineString(reproj_coords)
        shape_length_in_meter = line.length

        shape_infos.append( {
            "shape_id": shape_id,
            "geom" : line.wkt,
            "shape_length_in_meter" : shape_length_in_meter
        })
    return pd.DataFrame(shape_infos)

def get_trip_frequencies(gtfs_source):
    with zipfile.ZipFile(gtfs_source, 'r') as myzip:
        if not 'frequencies.txt' in myzip.namelist():
            empty_df = pd.DataFrame()
            empty_df['trip_id'] = np.nan
            empty_df['trip_count'] = np.nan
            return empty_df
        frequencies_file = myzip.open('frequencies.txt')
        frequencies_data = pd.read_csv(frequencies_file)
    #convert start_time and end_time to seconds and compute the count of travels for a trip_id
    frequencies_data["start_time"] = frequencies_data["start_time"].map(lambda x: int(x.split(':')[0])*3600 + int(x.split(':')[1])*60 + int(x.split(':')[2]))
    frequencies_data["end_time"] = frequencies_data["end_time"].map(lambda x: int(x.split(':')[0])*3600 + int(x.split(':')[1])*60 + int(x.split(':')[2]))
    frequencies_data["time_delta"] = frequencies_data["end_time"] - frequencies_data["start_time"]
    frequencies_data["trip_count"] = frequencies_data["time_delta"] / frequencies_data["headway_secs"]
    frequencies_data["trip_count"] = np.floor(frequencies_data["trip_count"]).astype(int)
    frequencies_grouped = frequencies_data.groupby('trip_id')
    trips_count = []
    for trip_id in frequencies_grouped.groups:
        trips_group = frequencies_grouped.get_group(trip_id)
        trips_sum = trips_group['trip_count'].sum()

        trips_count.append( {
            "trip_id": trip_id,
            "trip_daily_count" : trips_sum
        })

    return pd.DataFrame(trips_count)

def get_lines_total_distance_and_frequency(gtfs_source):
    with zipfile.ZipFile(gtfs_source, 'r') as myzip:
        trips_file = myzip.open('trips.txt')
        trips_data = pd.read_csv(trips_file)

    shape_infos = get_shape_infos(gtfs_source)
    frequencies_infos = get_trip_frequencies(gtfs_source)
    frequencies_infos.to_sql("frequencies_data", db_conn, if_exists="replace")

    trips_data = trips_data.merge(shape_infos, how='left', on="shape_id")
    trips_data = trips_data.merge(frequencies_infos, how='left', on="trip_id")
    trips_data["trip_daily_count"] = trips_data["trip_daily_count"].fillna(1)
    return trips_data


def db_table_exists(db_connection, table_name):
    sql = "SELECT name FROM sqlite_master WHERE type='table' AND name='{}';".format(table_name)
    cur = db_connection.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    return len(rows) > 0


if __name__ == "__main__":
    gtfs_source = "https://github.com/AFDLab4Dev/AccraMobility/raw/master/GTFS/GTFS_Accra.zip"
    CO2_source = "data/co2_per_line.csv"
    dest_db = "data/accra_indicators.db"
    project_root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    CO2_source = os.path.join(project_root_dir, CO2_source)
    dest_db = os.path.join(project_root_dir, dest_db)

    db_conn = sqlite3.connect(dest_db)

    trips_data = get_lines_total_distance_and_frequency('/home/prhod/github/accra_dashboard/data/GTFS_Accra.zip')
    trips_data.to_sql("trips_data", db_conn, if_exists="replace")
    exit()
    r = requests.get(gtfs_source)
    lines_data = get_lines_infos(BytesIO(r.content), CO2_source, 150)
    # stoppoint avec lien vers ligne
    lines_data.to_sql("lines_infos", db_conn, if_exists="replace")
