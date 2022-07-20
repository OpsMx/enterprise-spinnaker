import datetime
import json
import uuid
import psycopg2
import sys
import requests
import logging
import shlex
import subprocess


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


def perform_migrate():
    global is_error_occurred
    try:
        try:
            create_audit_events()
            perform_Audit_migration()
            policy_audits = fetch_policy_audit()
            migrate_policy_audit(policy_audits)
        except Exception as e:
            logging.error("Failure at step 1", exc_info=True)
            is_error_occurred = True

        url = 'https://api.github.com'
        hosturl = 'https://github.com'
        try:
            alter_approval_gate_approval()
        except Exception as e:
            logging.error("Failure at step 2", exc_info=True)
            is_error_occurred = True

        try:
            modifyOpsmxdb()
        except Exception as e:
            logging.error("Failure at step 3", exc_info=True)
            is_error_occurred = True

        try:
            updatescript()
        except Exception as e:
            logging.error("Failure at step 4", exc_info=True)
            is_error_occurred = True

        try:
            updateautopilotconstraints()
        except Exception as e:
            logging.error("Failure at step 5", exc_info=True)
            is_error_occurred = True

        try:
            modifyGit(hosturl)
        except Exception as e:
            logging.error("Failure at step 6", exc_info=True)
            is_error_occurred = True

        try:
            modifygitname()
        except Exception as e:
            logging.error("Failure at step 7", exc_info=True)
            is_error_occurred = True

        try:
            modifyGithub(hosturl, url)
        except Exception as e:
            logging.error("Failure at step 8", exc_info=True)
            is_error_occurred = True


        if is_error_occurred == True:
            print(
                f"{bcolors.FAIL} {bcolors.BOLD}FAILURE: {bcolors.ENDC}{bcolors.FAIL}Migration script execution failed. Please contact the support team{bcolors.ENDC}")
            logging.critical("FAILURE: Migration script execution failed. Please contact the support team.")
            raise Exception("FAILURE: Migration script execution failed. Please contact the support team.")
        else:
            print(f"{bcolors.OKGREEN}{bcolors.BOLD}Successfully completed the migration.{bcolors.ENDC}")
            logging.info("Successfully completed the migration.")
            commit_transactions()

    except Exception as e:
        logging.critical(e.__str__(), exc_info=True)
        rollback_transactions()
        exit(1)
    finally:
        close_connections()


def create_auditdb():
    try:
        pg_conn = psycopg2.connect(user=super_user, password=super_password, host=opsmx_host, port=port)
        pg_conn.autocommit = True
        pg_cur = pg_conn.cursor()
        pg_cur.execute("DROP DATABASE IF EXISTS auditdb")
        pg_cur.execute("CREATE DATABASE auditdb OWNER postgres")
        global audit_conn
        audit_conn = psycopg2.connect(database='auditdb', user='postgres', password='networks123',
                                      host=opsmx_host, port=port)
        logging.info('audit database connection established successfully')
    except Exception as e:
        logging.critical("Exception occurred while creating auditdb : ", exc_info=True)
        raise e


def create_audit_events():
    try:
        audit_cursor.execute("CREATE TABLE IF NOT EXISTS audit_events (id serial PRIMARY KEY, created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ, data jsonb, event_id VARCHAR(255) NOT NULL, source VARCHAR(50))")
    except Exception as e:
        logging.critical("Exception occurred while creating audit_events table : ", exc_info=True)
        raise e


def close_connections():
    try:
        platform_conn.close()
        visibility_conn.close()
        opsmxdb_conn.close()
        if audit_conn is not None:
            audit_conn.close()
    except Exception as e:
        logging.warning("Exception occurred while closing the DB connection : ", exc_info=True)



def rollback_transactions():
    try:
        platform_conn.rollback()
        visibility_conn.rollback()
        opsmxdb_conn.rollback()
        if audit_conn is not None:
            audit_conn.rollback()
    except Exception as e:
        logging.critical("Exception occurred while rolling back the transactions : ", exc_info=True)
        raise e


