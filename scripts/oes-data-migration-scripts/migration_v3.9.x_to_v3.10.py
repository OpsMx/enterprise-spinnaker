import datetime
import json
import uuid
import psycopg2
import sys
import requests


def perform_migration():
    try:
        print('Migrating from v3.9.x to v3.10')
        url = 'https://api.github.com'
        hosturl = 'https://github.com'
        alter_approval_gate_approval()
        print("Altered table approval_gate_approval in visibilitydb")
        modifyOpsmxdb()
        print("Altered column verification_type value of table userservicetemplate in opsmdb")
        print("Alter autopilot db table entropy")
        updatescript()
        print("Alter autopilot db table servicegate and serviceriskanalysis in opsmx db")
        updateautopilotconstraints()
        modifyGit(hosturl)
        print("Modified config data of Datasource type 'GIT'")
        modifygitname()
        print("Modified config data of Datasource type 'GIT to GITHUB'")
        modifyGithub(hosturl, url)
        print("Modified config data of Datasource type 'GITHUB'")
        platform_conn.commit()
        visibility_conn.commit()
        opsmxdb_conn.commit()
        print("***** Successfully migrated table data for visibility, opsmx, platform")
        print("Migrating Audit details to v3.10")
        perform_Audit_migration()
        print("Migrating policy audits")
        policy_audits = fetch_policy_audit()
        migrate_policy_audit(policy_audits)
        print("Successfully migrated policy audits")
        audit_conn.commit()
        print("***** Successfully migrated audit details")
    except Exception as e:
        audit_conn.rollback()
        print('Exception occurred during migration : ', e)
    finally:
        audit_conn.close()
        oesdb_conn.close()


def perform_Audit_migration():
    try:
        print("Checking spinnaker configuration in oes db")
        verifySpinnakerConfigurationAndGetURL()
        print("Spinnaker configured url " + url)
        print("Fetch spinnaker applications")
        applications = fetchSpinnakerApplication(url)
        print("List of spinnaker application names :" + ', '.join(applications))
        applicationPipelineDict = fetchSpinnakerPipelineExecutionByApp(applications, url)
        applicationPipelineConfigDict = fetchSpinnakerPipelineConfigExecution(applications, url)
        migratePipelineExecutions(applicationPipelineDict)
        migratePipelineConfigExecutionS(applicationPipelineConfigDict)
    except Exception as e:
        print('Exception occurred during fetching spinnaker pipeline applications : ', e)
        raise e


def verifySpinnakerConfigurationAndGetURL():
    try:
        cur = oesdb_conn.cursor()
        cur.execute("select id,url from spinnaker;")
        result = cur.fetchall()
        if result is  None:
            raise Exception("Please configure spinnaker before proceeding with audit migration")
    except Exception as e:
        print("Exception occurred while fetching spinnaker configuration from oes db: ", e)
        raise e



def fetchSpinnakerApplication(url):
    try:
        url = url + "/applications"
        headers = {'Cookie': session_id}
        response = requests.get(url=url, headers=headers).json()
        applications = [res.get('name') for res in response]
    except Exception as e:
        print("Exception occurred while fetching spinnaker applications : ", e)
        raise e
    return applications


def fetchSpinnakerPipelineExecutionByApp(applications, url):
    applicationPipelineDict = []
    try:
        url = url + "/applications/{application}/pipelines"
        appcount = 0
        for application in applications:
            updated_url = str(url).replace('{application}', application)
            headers = {'Cookie': session_id}
            response = requests.get(url=updated_url, headers=headers)
            if response.json() != []:
                # print("SPINNAKER APPLICATION - " + application + " PIPELINE DETAILS: " + str(response.json()))
                pipelineArray = {application: json.loads(response.content)}
                appcount += 1
                print("Total application pipeline executions : " + str(appcount))
                applicationPipelineDict.append(pipelineArray)
    except Exception as e:
        print("Error : Please check spinnaker connection with active sessionId")
        print("Exception occurred while fetching spinnaker pipeline execution : ", e)
        raise e
    return applicationPipelineDict


