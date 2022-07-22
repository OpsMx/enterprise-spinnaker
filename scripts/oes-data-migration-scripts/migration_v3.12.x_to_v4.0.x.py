import psycopg2
import sys
import subprocess
import json
import logging
import requests


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
        logging.info('Migrating from v3.12.x to v4.0')
        try:
            logging.info("Alter platform db table app_environment")
            print("Alter platform db table app_environment")
            alterAppEnvironmentTable()
        except Exception as e:
            logging.error("Failure at step 1", exc_info=True)
            is_error_occurred = True

        try:
            logging.info("Fetch spinnaker environments details from sapor db")
            print("Fetch spinnaker environments details from sapor db")
            getEnvironmentData()
        except Exception as e:
            logging.error("Failure at step 2", exc_info=True)
            is_error_occurred = True

        try:
            logging.info("Update spinnaker environments Id details in app_environment table")
            print("Update spinnaker environments Id details in app_environment table")
            environmentUpdate()
        except Exception as e:
            logging.error("Failure at step 3", exc_info=True)
            is_error_occurred = True

        try:
            logging.info("Alter platform db table service_gate")
            print("Alter platform db table service_gate")
            alterServiceGateTable()
        except Exception as e:
            logging.error("Failure at step 4", exc_info=True)
            is_error_occurred = True

        try:
            logging.info("Update spinnaker environments Id details in app_environment table")
            print("Update spinnaker environments Id details in app_environment table")
            updateRefId()
        except Exception as e:
            logging.error("Failure at step 5", exc_info=True)
            is_error_occurred = True

        try:
            logging.info("Alter platform db table service_deployments_current")
            print("Alter platform db table service_deployments_current")
            add_columns_in_service_deployment_current()
        except Exception as e:
            logging.error("Failure at step 6", exc_info=True)
            is_error_occurred = True

        try:
            logging.info("Alter autopilot db table userlogfeedback and loganalysis")
            print("Alter autopilot db table userlogfeedback and loganalysis")
            update_autopilot_constraints()
        except Exception as e:
            logging.error("Failure at step 7", exc_info=True)
            is_error_occurred = True

        try:
            logging.info("Update service_deployments_current table sync column data in platform db")
            print("Update service_deployments_current table sync column data in platform db")
            update_sync_status()
        except Exception as e:
            logging.error("Failure at step 8", exc_info=True)
            is_error_occurred = True

        try:
            logging.info("Update cluster name in service_deployments_current table")
            print("Update cluster name in service_deployments_current table")
            pipeline_executions = fetch_pipeline_executions()
            persist_cluster(pipeline_executions)
        except Exception as e:
            logging.error("Failure at step 9", exc_info=True)
            is_error_occurred = True

        try:
            logging.info("Updating Spinnaker existing gate Json in spinnaker")
            print("Updating Spinnaker existing gate Json in spinnaker")
            cookie = login_to_isd()
            processPipelineJsonForExistingGates(cookie)
        except Exception as e:
            logging.error("Failure at step 10", exc_info=True)
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
        print("Exception occurred while migration : ", e)
        logging.error("Exception occurred during migration from v3.12.x to v4.0:", exc_info=True)
        logging.critical(e.__str__(), exc_info=True)
        rollback_transactions()
        exit(1)
    finally:
        close_connections()


def commit_transactions():
    global audit_conn
    try:
        platform_conn.commit()
        oesdb_conn.commit()
        autopilot_conn.commit()
        audit_conn.commit()
        logging.info("Successfully migrated")
    except Exception as e:
        logging.critical("Exception occurred while committing transactions : ", exc_info=True)
        raise e


def close_connections():
    global audit_conn
    try:
        platform_conn.close()
        oesdb_conn.close()
        autopilot_conn.close()
        audit_conn.close()
        if audit_conn is not None:
            audit_conn.close()
    except Exception as e:
        logging.warning("Exception occurred while closing the DB connection : ", exc_info=True)


def rollback_transactions():
    global audit_conn
    try:
        platform_conn.rollback()
        oesdb_conn.rollback()
        autopilot_conn.rollback()
        if audit_conn is not None:
            audit_conn.rollback()
    except Exception as e:
        logging.critical("Exception occurred while rolling back the transactions : ", exc_info=True)
        raise e


def add_columns_in_service_deployment_current():
    try:
        cur_platform.execute(
            "ALTER TABLE service_deployments_current ADD COLUMN IF NOT EXISTS cluster character varying DEFAULT NULL")
        cur_platform.execute(
            "ALTER TABLE service_deployments_current ADD COLUMN IF NOT EXISTS sync character varying DEFAULT NULL")
    except Exception as e:
        logging.critical("Exception occurred while adding columns to service_deployments_current table : ",
                         exc_info=True)
        raise e


