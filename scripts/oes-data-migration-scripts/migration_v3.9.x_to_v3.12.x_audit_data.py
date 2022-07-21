import datetime
import json
import uuid
import psycopg2
import sys
import requests
import logging
import shlex
import subprocess
import time


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
    global is_error_occurred
    imported_apps = []
    app_sync_status = None
    try:
        spin_gate_url, spinnaker_connectivity_status = fetch_configured_spinnaker_details()
        if spinnaker_connectivity_status == 'Connected':
            imported_apps = import_apps_from_spinnaker(app_sync_status, imported_apps)
            perform_audit_migration(imported_apps, spin_gate_url)
            addingDataToPipelineExecutionAuditEvents()
            getexecutionIdWithTime()

        else:
            print(f"{bcolors.FAIL} {bcolors.BOLD}Spinnaker not connected and hence cannot proceed with the app sync{bcolors.ENDC}")
            logging.critical("Spinnaker not connected and hence cannot proceed with the app sync")
            raise Exception("Spinnaker not connected and hence cannot proceed with the app sync")


        if is_error_occurred == True:
            logging.critical("FAILURE: Migration script execution failed. Please contact the support team.")
            raise Exception("FAILURE: Migration script execution failed. Please contact the support team.")
        else:
            print(f"{bcolors.OKGREEN}{bcolors.BOLD}Successfully completed the migration.{bcolors.ENDC}")
            logging.info("Successfully completed the migration.")

    except Exception as e:
        logging.critical(e.__str__(), exc_info=True)
        print(
            f"{bcolors.FAIL} {bcolors.BOLD}FAILURE: {bcolors.ENDC}{bcolors.FAIL}Migration script execution failed. Please contact the support team{bcolors.ENDC}")
        audit_conn.rollback()
    finally:
        audit_conn.close()
        oesdb_conn.close()
        platform_conn.close()


def fetch_configured_spinnaker_details():
    print("Checking spinnaker configuration in oes db")
    logging.info("Checking spinnaker configuration in oes db")
    spinnaker = verifySpinnakerConfigurationAndGetURL()
    spin_gate_url = spinnaker[0][1]
    print("Configured spinnaker url: " + spin_gate_url)
    logging.info("Configured spinnaker url: " + spin_gate_url)
    spinnaker_connectivity_status = spinnaker[0][2]
    return spin_gate_url, spinnaker_connectivity_status


def import_apps_from_spinnaker(app_sync_status, imported_apps):
    app_sync()
    status = 'running'
    print("Importing applications from spinnaker")
    logging.info("Importing applications from spinnaker")
    while status != 'completed' and status != 'aborted':
        time.sleep(5)
        app_sync_status = track_app_sync_status()
        status = app_sync_status['status']
    logging.info(f"app_sync_status : {app_sync_status}")
    if status == 'aborted':
        raise Exception("App sync aborted")
    else:
        print("App sync operation completed")
        logging.info("App sync operation completed")
        app_sync_details = app_sync_status['appSyncDetails']
        try:
            more = app_sync_details['more']
            imported_apps = more['importedApps']
        except KeyError as ke:
            pass
    return imported_apps


def app_sync():
    try:
        url = oes_platform_service_url + "/platformservice/v3/applications/import/start"
        headers = {'Content-Type': 'application/json', 'x-spinnaker-user': oes_admin_username}
        response = requests.post(url=url, headers=headers)
        if response is not None and response.status_code != 202:
            raise Exception("Error while syncing apps")
    except Exception as e:
        print("Exception occurred while syncing applications : ", e)
        logging.error("Exception occurred while syncing applications : ", exc_info=True)
        raise e


def track_app_sync_status():
    try:
        app_sync_status = None
        url = oes_platform_service_url + "/platformservice/v3/applications/import/status"
        headers = {'Content-Type': 'application/json', 'x-spinnaker-user': oes_admin_username}
        response = requests.get(url=url, headers=headers)
        if response.status_code == 200:
            app_sync_status = response.json()
        return app_sync_status
    except Exception as e:
        print("Exception occurred while checking app sync status : ", e)
        logging.error("Exception occurred while checking app sync status : ", exc_info=True)
        raise e


