import datetime
import json
import logging
import sys
import shlex
import subprocess
from itertools import repeat

import psycopg2
import requests
from psycopg2.extras import execute_values
from concurrent.futures import ThreadPoolExecutor
from time import sleep




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
    gate_pipeline_maps = None
    try:
        try:
            drop_table_user_group_permission_3_11()
            print("Successfully dropped user_group_permission_3_11 table from platform db")
            logging.info("Successfully dropped user_group_permission_3_11 table from platform db")
        except Exception as e:
            print("Exception occurred while dropping the table user_group_permission_3_11 from platform db : ", e)
            logging.error("Exception occurred while dropping the table user_group_permission_3_11 from platform db : ",
                          exc_info=True)
            is_error_occurred = True

        try:
            drop_table_role_user_group()
            print("Successfully dropped role_user_group table from platform db")
            logging.info("Successfully dropped role_user_group table from platform db")
        except Exception as e:
            print("Exception occurred while dropping the table role_user_group from platform db : ", e)
            logging.error("Exception occurred while dropping the table role_user_group from platform db : ",
                          exc_info=True)
            is_error_occurred = True

        try:
            drop_table_role_feature_permission()
            print("Successfully dropped role_feature_permission table from platform db")
            logging.info("Successfully dropped role_feature_permission table from platform db")
        except Exception as e:
            print("Exception occurred while dropping the table role_feature_permission from platform db : ", e)
            logging.error("Exception occurred while dropping the table role_feature_permission from platform db : ",
                          exc_info=True)
            is_error_occurred = True

        try:
            drop_table_role()
            print("Successfully dropped role table from platform db")
            logging.info("Successfully dropped role table from platform db")
        except Exception as e:
            print("Exception occurred while dropping the table role from platform db : ", e)
            logging.error("Exception occurred while dropping the table role from platform db : ",
                          exc_info=True)
            is_error_occurred = True

        try:
            drop_constraints_feature_permission()
            print("Successfully dropped role table from platform db")
            logging.info("Successfully dropped role table from platform db")
        except Exception as e:
            print("Exception occurred while dropping the table role from platform db : ", e)
            logging.error("Exception occurred while dropping the table role from platform db : ",
                          exc_info=True)
            is_error_occurred = True

        try:
            drop_table_permission_3_11()
            print("Successfully dropped permission_3_11 table from platform db")
            logging.info("Successfully dropped permission_3_11 table from platform db")
        except Exception as e:
            print("Exception occurred while dropping the table permission_3_11 from platform db : ", e)
            logging.error("Exception occurred while dropping the table permission_3_11 from platform db : ",
                          exc_info=True)
            is_error_occurred = True

        try:
            policies = get_policy()
            clear_policy_data()
            migrate_policy(policies)
            print("Successfully migrated policy data from oes db to platform db")
            logging.info("Successfully migrated policy data from oes db to platform db")
        except Exception as e:
            print("Exception occurred while migrating policy data from oes db to platform db : ", e)
            logging.error("Exception occurred while migrating policy data from oes db to platform db : ", exc_info=True)
            is_error_occurred = True

        try:
            cloud_providers = get_cloud_provider()
            clear_cloud_provider_data()
            migrate_cloud_providers(cloud_providers)
            print("Successfully migrated all cloud providers data from oes db to platform db")
            logging.info("Successfully migrated all cloud providers data from oes db to platform db")
        except Exception as e:
            print("Exception occurred while migrating cloud providers data from oes db to platform db : ",
                  e)
            logging.error("Exception occurred while migrating cloud providers data from oes db to platform db : ",
                          exc_info=True)
            is_error_occurred = True

        try:
            agents = get_agent()
            clear_agents()
            migrate_agents(agents)
            print("Successfully migrated all agent data from oes db to platform db")
            logging.info("Successfully cleared all agent data from from oes db to platform db")
        except Exception as e:
            print("Exception occurred while migrating agent data from oes db to platform db : ", e)
            logging.error("Exception occurred while migrating agent data from oes db to platform db : ", exc_info=True)
            is_error_occurred = True

        try:
            user_group_permissions = get_user_group_permission()
            # clear_user_group_permission()
            create_3_12_permission_related_tables()
            migrate_user_group_permission(user_group_permissions)
            print("Successfully migrated user group permission data to user_group_permission_3_12 table in "
                  "platform db")
            logging.info("Successfully migrated user group permission data to user_group_permission_3_12 table in "
                         "platform db")
        except Exception as e:
            print("Exception occurred while migrating user group permissions data to user_group_permission_3_12 table "
                  "in platform db : ", e)
            logging.error("Exception occurred while migrating user group permissions data to "
                          "user_group_permission_3_12 table in platform db : ", exc_info=True)
            is_error_occurred = True

        try:

            gate_pipeline_maps = get_gate_pipeline_map()
            if gate_pipeline_maps is not None and len(gate_pipeline_maps) > 0:
                pipelines = get_pipelines(gate_pipeline_maps)
                update_pipeline_json_with_unified_url(pipelines)
                print("Successfully updated pipeline json in pipeline table of platform db")
                logging.info("Successfully updated pipeline json in pipeline table of platform db")
        except Exception as e:
            print(
                "Exception occurred while updating pipeline json with unified url in pipeline table of platform db : ",
                e)
            logging.error("Exception occurred while updating pipeline json with unified url in pipeline table of "
                          "platform db : ", exc_info=True)
            is_error_occurred = True

        try:
            update_spinnaker_gate_url()
            print("Successfully updated spinnaker gate url in spinnaker table of oes db")
            logging.info("Successfully updated spinnaker gate url in spinnaker table of oes db")
        except Exception as e:
            print("Exception occurred while updating spinnaker gate url in spinnaker table of oes db : ", e)
            logging.error("Exception occurred while updating spinnaker gate url in spinnaker table of oes db : ",
                          exc_info=True)
            is_error_occurred = True

        try:
            updateautopilotconstraints()
            print("Successfully updated constraints in autopilot db")
            logging.info("Successfully updated constraints in autopilot db")
        except Exception as e:
            print("Exception occurred while updating constraints in autopilot db : ", e)
            logging.error("Exception occurred while updating constraints in autopilot db : ", exc_info=True)
            is_error_occurred = True

        try:
            updateApprovalGateAUdit()
            print("Successfully updated json in audit_events table in audit db")
            logging.info("Successfully updated json in audit_events table in audit db")
        except Exception as e:
            print("Exception occurred while updating json in audit_events table in audit db : ", e)
            logging.error("Exception occurred while updating json in audit_events table in audit db : ", exc_info=True)
            is_error_occurred = True

        if is_error_occurred:
            print(
                f"{bcolors.FAIL} {bcolors.BOLD}FAILURE: {bcolors.ENDC}{bcolors.FAIL}Migration script execution failed. "
                f"Please contact the support team{bcolors.ENDC}")
            raise Exception("FAILURE: Migration script execution failed. Please contact the support team.")
        else:
            commit_transactions()

        try:
            if gate_pipeline_maps is not None and len(gate_pipeline_maps) > 0:
                cookie = login_to_isd()
                update_pipeline_with_unified_url(gate_pipeline_maps, cookie)
                print("Successfully updated pipeline with unified url")
                logging.info("Successfully updated pipeline with unified url")
            else:
                print("There is no data in gate_pipeline_map table to update pipeline with unified url")
                logging.info("There is no data in gate_pipeline_map table to update pipeline with unified url",
                             exc_info=True)
        except Exception as e:
            print("Exception occurred while updating pipeline with unified url : ", e)
            logging.error("Exception occurred while updating pipeline with unified url : ", exc_info=True)
            is_error_occurred = True

        if is_error_occurred:
            print(
                f"{bcolors.FAIL} {bcolors.BOLD}FAILURE: {bcolors.ENDC}{bcolors.FAIL}Migration script execution failed. "
                f"Please contact the support team{bcolors.ENDC}")
            raise Exception("FAILURE: Migration script execution failed. Please contact the support team.")
        else:
            print(f"{bcolors.OKGREEN}{bcolors.BOLD}Successfully completed the migration.{bcolors.ENDC}")
            logging.info("Successfully completed the migration.")

    except Exception as e:
        print("Migration script execution failed with exception ", e)
        logging.critical(e.__str__(), exc_info=True)
        rollback_transactions()
        exit(1)
    finally:
        close_connections()


