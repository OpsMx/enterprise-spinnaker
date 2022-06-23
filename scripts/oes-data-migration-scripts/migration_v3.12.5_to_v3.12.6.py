
import psycopg2
import sys
import json


def perform_migration():
    try:
        updateApprovalGateAUdit()
        audit_conn.commit()
        print("successfully migrated audit db")
    except Exception as e:
        print("Exception occurred while migration : ", e)
        audit_conn.rollback()
    finally:
        audit_conn.close()



def updateApprovalGateAUdit():
    try:
        cur_audit.execute("select id,data from audit_events where data->>'eventType' = 'APPROVAL_GATE_AUDIT'")
        approval_audit_details = cur_audit.fetchall()
        for auditdata in approval_audit_details:
            jsonData = json.loads(json.dumps(listData(auditdata)))
            if 'gateId' in jsonData['auditData']['details']:
                audit_events_table_id = auditdata[0]
                gateId = jsonData['auditData']['details']['gateId']
                cur_visibility.execute('select pipeline_id from approval_gate where id =' + str(gateId))
                pipelineId = cur_visibility.fetchone()
                if pipelineId is not None:
                    pipelineId = str(pipelineId[0])
                    cur_platform.execute('select distinct(a.name) as applicationName from applications a left outer join service s on a.id=s.application_id left outer join service_pipeline_map sp on s.id=sp.service_id where sp.pipeline_id =' + str(pipelineId))
                    applicationName = cur_platform.fetchone()
                    if applicationName is not None:
                        applicationName = str(applicationName[0])
                        print("GateId: {},pipelineId: {} ,applicationName: {} ,audit_events_table_id :{}".format(gateId,pipelineId,applicationName,audit_events_table_id))
                        fetchJsonAndUpdate(audit_events_table_id,applicationName,jsonData)
    except Exception as e:
        print("Exception occurred while  updating script : ", e)
        raise e

def listData(results):
    resultData = {}
    for result in results :
        resultData = result
    return resultData



def fetchJsonAndUpdate(audit_events_table_id, applicationName,jsonData):
    try:
        oldAppName = jsonData['auditData']['details']['application']
        if oldAppName is not applicationName:
            updateJson = json.loads(json.dumps(jsonData).replace(oldAppName,applicationName))
            updateApprovalAuditJson(audit_events_table_id,updateJson)
    except Exception as e:
        print("Exception occurred while mapping application name : ", e)
        raise e

def  updateApprovalAuditJson(audit_events_table_id,updateJson):
    try:
        updatedConfig = "'" + str(json.dumps(updateJson)) + "'"
        cur_audit.execute('update audit_events set data ='+updatedConfig+' where id ={}'.format(audit_events_table_id))
    except Exception as e:
        print("Exception occurred while updating update json : ", e)
        raise e

if __name__ == '__main__':
    n = len(sys.argv)

    if n != 10:
        print(
            "Please pass valid 9 arguments <audit_db-name> <audit-db-host> <visibility_db-name> <visibility-db-host> <platform-db-name> <platform-db-host> <db-port> <user-name> <password>")

    audit_db = sys.argv[1]
    audit_host = sys.argv[2]
    visibility_db = sys.argv[3]
    visibility_host = sys.argv[4]
    platform_db = sys.argv[5]
    platform_host = sys.argv[6]
    port = sys.argv[7]
    user_name = sys.argv[8]
    password = sys.argv[9]

    # Establishing the audit db connection
    audit_conn = psycopg2.connect(database=audit_db, user=user_name, password=password, host=audit_host, port=port)
    print('Opened audit database connection successfully')

    # Establishing the visibility db connection
    visibility_conn = psycopg2.connect(database=visibility_db, user=user_name, password=password,host=visibility_host, port=port)
    print("Visibility database connection established successfully")

    # Establishing the platform db connection
    platform_conn = psycopg2.connect(database=platform_db, user=user_name, password=password, host=platform_host,
                                     port=port)
    print('Opened platform database connection successfully')

    cur_audit = audit_conn.cursor()
    cur_visibility = visibility_conn.cursor()
    cur_platform = platform_conn.cursor()
    perform_migration()