def update_sync_status():
    try:
        cur_platform.execute("UPDATE service_deployments_current SET sync = 'OUT_OF_SYNC'")
        logging.info("Successfully updated sync column data in service_deployments_current table")
        print("Successfully updated sync column data in service_deployments_current table")
    except Exception as e:
        print("Exception occurred while updating sync status : ", e)
        logging.error("Exception occurred while updating sync status:", exc_info=True)
        raise e


def persist_cluster(pipeline_executions):
    try:
        logging.info("Migration to update the cluster name")
        print("Migration to update the cluster name")
        for pipeline_execution in pipeline_executions:
            pipeline_execution_json = pipeline_execution[1]
            try:
                details = pipeline_execution_json['details']
                app_name = details['application']
                content = pipeline_execution_json['content']
                execution = content['execution']
                if execution['type'] == 'PIPELINE':
                    pipeline_name = execution['name']
                stages = execution['stages']
                for stage in stages:
                    if stage['type'] == 'deployManifest':
                        context = stage['context']
                        outputs_manifests = context['outputs.manifests']
                        for outputs_manifest in outputs_manifests:
                            if outputs_manifest['kind'] == 'Deployment':
                                metadata = outputs_manifest['metadata']
                                annotations = metadata['annotations']
                                cluster = annotations['moniker.spinnaker.io/cluster']
                                select_data = pipeline_name, app_name
                                cur_platform.execute(
                                    "select a.id as application_id, p.id as pipeline_id from applications a LEFT OUTER JOIN service s ON a.id = s.application_id LEFT OUTER JOIN service_pipeline_map spm ON spm.service_id = s.id LEFT OUTER JOIN pipeline p ON spm.pipeline_id = p.id where p.pipeline_name = %s and a.name = %s",
                                    select_data)
                                records = cur_platform.fetchall()
                                for record in records:
                                    data = cluster, record[0], record[1]
                                    print("updating cluster for the app and pipeline : ", select_data)
                                    print("data : ", data)
                                    cur_platform.execute(
                                        "UPDATE service_deployments_current SET cluster = %s WHERE application_id = %s and pipeline_id = %s",
                                        data)
            except KeyError as ke:
                pass
            except Exception as ex:
                print("Exception in nested catch block : ", ex)
                logging.error("Exception in nested catch block:", exc_info=True)
                raise ex
    except Exception as e:
        print("Exception occurred while persisting the cluster name: ", e)
        logging.error("Exception occurred while persisting the cluster name:", exc_info=True)
        raise e


def fetch_pipeline_executions():
    try:
        logging.info("Fetch pipeline execution data from pipeline_execution_audit_events table under audit db")
        print("Fetch pipeline execution data from pipeline_execution_audit_events table under audit db")
        cur_audit.execute(
            "select id, pipeline_execution_data from pipeline_execution_audit_events where pipeline_execution_data -> 'details' ->> 'type' IN ('orca:pipeline:complete', 'orca:pipeline:failed')")
        return cur_audit.fetchall()
    except Exception as e:
        print("Exception occurred while fetching cluster : ", e)
        logging.error("Exception occurred while fetching cluster:", exc_info=True)
        raise e


def update_autopilot_constraints():
    try:
        cur_autopilot.execute(" ALTER TABLE userlogfeedback ALTER COLUMN logtemplate_id DROP not null ")
        cur_autopilot.execute(" ALTER TABLE loganalysis ALTER COLUMN log_template_opsmx_id DROP not null ")
    except Exception as e:
        print("Exception occurred while  updating script : ", e)
        raise e


def alterAppEnvironmentTable():
    try:
        cur_platform.execute("ALTER TABLE app_environment ADD COLUMN IF NOT EXISTS spinnaker_environment_id int")
        logging.info("Successfully altered app_environment table")
        print("Successfully altered app_environment table")
    except Exception as e:
        print("Exception occurred in alterAppEnvironmentTable while updating script : ", e)
        logging.error("Exception occurred in alterAppEnvironmentTable while updating script: ", exc_info=True)
        raise e


def alterServiceGateTable():
    try:
        cur_platform.execute("ALTER TABLE service_gate ADD COLUMN IF NOT EXISTS ref_id int")
        print("Successfully altered service_gate table")
        logging.info("Successfully altered service_gate table")
    except Exception as e:
        print("Exception occurred in alter service_gate while updating script : ", e)
        logging.error("Exception occurred in alter service_gate while updating script: ", exc_info=True)
        raise e