def close_connections():
    try:
        platform_conn.close()
        oesdb_conn.close()
        autopilot_conn.close()
        audit_conn.close()
        visibility_conn.close()
    except Exception as e:
        logging.warning("Exception occurred while closing the DB connection : ", exc_info=True)


def rollback_transactions():
    try:
        platform_conn.rollback()
        oesdb_conn.rollback()
        autopilot_conn.rollback()
        audit_conn.rollback()
        # Visibility connection rollback is not required as we are just using the connection to fetch the data
        # visibility_conn.rollback()
    except Exception as e:
        logging.critical("Exception occurred while rolling back the transactions : ", exc_info=True)
        raise e


def commit_transactions():
    try:
        platform_conn.commit()
        oesdb_conn.commit()
        autopilot_conn.commit()
        audit_conn.commit()
        # Visibility connection commit is not required as we are just using the connection to fetch the data
        # visibility_conn.commit()
    except Exception as e:
        logging.critical("Exception occurred while committing transactions : ", exc_info=True)
        raise e


def update_spinnaker_gate_url():
    try:
        oesdb_cursor.execute("UPDATE spinnaker set url = '" + str(spinnaker_gate_url) + "'")
    except Exception as e:
        oesdb_conn.rollback()
        raise e


def get_gate_pipeline_map():
    try:
        platform_cursor.execute("SELECT pipeline_id, service_gate_id FROM gate_pipeline_map ")
        return platform_cursor.fetchall()
    except Exception as e:
        platform_conn.rollback()
        raise e