def perform_audit_migration(imported_apps, spin_gate_url):
    global is_error_occurred
    try:
        session_id = login_to_spinnaker(spin_gate_url)
        if imported_apps is None or len(imported_apps) <= 0:
            logging.info("Fetch spinnaker applications from ISD db")
            # applications = fetchSpinnakerApplication(spin_gate_url, session_id)
            applications = fetch_spinnaker_applications_from_isd_db()
        else:
            applications = imported_apps

        logging.info("List of spinnaker application names : " + ', '.join(applications))

        print("Performing audit migration")
        logging.info("Performing audit migration")

        for application in applications:
            try:
                if is_pipeline_execution_record_exist(application) == False or is_pipeline_config_record_exist(
                        application) == False:
                    print("Processing application : ", application)
                    logging.info(f"Processing application : {application}")
                    applicationPipelineDict = fetchSpinnakerPipelineExecutionByApp(application, spin_gate_url,
                                                                                   session_id)
                    migratePipelineExecutions(applicationPipelineDict)

                    applicationPipelineConfigDict = fetchSpinnakerPipelineConfigExecution(application, spin_gate_url,
                                                                                          session_id)
                    migratePipelineConfigExecutionS(applicationPipelineConfigDict)
                    audit_conn.commit()
                else:
                    print(
                        f"Ignoring the application : {application} as it was already processed")
                    logging.info(f"Ignoring the application : {application} as it was already processed")
            except Exception as e:
                print(f"Exception occurred while processing the application : {application} and the exception is : ", e)
                logging.error(
                    f"Exception occurred while processing the application : {application} and the exception is : ",
                    exc_info=True)
                is_error_occurred = True

    except Exception as e:
        print('Exception occurred during fetching spinnaker pipeline applications : ', e)
        logging.error("Exception occurred during fetching spinnaker pipeline applications", exc_info=True)
        raise e


def verifySpinnakerConfigurationAndGetURL():
    try:
        oesdb_cursor.execute("select id,url,status from spinnaker")
        result = oesdb_cursor.fetchall()
        if result is None or len(result)<=0:
            raise Exception("Please configure spinnaker before proceeding with audit migration")
        return result
    except Exception as e:
        print("Exception occurred while fetching spinnaker configuration from oes db: ", e)
        logging.error("Exception occurred while fetching spinnaker configuration from oes db: ", exc_info=True)
        raise e


def login_to_spinnaker(url):
    try:
        cookie = ""
        cmd = "curl -vvv -X POST '" + url + "/login?username=" + spinnaker_login_id + "&password=" + spinnaker_password + "&submit=Login'"
        output = subprocess.getoutput(cmd=cmd)
        output = output.replace(spinnaker_login_id, "***").replace(spinnaker_password, "***")
        logging.info(f"Output for spinnaker login : {output}")
        components = output.split("<")
        for comp in components:
            if comp.__contains__("set-cookie") or comp.__contains__("Set-Cookie"):
                cookie = comp.split(":")[1].strip()
        return cookie
    except Exception as e:
        print("Exception occurred while logging in to spinnaker : ", e)
        logging.error("Exception occurred while logging in to spinnaker : ", exc_info=True)
        raise e


def fetchSpinnakerApplication(url, session_id):
    try:
        url = url + "/applications"
        headers = {'Cookie': session_id}
        response = requests.get(url=url, headers=headers).json()
        applications = [res.get('name') for res in response]
    except Exception as e:
        print("Exception occurred while fetching spinnaker applications : ", e)
        logging.error("Exception occurred while fetching spinnaker applications : ", exc_info=True)
        raise e
    return applications


def fetch_spinnaker_applications_from_isd_db():
    apps = []
    try:
        platformdb_cursor.execute("select name from applications where source = 'Spinnaker'")
        applications = platformdb_cursor.fetchall()
        for app in applications:
            apps.append(app[0])
        return apps
    except Exception as e:
        print("Exception occurred while fetching spinnaker applications : ", e)
        logging.error("Exception occurred while fetching spinnaker applications : ", exc_info=True)


def is_pipeline_execution_record_exist(app_name):
    try:
        query = f"select * from audit_events where data -> 'details' ->> 'application' @@ '{app_name}'"
        audit_cursor.execute(query)
        result = audit_cursor.fetchall()
        if result is not None and len(result) > 0:
            return True
        else:
            return False
    except Exception as e:
        print("Exception occurred while checking is pipeline execution record exists : ", e)
        logging.error("Exception occurred while checking is pipeline execution record exists : ", exc_info=True)
        raise e