def getEnvironmentData():
    try:
        logging.info("Fetch environment data from app_environment and map to spinnaker_environment table")
        print("Fetch environment data from app_environment and map to spinnaker_environment table")
        cur_platform.execute("select distinct(environment) from app_environment")
        appEnvironmentNameUnique = [item[0] for item in cur_platform.fetchall()]
        cur_oesdb.execute("select * from spinnaker_environment")
        spinakerEnvName = [item[1] for item in cur_oesdb.fetchall()]
        appEnvironmentNameUniqueTuple = [tuple(x) for x in appEnvironmentNameUnique]
        spinakerEnvNameTuple = [tuple(x) for x in spinakerEnvName]
        appEnvNotInSpinakerEnv = list(set(appEnvironmentNameUniqueTuple) - set(spinakerEnvNameTuple))
        for appEnvNotInSpinakerEnvName in appEnvNotInSpinakerEnv:
            spinInsertData = "INSERT INTO spinnaker_environment (spinnaker_environment) VALUES ({})".format(
                "'" + str("".join(appEnvNotInSpinakerEnvName) + "'"))
            cur_oesdb.execute(spinInsertData)
    except Exception as e:
        print("Exception occurred in fetching environments details while updating script : ", e)
        logging.error("Exception occurred in fetching environments details while updating script :", exc_info=True)
        raise e


def environmentUpdate():
    try:
        cur_oesdb.execute("select * from spinnaker_environment")
        spinakerEnvDatas = cur_oesdb.fetchall()
        if spinakerEnvDatas != None:
            for spinakerEnvData in spinakerEnvDatas:
                platScript = "UPDATE app_environment SET spinnaker_environment_id = {} WHERE environment = {}".format(
                    spinakerEnvData[0], "'" + spinakerEnvData[1] + "'")
                cur_platform.execute(platScript)
        print("Successfully updated the spinnaker_environment_id in app_environment")
        logging.info("Successfully updated the spinnaker_environment_id in app_environment")
    except Exception as e:
        print("Exception occurred while updating environments in app_environment table: ", e)
        logging.error("Exception occurred while updating environments in app_environment table", exc_info=True)
        raise e


def updateRefId():
    try:
        cur_platform.execute(
            "select id, pipeline_json from pipeline where not pipeline_json::jsonb ->> 'stages' = '[]' limit 1")
        pipelineDatas = cur_platform.fetchall()
        for pipelineData in pipelineDatas:
            strpipelineData = """{}""".format(pipelineData[1])
            jsonpipelineData = json.loads(strpipelineData)
            if len(jsonpipelineData["stages"]):
                platScriptdataformGatePipelineMap = "select service_gate_id from gate_pipeline_map WHERE pipeline_id = '{}'".format(
                    pipelineData[0])
                cur_platform.execute(platScriptdataformGatePipelineMap)
                serviceGateIds = cur_platform.fetchall()
                if len(serviceGateIds):
                    for serviceGateId in serviceGateIds:
                        for stageData in jsonpipelineData["stages"]:
                            platScript = "UPDATE service_gate SET ref_id = {} WHERE id = '{}' and gate_name = '{}' and gate_type = '{}' and ref_id is null".format(
                                stageData["refId"], serviceGateId[0], stageData["name"], stageData["type"])
                            cur_platform.execute(platScript)
        print("Successfully updated the ref_id in service_gate")
        logging.info("Successfully updated the ref_id in service_gate")
    except Exception as e:
        print("Exception occurred in updateRefId while updating script : ", e)
        logging.error("Exception occurred in updateRefId while updating script :", exc_info=True)
        raise e


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
                    cur_platform.execute(
                        'select distinct(a.name) as applicationName from applications a left outer join service s on a.id=s.application_id left outer join service_pipeline_map sp on s.id=sp.service_id where sp.pipeline_id =' + str(
                            pipelineId))
                    applicationName = cur_platform.fetchone()
                    if applicationName is not None:
                        applicationName = str(applicationName[0])
                        print("GateId: {},pipelineId: {} ,applicationName: {} ,audit_events_table_id :{}".format(gateId,
                                                                                                                 pipelineId,
                                                                                                                 applicationName,
                                                                                                                 audit_events_table_id))
                        fetchJsonAndUpdate(audit_events_table_id, applicationName, jsonData)
    except Exception as e:
        print("Exception occurred while  updating script : ", e)
        raise e


def listData(results):
    resultData = {}
    for result in results:
        resultData = result
    return resultData


def fetchJsonAndUpdate(audit_events_table_id, applicationName, jsonData):
    try:
        oldAppName = jsonData['auditData']['details']['application']
        if oldAppName is not applicationName:
            updateJson = json.loads(json.dumps(jsonData).replace(oldAppName, applicationName))
            updateApprovalAuditJson(audit_events_table_id, updateJson)
    except Exception as e:
        print("Exception occurred while mapping application name : ", e)
        raise e


def updateApprovalAuditJson(audit_events_table_id, updateJson):
    try:
        updatedConfig = "'" + str(json.dumps(updateJson)) + "'"
        cur_audit.execute(
            'update audit_events set data =' + updatedConfig + ' where id ={}'.format(audit_events_table_id))
    except Exception as e:
        print("Exception occurred while updating update json : ", e)
        raise e


