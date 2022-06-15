import psycopg2
import sys
import datetime
import json


def perform_migration():
    try:
        getEnvironmentData()
        #alterAppEnvironmentTable()
        environmentUpdate()
        updateRefId()
        platform_conn.commit()
        print("successfully migrated platform db")
        oesdb_conn.commit()
        print("successfully migrated oesdb")
        update_autopilot_constraints()
        autopilot_conn.commit()
        print("successfully migrated autopilot db")

    except Exception as e:
        print("Exception occurred while migration : ", e)
        platform_conn.rollback()
        oesdb_conn.rollback()
        autopilot_conn.rollback()
    finally:
        platform_conn.close()
        oesdb_conn.close()
        autopilot_conn.close()


def update_autopilot_constraints():
    try:
        cur_autopilot.execute(" ALTER TABLE userlogfeedback ALTER COLUMN logtemplate_id DROP not null ")
        cur_autopilot.execute(" ALTER TABLE loganalysis ALTER COLUMN log_template_opsmx_id DROP not null ")
    except Exception as e:
        print("Exception occured while  updating script : ", e)
        raise e


def alterAppEnvironmentTable():
    try:
        cur_platform.execute("ALTER TABLE app_environment ADD COLUMN IF NOT EXISTS spinnaker_environment_id int")
        print("Successfully altered app_environment table")
    except Exception as e:
        print("Exception occured in alterAppEnvironmentTable while updating script : ", e)
        raise e


def getEnvironmentData():
    try:
        cur_platform.execute("select distinct(environment) from app_environment")
        appEnvironmentNameUnique = [item[0] for item in cur_platform.fetchall()]
        cur_oesdb.execute("select * from spinnaker_environment")
        spinakerEnvName = [item[1] for item in cur_oesdb.fetchall()]
        appEnvironmentNameUniqueTuple = [tuple(x) for x in appEnvironmentNameUnique]
        spinakerEnvNameTuple = [tuple(x) for x in spinakerEnvName]
        appEnvInSpinakerEnv =  list(set(appEnvironmentNameUniqueTuple) & set(spinakerEnvNameTuple))
        appEnvNotInSpinakerEnv = list(set(appEnvironmentNameUniqueTuple) - set(spinakerEnvNameTuple))
        for appEnvNotInSpinakerEnvName in appEnvNotInSpinakerEnv:
            spinInsertData = "INSERT INTO spinnaker_environment (spinnaker_environment) VALUES ({})".format("'"+str("".join(appEnvNotInSpinakerEnvName)+"'"))
            # print(spinInsertData)
            cur_oesdb.execute(spinInsertData)
    except Exception as e:
        print("Exception occured in alterAppEnvironmentTable while updating script : ", e)
        raise e


def environmentUpdate():
    try:
        cur_oesdb.execute("select * from spinnaker_environment")
        spinakerEnvDatas = cur_oesdb.fetchall()
        if spinakerEnvDatas != None:
            for spinakerEnvData in spinakerEnvDatas:
                platScript = "UPDATE app_environment SET spinnaker_environment_id = {} WHERE environment = {}".format(spinakerEnvData[0], "'"+spinakerEnvData[1]+"'")
                # print(platScript)
                cur_platform.execute(platScript)
        print("Successfully updated the spinnaker_environment_id in app_environment")
    except Exception as e:
        print("Exception occured in environmentUpdate while updating script : ", e)
        raise e

def updateRefId():
    try:
        cur_platform.execute("select id, pipeline_json from pipeline where not pipeline_json::jsonb ->> 'stages' = '[]' limit 1")
        pipelineDatas = cur_platform.fetchall()
        for pipelineData in pipelineDatas:
            strpipelineData = """{}""".format(pipelineData[1])
            jsonpipelineData = json.loads(strpipelineData)
            if len(jsonpipelineData["stages"]):
                platScriptdataformGatePipelineMap= "select service_gate_id from gate_pipeline_map WHERE pipeline_id = '{}'".format(pipelineData[0])
                cur_platform.execute(platScriptdataformGatePipelineMap)
                serviceGateIds = cur_platform.fetchall()
                if len(serviceGateIds):
                    for serviceGateId in serviceGateIds:
                        # print(serviceGateId[0])
                        for stageData in jsonpipelineData["stages"]:
                            platScript = "UPDATE service_gate SET ref_id = {} WHERE id = '{}' and gate_name = '{}' and gate_type = '{}' and ref_id is null".format(stageData["refId"], serviceGateId[0],stageData["name"], stageData["type"])
                            cur_platform.execute(platScript)
        print("Successfully updated the ref_id in service_gate")
    except Exception as e:
        print("Exception occured in updateRefId while updating script : ", e)
        raise e



if __name__ == '__main__':
    n = len(sys.argv)

    if n != 8:
        print(
            "Please pass valid 7 arguments <platform_db-name> <platform_host> <oes-db-name> <oes-db-host> <db-port> <user-name> <password>")

    platform_db = sys.argv[1]
    platform_host = sys.argv[2]
    oes_db = sys.argv[3]
    oes_host = sys.argv[4]
    autopilot_db = sys.argv[5]
    autopilot_host = sys.argv[6]
    port = sys.argv[7]
    user_name = sys.argv[8]
    password = sys.argv[9]

    # Establishing the platform db connection
    platform_conn = psycopg2.connect(database=platform_db, user=user_name, password=password, host=platform_host, port=port)
    print('Opened platform database connection successfully')

    # Establishing the oesdb db connection
    oesdb_conn = psycopg2.connect(database=oes_db, user=user_name, password=password,
                                  host=oes_host, port=port)
    print("Sapor database connection established successfully")

    # Establishing the opsmx db connection
    autopilot_conn = psycopg2.connect(database=autopilot_db, user=user_name, password=password, host=autopilot_host
                                      , port=port)
    print("autopilot database connection established successfully")
    cur_platform = platform_conn.cursor()
    cur_oesdb = oesdb_conn.cursor()
    cur_autopilot = autopilot_conn.cursor()
    perform_migration()