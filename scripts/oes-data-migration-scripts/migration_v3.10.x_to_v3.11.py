import datetime

import psycopg2
import sys
import requests


def perform_migration():
    try:
        print('Migrating from v3.10.x to v3.11')
        print("Alter autopilot db table entropy")
        updatescript()
        print("Migrating audit details from v3.10.x to v3.11...")
        addingDataToPipelineExecutionAuditEvents()
        getexecutionIdWithTime()
        print("Successfully migrated audit details to pipeline execution table")
        autopilot_conn.commit()
        audit_conn.commit()
        print("Successfully migrated")
    except Exception as e:
        autopilot_conn.rollback()
        audit_conn.rollback()
        print("Exception occurred during migration from v3.10.x to v3.11:", e)
    finally:
        autopilot_conn.close()
        audit_conn.close()


def updatescript():
    try:
        cur = autopilot_conn.cursor()
        cur.execute(" ALTER TABLE entropy ALTER COLUMN service_id DROP NOT NULL ")
        print("Successfully altered entropy table in autopilot db")
    except Exception as e:
        print("Exception occured while  updating script : ", e)
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
                count +=1
                postingPipelineExecutionAuditEvents(auditData)
        print("Data received from audit events table :" + str(count))
    except Exception as e:
        print("Exception occurred while fetching audit_events data : ", e)
        raise e

def postingPipelineExecutionAuditEvents(auditData):
    try:
        url = oes_audit_service_url + "/auditservice/v1/echo/events/" + str(auditData[0])
        headers = {'Content-Type': 'application/json'}
        requests.post(url=url, headers=headers)
    except Exception as e:
        print("Exception occurred while posting Pipeline Execution Audit Events : ", e)
        raise e

def getexecutionIdWithTime():
    try:
        cur = audit_conn.cursor()
        cur.execute("select audit_data -> 'executionId' as executionId from pipeline_execution_audit_events")
        executionIdList = [item[0] for item in cur.fetchall()]
        count = 0
        if executionIdList != None:
            print("Updating pipeline execution time")
            for executionId in executionIdList:
                cur.execute("select data -> 'details' ->>'created' as executionTime from audit_events where data -> 'content' ->> 'executionId' ='" +executionId+ "'")
                dateDetails = [executionTime[0] for executionTime in cur.fetchall()]
                if dateDetails != None:
                    count +=1
                    dateDetails = str(dateDetails[0])
                    updatedTime_date_time = datetime.datetime.utcfromtimestamp(int(dateDetails) / 1000)
                    val = """UPDATE pipeline_execution_audit_events SET created_at ={}, updated_at ={} WHERE audit_data ->> 'executionId' = {}""".format(
                        '\'' + str(updatedTime_date_time) + '\'', '\'' + str(updatedTime_date_time) + '\'',
                        '\'' + executionId + '\'')
                    cur.execute(val)
        print("Total updated created time for pipeline execution Data: " + str(count))
    except Exception as e:
        print("Exception occurred while fetching and update time for pipeline_execution_audit_events data : ", e)
        raise e

if __name__ == '__main__':
    n = len(sys.argv)
    if n != 7:
        print(
            'Please pass valid 6 arguments <audit_db-name> <audit-db-host> <autopilot-db-name> <autopilot-db-host> <oes-audit-service-url> <db-port>')

    audit_db = sys.argv[1]
    audit_db_host = sys.argv[2]
    autopilot_db = sys.argv[3]
    autopilot_host = sys.argv[4]
    oes_audit_service_url = sys.argv[5]
    port = sys.argv[6]

    # Establishing the audit db connection
    audit_conn = psycopg2.connect(database=audit_db, user='postgres', password='networks123',
                                  host=audit_db_host, port=port)
    print("audit database connection established successfully")

    # Establishing the autopilot db connection
    autopilot_conn = psycopg2.connect(database=autopilot_db, user="postgres", password="networks123",
                                      host=autopilot_host,
                                      port=port)
    print("autopilot database connection established successfully")

    perform_migration()