def fetchSpinnakerPipelineConfigExecution(applications, url):
    applicationPipelineConfigDict = []
    try:
        url = url + "/applications/{application}/pipelineConfigs"
        appcount = 0
        for application in applications:
            updated_url = str(url).replace('{application}', application)
            headers = {'Cookie': session_id}
            response = requests.get(url=updated_url, headers=headers)
            if response.json() != []:
                # print("SPINNAKER APPLICATION - " + application + " PIPELINE CONFIG DETAILS: " + str(response.json()))
                pipelineArray = {application: json.loads(response.content)}
                appcount += 1
                print("Total application pipeline config executions " + str(appcount))
                applicationPipelineConfigDict.append(pipelineArray)
    except Exception as e:
        print("Error : Please check spinnaker connection with active sessionId")
        print("Exception occurred while fetching spinnaker pipeline execution : ", e)
        raise e
    return applicationPipelineConfigDict


def migratePipelineExecutions(applicationPipelineDict):
    try:
        startcount = 0;
        savedCount = 0;
        rejectedCount = 0;
        rejectedPipelineExecutionJson = []
        rejectedAppList = set()
        for applicationPipelines in applicationPipelineDict:
            for application, pipelineExecutions in applicationPipelines.items():
                for pipelineExecution in pipelineExecutions:
                    startcount += 1
                    print("********** Received Pipeline Execution count::" + str(startcount))
                    if 'id' in pipelineExecution and 'buildTime' in pipelineExecution and 'status' in pipelineExecution:
                        eventId = getEventId(pipelineExecution)
                        if eventId != None:
                            pipelineExecutionJson = json.dumps(pipelineExecution)
                            executionId = pipelineExecution['id']
                            print(
                                "Started inserting pipeline execution details application Id - " + application + " and execution Id: " + executionId)
                            if isDataAlreadyPresent(application, executionId) == False:
                                if getPipelineStatus(pipelineExecution['status']) != None:
                                    pipeline_upper_json = """{"details": { "source": "orca","type": "orca:pipeline:{status}","created":{created},"application": "{application}","requestHeaders": {}},"content": {"execution":"""
                                    pipeline_lower_json = ""","executionId": "{executionId}"},"eventId": "{eventId}"}"""
                                    created = pipelineExecution['buildTime']
                                    status = getPipelineStatus(pipelineExecution['status'])
                                    print(
                                        "** Extracted Data  executionId: " + executionId + ",status: " + status + ",created: " + str(
                                            created) + ",eventId: " + eventId)
                                    updated_pipeline_upper_json = pipeline_upper_json.replace('{status}',
                                                                                              status).replace(
                                        '{created}', str(created)).replace('{application}', application)
                                    updated_pipeline_lower_json = pipeline_lower_json.replace('{executionId}',
                                                                                              executionId).replace(
                                        '{eventId}', eventId)
                                    updated_pipeline_execution = json.loads(
                                        updated_pipeline_upper_json + pipelineExecutionJson + updated_pipeline_lower_json)
                                    updated_pipeline_execution_Json = json.dumps(updated_pipeline_execution)
                                    # print("Updated Pipeline execution details for application : " + application + " :: " + updated_pipeline_execution_Json)
                                    insertPipelineExecutionData(eventId, updated_pipeline_execution_Json)
                                    savedCount += 1
                                    print("********** Saved Pipeline Execution count::" + str(savedCount))
                    else:
                        rejectedCount += 1;
                        rejectedAppList.add(str(application))
                        print("********** Received Rejected count of Pipeline Execution count::" + str(
                            rejectedCount) + " application : " + str(application))
                        rejectedPipelineExecutionJson.append(str(pipelineExecution));
        print("Total Received count : " + str(startcount))
        print("Total Saved count : " + str(savedCount))
        print("Total Rejected count : " + str(rejectedCount) + " Rejected App list :" + str(rejectedAppList))
    except Exception as e:
        print("Exception occurred while updating pipeline execution data : ", e)
        raise e


def getEventId(pipelineExecution):
    if 'eventId' in pipelineExecution['trigger']:
        eventId = pipelineExecution['trigger']['eventId']
    elif ('parentExecution' in pipelineExecution['trigger'] and 'trigger' in pipelineExecution['trigger'][
        'parentExecution'] and 'eventId' in pipelineExecution['trigger']['parentExecution']['trigger']):
        eventId = pipelineExecution['trigger']['parentExecution']['trigger']['eventId']
    else:
        eventId = str(uuid.uuid4())
    return eventId