def get_pipelines(gate_pipeline_maps):
    try:
        pipeline_ids = []
        for gate_pipeline_map in gate_pipeline_maps:
            logging.info("Gate pipeline map data " + ' '.join(str(gate_pipeline_map)))
            pipeline_ids.append(gate_pipeline_map[0])

        data = tuple(pipeline_ids)
        platform_cursor.execute("SELECT id, pipeline_json from pipeline where id IN %s", (data,))
        return platform_cursor.fetchall()
    except Exception as e:
        platform_conn.rollback()
        raise e


def update_pipeline_json_with_unified_url(pipelines):
    try:
        for pipeline in pipelines:
            logging.info("Pipeline data to update unified url : \n" + ''.join(str(pipeline)) + '\n')
            pipe_json = json.loads(pipeline[1])
            pipeline_id = pipeline[0]
            if pipe_json is not None and len(pipe_json) > 0:
                stages = pipe_json["stages"]
                updated_stages = []
                for stage in stages:
                    try:
                        parameters = stage["parameters"]
                        try:
                            gate_url = parameters["gateUrl"]
                        except KeyError as ke:
                            gate_url = parameters["gateurl"]

                        host_url_comps = unified_host_url.split("/")
                        if len(host_url_comps) == 3:
                            domain_name = host_url_comps[2]
                        else:
                            domain_name = host_url_comps[2] + "/" + host_url_comps[3]

                        url_comps = str(gate_url).split("/")
                        url_comps[2] = domain_name
                        gate_url = "/"
                        gate_url = str(gate_url).join(url_comps)
                        try:
                            if parameters["gateUrl"] is not None:
                                parameters["gateUrl"] = gate_url
                        except KeyError as ke:
                            parameters["gateurl"] = gate_url

                        stage["parameters"] = parameters
                    except KeyError as ke:
                        pass
                    updated_stages.append(stage)
                if stages is not None and len(updated_stages) > 0:
                    pipe_json["stages"] = updated_stages
                    update_data = json.dumps(pipe_json), pipeline_id
                    logging.info("Updated pipeline data to update unified url : \n" + ''.join(str(update_data)) + '\n')
                    platform_cursor.execute("UPDATE pipeline SET pipeline_json = %s WHERE id = %s", update_data)
    except Exception as e:
        platform_conn.rollback()
        raise e


