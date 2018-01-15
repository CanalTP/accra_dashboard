sqlite3 -header -csv superset/superset.db "select * from dashboards;" > superset/dashboard_conf/dashboards.csv
sqlite3 -header -csv superset/superset.db "select * from dashboard_user;" > superset/dashboard_conf/dashboard_user.csv
sqlite3 -header -csv superset/superset.db "select * from dashboard_slices;" > superset/dashboard_conf/dashboard_slices.csv
sqlite3 -header -csv superset/superset.db "select * from tables;" > superset/dashboard_conf/tables.csv
sqlite3 -header -csv superset/superset.db "select * from slices;" > superset/dashboard_conf/slices.csv