def getPipelineStatus(pipelineStatus):
    if pipelineStatus == "TERMINAL":
        return "failed"
    elif pipelineStatus == "SUCCEEDED":
        return "complete"
    elif pipelineStatus == "RUNNING":
        return "starting"
    elif pipelineStatus == "CANCELED":
        return "failed"
    elif pipelineStatus == "NOT_STARTED":
        return "failed"


def insertPipelineExecutionData(eventId, updated_pipeline_execution):
    try:
        cur = audit_conn.cursor()
        date_time = datetime.datetime.now()
        data = date_time, date_time, updated_pipeline_execution, eventId, 'spinnaker'
        cur.execute(
            "INSERT INTO audit_events (created_at, updated_at,data,event_id,source) VALUES (%s, %s, %s, %s, %s)",
            data)
        print("Successfully inserted data into audit_events table")
    except Exception as e:
        print("Exception occurred while inserting data into audit_events table : ", e)
        raise e


def isDataAlreadyPresent(application, executionId):
    try:
        cur = audit_conn.cursor()
        cur.execute(
            "SELECT count(*) FROM audit_events WHERE data -> 'content' -> 'execution' ->> 'application' = '" + application + "' AND data -> 'content' ->> 'executionId' = '" + executionId + "'")
        result = cur.fetchone()[0]
        if result > 0:
            return bool(True)
        else:
            return bool(False)
    except Exception as e:
        print("Exception occurred while fetch data into audit_events table : ", e)
        raise e


def migratePipelineConfigExecutionS(applicationPipelineDict):
    try:
        startcount = 0;
        savedCount = 0;
        rejectedCount = 0;
        rejectedPipelineExecutionJson = []
        rejectedAppList = []
        for applicationPipelines in applicationPipelineDict:
            for application, pipelineConfigExecutions in applicationPipelines.items():
                for pipelineExecutionConfig in pipelineConfigExecutions:
                    startcount += 1
                    print("********** Received Pipeline config Execution count::" + str(startcount))
                    if 'name' in pipelineExecutionConfig and 'lastModifiedBy' in pipelineExecutionConfig and 'application' in pipelineExecutionConfig and 'id' in pipelineExecutionConfig and 'updateTs' in pipelineExecutionConfig:
                        pipeline_config_upper_json = """{"content": {"name": "savePipeline","context": {"user": "{user}","application": "{appName}","pipeline.id": "{pipelineId}","pipeline.name": "{pipelineName}"}, "execution": {"stages": [{ "status": "SUCCEEDED"}]}}}"""
                        user = pipelineExecutionConfig['lastModifiedBy']
                        application = pipelineExecutionConfig['application']
                        pipelineId = pipelineExecutionConfig['id']
                        pipelineName = pipelineExecutionConfig['name']
                        updatedTime = pipelineExecutionConfig['updateTs']
                        print(
                            "** Extracted pipeline config Data  user: " + user + ",application: " + application + ",pipelineId: " + pipelineId + ",pipelineName: " + pipelineName)
                        updated_pipeline_config_upper_json = json.loads(
                            pipeline_config_upper_json.replace('{user}', user).replace('{appName}',
                                                                                       application).replace(
                                '{pipelineId}', pipelineId).replace('{pipelineName}', pipelineName))
                        updated_pipeline_config_execution_Json = json.dumps(updated_pipeline_config_upper_json)
                        print(
                            "Updated Pipeline config execution details for application : " + application + " :: " + updated_pipeline_config_execution_Json)
                        eventId = uuid.uuid4()
                        insertPipelineConfigExecutionData(updatedTime, eventId, updated_pipeline_config_execution_Json)
                        savedCount += 1
                        print("********** Saved Pipeline Execution count::" + str(savedCount))
                    else:
                        rejectedCount += 1;
                        rejectedAppList.append(str(application))
                        print("********** Received Rejected count of Pipeline config Execution count::" + str(
                            rejectedCount) + " application : " + str(application))
                        rejectedPipelineExecutionJson.append(str(pipelineExecutionConfig));
        print("Total Received count : " + str(startcount))
        print("Total Saved count : " + str(savedCount))
        print("Total Rejected count : " + str(rejectedCount) + " Rejected App list :" + str(rejectedAppList))
    except Exception as e:
        print("Exception occurred while updating pipeline execution data : ", e)
        raise e