def update_pipeline_with_unified_url(gate_pipeline_maps, cookie):
    try:
        with ThreadPoolExecutor(max_workers = thread_pool_size) as executor:
            executor.map(update_gate_information,repeat(cookie), gate_pipeline_maps)
    except Exception as e:
        raise e


def update_gate_information(cookie, gate_pipeline_map):
    try:
        pipeline_id = gate_pipeline_map[0]
        gate_id = gate_pipeline_map[1]
        url = host_url + "/dashboardservice/v4/pipelines/" + str(pipeline_id) + "/gates/" + str(gate_id)
        headers = {'Cookie': cookie}
        response = requests.get(url=url, headers=headers)
        gate_response = json.loads(response.content)
        logging.info("Gate data from dashboard api : \n" + str(gate_response) + '\n')
        update_gate(gate_response, pipeline_id, gate_id, cookie)
    except Exception as e:
        logging.error("Exception occurred while updating gate information : ", exc_info=True)
        raise e


def update_gate(gate_response, pipeline_id, gate_id, cookie):
    try:
        platform_cursor.execute("SELECT service_id FROM service_pipeline_map where pipeline_id = " + str(pipeline_id))
        service_id = platform_cursor.fetchone()[0]
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

        try:
            req_payload["approvalGateId"] = gate_response["approvalGateId"]
        except KeyError as ke:
            pass

        try:
            req_payload["id"] = gate_id
        except KeyError as ke:
            pass

        try:
            req_payload["logTemplateName"] = gate_response["logTemplateName"]
        except KeyError as ke:
            pass

        try:
            req_payload["metricTemplateName"] = gate_response["metricTemplateName"]
        except KeyError as ke:
            pass

        try:
            req_payload["policyId"] = gate_response["policyId"]
        except KeyError as ke:
            pass

        try:
            req_payload["policyName"] = gate_response["policyName"]
        except KeyError as ke:
            pass

        url = host_url + "/dashboardservice/v4/pipelines/" + str(pipeline_id) + "/gates/" + str(gate_id)
        headers = {'Cookie': cookie,
                   'Content-Type': 'application/json'}
        req_payload = json.dumps(req_payload)

        requests.put(url=url, data=req_payload, headers=headers)
        logging.info("Updated the gate data : \n" + str(req_payload) + '\n')
    except Exception as e:
        platform_conn.rollback()
        raise e


def updateautopilotconstraints():
    try:
        autopilot_cursor.execute(
            " ALTER TABLE serviceriskanalysis  DROP CONSTRAINT IF EXISTS fkmef9blhpcxhcj431kcu52nm1e ")
        autopilot_cursor.execute(" ALTER TABLE servicegate  DROP CONSTRAINT IF EXISTS uk_lk3buh56ebai2gycw560j2oxm ")
        autopilot_cursor.execute(" ALTER TABLE canaryanalysis ALTER COLUMN metric_template_opsmx_id DROP not null ")
        autopilot_cursor.execute(" ALTER TABLE userlogfeedback ALTER COLUMN logtemplate_id DROP not null ")
        autopilot_cursor.execute(" ALTER TABLE loganalysis ALTER COLUMN log_template_opsmx_id DROP not null ")
    except Exception as e:
        autopilot_conn.rollback()
        raise e


def drop_table_permission_3_11():
    try:
        platform_cursor.execute("DROP TABLE IF EXISTS permission_3_11")
    except Exception as e:
        platform_conn.rollback()
        raise e


def drop_table_user_group_permission_3_11():
    try:
        platform_cursor.execute("DROP TABLE IF EXISTS user_group_permission_3_11")
    except Exception as e:
        platform_conn.rollback()
        raise e


def drop_table_role_feature_permission():
    try:
        platform_cursor.execute("DROP TABLE IF EXISTS role_feature_permission")
    except Exception as e:
        platform_conn.rollback()
        raise e