def processPipelineJsonForExistingGates(cookie):
    try:
        cur_platform.execute(
            "select s.application_id, sp.service_id, g.id, g.gate_name, g.gate_type, g.payload_constraint, gp.pipeline_id, a.name from "
            "service_gate g left outer join gate_pipeline_map gp on g.id = gp.service_gate_id left outer join service_pipeline_map sp on gp.pipeline_id = sp.pipeline_id "
            "left outer join service s on sp.service_id=s.id left outer join applications a on s.application_id = a.id where a.source = 'Spinnaker' ;")
        records = cur_platform.fetchall()
        for record in records:
            applicationId = record[0]
            serviceId = record[1]
            gateId = record[2]
            gateName = record[3]
            gateType = record[4]
            pipelineId = record[6]
            appName = record[7]
            env_json = formEnvJson(gateId)
            payloadConstraint = formPayloadConstraint()
            stageJson = ""
            if gateType.__eq__("policy"):
                stageJson = policyGateProcess(applicationId, serviceId, gateId, gateName, gateType,
                                              payloadConstraint, pipelineId, env_json)
            elif gateType.__eq__("verification"):
                stageJson = verificationGateProcess(applicationId, serviceId, gateId, gateName, gateType,
                                                    payloadConstraint, pipelineId, env_json, cookie)
            elif gateType.__eq__("approval"):
                stageJson = approvalGateProcess(applicationId, serviceId, gateId, gateName, gateType,
                                                payloadConstraint, pipelineId, env_json, cookie)
            if stageJson is not None:
                stageJson["application"] = appName
                logging.info("StageJson is : ", stageJson)
                pipelineJson = updatePipelineJson(pipelineId, stageJson)
                postingGateJson(pipelineJson, cookie)
    except Exception as e:
        print("Exception occurred while processing the pipeline json for existing gates : ", e)
        logging.error("Exception occurred while processing the pipeline json for existing gates :", exc_info=True)
        raise e


def formEnvJson(gateId):
    try:
        cur_platform.execute(
            "select ae.spinnaker_environment_id , ae.environment from app_environment ae left outer join service_gate sg on ae.id=sg.app_environment_id where sg.id=" + str(
                gateId))
        spinnakerEnvironments = cur_platform.fetchone()
        spinnakerEnvironmentId = spinnakerEnvironments[0]
        spinnakerEnvironmentName = spinnakerEnvironments[1]
        env_json = {
            "id": spinnakerEnvironmentId,
            "spinnakerEnvironment": str(spinnakerEnvironmentName)
        }
        logging.info("Fetched environment information for GateId :" + str(gateId) + "  :" + str(env_json))
        return env_json
    except Exception as e:
        print("Exception occurred while forming environment json for existing gates : ", e)
        logging.error("Exception occurred while forming environment json for existing gates :", exc_info=True)
        raise e


def formPayloadConstraint():
    try:
        payloadConstraint = [{
            "connectorType": "PayloadConstraints",
            "helpText": "Payload Constraints",
            "isMultiSupported": bool(True),
            "label": "Payload Constraints",
            "selectInput": bool(False),
            "supportedParams": [{
                "helpText": "Key",
                "label": "Key",
                "name": "label",
                "type": "string"
            }, {
                "helpText": "Value",
                "label": "Value",
                "name": "value",
                "type": "string"
            }],
            "values": []
        }]
        logging.info("Payload Json :" + str(payloadConstraint))
        return payloadConstraint
    except Exception as e:
        print("Exception occurred while processing the payload constraint json for existing gates : ", e)
        logging.error("Exception occurred while processing the payload constraint json for existing gates :",
                      exc_info=True)
        raise e


def policyGateProcess(applicationId, serviceId, gateId, gateName, gateType, payloadConstraint, pipelineId,
                      env_json_formatted):
    try:
        logging.info("process policy gate json for application Id: " + str(applicationId) + " ,serviceId: " + str(
            serviceId) + " ,gateId: " + str(gateId))
        parameters = policyParametersDataFilter(gateId, env_json_formatted, payloadConstraint)
        policy_pipeline_json = {
            "applicationId": applicationId,
            "isNew": bool(True),
            "name": str(gateName),
            "parameters": parameters,
            "pipelineId": pipelineId,
            "serviceId": serviceId,
            "type": str(gateType),
            "refId": "",
            "requisiteStageRefIds": []
        }
        return policy_pipeline_json
    except Exception as e:
        print("Exception occurred while formatting the policy pipeline json for existing gates : ", e)
        logging.error("Exception occurred while formatting the policy pipeline json for existing gates :",
                      exc_info=True)
        raise e


def policyParametersDataFilter(gateId, env_json_formatted, gateSecurity):
    try:
        cur_oesdb.execute(
            "select policy_id,policy_name from policy_gate where gate_id=" + str(gateId))
        policy = cur_oesdb.fetchone()
        policyId = policy[0]
        policyName = policy[1]
        approval_pipeline_json = {
            "customEnvironment": "",
            "environment": env_json_formatted,
            "gateSecurity": gateSecurity,
            "policyId": policyId,
            "policyName": str(policyName)
        }
        return approval_pipeline_json
    except Exception as e:
        print("Exception occurred while processing the policy parameter json: ", e)
        logging.error("Exception occurred while processing the policy parameter json:", exc_info=True)
        raise e


