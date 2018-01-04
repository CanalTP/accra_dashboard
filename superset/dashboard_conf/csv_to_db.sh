sqlite3 superset/superset.db "drop table dashboards;"
echo -e ".separator ","\n.import superset/dashboard_conf/dashboards.csv dashboards" | sqlite3 superset/superset.db

sqlite3 superset/superset.db "drop table dashboard_slices;"
echo -e ".separator ","\n.import superset/dashboard_conf/dashboard_slices.csv dashboard_slices" | sqlite3 superset/superset.db

sqlite3 superset/superset.db "drop table dashboard_user;"
echo -e ".separator ","\n.import superset/dashboard_conf/dashboard_user.csv dashboard_user" | sqlite3 superset/superset.db