def drop_table_role_user_group():
    try:
        platform_cursor.execute("DROP TABLE IF EXISTS role_user_group")
    except Exception as e:
        platform_conn.rollback()
        raise e


def drop_table_role():
    try:
        platform_cursor.execute("DROP TABLE IF EXISTS role")
    except Exception as e:
        platform_conn.rollback()
        raise e


def get_policy():
    try:
        oesdb_cursor.execute("SELECT created_at, updated_at, id, name from policy")
        return oesdb_cursor.fetchall()
    except Exception as e:
        oesdb_conn.rollback()
        raise e


def clear_policy_data():
    try:
        platform_cursor.execute("DELETE FROM policy")
    except Exception as e:
        platform_conn.rollback()
        raise e


def migrate_policy(policies):
    try:
        for policy in policies:
            data = policy[0], policy[1], policy[2], policy[3]
            platform_cursor.execute(
                "INSERT INTO policy (created_at, updated_at, policy_id, name) VALUES (%s, %s, %s, %s)",
                data)
    except Exception as e:
        platform_conn.rollback()
        raise e


def get_cloud_provider():
    try:
        oesdb_cursor.execute("SELECT created_at, updated_at, id, account_name from cloud_providers")
        return oesdb_cursor.fetchall()
    except Exception as e:
        oesdb_conn.rollback()
        raise e


def clear_cloud_provider_data():
    try:
        platform_cursor.execute("DELETE FROM cloud_provider")
    except Exception as e:
        platform_conn.rollback()
        raise e


def migrate_cloud_providers(cloud_providers):
    try:
        for cloud_provider in cloud_providers:
            data = cloud_provider[0], cloud_provider[1], cloud_provider[2], cloud_provider[3]
            platform_cursor.execute(
                "INSERT INTO cloud_provider (created_at, updated_at, cloud_provider_id, name) VALUES (%s, %s, %s, %s)",
                data)
    except Exception as e:
        platform_conn.rollback()
        raise e


def get_agent():
    try:
        oesdb_cursor.execute("SELECT id, agent_name FROM generic_agent")
        return oesdb_cursor.fetchall()
    except Exception as e:
        oesdb_conn.rollback()
        raise e


def clear_agents():
    try:
        platform_cursor.execute("DELETE FROM agent")
    except Exception as e:
        platform_conn.rollback()
        raise e


def migrate_agents(agents):
    try:
        for agent in agents:
            date = datetime.datetime.now()
            data = date, date, agent[0], agent[1]
            platform_cursor.execute(
                "INSERT INTO agent (created_at, updated_at, agent_id, name) VALUES (%s, %s, %s, %s)", data)
    except Exception as e:
        platform_conn.rollback()
        raise e


def get_user_group_permission():
    try:
        platform_cursor.execute("SELECT id, created_at, updated_at, object_id, object_type, permission_id, group_id "
                                "FROM user_group_permission")
        return platform_cursor.fetchall()
    except Exception as e:
        platform_conn.rollback()
        raise e


# This function is required if we update images first and then update the DB.
# Not required when we do db update first and then images update later.
def clear_user_group_permission():
    try:
        platform_cursor.execute("DELETE FROM user_group_permission_3_12")
    except Exception as e:
        platform_conn.rollback()
        raise e


