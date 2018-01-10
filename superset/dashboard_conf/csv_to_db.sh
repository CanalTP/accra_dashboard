sqlite3 superset/superset.db "drop table dashboards;"
echo -e ".separator ","\n.import superset/dashboard_conf/dashboards.csv dashboards" | sqlite3 superset/superset.db

sqlite3 superset/superset.db "drop table dashboard_slices;"
echo -e ".separator ","\n.import superset/dashboard_conf/dashboard_slices.csv dashboard_slices" | sqlite3 superset/superset.db

sqlite3 superset/superset.db "drop table dashboard_user;"
echo -e ".separator ","\n.import superset/dashboard_conf/dashboard_user.csv dashboard_user" | sqlite3 superset/superset.db

sqlite3 superset/superset.db "drop table tables;"
echo -e ".separator ","\n.import superset/dashboard_conf/tables.csv tables" | sqlite3 superset/superset.db

sqlite3 superset/superset.db "drop table slices;"
echo -e ".separator ","\n.import superset/dashboard_conf/slices.csv slices" | sqlite3 superset/superset.db

sqlite3 superset/superset.db "drop saved_query;"
echo -e ".separator ","\n.import superset/dashboard_conf/saved_query.csv saved_query" | sqlite3 superset/superset.db