def commit_transactions():
    try:
        platform_conn.commit()
        visibility_conn.commit()
        opsmxdb_conn.commit()
        audit_conn.commit()
    except Exception as e:
        logging.critical("Exception occurred while committing transactions : ", exc_info=True)
        raise e


def perform_Audit_migration():
    global is_error_occurred
    try:
        print("Checking spinnaker configuration in oes db")
        logging.info("Checking spinnaker configuration in oes db")
        spinnaker = verifySpinnakerConfigurationAndGetURL()
        spin_gate_url = spinnaker[0][1]
        print("Spinnaker configured url " + spin_gate_url)
        logging.info("Spinnaker configured url " + spin_gate_url)
        session_id = login_to_spinnaker(spin_gate_url)
        logging.info("Fetch spinnaker applications")
        applications = fetchSpinnakerApplication(spin_gate_url, session_id)
        logging.info("List of spinnaker application names : " + ', '.join(applications))

        for application in applications:
            try:
                if is_pipeline_execution_record_exist(application) == False or is_pipeline_config_record_exist(application) == False:
                    print("Processing application : ", application)
                    logging.info(f"Processing application : {application}")
                    applicationPipelineDict = fetchSpinnakerPipelineExecutionByApp(application, spin_gate_url,
                                                                                   session_id)
                    migratePipelineExecutions(applicationPipelineDict)
                    
                    applicationPipelineConfigDict = fetchSpinnakerPipelineConfigExecution(application, spin_gate_url,
                                                                                          session_id)
                    migratePipelineConfigExecutionS(applicationPipelineConfigDict)
                else:
                    print(
                        f"Ignoring the application : {application} as it was already processed")
                    logging.info(f"Ignoring the application : {application} as it was already processed")
                audit_conn.commit()
            except Exception as e:
                print(f"Exception occurred while processing the application : {application} and the exception is : ", e)
                logging.error(f"Exception occurred while processing the application : {application} and the exception is : ", exc_info=True)
                is_error_occurred=True

    except Exception as e:
        print('Exception occurred during fetching spinnaker pipeline applications : ', e)
        logging.error("Exception occurred during fetching spinnaker pipeline applications", exc_info=True)
        raise e


def is_pipeline_execution_record_exist(app_name):
    try:
        query = f"select * from audit_events where data -> 'details' ->> 'application' @@ '{app_name}'"
        audit_cursor.execute(query)
        result = audit_cursor.fetchall()
        if result is not None and len(result)>0:
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
        if result is not None and len(result)>0:
            return True
        else:
            return False
    except Exception as e:
        print("Exception occurred while checking is pipeline config record exists : ", e)
        logging.error("Exception occurred while checking is pipeline config record exists : ", exc_info=True)
        raise e


def verifySpinnakerConfigurationAndGetURL():
    try:
        oesdb_cursor.execute("select id,url from spinnaker")
        result = oesdb_cursor.fetchall()
        if result is  None:
            raise Exception("Please configure spinnaker before proceeding with audit migration")
        return result
    except Exception as e:
        print("Exception occurred while fetching spinnaker configuration from oes db: ", e)
        logging.error("Exception occurred while fetching spinnaker configuration from oes db: ", exc_info=True)
        raise e