# This function is required if we update DB first and then update the images.
# Not required when we do images update first and then DB update later.
def create_3_12_permission_related_tables():
    try:
        platform_cursor.execute("CREATE TABLE IF NOT EXISTS public.permission_3_12 (id varchar(25) NOT NULL, "
                                "description varchar(50) NULL, display_name varchar(255) NOT NULL, "
                                "CONSTRAINT permission_3_12_pkey PRIMARY KEY (id) );")

        records_to_insert = [('view', 'view a feature', 'View'),
                             ('edit', 'edit a feature', 'Create/Edit'),
                             ('delete', 'delete a feature', 'Delete'),
                             ('runtime_access', 'execute (trigger custom gate)', 'Runtime Access'),
                             ('approve_gate', 'approve a visibility gate', 'Approval Gate')]

        insert_query = """INSERT INTO public.permission_3_12 (id, description, display_name)
                          SELECT * FROM (VALUES %s) s
                          WHERE NOT EXISTS (SELECT 1 FROM public.permission_3_12 ) """

        execute_values(platform_cursor, insert_query, records_to_insert)

        # cur.execute("INSERT INTO public.permission_3_12 (id, description, display_name)"
        #             "VALUES ('view', 'view a feature', 'View'), ('edit', 'edit a feature', 'Create/Edit'), "
        #             "('delete', 'delete a feature', 'Delete'), ('runtime_access', 'execute (trigger custom gate)', "
        #             " 'Runtime Access'), ('approve_gate', 'approve a visibility gate', 'Approval Gate') ")

        platform_cursor.execute("CREATE TABLE IF NOT EXISTS public.user_group_permission_3_12 (id int4 NOT NULL "
                                "GENERATED BY DEFAULT AS IDENTITY, created_at timestamp NOT NULL, updated_at timestamp NOT NULL, "
                                "object_id int4 NOT NULL, object_type varchar(255) NOT NULL, "
                                "permission_id varchar(25) NOT NULL REFERENCES public.permission_3_12(id), "
                                "group_id int4 NOT NULL REFERENCES public.user_group(id), "
                                "CONSTRAINT user_group_permission_3_12_pkey PRIMARY KEY (id) );")
        print("Successfully created table and inserted")

    except Exception as e:
        platform_conn.rollback()
        raise e


def migrate_user_group_permission(user_group_permissions):
    try:
        for user_group_permission in user_group_permissions:
            permission_id = user_group_permission[5]
            if permission_id == "read":
                permission_id = "view"
            elif permission_id == "write":
                permission_id = "edit"
                data = user_group_permission[1], user_group_permission[2], user_group_permission[3], \
                       user_group_permission[4], permission_id, user_group_permission[6]
                logging.info("User group permission data : " + ''.join(str(data)))
                platform_cursor.execute(
                    "INSERT INTO user_group_permission_3_12 (created_at, updated_at, object_id, object_type, "
                    "permission_id, group_id) VALUES (%s, %s, %s, %s, %s, %s)",
                    data)
                permission_id = "delete"
            elif permission_id == "execute":
                permission_id = "runtime_access"

            data = user_group_permission[1], user_group_permission[2], user_group_permission[3], user_group_permission[
                4], permission_id, user_group_permission[6]
            logging.info("User group permission data : " + ''.join(str(data)))
            platform_cursor.execute(
                "INSERT INTO user_group_permission_3_12 (created_at, updated_at, object_id, object_type, "
                "permission_id, group_id) VALUES (%s, %s, %s, %s, %s, %s)",
                data)
    except Exception as e:
        platform_conn.rollback()
        raise e


def updateApprovalGateAUdit():
    try:
        audit_cursor.execute("select id,data from audit_events where data->>'eventType' = 'APPROVAL_GATE_AUDIT'")
        approval_audit_details = audit_cursor.fetchall()
        for auditdata in approval_audit_details:
            jsonData = json.loads(json.dumps(listData(auditdata)))
            logging.info("Json data for approval gate audit \n" + str(jsonData) + "\n")
            if 'gateId' in jsonData['auditData']['details']:
                audit_events_table_id = auditdata[0]
                gateId = jsonData['auditData']['details']['gateId']
                visibility_cursor.execute('select pipeline_id from approval_gate where id =' + str(gateId))
                pipelineId = visibility_cursor.fetchone()
                if pipelineId is not None:
                    pipelineId = str(pipelineId[0])
                    platform_cursor.execute(
                        'select distinct(a.name) as applicationName from applications a left outer join service s on '
                        'a.id=s.application_id left outer join service_pipeline_map sp on s.id=sp.service_id where '
                        'sp.pipeline_id =' + str(
                            pipelineId))
                    applicationName = platform_cursor.fetchone()
                    if applicationName is not None:
                        applicationName = str(applicationName[0])
                        logging.info("Gate id: " + str(gateId) + " pipeline id " + str(pipelineId) +
                                     " application name " + str(applicationName) + " audit_events_table_id " +
                                     str(audit_events_table_id))
                        fetchJsonAndUpdate(audit_events_table_id, applicationName, jsonData)
    except Exception as e:
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
        raise e