def verificationParametersDataFilter(applicationId, gateId, env_json_formatted, cookie):
    try:
        logAndMetricInfoRes = getLogAndMetricName(applicationId, gateId, cookie)
        verification_pipeline_json = {
            "baselineRealTime": bool(False),
            "baselinestarttime": "",
            "canaryRealTime": bool(False),
            "canaryresultscore": "",
            "canarystarttime": "",
            "customEnvironment": "",
            "environment": env_json_formatted,
            "gateSecurity": [{
                "connectorType": "PayloadConstraints",
                "helpText": "Payload Constraints",
                "isMultiSupported": bool(True),
                "label": "Payload Constraints",
                "selectInput": bool(False),
                "supportedParams": [{
                    "helpText": "Key",
                    "label": "Key",
                    "name": "label",
                    "type": "string"
                }, {
                    "helpText": "Value",
                    "label": "Value",
                    "name": "value",
                    "type": "string"
                }],
                "values": []
            }],
            "lifetime": "",
            "logTemplate": logAndMetricInfoRes["logTemplateName"],
            "metricTemplate": logAndMetricInfoRes["metricTemplateName"],
            "minicanaryresult": ""
        }
        return verification_pipeline_json
    except Exception as e:
        print("Exception occurred while processing the verification pipeline json for existing gates : ", e)
        logging.error("Exception occurred while processing the verification pipeline json for existing gates :",
                      exc_info=True)
        raise e


def getLogAndMetricName(applicationId, gateId, cookie):
    try:
        URL = isd_gate_url + "/autopilot/api/v3/applications/{}/gates/{}".format(applicationId, gateId)
        logging.info(URL)
        headers = {'cookie': cookie, 'x-spinnaker-user': isd_admin_username}
        request = requests.get(url=URL, headers=headers)
        return request.json()
    except Exception as e:
        print("Exception occurred while fetching log and metric template name: ", e)
        logging.error("Exception occurred while fetching log and metric template name:", exc_info=True)
        raise e


def verificationGateProcess(applicationId, serviceId, gateId, gateName, gateType, payloadConstraint, pipelineId,
                            env_json_formatted, cookie):
    try:
        logging.info("process verification gate json for application Id: " + str(applicationId) + " ,serviceId: " + str(
            serviceId) + " ,gateId: " + str(gateId))
        parameters = verificationParametersDataFilter(applicationId, gateId, env_json_formatted, cookie)
        if (parameters is not None):
            verification_pipeline_json = {
                "applicationId": applicationId,
                "isNew": bool(True),
                "name": str(gateName),
                "parameters": parameters,
                "pipelineId": pipelineId,
                "serviceId": serviceId,
                "type": str(gateType),
                "refId": "",
                "requisiteStageRefIds": []
            }
            return verification_pipeline_json
    except Exception as e:
        print("Exception occurred while formatting the verification pipeline json for existing gates : ", e)
        logging.error("Exception occurred while formatting the verification pipeline json for existing gates :",
                      exc_info=True)
        raise e


def approvalGateProcess(applicationId, serviceId, gateId, gateName, gateType, payloadConstraint, pipelineId, env_json,
                        cookie):
    try:
        logging.info("process approval gate json for application Id: " + str(applicationId) + " ,serviceId: " + str(
            serviceId) + " ,gateId: " + str(gateId))
        parameters = approvalParametersDataFilter(gateId, env_json, payloadConstraint, cookie)
        approval_pipeline_json = {
            "applicationId": applicationId,
            "isNew": bool(True),
            "name": str(gateName),
            "parameters": parameters,
            "pipelineId": pipelineId,
            "serviceId": serviceId,
            "type": str(gateType),
            "refId": "",
            "requisiteStageRefIds": []
        }
        return approval_pipeline_json
    except Exception as e:
        print("Exception occurred while processing the pipeline json for existing gates : ", e)
        logging.error("Exception occurred while processing the pipeline json for existing gates :", exc_info=True)
        raise e


def approvalParametersDataFilter(gateId, env_json_formatted, payloadConstraint, cookie):
    try:
        approvalGroupsData = getApprovalGroupsDataFilter(gateId, cookie)
        automatedApproval = getAutomatedApproval(gateId)
        connectors = getConnectorsDataFilter(gateId, cookie)
        selectedConnectors = getSelectedConnectors(gateId, cookie)
        approval_pipeline_json = {
            "approvalGroups": approvalGroupsData,
            "automatedApproval": automatedApproval,
            "connectors": connectors,
            "customEnvironment": "",
            "environment": env_json_formatted,
            "gateSecurity": payloadConstraint,
            "selectedConnectors": selectedConnectors
        }
        return approval_pipeline_json
    except Exception as e:
        print("Exception occurred while processing the approval pipeline json for existing gates : ", e)
        logging.error("Exception occurred while processing the approval pipeline json for existing gates :",
                      exc_info=True)
        raise e


