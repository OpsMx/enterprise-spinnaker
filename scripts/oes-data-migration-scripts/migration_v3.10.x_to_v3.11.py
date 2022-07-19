import datetime
import psycopg2
import sys
import requests
import logging


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def perform_migration():
    try:
        global is_error_occurred
        logging.info('Migrating from v3.10.x to v3.11')
        try:
            logging.info("Alter autopilot db table entropy")
            print("Alter autopilot db table entropy")
            updatescript()
        except Exception as e:
            logging.error("Failure at step 1", exc_info=True)
            is_error_occurred = True

        try:
            logging.info("Alter autopilot db table servicegate and serviceriskanalysis in opsmx db")
            updateautopilotconstraints()
        except Exception as e:
            logging.error("Failure at step 2", exc_info=True)
            is_error_occurred = True

        try:
            logging.info("Alter autopilot db table casservicemetricdetails")
            updatescriptformetricdetails()
        except Exception as e:
            logging.error("Failure at step 3", exc_info=True)
            is_error_occurred = True


        try:
            logging.info("Migrating audit details from v3.10.x to v3.11...")
            print("Migrating audit details from v3.10.x to v3.11...")
            addingDataToPipelineExecutionAuditEvents()
            getexecutionIdWithTime()
        except Exception as e:
            logging.error("Failure at step 4", exc_info=True)
            is_error_occurred = True

        if is_error_occurred == True:
            logging.info(
                f"{bcolors.FAIL} {bcolors.BOLD}FAILURE: {bcolors.ENDC}{bcolors.FAIL}Migration script execution failed. Please contact the support team{bcolors.ENDC}")
            raise Exception("FAILURE: Migration script execution failed. Please contact the support team.")
        else:
            logging.info(f"{bcolors.OKGREEN}{bcolors.BOLD}Successfully completed the migration.{bcolors.ENDC}")
            print(f"{bcolors.OKGREEN}{bcolors.BOLD}Successfully completed the migration.{bcolors.ENDC}")
            commit_transactions()


    except Exception as e:
        logging.critical(e.__str__(), exc_info=True)
        rollback_transactions()
        exit(1)
        logging.error("Exception occurred during migration from v3.10.x to v3.11:", e)
    finally:
        close_connections()


def commit_transactions():
    global audit_conn
    try:
        logging.info("Successfully migrated audit details to pipeline execution table")
        autopilot_conn.commit()
        audit_conn.commit()
        logging.info("Successfully migrated")
    except Exception as e:
        logging.critical("Exception occurred while committing transactions : ", exc_info=True)
        raise e

def close_connections():
    global audit_conn
    try:
        autopilot_conn.close()
        audit_conn.close()
        if audit_conn is not None:
            audit_conn.close()
    except Exception as e:
        logging.warning("Exception occurred while closing the DB connection : ", exc_info=True)


def rollback_transactions():
    global audit_conn
    try:
        autopilot_conn.rollback()
        audit_conn.rollback()
        if audit_conn is not None:
            audit_conn.rollback()
    except Exception as e:
        logging.critical("Exception occurred while rolling back the transactions : ", exc_info=True)
        raise e


def updatescript():
    try:
        cur = autopilot_conn.cursor()
        cur.execute(" ALTER TABLE entropy ALTER COLUMN service_id DROP NOT NULL ")
        logging.info("Successfully altered entropy table in autopilot db")
        print("Successfully altered entropy table in autopilot db")
    except Exception as e:
        print("Exception occurred while  altering the entropy table : ", e)
        logging.error("Exception occurred while  altering the entropy table ", exc_info=True)
        raise e


def updateautopilotconstraints():
    try:
        cur = autopilot_conn.cursor()
        cur.execute(" ALTER TABLE serviceriskanalysis  DROP CONSTRAINT IF EXISTS fkmef9blhpcxhcj431kcu52nm1e ")
        logging.info("Successfully dropped constraint serviceriskanalysis table in autopilot db")
        cur.execute(" ALTER TABLE servicegate  DROP CONSTRAINT IF EXISTS uk_lk3buh56ebai2gycw560j2oxm ")
        logging.info("Successfully dropped constraint servicegate table in autopilot db")
        print("Successfully dropped constraint serviceriskanalysis and servicegate table in autopilot db")
    except Exception as e:
        print("Exception occurred while  altering the serviceriskanalysis and servicegate table : ", e)
        logging.error("Exception occurred while  altering the serviceriskanalysis and servicegate table ", exc_info=True)
        raise e