def is_pipeline_config_record_exist(app_name):
    try:
        query = f"select * from audit_events where data -> 'content' -> 'context' ->> 'application' @@ '{app_name}'"
        audit_cursor.execute(query)
        result = audit_cursor.fetchall()
        if result is not None and len(result) > 0:
            return True
        else:
            return False
    except Exception as e:
        print("Exception occurred while checking is pipeline config record exists : ", e)
        logging.error("Exception occurred while checking is pipeline config record exists : ", exc_info=True)
        raise e

def fetchSpinnakerPipelineExecutionByApp(application, url, session_id):
    applicationPipelineDict = []
    global is_error_occurred
    try:
        url = url + "/applications/{application}/pipelines"
        updated_url = str(url).replace('{application}', application)
        headers = {'Cookie': session_id}
        response = requests.get(url=updated_url, headers=headers)
        if response.json() != []:
            pipelineArray = {application: json.loads(response.content)}
            applicationPipelineDict.append(pipelineArray)
    except Exception as e:

        print("Exception occurred while fetching spinnaker pipeline execution : ", e)
        logging.error("Exception occurred while fetching spinnaker pipeline execution : ", exc_info=True)
        raise e
    return applicationPipelineDict


def fetchSpinnakerPipelineConfigExecution(application, url, session_id):
    applicationPipelineConfigDict = []
    global is_error_occurred
    try:
        url = url + "/applications/{application}/pipelineConfigs"
        updated_url = str(url).replace('{application}', application)
        headers = {'Cookie': session_id}
        response = requests.get(url=updated_url, headers=headers)
        if response.json() != []:
            pipelineArray = {application: json.loads(response.content)}
            applicationPipelineConfigDict.append(pipelineArray)
    except Exception as e:
        print("Exception occurred while fetching spinnaker pipeline execution : ", e)
        logging.error("Exception occurred while fetching spinnaker pipeline execution : ", exc_info=True)
        raise e
    return applicationPipelineConfigDict


def migratePipelineExecutions(applicationPipelineDict):
    global is_error_occurred
    try:
        startcount = 0
        savedCount = 0
        rejectedCount = 0
        rejectedPipelineExecutionJson = []
        rejectedAppList = set()
        for applicationPipelines in applicationPipelineDict:
            try:
                for application, pipelineExecutions in applicationPipelines.items():
                    try:
                        for pipelineExecution in pipelineExecutions:
                            try:
                                startcount += 1
                                logging.info("********** Received Pipeline Execution count::" + str(startcount))
                                if 'id' in pipelineExecution and 'buildTime' in pipelineExecution and 'status' in pipelineExecution:
                                    eventId = getEventId(pipelineExecution)
                                    if eventId != None:
                                        pipelineExecutionJson = json.dumps(pipelineExecution)
                                        executionId = pipelineExecution['id']
                                        logging.info(
                                            "Started inserting pipeline execution details application Id - " + application + " and execution Id: " + executionId)
                                        if isDataAlreadyPresent(application, executionId) == False:
                                            if getPipelineStatus(pipelineExecution['status']) != None:
                                                pipeline_upper_json = """{"details": { "source": "orca","type": "orca:pipeline:{status}","created":{created},"application": "{application}","requestHeaders": {}},"content": {"execution":"""
                                                pipeline_lower_json = ""","executionId": "{executionId}"},"eventId": "{eventId}"}"""
                                                created = pipelineExecution['buildTime']
                                                status = getPipelineStatus(pipelineExecution['status'])
                                                logging.info(
                                                    "** Extracted Data  executionId: " + executionId + ",status: " + status + ",created: " + str(
                                                        created) + ",eventId: " + eventId)
                                                updated_pipeline_upper_json = pipeline_upper_json.replace('{status}',
                                                                                                          status).replace(
                                                    '{created}', str(created)).replace('{application}', application)
                                                updated_pipeline_lower_json = pipeline_lower_json.replace(
                                                    '{executionId}',
                                                    executionId).replace(
                                                    '{eventId}', eventId)
                                                updated_pipeline_execution = json.loads(
                                                    updated_pipeline_upper_json + pipelineExecutionJson + updated_pipeline_lower_json)
                                                updated_pipeline_execution_Json = json.dumps(updated_pipeline_execution)
                                                # print("Updated Pipeline execution details for application : " + application + " :: " + updated_pipeline_execution_Json)
                                                insertPipelineExecutionData(eventId, updated_pipeline_execution_Json)
                                                savedCount += 1
                                                logging.info(
                                                    "********** Saved Pipeline Execution count::" + str(savedCount))
                                else:
                                    rejectedCount += 1
                                    rejectedAppList.add(str(application))
                                    logging.info(
                                        "********** Received Rejected count of Pipeline Execution count::" + str(
                                            rejectedCount) + " application : " + str(application))
                                    rejectedPipelineExecutionJson.append(str(pipelineExecution))
                            except Exception as e:
                                logging.error(
                                    f"Exception occurred while processing pipeline execution : {pipelineExecution}",
                                    exc_info=True)
                                is_error_occurred = True
                    except Exception as e:
                        logging.error(
                            f"Exception occurred while processing application pipeline items : {application} , {pipelineExecutions}",
                            exc_info=True)
                        is_error_occurred = True
            except Exception as e:
                logging.error(f"Exception occurred while processing applicationPipelines : {applicationPipelines}",
                              exc_info=True)
                is_error_occurred = True

        logging.info("Total Received count : " + str(startcount))
        logging.info("Total Saved count : " + str(savedCount))
        logging.info("Total Rejected count : " + str(rejectedCount) + " Rejected App list :" + str(rejectedAppList))
    except Exception as e:
        print("Exception occurred while updating pipeline execution data : ", e)
        logging.error("Exception occurred while updating pipeline execution data : ", exc_info=True)
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