def getApprovalGroupsName(gateId, cookie):
    try:
        URL = isd_gate_url + "/platformservice/v6/usergroups/permissions/resources/{}".format(gateId)
        logging.info(URL)
        PARAMS = {'featureType': 'APPROVAL_GATE'}
        headers = {'cookie': cookie, 'x-spinnaker-user': isd_admin_username}
        request = requests.get(url=URL, headers=headers, params=PARAMS)
        return request.json()
    except Exception as e:
        print("Exception occurred while fetching usergroups permission resources: ", e)
        logging.error("Exception occurred while fetching usergroups permission resources:", exc_info=True)
        raise e


def getApprovalGroupsDataJson(cookie):
    try:
        URL = isd_gate_url + "/platformservice/v2/usergroups"
        logging.info(URL)
        headers = {'cookie': cookie}
        request = requests.get(url=URL, headers=headers)
        return request.json()
    except Exception as e:
        print("Exception occurred while fetching approval groups data : ", e)
        logging.error("Exception occurred while fetching approval groups data:", exc_info=True)
        raise e


def getApprovalGroupsDataFilter(gateId, cookie):
    dataList = []
    getApprovalGroupsNamesData = getApprovalGroupsName(gateId, cookie)
    getApprovalGroupsData = getApprovalGroupsDataJson(cookie)
    if ('userGroupName' in getApprovalGroupsNamesData):
        getUserGroupsName = getApprovalGroupsNamesData['userGroupName']
    else:
        return dataList
    if ('approvalGroups' in getApprovalGroupsData):
        getApprovalGroupsData = getApprovalGroupsData['approvalGroups']
    for getApprovalGroupData in getApprovalGroupsData:
        if getUserGroupsName == getApprovalGroupData['userGroupName']:
            dataList.append(getApprovalGroupData)
    logging.info("Fetched approval groups data for gateId- " + str(gateId) + str(dataList))
    return dataList


def getAutomatedApproval(gateId):
    try:
        dataList = []
        data = gateId
        cur_visibility.execute(
            "select policy_id,policy_name from approval_gate_policy ap left outer join approval_service_gate_map sm on ap.approval_gate_id=sm.approval_gate_id where sm.service_gate_id=%s",
            [data])
        policyDatas = cur_visibility.fetchall()
        if policyDatas is not None:
            for policyData in policyDatas:
                automatedApprovalData = {
                    "policyId": policyData[0],
                    "policyName": policyData[1]
                }
                dataList.append(automatedApprovalData)
        else:
            automatedApprovalData = {
                "policyId": None,
                "policyName": ""
            }
            dataList.append(automatedApprovalData)
        return dataList
    except Exception as e:
        print("Exception occurred while processing the getAutomatedApproval data : ", e)
        logging.error("Exception occurred while processing the getAutomatedApproval data:", exc_info=True)
        raise e


def getConnectorsDataFilter(gateId, cookie):
    try:
        logging.info("Fetching connector data for gateId: " + str(gateId))
        dataList = []
        getConnectorsNames = getConnectorsConfiguredNames(gateId, cookie)
        if ('error' in getConnectorsNames):
            return dataList
        getConnectorsNameDatas = getAllConnectorsNameData(cookie)
        for getConnectorsName in getConnectorsNames:
            connectorType = getConnectorsName['connectorType']
            accountName = getConnectorsName['accountName']
            for getConnectorsNameData in getConnectorsNameDatas:
                if 'connectorType' in getConnectorsNameData and getConnectorsNameData[
                    'connectorType'] == connectorType and 'accountName' in getConnectorsNameData and \
                        getConnectorsNameData[
                            'accountName'] == accountName:
                    data = gateId
                    cur_visibility.execute(
                        "select key,value,connector_type from approval_gate_parameter where approval_gate_instance_id=(select id from approval_gate_instance where approval_gate_id=%s order by id desc limit 1);",
                        data)
                    visibilityDatas = cur_visibility.fetchall()
                    getConnectorsNameData["values"] = visibilityDatas
                    dataList.append(getConnectorsNameData)
        return dataList
    except Exception as e:
        print("Exception occurred while processing the connector data : ", e)
        logging.error("Exception occurred while processing the connector data :", exc_info=True)
        raise e


def getConnectorsConfiguredNames(gateId, cookie):
    try:
        URL = isd_gate_url + "/visibilityservice/v1/approvalGates/{}/toolConnectors".format(gateId)
        logging.info(URL)
        headers = {'cookie': cookie}
        request = requests.get(url=URL, headers=headers)
        return request.json()
    except Exception as e:
        print("Exception occurred while fetching connector configured names : ", e)
        logging.error("Exception occurred while fetching connector configured names:", exc_info=True)
        raise e


