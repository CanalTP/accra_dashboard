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

def get_lines_total_distance_and_frequency(gtfs_source):
    with zipfile.ZipFile(gtfs_source, 'r') as myzip:
        trips_file = myzip.open('trips.txt')
        trips_data = pd.read_csv(trips_file)
        shapes_file = myzip.open('shapes.txt')
        shapes_data = pd.read_csv(shapes_file)
    grouped_shapes = shapes_data.groupby('shape_id')
    shape_infos = []
    for shape_id in grouped_shapes.groups:
        shape_points = grouped_shapes.get_group(shape_id)
        shape_points = shape_points.sort_values('shape_pt_sequence')
        line = LineString([(x[0], x[1]) for x in zip(shape_points["shape_pt_lat"].data, shape_points["shape_pt_lon"].data)])
        shape_infos.append( {
            "shape_id": shape_id,
            "geom" : line.wkt,
            "geom_distance" : line.length
        })
    shape_infos = pd.DataFrame(shape_infos)
    trips_data = trips_data.merge(shape_infos, how='left', on="shape_id")
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

    # trips_data = get_lines_total_distance_and_frequency('/home/prhod/github/accra_dashboard/data/GTFS_Accra.zip')
    # trips_data.to_sql("trips_data", db_conn, if_exists="replace")
    # exit()
    r = requests.get(gtfs_source)
    lines_data = get_lines_infos(BytesIO(r.content), CO2_source, 150)
    # stoppoint avec lien vers ligne
    lines_data.to_sql("lines_infos", db_conn, if_exists="replace")
