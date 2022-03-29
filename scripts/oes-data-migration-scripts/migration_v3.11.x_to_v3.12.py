import psycopg2
import sys
import datetime
from tqdm import tqdm
import requests
import json


def perform_migration():
    try:
        for step in tqdm(range(17), desc="Migrating from v3.11 to v3.12..."):
            if step == 0:
                drop_table_user_group_permission_3_11()
            elif step == 1:
                drop_table_role_user_group()
            elif step == 2:
                drop_table_role_feature_permission()
            elif step == 3:
                drop_table_role()
            elif step == 4:
                drop_table_permission_3_11()
            elif step == 5:
                policies = get_policy()
            elif step == 6:
                migrate_policy(policies)
            elif step == 7:
                cloud_providers = get_cloud_provider()
            elif step == 8:
                migrate_cloud_providers(cloud_providers)
            elif step == 9:
                agents = get_agent()
            elif step == 10:
                migrate_agents(agents)
            elif step == 11:
                user_group_permissions = get_user_group_permission()
            elif step == 12:
                migrate_user_group_permission(user_group_permissions)
            elif step == 13:
                gate_pipeline_maps = get_gate_pipeline_map()
            elif step == 14:
                update_pipeline_with_unified_url(gate_pipeline_maps)
            elif step == 15:
                platform_conn.commit()
            elif step == 16:
                updateautopilotconstraints()
                autopilot_conn.commit()

        print("Successfully migrated to v3.12")
    except Exception as e:
        print("Exception occured while migration : ", e)
        platform_conn.rollback()
        autopilot_conn.rollback()
    finally:
        platform_conn.close()
        oesdb_conn.close()
        autopilot_conn.close()


def get_gate_pipeline_map():
    try:
        cur = platform_conn.cursor()
        cur.execute("SELECT pipeline_id, service_gate_id FROM gate_pipeline_map")
        return cur.fetchall()
    except Exception as e:
        print("Exception occurred while fetching gate pipeline map details : ", e)
        raise e


def update_pipeline_with_unified_url(gate_pipeline_maps):
    try:
        for gate_pipeline_map in gate_pipeline_maps:
            pipeline_id = gate_pipeline_map[0]
            gate_id = gate_pipeline_map[1]
            url = host_url + "/dashboardservice/v3/pipelines/" + str(pipeline_id) + "/gates/" + str(gate_id)
            headers = {'Cookie': cookie}
            response = requests.get(url=url, headers=headers)
            gate_response = json.loads(response.content)
            update_gate(gate_response, pipeline_id, gate_id)
    except Exception as e:
        print("Exception occurred while updating the pipeline with unified url : ", e)
        raise e


def update_gate(gate_response, pipeline_id, gate_id):
    try:
        cur = platform_conn.cursor()
        cur.execute("SELECT service_id FROM service_pipeline_map where pipeline_id = " + str(pipeline_id))
        service_id = cur.fetchone()[0]
        try:
            if gate_response["dependsOn"] is None:
                gate_response["dependsOn"] = []
        except KeyError as e:
            gate_response["dependsOn"] = []

        try:
            if gate_response["payloadConstraint"] is None:
                gate_response["payloadConstraint"] = []
        except KeyError as e:
            gate_response["payloadConstraint"] = []

        req_payload = {
            "applicationId": gate_response["applicationId"],
            "approvalGateId": gate_response["approvalGateId"],
            "approvalGatePolicies": gate_response["approvalGatePolicies"],
            "isAutomatedApproval": gate_response["isAutomatedApproval"],
            "gateId": gate_response["gateId"],
            "gateName": gate_response["gateName"],
            "dependsOn": gate_response["dependsOn"],
            "environmentId": gate_response["environmentId"],
            "gateType": gate_response["gateType"],
            "refId": gate_response["refId"],
            "serviceId": service_id,
            "pipelineId": pipeline_id,
            "payloadConstraint": gate_response["payloadConstraint"]
        }
        url = host_url + "/dashboardservice/v4/pipelines/" + str(pipeline_id) + "/gates/" + str(gate_id)
        headers = {'Cookie': cookie,
                   'Content-Type': 'application/json'}
        req_payload = json.dumps(req_payload)

        requests.put(url=url, data=req_payload, headers=headers)
    except Exception as e:
        print("Exception occurred while updating gate : ", e)
        raise e