def login_to_spinnaker(url):
    try:
        cookie = ""
        cmd = "curl -vvv -X POST '"+ url + "/login?username="+spinnaker_login_id+"&password="+spinnaker_password+"&submit=Login'"
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
                                                updated_pipeline_lower_json = pipeline_lower_json.replace('{executionId}',
                                                                                                          executionId).replace(
                                                    '{eventId}', eventId)
                                                updated_pipeline_execution = json.loads(
                                                    updated_pipeline_upper_json + pipelineExecutionJson + updated_pipeline_lower_json)
                                                updated_pipeline_execution_Json = json.dumps(updated_pipeline_execution)
                                                # print("Updated Pipeline execution details for application : " + application + " :: " + updated_pipeline_execution_Json)
                                                insertPipelineExecutionData(eventId, updated_pipeline_execution_Json)
                                                savedCount += 1
                                                logging.info("********** Saved Pipeline Execution count::" + str(savedCount))
                                else:
                                    rejectedCount += 1
                                    rejectedAppList.add(str(application))
                                    logging.info("********** Received Rejected count of Pipeline Execution count::" + str(
                                        rejectedCount) + " application : " + str(application))
                                    rejectedPipelineExecutionJson.append(str(pipelineExecution))
                            except Exception as e:
                                logging.error(f"Exception occurred while processing pipeline execution : {pipelineExecution}", exc_info=True)
                                is_error_occurred = True
                    except Exception as e:
                        logging.error(f"Exception occurred while processing application pipeline items : {application} , {pipelineExecutions}", exc_info=True)
                        is_error_occurred = True
            except Exception as e:
                logging.error(f"Exception occurred while processing applicationPipelines : {applicationPipelines}", exc_info=True)
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
                                    updated_pipeline_config_execution_Json = json.dumps(updated_pipeline_config_upper_json)
                                    logging.info(
                                        "Updated Pipeline config execution details for application : " + application + " :: " + updated_pipeline_config_execution_Json)
                                    eventId = uuid.uuid4()
                                    insertPipelineConfigExecutionData(updatedTime, eventId, updated_pipeline_config_execution_Json)
                                    savedCount += 1
                                    logging.info("********** Saved Pipeline Execution count::" + str(savedCount))
                                else:
                                    rejectedCount += 1
                                    rejectedAppList.append(str(application))
                                    logging.info("********** Received Rejected count of Pipeline config Execution count::" + str(
                                        rejectedCount) + " application : " + str(application))
                                    rejectedPipelineExecutionJson.append(str(pipelineExecutionConfig))
                            except Exception as e:
                                logging.error(f"Exception occurred while processing pipelineExecutionConfig : {pipelineExecutionConfig}", exc_info=True)
                                is_error_occurred = True
                    except Exception as e:
                        logging.error(f"Exception occurred while processing application pipeline items : {application} , {pipelineConfigExecutions}", exc_info=True)
                        is_error_occurred = True
            except Exception as e:
                logging.error(f"Exception occurred while processing application pipelines : {applicationPipelines}", exc_info=True)
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
        logging.error("Exception occurred while inserting  pipeline config data into audit_events table : ", exc_info=True)
        raise e


def getGitUsernameBytoken(token, url):
    try:
        url = url + "/user"
        headers = {'Authorization': 'token ' + token}
        login = requests.get(url=url, headers=headers).json()
        logging.info("git username: " + login['login'])
        return login['login']
    except Exception as e:
        print("Exception occured while getting user name of datasource type GIT : ", e)
        logging.error("Exception occured while getting user name of datasource type GIT : ", exc_info=True)
        return " "


def alter_approval_gate_approval():
    try:
        visibility_cursor.execute("ALTER TABLE approval_gate_approval ALTER COLUMN approver_comment TYPE TEXT")
    except Exception as e:
        print("Exception occured while altering the approval_gate_parameter table : ", e)
        logging.error("Exception occured while altering the approval_gate_parameter table : ", exc_info=True)
        raise e


def modifyOpsmxdb():
    global is_error_occurred
    try:

        opsmxdb_cursor.execute("select opsmx_id from userservicetemplate where verification_type = null")
        result = opsmxdb_cursor.fetchall()
        if result != None:
            for opsmx_id in result:
                try:
                    opsmxdb_cursor.execute(
                    "update userservicetemplate set verification_type = 'VERIFICATION' where opsmx_id=" + str(opsmx_id))
                except Exception as e:
                    logging.error(f"Exception occurred while processing the opsmx_id : {opsmx_id}", exc_info=True)
                    is_error_occurred = True

    except Exception as e:
        print("Exception occurred while fetching userservicetemplate data : ", e)
        logging.error("Exception occurred while fetching userservicetemplate data : ", exc_info=True)
        raise e