def insertPipelineConfigExecutionData(updatedTime, eventId, updated_pipeline_config_execution):
    try:
        cur = audit_conn.cursor()
        # date_time = datetime.datetime.now()
        updatedTime_date_time = datetime.datetime.utcfromtimestamp(int(updatedTime) / 1000)
        data = str(updatedTime_date_time), str(updatedTime_date_time), updated_pipeline_config_execution, str(
            eventId), 'spinnaker '
        cur.execute(
            "INSERT INTO audit_events (created_at, updated_at,data,event_id,source) VALUES (%s, %s, %s, %s, %s)",
            data)
        print("Successfully inserted pipeline config data into audit_events table")
    except Exception as e:
        print("Exception occurred while inserting  pipeline config data into audit_events table : ", e)
        raise e


def getGitUsernameBytoken(token, url):
    try:
        url = url + "/user"
        headers = {'Authorization': 'token ' + token}
        login = requests.get(url=url, headers=headers).json()
        print("git username: " + login['login'])
        return login['login']
    except Exception as e:
        print("Exception occured while getting user name of datasource type GIT : ", e)
        return " "


def alter_approval_gate_approval():
    try:
        cur = visibility_conn.cursor()
        cur.execute("ALTER TABLE approval_gate_approval ALTER COLUMN approver_comment TYPE TEXT")
    except Exception as e:
        print("Exception occured while altering the approval_gate_parameter table : ", e)
        raise e


def modifyOpsmxdb():
    try:
        cur = opsmxdb_conn.cursor()
        cur.execute("select opsmx_id from userservicetemplate where verification_type = null;")
        result = cur.fetchall()
        if result != None:
            for opsmx_id in result:
                cur.execute(
                    "update userservicetemplate set verification_type = 'VERIFICATION' where opsmx_id=" + str(opsmx_id))
    except Exception as e:
        print("Exception occurred while fetching userservicetemplate data : ", e)
        raise e


def updatescript():
    try:
        cur = opsmxdb_conn.cursor()
        cur.execute(" ALTER TABLE entropy ALTER COLUMN service_id DROP NOT NULL ")
        print("Successfully altered entropy table in autopilot db")
    except Exception as e:
        print("Exception occured while  updating script : ", e)
        raise e

def updateautopilotconstraints():
    try:
        cur = opsmxdb_conn.cursor()
        cur.execute(" ALTER TABLE serviceriskanalysis  DROP CONSTRAINT IF EXISTS fkmef9blhpcxhcj431kcu52nm1e ")
        print("Successfully dropped constraint serviceriskanalysis table in autopilot db")
        cur.execute(" ALTER TABLE servicegate  DROP CONSTRAINT IF EXISTS uk_lk3buh56ebai2gycw560j2oxm ")
        print("Successfully dropped constraint servicegate table in autopilot db")
    except Exception as e:
        print("Exception occured while  updating script : ", e)
        raise e  

def modifyGit(hosturl):
    try:
        cur = platform_conn.cursor()
        cur.execute("select id,config from datasource where datasourcetype = 'GIT';")
        result = cur.fetchall()
        if result != None:
            for data in result:
                configData = json.loads(data[1])
                jdata = {"hostUrl": hosturl, "url": configData['url'],
                         "username": getGitUsernameBytoken(configData['token'], configData['url']),
                         "token": configData['token']}
                updatedConfig = "'" + str(json.dumps(jdata)) + "'"
                print("GIT Datasource Json data of Id:" + str(data[0]) + " :" + updatedConfig)
                cur.execute('update datasource SET config =' + updatedConfig + ' where id =' + str(data[0]))
    except Exception as e:
        print("Exception occurred while modify datasource data of GIT: ", e.with_traceback())
        raise e


def modifygitname():
    try:
        cur = platform_conn.cursor()
        cur.execute("select id from datasource where datasourcetype = 'GIT';")
        result = cur.fetchall()
        if result != None:
            for id in result:
                cur.execute("update datasource set datasourcetype = 'GITHUB' where id=" + str(id[0]))
    except Exception as e:
        print("Exception occurred while modify datasource data of GIT to GITHUB : ", e)
        raise e