def isDataAlreadyPresent(application, executionId):
    try:
        audit_cursor.execute(
            "SELECT count(*) FROM audit_events WHERE data -> 'content' -> 'execution' ->> 'application' = '" + application + "' AND data -> 'content' ->> 'executionId' = '" + executionId + "'")
        result = audit_cursor.fetchone()[0]
        if result > 0:
            return bool(True)
        else:
            return bool(False)
    except Exception as e:
        print("Exception occurred while fetch data into audit_events table : ", e)
        logging.error("Exception occurred while fetch data into audit_events table : ", exc_info=True)
        raise e


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
        date_time = datetime.datetime.now()
        data = date_time, date_time, updated_pipeline_execution, eventId, 'spinnaker'
        audit_cursor.execute(
            "INSERT INTO audit_events (created_at, updated_at,data,event_id,source) VALUES (%s, %s, %s, %s, %s)",
            data)
        logging.info("Successfully inserted data into audit_events table")
    except Exception as e:
        print("Exception occurred while inserting data into audit_events table : ", e)
        logging.error("Exception occurred while inserting data into audit_events table : ", exc_info=True)
        raise e


def migratePipelineConfigExecutionS(applicationPipelineDict):
    global is_error_occurred
    try:
        startcount = 0
        savedCount = 0
        rejectedCount = 0
        rejectedPipelineExecutionJson = []
        rejectedAppList = []
        for applicationPipelines in applicationPipelineDict:
            try:
                for application, pipelineConfigExecutions in applicationPipelines.items():
                    try:
                        for pipelineExecutionConfig in pipelineConfigExecutions:
                            try:
                                startcount += 1
                                logging.info("********** Received Pipeline config Execution count::" + str(startcount))
                                if 'name' in pipelineExecutionConfig and 'lastModifiedBy' in pipelineExecutionConfig and 'application' in pipelineExecutionConfig and 'id' in pipelineExecutionConfig and 'updateTs' in pipelineExecutionConfig:
                                    pipeline_config_upper_json = """{"content": {"name": "savePipeline","context": {"user": "{user}","application": "{appName}","pipeline.id": "{pipelineId}","pipeline.name": "{pipelineName}"}, "execution": {"stages": [{ "status": "SUCCEEDED"}]}}}"""
                                    user = pipelineExecutionConfig['lastModifiedBy']
                                    application = pipelineExecutionConfig['application']
                                    pipelineId = pipelineExecutionConfig['id']
                                    pipelineName = pipelineExecutionConfig['name']
                                    updatedTime = pipelineExecutionConfig['updateTs']
                                    logging.info(
                                        "** Extracted pipeline config Data  user: " + user + ",application: " + application + ",pipelineId: " + pipelineId + ",pipelineName: " + pipelineName)
                                    updated_pipeline_config_upper_json = json.loads(
                                        pipeline_config_upper_json.replace('{user}', user).replace('{appName}',
                                                                                                   application).replace(
                                            '{pipelineId}', pipelineId).replace('{pipelineName}', pipelineName))
                                    updated_pipeline_config_execution_Json = json.dumps(
                                        updated_pipeline_config_upper_json)
                                    logging.info(
                                        "Updated Pipeline config execution details for application : " + application + " :: " + updated_pipeline_config_execution_Json)
                                    eventId = uuid.uuid4()
                                    insertPipelineConfigExecutionData(updatedTime, eventId,
                                                                      updated_pipeline_config_execution_Json)
                                    savedCount += 1
                                    logging.info("********** Saved Pipeline Execution count::" + str(savedCount))
                                else:
                                    rejectedCount += 1
                                    rejectedAppList.append(str(application))
                                    logging.info(
                                        "********** Received Rejected count of Pipeline config Execution count::" + str(
                                            rejectedCount) + " application : " + str(application))
                                    rejectedPipelineExecutionJson.append(str(pipelineExecutionConfig))
                            except Exception as e:
                                logging.error(
                                    f"Exception occurred while processing pipelineExecutionConfig : {pipelineExecutionConfig}",
                                    exc_info=True)
                                is_error_occurred = True
                    except Exception as e:
                        logging.error(
                            f"Exception occurred while processing application pipeline items : {application} , {pipelineConfigExecutions}",
                            exc_info=True)
                        is_error_occurred = True
            except Exception as e:
                logging.error(f"Exception occurred while processing application pipelines : {applicationPipelines}",
                              exc_info=True)
                is_error_occurred = True
        logging.info("Total Received count : " + str(startcount))
        logging.info("Total Saved count : " + str(savedCount))
        logging.info("Total Rejected count : " + str(rejectedCount) + " Rejected App list :" + str(rejectedAppList))
    except Exception as e:
        print("Exception occurred while updating pipeline execution data : ", e)
        logging.error("Exception occurred while updating pipeline execution data : ", exc_info=True)
        raise e