def updateautopilotconstraints():
    try:
        opsmxdb_cursor.execute(" ALTER TABLE serviceriskanalysis  DROP CONSTRAINT IF EXISTS fkmef9blhpcxhcj431kcu52nm1e ")
        print("Successfully dropped constraint serviceriskanalysis table in autopilot db")
        logging.info("Successfully dropped constraint serviceriskanalysis table in autopilot db")
        opsmxdb_cursor.execute(" ALTER TABLE servicegate  DROP CONSTRAINT IF EXISTS uk_lk3buh56ebai2gycw560j2oxm ")
        print("Successfully dropped constraint servicegate table in autopilot db")
        logging.info("Successfully dropped constraint servicegate table in autopilot db")
    except Exception as e:
        print("Exception occured while  updating script : ", e)
        logging.error("Exception occured while  updating script : ", exc_info=True)
        raise e


def updatescript():
    try:
        opsmxdb_cursor.execute(" ALTER TABLE entropy ALTER COLUMN service_id DROP NOT NULL ")
        print("Successfully altered entropy table in autopilot db")
        logging.info("Successfully altered entropy table in autopilot db")
    except Exception as e:
        print("Exception occured while  updating script : ", e)
        logging.error("Exception occured while  updating script : ", exc_info=True)
        raise e


def modifyGit(hosturl):
    global is_error_occurred
    try:
        platform_cursor.execute("select id,config from datasource where datasourcetype = 'GIT'")
        result = platform_cursor.fetchall()
        if result != None:
            for data in result:
                try:
                    configData = json.loads(data[1])
                    jdata = {"hostUrl": hosturl, "url": configData['url'],
                             "username": getGitUsernameBytoken(configData['token'], configData['url']),
                             "token": configData['token']}
                    updatedConfig = "'" + str(json.dumps(jdata)) + "'"
                    logging.info("GIT Datasource Json data of Id:" + str(data[0]) + " :" + updatedConfig)
                    platform_cursor.execute('update datasource SET config =' + updatedConfig + ' where id =' + str(data[0]))
                except Exception as e:
                    logging.error(f"Exception occurred while processing the config data : {data}", exc_info=True)
                    is_error_occurred = True
    except Exception as e:
        print("Exception occurred while modify datasource data of GIT: ", e)
        logging.error("Exception occurred while modify datasource data of GIT: ", exc_info=True)
        raise e


def modifygitname():
    global is_error_occurred
    try:
        platform_cursor.execute("select id from datasource where datasourcetype = 'GIT'")
        result = platform_cursor.fetchall()
        if result != None:
            for id in result:
                try:
                    platform_cursor.execute("update datasource set datasourcetype = 'GITHUB' where id=" + str(id[0]))
                except Exception as e:
                    logging.error(f"Exception occurred while processing for the datasource id : {id}", exc_info=True)
                    is_error_occurred = True
    except Exception as e:
        print("Exception occurred while modify datasource data of GIT to GITHUB : ", e)
        logging.error("Exception occurred while modify datasource data of GIT to GITHUB : ", exc_info=True)
        raise e


def modifyGithub(hosturl, url):
    global is_error_occurred
    try:
        platform_cursor.execute("select id,config from datasource where datasourcetype = 'GITHUB'")
        result = platform_cursor.fetchall()
        if result != None:
            for data in result:
                try:
                    configData = json.loads(data[1])
                    updateUsername = " "
                    if 'username' in configData:
                        updateUsername = configData['username']
                    jdata = {"hostUrl": hosturl, "url": url, "username": updateUsername, "token": configData['token']}
                    updatedConfig = "'" + str(json.dumps(jdata)) + "'"
                    logging.info("GITHUB Datasource Json data of Id: " + str(data[0]) + " :" + updatedConfig)
                    platform_cursor.execute('update datasource SET config =' + updatedConfig + ' where id=' + str(data[0]))
                except Exception as e:
                    logging.error(f"Exception occurred while processing github data : {data}", exc_info=True)
                    is_error_occurred = True
    except Exception as e:
        print("Exception occurred while modify datasource of tpe GITHUB: ", e)
        logging.error("Exception occurred while modify datasource of tpe GITHUB: ", exc_info=True)
        raise e