def modifyGithub(hosturl, url):
    try:
        cur = platform_conn.cursor()
        cur.execute("select id,config from datasource where datasourcetype = 'GITHUB';")
        result = cur.fetchall()
        if result != None:
            for data in result:
                configData = json.loads(data[1])
                updateUsername = " "
                if 'username' in configData:
                    updateUsername = configData['username']
                jdata = {"hostUrl": hosturl, "url": url, "username": updateUsername, "token": configData['token']}
                updatedConfig = "'" + str(json.dumps(jdata)) + "'"
                print("GITHUB Datasource Json data of Id: " + str(data[0]) + " :" + updatedConfig)
                cur.execute('update datasource SET config =' + updatedConfig + ' where id=' + str(data[0]))
    except Exception as e:
        print("Exception occurred while modify datasource of tpe GITHUB: ", e)
        raise e


def migrate_policy_audit(policy_audits):
    try:
        cur = audit_conn.cursor()
        for policy_audit in policy_audits:
            audit = {"action": policy_audit[0],
                     "application": policy_audit[1],
                     "description": policy_audit[2],
                     "executionId": policy_audit[3],
                     "stage": policy_audit[4],
                     "pipeline": policy_audit[5],
                     "type": policy_audit[6],
                     "name": policy_audit[7],
                     "result": policy_audit[8],
                     "user": policy_audit[9]
                     }

            event_type = "POLICY_AUDIT"
            if audit['type'] is not None and audit['type'] == "EVAL_RUNTIME":
                event_type = "POLICY_GATE_AUDIT"

            audit_data = {
                "eventType": event_type,
                "eventId": str(uuid.uuid4()),
                "auditData": audit
            }
            opsmxtime = str(policy_audit[10])
            print("Policy data inserting into DB: " + str(audit_data))
            data = opsmxtime, opsmxtime, json.dumps(audit_data), audit_data['eventId'], 'OES'
            cur.execute(
                "INSERT INTO audit_events (created_at, updated_at, data, event_id, source) VALUES (%s, %s, %s, %s, %s)",
                data)

    except Exception as e:
        print("Exception occurred while migrating policy audit : ", e)
        raise e


def fetch_policy_audit():
    try:
        cur = oesdb_conn.cursor()
        cur.execute(
            "select action, application, description, execution_id, gate, pipeline, policy_event, policy_name, result, user_id,created_date from policy_audit")
        return cur.fetchall()
    except Exception as e:
        print("Exception occurred while fetching policy audit : ", e)
        raise e


if __name__ == '__main__':
    n = len(sys.argv)
    if n != 13:
        print(
            'Please pass valid 11 arguments visibilitydb <visibility-db-host> <platform_db-name> <platform_hostt> <opsmx-db-name> <opsmx-db-host> '
            '<oes-db-name> <oes-db-host> <audit_db-name> <audit_db_host> <db-port> <url>(spinnaker gate url) <session_id>(configured spinnaker active session Id)')

    visibility_db = 'visibilitydb'
    visibility_host = sys.argv[2]
    platform_db = sys.argv[3]
    platform_host = sys.argv[4]
    opsmx_db = sys.argv[5]
    opsmx_host = sys.argv[6]
    oes_db = sys.argv[7]
    oes_host = sys.argv[8]
    audit_db = sys.argv[9]
    audit_host = sys.argv[10]
    port = sys.argv[11]
    url = sys.argv[12]
    session_id = sys.argv[13]

    print("Using default host url ex:http://github.com")

    # Establishing the visibility db connection
    visibility_conn = psycopg2.connect(database=visibility_db, user='postgres', password='networks123',
                                       host=visibility_host, port=port)
    print("Visibility database connection established successfully")

    # Establishing the platform db connection
    platform_conn = psycopg2.connect(database=platform_db, user='postgres', password='networks123', host=platform_host,
                                     port=port)
    print('Opened platform database connection successfully')

    # Establishing the opsmx db connection
    opsmxdb_conn = psycopg2.connect(database=opsmx_db, user='postgres', password='networks123', host=opsmx_host,
                                    port=port)
    print("opsmx database connection established successfully")

    # Establishing the opsmx db connection
    oesdb_conn = psycopg2.connect(database=oes_db, user='postgres', password='networks123',
                                  host=oes_host, port=port)
    print("oes(sapor) database connection established successfully")

    # Establishing the audit db connection
    audit_conn = psycopg2.connect(database=audit_db, user='postgres', password='networks123',
                                  host=audit_host, port=port)
    print('audit database connection successfully')

    perform_migration()