def getAllConnectorsNameData(cookie):
    try:
        URL = isd_gate_url + "/visibilityservice/v6/getAllConnectorFields"
        logging.info(URL)
        headers = {'cookie': cookie}
        request = requests.get(url=URL, headers=headers)
        return request.json()
    except Exception as e:
        print("Exception occurred while fetching all connectors fields : ", e)
        logging.error("Exception occurred while fetching all connectors fields:", exc_info=True)
        raise e


def getSelectedConnectors(gateId, cookie):
    try:
        logging.info("Formatting selected connectors for gateId: " + str(gateId))
        getConnectorsNames = getConnectorsConfiguredNames(gateId, cookie)
        defaultData = {
            "connectorType": "Connectors *",
            "helpText": "List of Connectors Configured",
            "isMultiSupported": bool(True),
            "label": "Connectors *",
            "selectInput": bool(True),
            "supportedParams": [
                {
                    "helpText": "Select Data Sources relevant to this pipeline",
                    "label": "Connector",
                    "name": "connector",
                    "type": "string"
                },
                {
                    "helpText": "Select the account of interest in the configured data source ",
                    "label": "Account",
                    "name": "account",
                    "type": "string"
                }
            ]}
        mainData = []
        for getConnectorsName in getConnectorsNames:
            if ('connectorType' in getConnectorsName and 'accountName' in getConnectorsName):
                tempData = {"connector": getConnectorsName['connectorType'],
                            "account": getConnectorsName['accountName']}
                mainData.append(tempData)
        defaultData["values"] = mainData
        return defaultData
    except Exception as e:
        print("Exception occurred while processing the pipeline json for existing gates : ", e)
        logging.error("Exception occurred while processing the pipeline json for existing gates ", exc_info=True)
        raise e


def verifySpinnakerConfigurationAndGetURL():
    try:
        cur = oesdb_conn.cursor()
        cur.execute("select id,url from spinnaker;")
        result = cur.fetchall()
        if result is None:
            raise Exception("Please configure spinnaker before proceeding with audit migration")
    except Exception as e:
        print("Exception occurred while fetching spinnaker configuration from oes db: ", e)
        logging.error("Exception occurred while fetching spinnaker configuration from oes db", exc_info=True)
        raise e


def updatePipelineJson(pipelineId, stageJson):
    try:
        logging.info("updating pipeline Json for pipelineId: " + str(pipelineId))
        if stageJson is not None and len(stageJson) > 0:
            cur_platform.execute("SELECT id, pipeline_json from pipeline where id =" + str(pipelineId))
            result = cur_platform.fetchall()
            if result is not None:
                pipelineJson = formPipelineJson(pipelineId, json.loads(result[0][1]), stageJson)
                if pipelineJson is not None:
                    updatePipelineJsonInPlatformDb(pipelineJson, pipelineId)
                return pipelineJson
    except Exception as e:
        print("Exception occurred while updating pipeline Json: ", e)
        logging.error("Exception occurred while updating pipeline Json", exc_info=True)
        raise e


def updatePipelineJsonInPlatformDb(pipelineJson, pipelineId):
    try:
        update_data = json.dumps(pipelineJson), pipelineId
        logging.info("Updated pipeline data to update unified url : \n" + ''.join(str(update_data)) + '\n')
        cur_platform.execute("UPDATE pipeline SET pipeline_json = %s WHERE id = %s", update_data)
    except Exception as e:
        print("Exception occurred while updating pipeline Json in platform db: ", e)
        logging.error("Exception occurred while updating pipeline Json in platform db ", exc_info=True)
        raise e


def formPipelineJson(pipelineId, dbPipelineJson, stageJson):
    try:
        if dbPipelineJson is not None and len(dbPipelineJson) > 0:
            stages = dbPipelineJson["stages"]
            updated_stages = []
            for stage in stages:
                try:
                    dbPipelineGateName = stage["name"]
                    newsPipelineGateName = stageJson["name"]
                    dbPipelineGateType = stage["type"]
                    newsPipelineGateType = stage["type"]
                    if dbPipelineGateName.__eq__(newsPipelineGateName) and dbPipelineGateType.__eq__(
                            newsPipelineGateType):
                        stageJson["refId"] = stage["refId"]
                        stageJson["requisiteStageRefIds"] = stage["requisiteStageRefIds"]
                        if newsPipelineGateType.__eq__("verification"):
                            stageJson["parameters"]["baselinestarttime"] = stage["parameters"]["baselinestarttime"]
                            stageJson["parameters"]["canaryresultscore"] = stage["parameters"]["canaryresultscore"]
                            stageJson["parameters"]["canarystarttime"] = stage["parameters"]["canarystarttime"]
                            stageJson["parameters"]["lifetime"] = stage["parameters"]["lifetime"]
                            stageJson["parameters"]["minicanaryresult"] = stage["parameters"]["minicanaryresult"]
                        stage = stageJson
                except KeyError as ke:
                    print("Exception occurred while formatting pipeline Json to update in db: ")
                    logging.error("Exception occurred while formatting pipeline Json to update in db: ", exc_info=True)
                    raise ke
                updated_stages.append(stage)

            dbPipelineJson["stages"] = updated_stages
            return dbPipelineJson
    except Exception as e:
        print("Exception occurred while formatting pipeline Json to update in db: ", e)
        logging.error("Exception occurred while formatting pipeline Json to update in db", exc_info=True)
        raise e