def insertPipelineConfigExecutionData(updatedTime, eventId, updated_pipeline_config_execution):
    try:
        # date_time = datetime.datetime.now()
        updatedTime_date_time = datetime.datetime.utcfromtimestamp(int(updatedTime) / 1000)
        data = str(updatedTime_date_time), str(updatedTime_date_time), updated_pipeline_config_execution, str(
            eventId), 'spinnaker '
        audit_cursor.execute(
            "INSERT INTO audit_events (created_at, updated_at,data,event_id,source) VALUES (%s, %s, %s, %s, %s)",
            data)
        logging.info("Successfully inserted pipeline config data into audit_events table")
    except Exception as e:
        print("Exception occurred while inserting  pipeline config data into audit_events table : ", e)
        logging.error("Exception occurred while inserting  pipeline config data into audit_events table : ",
                      exc_info=True)
        raise e


def addingDataToPipelineExecutionAuditEvents():
    global is_error_occurred
    try:
        count = 0
        audit_cursor.execute(
            "select id, data -> 'content' ->> 'executionId' as executionId,data from audit_events where source='spinnaker' "
            "and (data -> 'details' ->> 'type' = 'orca:pipeline:complete' or data -> 'details' ->> 'type'='orca:pipeline:failed');")
        result = audit_cursor.fetchall()
        if result != None:
            for auditData in result:
                try:
                    if is_pipeline_execution_data_exist(auditData[0]) == False:
                        count +=1
                        postingPipelineExecutionAuditEvents(auditData)
                except Exception as e:
                    logging.error(f"Exception occurred while posting pipeline execution audit events : {auditData} and the exception is : ", exc_info=True)
                    is_error_occurred = True
        logging.info("Data received from audit events table :" + str(count))
    except Exception as e:
        print("Exception occurred while fetching audit_events data : ", e)
        logging.error("Exception occurred while fetching audit_events data : ", exc_info=True)
        raise e


def is_pipeline_execution_data_exist(audit_events_id):
    is_pipeline_execution_data_exist = False
    try:
        audit_cursor.execute(f"select pipeline_execution_data from pipeline_execution_audit_events where audit_events_id = {audit_events_id}")
        result = audit_cursor.fetchall()
        if result is not None and len(result) > 0:
            is_pipeline_execution_data_exist = True
    except Exception as e:
        print("Exception occurred while checking if pipeline execution data exists : ", e)
        logging.error("Exception occurred while checking if pipeline execution data exists : ", exc_info=True)
    return is_pipeline_execution_data_exist

