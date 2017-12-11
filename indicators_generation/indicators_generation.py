# coding=utf8

import os
import sqlite3
import pandas as pd
import zipfile
import requests
import numpy as np
from io import BytesIO
from shapely.geometry import LineString
import csv
import datetime

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

def get_calendar_active_days(gtfs_source):
    # Loading all activated days for a service_id in a dictionnary
    service_days = {}
    with zipfile.ZipFile(gtfs_source, 'r') as myzip:
        calendar_data = pd.read_csv(myzip.open('calendar.txt'))
        calendar_data["start_date"] = calendar_data["start_date"].apply(str)
        calendar_data["start_date"] = pd.to_datetime(calendar_data["start_date"], format='%Y%m%d')
        calendar_data["end_date"] = calendar_data["end_date"].apply(str)
        calendar_data["end_date"] = pd.to_datetime(calendar_data["end_date"], format='%Y%m%d')
        for row in calendar_data.iterrows():
            service_id = row[1]['service_id']
            if not service_id in service_days:
                service_days[service_id] = []
            start_date = row[1]["start_date"]
            end_date = row[1]["end_date"]
            current = start_date
            while current <= end_date:
                current_is_active = (
                    (current.weekday() == 0 and row[1]['monday'] == 1) or
                    (current.weekday() == 1 and row[1]['tuesday'] == 1) or
                    (current.weekday() == 2 and row[1]['wednesday'] == 1) or
                    (current.weekday() == 3 and row[1]['thursday'] == 1) or
                    (current.weekday() == 4 and row[1]['friday'] == 1) or
                    (current.weekday() == 5 and row[1]['saturday'] == 1) or
                    (current.weekday() == 6 and row[1]['sunday'] == 1))
                if current_is_active and current not in service_days[service_id]:
                    service_days[service_id].append(current)
                current = current + datetime.timedelta(days=1)
        if 'calendar_dates.txt' in myzip.namelist():
            calendar_dates_data = pd.read_csv(myzip.open('calendar_dates.txt'))
            calendar_dates_data["date"] = calendar_dates_data["date"].apply(str)
            calendar_dates_data["date"] = pd.to_datetime(calendar_dates_data["date"], format='%Y%m%d')
            for row in calendar_dates_data.iterrows():
                service_id = row[1]["service_id"]
                current_date = row[1]["date"]
                if row[1]["exception_type"] == 1 and current_date not in service_days[service_id]:
                    service_days[service_id].append(current_date)
                elif row[1]["exception_type"] == 2 and current_date in service_days[service_id]:
                    service_days[service_id].remove(current_date)
    # formating the resuting data to ease the DataFrame creation
    serice_data = []
    for service_id, dates in service_days.items():
        min_date = min(dates)
        max_date = max(dates)
        serice_data.append({
            "service_id": service_id,
            "start_date": min_date,
            "end_date": max_date,
            "active_days_count": len(dates)
        })
    return pd.DataFrame(serice_data)


def get_trips_detailed_infos(gtfs_source):
    with zipfile.ZipFile(gtfs_source, 'r') as myzip:
        trips_file = myzip.open('trips.txt')
        trips_data = pd.read_csv(trips_file)

    shape_infos = get_shape_infos(gtfs_source)
    frequencies_infos = get_trip_frequencies(gtfs_source)
    service_data = get_calendar_active_days(gtfs_source)

    trips_data = trips_data.merge(shape_infos, how='left', on="shape_id")
    trips_data = trips_data.merge(frequencies_infos, how='left', on="trip_id")
    trips_data["trip_daily_count"] = trips_data["trip_daily_count"].fillna(1)
    trips_data = trips_data.merge(service_data, how='left', on="service_id")
    return trips_data


def db_table_exists(db_connection, table_name):
    sql = "SELECT name FROM sqlite_master WHERE type='table' AND name='{}';".format(table_name)
    cur = db_connection.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    return len(rows) > 0

