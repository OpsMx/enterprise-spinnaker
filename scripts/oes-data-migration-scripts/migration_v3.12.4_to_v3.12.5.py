import psycopg2
import sys
import datetime


def perform_migration():
    try:
        update_autopilot_constraints()
        autopilot_conn.commit()
        print("successfully migrated autopilot db")
    except Exception as e:
        print("Exception occurred while migration : ", e)
        autopilot_conn.rollback()
    finally:
        autopilot_conn.close()


def update_autopilot_constraints():

    try:
        cur_autopilot.execute(" ALTER TABLE userlogfeedback ALTER COLUMN logtemplate_id DROP not null ")
        cur_autopilot.execute(" ALTER TABLE loganalysis ALTER COLUMN log_template_opsmx_id DROP not null ")
    except Exception as e:
        print("Exception occured while  updating script : ", e)
        raise e


if __name__ == '__main__':
    n = len(sys.argv)

    if n != 6:
        print("Please pass valid 5 arguments <autopilot_db-name> <autopilot_host> <db-port> <user-name> <password>")
            
    autopilot_db = sys.argv[1]
    autopilot_host = sys.argv[2]
    port = sys.argv[3]
    user_name = sys.argv[4]
    password = sys.argv[5]
    
    autopilot_conn = psycopg2.connect(database=autopilot_db, user=user_name, password=password, host=autopilot_host,
                                      port=port)
    cur_autopilot = autopilot_conn.cursor()
    perform_migration()