def updatescriptformetricdetails():
    try:
        cur = autopilot_conn.cursor()
        cur.execute(" ALTER TABLE casservicemetricdetails ALTER metric_name TYPE varchar(1000) ")
        logging.info("Successfully altered casservicemetricdetails table in autopilot db")
        print("Successfully altered casservicemetricdetails table in autopilot db")
    except Exception as e:
        print("Exception occurred while  altering the casservicemetricdetails table : ", e)
        logging.error("Exception occurred while  altering the casservicemetricdetails table ", exc_info=True)
        raise e


def addingDataToPipelineExecutionAuditEvents():
    try:
        count = 0;
        cur = audit_conn.cursor()
        cur.execute(
            "select id, data -> 'content' ->> 'executionId' as executionId,data from audit_events where source='spinnaker' "
            "and (data -> 'details' ->> 'type' = 'orca:pipeline:complete' or data -> 'details' ->> 'type'='orca:pipeline:failed');")
        result = cur.fetchall()
        if result != None:
            for auditData in result:
                count += 1
                postingPipelineExecutionAuditEvents(auditData)
        logging.info("Data received from audit events table :" + str(count))
        print("Data received from audit events table :" + str(count))
    except Exception as e:
        print("Exception occurred while fetching audit_events data : ", e)
        logging.error("Exception occurred while fetching audit_events data ", exc_info=True)
        raise e


def postingPipelineExecutionAuditEvents(auditData):
    try:
        logging.info(oes_audit_service_url + "/auditservice/v1/echo/events/" + str(auditData[0]))
        url = oes_audit_service_url + "/auditservice/v1/echo/events/" + str(auditData[0])
        headers = {'Content-Type': 'application/json'}
        requests.post(url=url, headers=headers)
    except Exception as e:
        print("Exception occurred while posting Pipeline Execution Audit Events : ", e)
        logging.error("Exception occurred while posting Pipeline Execution Audit Events", exc_info=True)
        raise e


def getexecutionIdWithTime():
    try:
        cur = audit_conn.cursor()
        cur.execute("select audit_data -> 'executionId' as executionId from pipeline_execution_audit_events")
        executionIdList = [item[0] for item in cur.fetchall()]
        count = 0
        if executionIdList != None:
            for executionId in executionIdList:
                logging.info("Updating pipeline execution time for execution Id: "+ str(executionId))
                cur.execute(
                    "select data -> 'details' ->>'created' as executionTime from audit_events where data -> 'content' ->> 'executionId' ='" + executionId + "'")
                dateDetails = [executionTime[0] for executionTime in cur.fetchall()]
                if dateDetails != None:
                    count += 1
                    dateDetails = str(dateDetails[0])
                    updatedTime_date_time = datetime.datetime.utcfromtimestamp(int(dateDetails) / 1000)
                    val = """UPDATE pipeline_execution_audit_events SET created_at ={}, updated_at ={} WHERE audit_data ->> 'executionId' = {}""".format(
                        '\'' + str(updatedTime_date_time) + '\'', '\'' + str(updatedTime_date_time) + '\'',
                        '\'' + executionId + '\'')
                    cur.execute(val)
        logging.info("Total updated created time for pipeline execution Data: " + str(count))
        print("Total updated created time for pipeline execution Data: " + str(count))
    except Exception as e:
        print("Exception occurred while fetching and update time for pipeline_execution_audit_events data : ", e)
        logging.error("Exception occurred while fetching and update time for pipeline_execution_audit_events data", exc_info=True)
        raise e


if __name__ == '__main__':
    n = len(sys.argv)
    if n != 9:
        print(
            'Please pass valid 8 arguments <audit_db-name> <audit-db-host> <autopilot-db-name> <autopilot-db-host> <oes-audit-service-url> <db-port> <user-name> <password>')
        exit(1)

    global is_error_occurred
    is_error_occurred = False

    logging.basicConfig(filename='/tmp/migration_v3.10.x_to_v3.11.x.log', filemode='w',
                            format="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s", datefmt='%H:%M:%S',
                            level=logging.INFO)

    audit_db = sys.argv[1]
    audit_db_host = sys.argv[2]
    autopilot_db = sys.argv[3]
    autopilot_host = sys.argv[4]
    oes_audit_service_url = sys.argv[5]
    port = sys.argv[6]
    user_name = sys.argv[7]
    password = sys.argv[8]

    # Establishing the audit db connection
    audit_conn = psycopg2.connect(database=audit_db, user=user_name, password=password,
                                  host=audit_db_host, port=port)
    logging.info("audit database connection established successfully")
    print("audit database connection established successfully")


    # Establishing the autopilot db connection
    autopilot_conn = psycopg2.connect(database=autopilot_db, user=user_name, password=password,
                                      host=autopilot_host,
                                      port=port)
    logging.info("autopilot database connection established successfully")
    print("autopilot database connection established successfully")

    perform_migration()