def updateautopilotconstraints():
    try:
        cur = autopilot_conn.cursor()
        cur.execute(" ALTER TABLE serviceriskanalysis  DROP CONSTRAINT IF EXISTS fkmef9blhpcxhcj431kcu52nm1e ")
        print("Successfully dropped constraint serviceriskanalysis table in autopilot db")
        cur.execute(" ALTER TABLE servicegate  DROP CONSTRAINT IF EXISTS uk_lk3buh56ebai2gycw560j2oxm ")
        print("Successfully dropped constraint servicegate table in autopilot db")
        cur.execute(" ALTER TABLE canaryanalysis ALTER COLUMN metric_template_opsmx_id DROP not null ")
        print("Successfully dropped not null constraint canaryanalysis table in autopilot db")
    except Exception as e:
        print("Exception occured while  updating script : ", e)
        raise e


def drop_table_permission_3_11():
    try:
        cur = platform_conn.cursor()
        cur.execute("DROP TABLE IF EXISTS permission_3_11")
    except Exception as e:
        print("Exception occurred while dropping the table permission_3_11 from platformdb : ", e)
        raise e


def drop_table_user_group_permission_3_11():
    try:
        cur = platform_conn.cursor()
        cur.execute("DROP TABLE IF EXISTS user_group_permission_3_11")
    except Exception as e:
        print("Exception occurred while dropping the table user_group_permission_3_11 from platformdb : ", e)
        raise e


def drop_table_role_feature_permission():
    try:
        cur = platform_conn.cursor()
        cur.execute("DROP TABLE IF EXISTS role_feature_permission")
    except Exception as e:
        print("Exception occurred while dropping the table role_feature_permission : ", e)
        raise e


def drop_table_role_user_group():
    try:
        cur = platform_conn.cursor()
        cur.execute("DROP TABLE IF EXISTS role_user_group")
    except Exception as e:
        print("Exception occurred while dropping the table role_user_group : ", e)
        raise e


def drop_table_role():
    try:
        cur = platform_conn.cursor()
        cur.execute("DROP TABLE IF EXISTS role")
    except Exception as e:
        print("Exception occurred while dropping the table role : ", e)
        raise e


def get_policy():
    try:
        cur = oesdb_conn.cursor()
        cur.execute("SELECT created_at, updated_at, id, name from policy")
        return cur.fetchall()
    except Exception as e:
        print("Exception occured while reading policy from SAPOR db : ", e)
        raise e


def migrate_policy(policies):
    try:
        cur = platform_conn.cursor()
        for policy in policies:
            data = policy[0], policy[1], policy[2], policy[3]
            cur.execute(
                "INSERT INTO policy (created_at, updated_at, policy_id, name) VALUES (%s, %s, %s, %s)",
                data)
    except Exception as e:
        print("Exception occurred while migrating policy : ", e)
        raise e


def get_cloud_provider():
    try:
        cur = oesdb_conn.cursor()
        cur.execute("SELECT created_at, updated_at, id, account_name from cloud_providers")
        return cur.fetchall()
    except Exception as e:
        print("Exception occurred while reading cloud provider from SAPOR db : ", e)
        raise e


def migrate_cloud_providers(cloud_providers):
    try:
        cur = platform_conn.cursor()
        for cloud_provider in cloud_providers:
            data = cloud_provider[0], cloud_provider[1], cloud_provider[2], cloud_provider[3]
            cur.execute(
                "INSERT INTO cloud_provider (created_at, updated_at, cloud_provider_id, name) VALUES (%s, %s, %s, %s)",
                data)
    except Exception as e:
        print("Exception occurred while migrating cloud providers : ", e)
        raise e