def get_line_validity(trips_source_data):
    # for each route_id, compute the first and last active day
    grouped_trips = trips_source_data.groupby('route_id')
    route_infos = []
    for route_id in grouped_trips.groups:
        trips = grouped_trips.get_group(route_id)
        min_date = min(trips["start_date"]).to_datetime()
        max_date = min(trips["end_date"]).to_datetime()
        delta = (max_date - min_date).days + 1
        route_infos.append( {
            "route_id": route_id,
            "min_date" : min_date,
            "max_date" : max_date,
            "total_day_count": delta
        })
    return pd.DataFrame(route_infos)

def get_line_complementary_infos_from_trips(trips_source_data):
    # for each route_id, compute yearly traveled distance
    line_validity = get_line_validity(trips_source_data)
    trips_data = trips_source_data.merge(line_validity, how='left', on="route_id")
    trips_data["trip_yearly_count"] = (trips_data["trip_daily_count"] *
        trips_data["active_days_count"] / 365 *
        trips_data["total_day_count"]
    )
    trips_data["trip_yearly_length"] = trips_data["shape_length_in_meter"] * trips_data["trip_yearly_count"]
    grouped_trips = trips_data.groupby('route_id')
    route_infos = []
    for route_id in grouped_trips.groups:
        trips = grouped_trips.get_group(route_id)
        total_length = sum(trips["trip_yearly_length"])
        route_infos.append( {
            "route_id": route_id,
            "yearly_distance_km": total_length / 1000
        })
    return pd.DataFrame(route_infos)

def get_stops_data(gtfs_source):
    with zipfile.ZipFile(gtfs_source, 'r') as myzip:
        stops_data = pd.read_csv(myzip.open('stops.txt'))
    return stops_data

def get_stops_per_line(gtfs_source):
    with zipfile.ZipFile(gtfs_source, 'r') as myzip:
        stop_times_data = pd.read_csv(myzip.open('stop_times.txt'))
        for c in stop_times_data.columns:
            if c not in ["trip_id", "stop_id"]:
                stop_times_data = stop_times_data.drop(c, axis=1)
        stop_times_data = stop_times_data.drop_duplicates(subset=["trip_id", "stop_id"])
        trips_data = pd.read_csv(myzip.open('trips.txt'))
    trips_data = trips_data.merge(stop_times_data, how='left', on='trip_id')
    trips_data = trips_data.drop_duplicates(subset=["route_id", "stop_id"])
    for c in trips_data.columns:
        if c not in ["route_id", "stop_id"]:
            trips_data = trips_data.drop(c, axis=1)
    return trips_data

if __name__ == "__main__":
    gtfs_source = "https://github.com/AFDLab4Dev/AccraMobility/raw/master/GTFS/GTFS_Accra.zip"
    CO2_source = "data/co2_per_line.csv"
    dest_db = "data/accra_indicators.db"
    project_root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    CO2_source = os.path.join(project_root_dir, CO2_source)
    dest_db = os.path.join(project_root_dir, dest_db)

    db_conn = sqlite3.connect(dest_db)

    # gtfs_file = '/home/prhod/github/accra_dashboard/data/GTFS_Accra.zip'
    r = requests.get(gtfs_source)
    gtfs_file = BytesIO(r.content)
    trips_data = get_trips_detailed_infos(gtfs_file)
    trips_data.to_sql("trips_data", db_conn, if_exists="replace")
    line_complementary_infos_from_trips = get_line_complementary_infos_from_trips(trips_data)
    lines_data = get_lines_infos(gtfs_file, CO2_source, 150)
    lines_data = lines_data.merge(line_complementary_infos_from_trips, how='left', on="route_id")
    lines_data["total_co2"] = lines_data["yearly_distance_km"] * lines_data["co2_per_km"]
    lines_data.to_sql("lines_infos", db_conn, if_exists="replace")

    stops_data = get_stops_data(gtfs_file)
    stops_data.to_sql("stops", db_conn, if_exists="replace")
    stops_per_line = get_stops_per_line(gtfs_file)
    stops_per_line.to_sql("stops_per_line", db_conn, if_exists="replace")