def updateApprovalAuditJson(audit_events_table_id, updateJson):
    try:
        updatedConfig = "'" + str(json.dumps(updateJson)) + "'"
        logging.info("updated json data for approval gate audit " + str(updatedConfig))
        audit_cursor.execute(
            'update audit_events set data =' + updatedConfig + ' where id ={}'.format(audit_events_table_id))
    except Exception as e:
        audit_conn.rollback()
        raise e


def drop_constraints_feature_permission():
    try:
        platform_cursor.execute(
            " ALTER TABLE feature_permission DROP CONSTRAINT IF EXISTS fkdap3k7dwyp8yq5sn0kjf6eo42 ")
        platform_cursor.execute(
            " ALTER TABLE feature_permission DROP CONSTRAINT IF EXISTS fklantt6pc0wjwueula2lt5vmt8 ")
    except Exception as e:
        platform_conn.rollback()
        raise e


def login_to_isd():
    try:
        cookie = ""
        cmd = "curl -vvv -X POST '" + host_url + "/login?username=" + isd_admin_username + "&password=" + isd_admin_password + "&submit=Login'"
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

    if n != 20:
        print(
            "Please pass valid 19 arguments <platform_db-name> <platform_host> <oes-db-name> <oes-db-host> "
            "<autopilot_db> <autopilot_host> <audit_db-name> <audit-db-host> <visibility_db-name> <visibility-db-host> "
            "<db-port> <isd-host-url> <spinnaker-gate-url> <unified-host-url> <isd-admin-username> <isd-admin-password> <db-username> <db-password> <thread-pool-size>")
        exit(1)

    global is_error_occurred
    is_error_occurred = False

    logging.basicConfig(filename='/tmp/migration_v3.11.x_to_v3.12.x.log', filemode='w',
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
    host_url = sys.argv[12]
    spinnaker_gate_url = sys.argv[13]
    unified_host_url = sys.argv[14]
    isd_admin_username = sys.argv[15]
    isd_admin_password = sys.argv[16]
    db_username = sys.argv[17]
    db_password = sys.argv[18]
    thread_pool_size = sys.argv[19]

    # Establishing the platform db connection
    platform_conn = psycopg2.connect(database=platform_db, user=db_username, password=db_password, host=platform_host,
                                     port=port)
    print('Platform database connection established successfully')
    logging.info('Platform database connection established successfully')

    platform_cursor = platform_conn.cursor()

    # Establishing the oesdb db connection
    oesdb_conn = psycopg2.connect(database=oes_db, user=db_username, password=db_password,
                                  host=oes_host, port=port)
    print("Sapor database connection established successfully")
    logging.info('Sapor database connection established successfully')

    oesdb_cursor = oesdb_conn.cursor()

    # Establishing the autopilot db connection
    autopilot_conn = psycopg2.connect(database=autopilot_db, user=db_username, password=db_password,
                                      host=autopilot_host,
                                      port=port)
    print("Autopilot database connection established successfully")
    logging.info('Autopilot database connection established successfully')

    autopilot_cursor = autopilot_conn.cursor()

    # Establishing the audit db connection
    audit_conn = psycopg2.connect(database=audit_db, user=db_username, password=db_password, host=audit_host,
                                  port=port)
    print('Audit database connection established successfully')
    logging.info('Audit database connection established successfully')

    audit_cursor = audit_conn.cursor()

    # Establishing the visibility db connection
    visibility_conn = psycopg2.connect(database=visibility_db, user=db_username, password=db_password,
                                       host=visibility_host,
                                       port=port)
    print("Visibility database connection established successfully")
    logging.info('Visibility database connection established successfully')

    visibility_cursor = visibility_conn.cursor()

    perform_migration()