def get_agent():
    try:
        cur = oesdb_conn.cursor()
        cur.execute("SELECT id, agent_name FROM generic_agent")
        return cur.fetchall()
    except Exception as e:
        print("Exception occurred while reading agent data from SAPOR db : ", e)
        raise e


def migrate_agents(agents):
    try:
        cur = platform_conn.cursor()
        for agent in agents:
            date = datetime.datetime.now()
            data = date, date, agent[0], agent[1]
            cur.execute("INSERT INTO agent (created_at, updated_at, agent_id, name) VALUES (%s, %s, %s, %s)", data)
    except Exception as e:
        print("Exception occurred while migrating agents : ", e)
        raise e


def get_user_group_permission():
    try:
        cur = platform_conn.cursor()
        cur.execute(
            "SELECT id, created_at, updated_at, object_id, object_type, permission_id, group_id FROM user_group_permission")
        return cur.fetchall()
    except Exception as e:
        print("Exception occurred while reading user group permission : ", e)
        raise e


def migrate_user_group_permission(user_group_permissions):
    try:
        cur = platform_conn.cursor()
        for user_group_permission in user_group_permissions:
            permission_id = user_group_permission[5]
            if permission_id == "read":
                permission_id = "view"
            elif permission_id == "write":
                permission_id = "edit"
                data = user_group_permission[1], user_group_permission[2], user_group_permission[3], \
                       user_group_permission[4], permission_id, user_group_permission[6]
                cur.execute(
                    "INSERT INTO user_group_permission_3_12 (created_at, updated_at, object_id, object_type, permission_id, group_id) VALUES (%s, %s, %s, %s, %s, %s)",
                    data)
                permission_id = "delete"
            elif permission_id == "execute":
                permission_id = "runtime_access"

            data = user_group_permission[1], user_group_permission[2], user_group_permission[3], user_group_permission[
                4], permission_id, user_group_permission[6]
            cur.execute(
                "INSERT INTO user_group_permission_3_12 (created_at, updated_at, object_id, object_type, permission_id, group_id) VALUES (%s, %s, %s, %s, %s, %s)",
                data)
    except Exception as e:
        print("Exception occurred while migrating user group permission : ", e)
        raise e


if __name__ == '__main__':
    n = len(sys.argv)

    if n != 8:
        print(
            "Please pass valid 7 arguments <platform_db-name> <platform_host> <oes-db-name> <oes-db-host> <autopilot_db> <autopilot_host> <db-port>")

    platform_db = sys.argv[1]
    platform_host = sys.argv[2]
    oes_db = sys.argv[3]
    oes_host = sys.argv[4]
    autopilot_db = sys.argv[5]
    autopilot_host = sys.argv[6]
    port = sys.argv[7]

    # Establishing the platform db connection
    platform_conn = psycopg2.connect(database=platform_db, user='postgres', password='networks123', host=platform_host,
                                     port=port)
    print('Opened platform database connection successfully')

    # Establishing the oesdb db connection
    oesdb_conn = psycopg2.connect(database=oes_db, user='postgres', password='networks123',
                                  host=oes_host, port=port)
    print("Sapor database connection established successfully")

    # Establishing the autopilot db connection
    autopilot_conn = psycopg2.connect(database=autopilot_db, user="postgres", password="networks123",
                                      host=autopilot_host,
                                      port=port)
    print("autopilot database connection established successfully")

    host_url = input('''Please enter the unified gate url 
                      ex:https://oes-release.dev.opsmx.org/gate ''')
    cookie = input('''Please enter the Cookie. Steps to retrieve the cookie are : 
    1. Login to ISD using admin credential.
    2. Open the browser network console.
    3. Under Headers tab -> Request Headers -> cookie :  ''')

    perform_migration()

