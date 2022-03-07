import datetime

import psycopg2
import sys
import requests


def perform_migration():
    try:
        print('Migrating from v3.11 to v3.11.x')
        print("Alter autopilot db table casservicemetricdetails")
        alter_metric_details_table()
        autopilot_conn.commit()
        print("Successfully migrated")
    except Exception as e:
        autopilot_conn.rollback()
        print("Exception occurred during migration from v3.11 to v3.11.x:", e)
    finally:
        autopilot_conn.close()


def alter_metric_details_table():
    try:
        cur = autopilot_conn.cursor()
        cur.execute(" ALTER TABLE casservicemetricdetails ALTER metric_name TYPE varchar(1000)")
        print("Successfully altered casservicemetricdetails table in autopilot db")
    except Exception as e:
        print("Exception occured while  updating script : ", e)
        raise e


if __name__ == '__main__':
    n = len(sys.argv)
    if n != 4:
        print('Please pass valid 3 arguments <autopilot-db-name> <autopilot-db-host> <db-port>')

    autopilot_db = sys.argv[1]
    autopilot_host = sys.argv[2]
    port = sys.argv[3]

    # Establishing the autopilot db connection
    autopilot_conn = psycopg2.connect(database=autopilot_db, user="postgres", password="networks123",
                                      host=autopilot_host,
                                      port=port)
    print("autopilot database connection established successfully")

    perform_migration()