def migrate_policy_audit(policy_audits):
    global is_error_occurred
    try:
        for policy_audit in policy_audits:
            try:
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
                logging.info("Policy data inserting into DB: " + str(audit_data))
                data = opsmxtime, opsmxtime, json.dumps(audit_data), audit_data['eventId'], 'OES'
                audit_cursor.execute(
                    "INSERT INTO audit_events (created_at, updated_at, data, event_id, source) VALUES (%s, %s, %s, %s, %s)",
                    data)
            except Exception as e:
                logging.error(f"Exception occurred while processing policy audit : {policy_audit}", exc_info=True)
                is_error_occurred = True

    except Exception as e:
        print("Exception occurred while migrating policy audit : ", e)
        logging.error("Exception occurred while migrating policy audit : ", exc_info=True)
        raise e


def fetch_policy_audit():
    try:
        oesdb_cursor.execute(
            "select action, application, description, execution_id, gate, pipeline, policy_event, policy_name, result, user_id,created_date from policy_audit")
        return oesdb_cursor.fetchall()
    except Exception as e:
        print("Exception occurred while fetching policy audit : ", e)
        logging.error("Exception occurred while fetching policy audit : ", exc_info=True)
        raise e


if __name__ == '__main__':
    n = len(sys.argv)
    if n != 16:
        print(
            'Please pass valid 15 arguments <visibility-db-name> <visibility-db-host> <platform_db-name> <platform_host> <opsmx-db-name> <opsmx-db-host> '
            '<oes-db-name> <oes-db-host> <audit-db-name> <audit-db-host> <db-port> <db-username> <db-password> <spinnaker-login-id> <spinnaker-password>')
        exit(1)

    global is_error_occurred
    is_error_occurred = False

    logging.basicConfig(filename='/tmp/migration_v3.9.x_to_v3.10.x.log', filemode='w',
                        format="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s", datefmt='%H:%M:%S',
                        level=logging.INFO)

    visibility_db = sys.argv[1]
    visibility_host = sys.argv[2]
    platform_db = sys.argv[3]
    platform_host = sys.argv[4]
    opsmx_db = sys.argv[5]
    opsmx_host = sys.argv[6]
    oes_db = sys.argv[7]
    oes_host = sys.argv[8]
    audit_db = sys.argv[9]
    audit_db_host = sys.argv[10]
    port = sys.argv[11]
    db_username = sys.argv[12]
    db_password = sys.argv[13]
    spinnaker_login_id = sys.argv[14]
    spinnaker_password = sys.argv[15]



    logging.info("Using default host url ex:http://github.com")

    # Establishing the visibility db connection
    visibility_conn = psycopg2.connect(database=visibility_db, user=db_username, password=db_password,
                                       host=visibility_host, port=port)
    logging.info("Visibility database connection established successfully")
    visibility_cursor = visibility_conn.cursor()

    # Establishing the platform db connection
    platform_conn = psycopg2.connect(database=platform_db, user=db_username, password=db_password, host=platform_host,
                                     port=port)
    logging.info('Opened platform database connection successfully')
    platform_cursor = platform_conn.cursor()

    # Establishing the opsmx db connection
    opsmxdb_conn = psycopg2.connect(database=opsmx_db, user=db_username, password=db_password, host=opsmx_host,
                                    port=port)
    logging.info("opsmx database connection established successfully")
    opsmxdb_cursor = opsmxdb_conn.cursor()


    # Establishing the opsmx db connection
    oesdb_conn = psycopg2.connect(database=oes_db, user=db_username, password=db_password,
                                  host=oes_host, port=port)
    logging.info("oes(sapor) database connection established successfully")
    oesdb_cursor = oesdb_conn.cursor()

    # Establishing the audit db connection

    audit_conn = psycopg2.connect(database=audit_db, user=db_username, password=db_password,
                                  host=audit_db_host, port=port)
    logging.info("auditdb database connection established successfully")

    audit_cursor = audit_conn.cursor()

    perform_migrate()