def postingPipelineExecutionAuditEvents(auditData):
    try:
        url = oes_audit_service_url + "/auditservice/v1/echo/events/" + str(auditData[0])
        headers = {'Content-Type': 'application/json'}
        requests.post(url=url, headers=headers)
    except Exception as e:
        print("Exception occurred while posting Pipeline Execution Audit Events : ", e)
        logging.error("Exception occurred while posting Pipeline Execution Audit Events : ", exc_info=True)
        raise e


def getexecutionIdWithTime():
    global is_error_occurred
    try:
        audit_cursor.execute("select audit_data -> 'executionId' as executionId from pipeline_execution_audit_events")
        executionIdList = [item[0] for item in audit_cursor.fetchall()]
        count = 0
        if executionIdList != None:
            logging.info("Updating pipeline execution time")
            for executionId in executionIdList:
                try:
                    audit_cursor.execute("select data -> 'details' ->>'created' as executionTime from audit_events where data -> 'content' ->> 'executionId' ='" +executionId+ "'")
                    dateDetails = [executionTime[0] for executionTime in audit_cursor.fetchall()]
                    if dateDetails != None:
                        count +=1
                        dateDetails = str(dateDetails[0])
                        updatedTime_date_time = datetime.datetime.utcfromtimestamp(int(dateDetails) / 1000)
                        val = """UPDATE pipeline_execution_audit_events SET created_at ={}, updated_at ={} WHERE audit_data ->> 'executionId' = {}""".format(
                            '\'' + str(updatedTime_date_time) + '\'', '\'' + str(updatedTime_date_time) + '\'',
                            '\'' + executionId + '\'')
                        audit_cursor.execute(val)
                        audit_conn.commit()
                except Exception as e:
                    logging.error(f"Exception occurred while updating pipeline execution time : {executionId} and the exception is : ", exc_info=True)
                    is_error_occurred = True
        logging.info(f"Total updated created time for pipeline execution Data: {count}")
    except Exception as e:
        print("Exception occurred while fetching and update time for pipeline_execution_audit_events data : ", e)
        logging.error("Exception occurred while fetching and update time for pipeline_execution_audit_events data : ", exc_info=True)
        raise e


if __name__ == '__main__':
    n = len(sys.argv)
    if n != 15:
        print("Please pass valid 14 arguments <audit-db-name> <audit-db-host> <oes-db-name> <oes-db-host> <platform-db-name> <platform-db-host> <db-port> <db-username> <db-password> <spinnaker-login-id> <spinnaker-password> <oes-audit-service-url> <oes-platform-service-url> <oes-admin-username>")
        exit(1)

    global is_error_occurred
    is_error_occurred = False

    logging.basicConfig(filename='/tmp/migration_v3.11.x_to_v3.12_albertson.log', filemode='w',
                        format="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s", datefmt='%H:%M:%S',
                        level=logging.INFO)

    audit_db = sys.argv[1]
    audit_host = sys.argv[2]
    oes_db = sys.argv[3]
    oes_db_host = sys.argv[4]
    platform_db = sys.argv[5]
    platform_db_host = sys.argv[6]
    db_port = sys.argv[7]
    db_username = sys.argv[8]
    db_password = sys.argv[9]
    spinnaker_login_id = sys.argv[10]
    spinnaker_password = sys.argv[11]
    oes_audit_service_url = sys.argv[12]
    oes_platform_service_url = sys.argv[13]
    oes_admin_username = sys.argv[14]

    audit_conn = psycopg2.connect(database=audit_db, user=db_username, password=db_password,
                                  host=audit_host, port=db_port)
    logging.info("auditdb connection established successfully")

    audit_cursor = audit_conn.cursor()

    # Establishing the oesdb connection
    oesdb_conn = psycopg2.connect(database=oes_db, user=db_username, password=db_password,
                                  host=oes_db_host, port=db_port)
    logging.info("oes(sapor) database connection established successfully")
    oesdb_cursor = oesdb_conn.cursor()

    # Establishing the platform db connection
    platform_conn = psycopg2.connect(database=platform_db, user=db_username, password=db_password, host=platform_db_host,
                                     port=db_port)
    logging.info('Opened platform database connection successfully')
    platformdb_cursor = platform_conn.cursor()

    perform_migration()