def postingGateJson(pipelineJson, cookie):
    try:
        api_url = isd_gate_url + "/oes/appOnboarding/spinnaker/pipeline/stage"
        logging.info(api_url)
        headers = {'Content-Type': 'application/json', 'cookie': cookie, 'x-user-cookie': cookie,
                   'x-spinnaker-user': isd_admin_username}
        response = requests.post(url=api_url, headers=headers, data=json.dumps(pipelineJson))
        logging.info("The response status is: " + str(response.status_code))
        if (response.status_code == 200 | response.status_code == 201):
            response.info("Successfully added stage! The response is:\n" + str(response.content) + '\n')
        else:
            logging.info("Failed to add stage; The response is:\n" + str(response.content) + '\n')
    except Exception as e:
        print("Exception occurred while posting gate: ", e)
        logging.error("Exception occurred while posting gate", exc_info=True)
        raise e


def login_to_isd():
    try:
        cookie = ""
        cmd = "curl -vvv -X POST '" + isd_gate_url + "/login?username=" + isd_admin_username + "&password=" + isd_admin_password + "&submit=Login'"
        output = subprocess.getoutput(cmd=cmd)
        output = output.replace(isd_admin_username, "***").replace(isd_admin_password, "***")
        logging.info(f"Output for ISD login : {output}")
        components = output.split("<")
        for comp in components:
            if comp.__contains__("set-cookie") or comp.__contains__("Set-Cookie"):
                cookie = comp.split(":")[1].strip()
        return cookie
    except Exception as e:
        print("Exception occurred while logging in to ISD : ", e)
        logging.error("Exception occurred while logging in to ISD : ", exc_info=True)
        raise e


if __name__ == '__main__':
    n = len(sys.argv)

    if n != 17:
        print(
            "Please pass valid 16 arguments <platform_db-name> <platform_host> <oes-db-name> <oes-db-host> <autopilot-db-name> <autopilot-db-host> <audit_db-name> <audit-db-host> <visibility_db-name> <visibility-db-host> "
            "<db-port> <user-name> <password> <isd-gate-url> <isd-admin-username> <isd-admin-password> ")
        exit(1)

    global is_error_occurred
    is_error_occurred = False

    logging.basicConfig(filename='/tmp/migration_v3.12.x_to_v4.0.log', filemode='w',
                        format="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s", datefmt='%H:%M:%S',
                        level=logging.INFO)

    platform_db = sys.argv[1]
    platform_host = sys.argv[2]
    oes_db = sys.argv[3]
    oes_host = sys.argv[4]
    autopilot_db = sys.argv[5]
    autopilot_host = sys.argv[6]
    audit_db = sys.argv[7]
    audit_host = sys.argv[8]
    visibility_db = sys.argv[9]
    visibility_host = sys.argv[10]
    port = sys.argv[11]
    user_name = sys.argv[12]
    password = sys.argv[13]
    isd_gate_url = sys.argv[14]
    isd_admin_username = sys.argv[15]
    isd_admin_password = sys.argv[16]

    # Establishing the platform db connection
    platform_conn = psycopg2.connect(database=platform_db, user=user_name, password=password, host=platform_host,
                                     port=port)
    print('Opened platform database connection successfully')

    # Establishing the oesdb db connection
    oesdb_conn = psycopg2.connect(database=oes_db, user=user_name, password=password,
                                  host=oes_host, port=port)
    print("Sapor database connection established successfully")

    # Establishing the opsmx db connection
    autopilot_conn = psycopg2.connect(database=autopilot_db, user=user_name, password=password, host=autopilot_host
                                      , port=port)
    print("autopilot database connection established successfully")

    # Establishing the audit db connection
    audit_conn = psycopg2.connect(database=audit_db, user=user_name, password=password, host=audit_host, port=port)
    print('Opened audit database connection successfully')

    # Establishing the visibility db connection
    visibility_conn = psycopg2.connect(database=visibility_db, user=user_name, password=password, host=visibility_host,
                                       port=port)
    print("Visibility database connection established successfully")

    cur_platform = platform_conn.cursor()
    cur_oesdb = oesdb_conn.cursor()
    cur_autopilot = autopilot_conn.cursor()
    cur_audit = audit_conn.cursor()
    cur_visibility = visibility_conn.cursor()

    perform_migration()

