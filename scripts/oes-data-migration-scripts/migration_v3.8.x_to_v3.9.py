import json
import psycopg2
import sys
import datetime
import string
import random
import requests

def perform_migration(input_string):
    try:
        print ('Migrating from v3.8.x to v3.9')

        print("Migrating UserGroups to map as single group and to lowercase")
        usergroups = fetch_usergroups_data()
        migration_usergroups_data(usergroups)

        # Modify existing user_group table
        modifyUserGroupTable()

        # add admin groups configuration to table
        print ('Printing all admin group names given:: ', input_string)
        admin_groups = input_string.split(',')
        for group_name in admin_groups:
            map_user_group_admin(group_name.lower())
        print("Successfully configured admin groups to table to v3.9")

        print("Migrating approval gate parameter entity")
        alter_approval_gate_parameter()
        approval_gate_instance_ids = fetch_distinct_gate_instances()
        for approval_gate_instance_id in approval_gate_instance_ids:
            connectors = fetch_distinct_connectors(approval_gate_instance_id[0])
            param_group_id = 1
            for connector in connectors:
                update_param_group_id(param_group_id, connector[0], approval_gate_instance_id[0])
                param_group_id = param_group_id + 1

        print("Migrating pipeline json")
        pipeline_jsons = fetch_pipeline_json()
        for pipeline_json in pipeline_jsons:
            if pipeline_json is not None and len(pipeline_json) > 0:
                migrate_pipeline_json(pipeline_json[0], pipeline_json[1])

        print("Migrating Cloud Configuration entity")
        alter_cloud_configuration()
        print("Successfully configured Cloud Configuration entity to table to v3.9")
        print("Successfully migrated to v3.9")

        platform_conn.commit()
        visibility_conn.commit()
        oesdb_conn.commit()
    except Exception as e:
        platform_conn.rollback()
        visibility_conn.rollback()
        oesdb_conn.rollback()
        print ('Exception occured during migration : ', e)
    finally:
        platform_conn.close()
        visibility_conn.close()
        oesdb_conn.close()

def fetch_usergroups_data():
    try:
        cur = platform_conn.cursor()
        cur.execute("select id,name from user_group")
        return cur.fetchall()
    except Exception as e:
        print("Exception occurred while fetching user_group data : ", e)
        raise e


def migration_usergroups_data(usergroups):
    print("Total usergroups: ",usergroups)
    user_groups_map = {usergroup[0]: usergroup[1] for usergroup in usergroups}
    for usergroup in usergroups:
        user_group_name = usergroup[1].lower()
        if (user_group_name in user_groups_map.values()) and (user_group_name != usergroup[1]):
            user_group_id = list(user_groups_map.keys())[list(user_groups_map.values()).index(user_group_name)]
            update_usergroup_permission_data(usergroup[0], user_group_id)
            delete_old_user_group_data(usergroup[0])
        else:
            update_usergroup_name_tolower(usergroup[0], user_group_name)


def update_usergroup_permission_data(old_user_group_id, new_user_group_id):
    try:
        cur = platform_conn.cursor()
        cur.execute("select count(*) from user_group_permission where group_id ="+ str(old_user_group_id))
        result = cur.fetchone()[0]
        print("Total usergroups permission for user_group_id: count: ", old_user_group_id, result)
        if result > 0:
            cur.execute("update user_group_permission set group_id = "+str(new_user_group_id)+" where group_id ="+str(old_user_group_id))
    except Exception as e:
        print("Exception occurred while updating data from user_group_permission table : ", e)
        raise e


def delete_old_user_group_data(old_user_group_id):
    try:
        cur = platform_conn.cursor()
        cur.execute("delete from user_group where id =" + str(old_user_group_id))
    except Exception as e:
        print("Exception occurred while deleting data from user_group table : ", e)
        raise e


def update_usergroup_name_tolower(user_group_id, user_group_name):
    try:
        cur = platform_conn.cursor()
        cur.execute("select count(*) from user_group where name='"+user_group_name+"'")
        result = cur.fetchone()[0]
        if result == 0:
            cur.execute("UPDATE user_group SET name ='"+user_group_name+ "' WHERE id =" + str(user_group_id))
    except Exception as e:
        print('Exception occurred while updating user_group table name to lowercase: ', e)
        raise e

def alter_approval_gate_parameter():
    try:
        cur = visibility_conn.cursor()
        cur.execute("ALTER TABLE approval_gate_parameter ADD COLUMN IF NOT EXISTS param_group_id INT NOT NULL DEFAULT 0")
    except Exception as e:
        print("Exception occured while altering the approval_gate_parameter table : ", e)
        raise e


def fetch_distinct_gate_instances():
    try:
        cur = visibility_conn.cursor()
        cur.execute("select distinct(approval_gate_instance_id) from approval_gate_parameter ORDER BY approval_gate_instance_id")
        return cur.fetchall()
    except Exception as e:
        print("Exception occured while fetching distinct gate instances : ", e)
        raise e


def fetch_distinct_connectors(gate_instance_id):
    try:
        cur = visibility_conn.cursor()
        cur.execute("select distinct(connector_type) from approval_gate_parameter where approval_gate_instance_id = "+str(gate_instance_id))
        return cur.fetchall()
    except Exception as e:
        print("Exception occured while fetching distinct connectors : ", e)
        raise e


def update_param_group_id(param_group_id, connector_type, approval_gate_instance_id):
    try:
        cur = visibility_conn.cursor()
        cur.execute("update approval_gate_parameter set param_group_id = " + str(param_group_id) + " where connector_type = '" + str(connector_type) + "' AND approval_gate_instance_id = "+str(approval_gate_instance_id))
    except Exception as e:
        print("Exception occured while updating param group id : ", e)
        raise e


def fetch_pipeline_json():
    try:
        cur = platform_conn.cursor()
        cur.execute("select id, pipeline_json from pipeline")
        return cur.fetchall()
    except Exception as e:
        print("Exception occured while fetching pipeline jsons : ", e)
        raise e


def migrate_pipeline_json(id, pipeline_json):
    try:
        cur = platform_conn.cursor()
        pipeline_json = str(pipeline_json).replace("\\u", "\\\\")
        pipe_json = json.loads(pipeline_json)
        if len(pipe_json) > 0:
            stages = pipe_json['stages']
            if stages is not None and len(stages)>0:
                for stage in stages:
                    gate_type = stage['type']
                    if gate_type is not None and len(gate_type)>0:
                        if str(gate_type).strip() == 'Visibility Approval':
                            migrate_approval_gate(stage)
                        elif str(gate_type).strip() == 'Verification':
                            migrate_verification_gate(stage)
                        elif str(gate_type).strip() == 'Test Verification':
                            migrate_test_verification_gate(stage)
                        elif str(gate_type).strip() == 'Policy Stage':
                            migrate_policy_gate(stage)

                pipe_json['stages'] = stages

                cur.execute("update pipeline set pipeline_json = '"+str(json.dumps(pipe_json).replace("\\\\", "\\u").replace("'", "\\u0027"))+"' where id="+str(id))
    except KeyError as ke:
        pass

    except Exception as e:
        print("Exception occured while migrating pipeline json : ", e)
        raise e


def migrate_policy_gate(stage):
    del stage['alias']
    stage['type'] = 'policy'


def migrate_test_verification_gate(stage):
    del stage['alias']
    del stage['comments']
    stage['type'] = 'testVerification'


def migrate_verification_gate(stage):
    del stage['alias']
    del stage['comments']
    stage['type'] = 'verification'


def migrate_approval_gate(stage):
    try:
        del stage['alias']
        stage['type'] = 'approval'
        parameters = stage['parameters']
        if parameters is not None and len(parameters) > 0:
            canaryid = get_canaryid(parameters)
            gitrepo = get_gitrepo(parameters)
            jenkinsartifact = get_jenkinsartifact(parameters)
            jenkinsbuild = get_jenkinsbuild(parameters)
            appscanid = get_appscanid(parameters)
            aquawave = get_aquawave(parameters)
            jenkinsjob = get_jenkinsjob(parameters)
            projectkey = get_projectkey(parameters)
            jiraid = get_jiraid(parameters)
            gitcommitid = get_gitcommitid(parameters)
            imageids = get_imageids(parameters)
            gateurl = get_gateurl(parameters)

            connectors = []
            if gateurl is not None and len(gateurl)>0:
                url_components = str(gateurl).split("/")
                approval_gate_id = url_components[len(url_components) - 2]
                configured_tool_connectors = fetch_configured_tool_connectors(approval_gate_id)
                if configured_tool_connectors is not None and len(configured_tool_connectors) > 0:
                    for configured_tool_connector in configured_tool_connectors:
                        connector_type = configured_tool_connector['connectorType']
                        if connector_type is not None:
                            if str(connector_type).strip().upper() == 'JIRA':
                                configure_jira(configured_tool_connector, jiraid)
                            elif str(connector_type).strip().upper() == 'GIT':
                                configure_git(configured_tool_connector, gitcommitid, gitrepo)
                            elif str(connector_type).strip().upper() == 'JENKINS':
                                configure_jenkins(configured_tool_connector, jenkinsartifact, jenkinsbuild, jenkinsjob)
                            elif str(connector_type).strip().upper() == 'AUTOPILOT':
                                configure_autopilot(canaryid, configured_tool_connector)
                            elif str(connector_type).strip().upper() == 'SONARQUBE':
                                configure_sonarqube(configured_tool_connector, projectkey)
                            elif str(connector_type).strip().upper() == 'APPSCAN':
                                configure_appscan(appscanid, configured_tool_connector)
                            elif str(connector_type).strip().upper() == 'AQUAWAVE':
                                configure_aquawave(aquawave, configured_tool_connector)
                            connectors.append(configured_tool_connector)
                            set_new_parameters(connectors, gateurl, imageids, stage)
                else:
                    set_new_parameters(connectors, gateurl, imageids, stage)

    except Exception as e:
        print("Exception occured while migrating approval gate : ", e)
        raise e


def get_canaryid(parameters):
    canaryid = ''
    try:
        canaryid = parameters['canaryid']
    except KeyError as ke:
        pass
    return canaryid


def get_gitrepo(parameters):
    gitrepo = ''
    try:
        gitrepo = parameters['gitrepo']
    except KeyError as ke:
        pass
    return gitrepo


def get_jenkinsartifact(parameters):
    jenkinsartifact = ''
    try:
        jenkinsartifact = parameters['jenkinsartifact']
    except KeyError as ke:
        pass
    return jenkinsartifact


def get_jenkinsbuild(parameters):
    jenkinsbuild = ''
    try:
        parameters['jenkinsbuild']
    except KeyError as ke:
        pass
    return jenkinsbuild


def get_appscanid(parameters):
    appscanid = ''
    try:
        appscanid = parameters['appscanid']
    except KeyError as ke:
        pass
    return appscanid


def get_aquawave(parameters):
    aquawave = ''
    try:
        aquawave = parameters['aquawave']
    except KeyError as ke:
        pass
    return aquawave


def get_jenkinsjob(parameters):
    jenkinsjob = ''
    try:
        jenkinsjob = parameters['jenkinsjob']
    except KeyError as ke:
        pass
    return jenkinsjob


def get_projectkey(parameters):
    projectkey = ''
    try:
        projectkey = parameters['projectkey']
    except KeyError as ke:
        pass
    return projectkey


def get_jiraid(parameters):
    jiraid = ''
    try:
        jiraid = parameters['jiraid']
    except KeyError as ke:
        pass
    return jiraid


def get_gitcommitid(parameters):
    gitcommitid = ''
    try:
        gitcommitid = parameters['gitcommitid']
    except KeyError as ke:
        pass
    return gitcommitid


def get_imageids(parameters):
    imageids = ''
    try:
        imageids = parameters['imageids']
    except KeyError as ke:
        pass
    return imageids


def get_gateurl(parameters):
    gateurl = None
    try:
        gateurl = parameters['gateurl']
    except KeyError as ke:
        pass
    return gateurl


def set_new_parameters(connectors, gateurl, imageids, stage):
    gateurl = str(gateurl).strip().replace("v4", "v5")
    gateurl = str(gateurl).strip().replace("v3", "v5")
    gateurl = str(gateurl).strip().replace("v2", "v5")
    gateurl = str(gateurl).strip().replace("v1", "v5")
    new_parameters = {"imageIds": imageids,
                      "connectors": connectors,
                      "gateUrl": gateurl}
    stage['parameters'] = new_parameters


def configure_aquawave(aquawave, configured_tool_connector):
    aqua = []
    param = {"imageId": aquawave}
    aqua.append(param)
    configured_tool_connector['values'] = aqua


def configure_appscan(appscanid, configured_tool_connector):
    appscan = []
    param = {"id": appscanid}
    appscan.append(param)
    configured_tool_connector['values'] = appscan


def configure_sonarqube(configured_tool_connector, projectkey):
    sonarqube = []
    param = {"projectKey": projectkey}
    sonarqube.append(param)
    configured_tool_connector['values'] = sonarqube


def configure_autopilot(canaryid, configured_tool_connector):
    autopilot = []
    param = {"canaryId": canaryid}
    autopilot.append(param)
    configured_tool_connector['values'] = autopilot


def configure_jenkins(configured_tool_connector, jenkinsartifact, jenkinsbuild, jenkinsjob):
    jenkins = []
    param = {"job": jenkinsjob,
             "buildId": jenkinsbuild,
             "artifact": jenkinsartifact}
    jenkins.append(param)
    configured_tool_connector['values'] = jenkins


def configure_git(configured_tool_connector, gitcommitid, gitrepo):
    git = []
    param = {"repo": gitrepo,
             "commitId": gitcommitid}
    git.append(param)
    configured_tool_connector['values'] = git


def configure_jira(configured_tool_connector, jiraid):
    jira_tickets = []
    if jiraid is not None and len(jiraid) > 0:
        jiraids = str(jiraid).split(",")
        for id in jiraids:
            param = {"jira_ticket_no": id}
            jira_tickets.append(param)
    configured_tool_connector['values'] = jira_tickets


def fetch_configured_tool_connectors(approval_gate_id):
    try:
        url = oes_visibility_url + "/visibilityservice/v1/approvalGates/"+str(approval_gate_id)+"/configuredtoolConnectors"
        headers = {'x-spinnaker-user': oes_admin_user}
        response = requests.get(url=url, headers=headers)
        return json.loads(response.content)
    except Exception as e:
        print("Exception occured while fetching configured tool connectors : ", e)
        raise e

def modifyUserGroupTable():
    try:
        cur = platform_conn.cursor()
        cur.execute("""ALTER TABLE user_group ADD COLUMN IF NOT EXISTS "is_admin" BOOLEAN NOT NULL DEFAULT FALSE"""
                    )
    except Exception as e:
        print ('Exception occured while modifying user_group table: ',
               e)
        raise e


def map_user_group_admin(group_name):
    try:
        cur = platform_conn.cursor()
        cur.execute("SELECT id FROM user_group Where name='"
                    + group_name + "'")
        user_group_id = cur.fetchone()
        update_user_group(user_group_id)
    except Exception as e:
        print ('Exception occured while fetching data from user_group table: '
               , e)
        raise e


def update_user_group(user_group_id):
    try:
        cur = platform_conn.cursor()
        cur.execute('UPDATE user_group SET is_admin = true WHERE id = '+str(user_group_id[0]))
    except Exception as e:
        print ('Exception occured while updating user_group table: ', e)
        raise e

def alter_cloud_configuration():
    try:
        cur = oesdb_conn.cursor()
        cur.execute("ALTER TABLE cloud_configuration ALTER COLUMN bakery_secret_key TYPE varchar(10000) USING bakery_secret_key::varchar")
        cur.execute("ALTER TABLE cloud_configuration ALTER COLUMN secret_key TYPE varchar(10000) USING secret_key::varchar")
    except Exception as e:
        print("Exception occured while altering the cloud_configuration table : ", e)
        raise e


if __name__ == '__main__':
    n = len(sys.argv)
    if n != 10:
        print ('Please pass valid 9 arguments <platform-db-name> <platform-db-host> <visibility-db-name> <visibility-db-host> <sapor-db-name> <sapor-db-host> <oes-visibility-url> <db-port> <oes-admin-user>')

    platform_db = sys.argv[1]
    platform_host = sys.argv[2]
    visibility_db = sys.argv[3]
    visibility_host = sys.argv[4]
    oes_db = sys.argv[5]
    oes_host = sys.argv[6]    
    oes_visibility_url = sys.argv[7]
    port = sys.argv[8]
    oes_admin_user = sys.argv[9]

    # Establishing the platform db connection

    platform_conn = psycopg2.connect(database=platform_db,
            user='postgres', password='networks123',
            host=platform_host, port=port)
    print ('Opened platform database connection successfully')

    visibility_conn = psycopg2.connect(database=visibility_db, user='postgres', password='networks123', host=visibility_host, port=port)
    print("Visibility database connection established successfully")
    
    
    # Establishing the sapor db connection

    oesdb_conn = psycopg2.connect(database=oes_db,
            user='postgres', password='networks123',
            host=oes_host, port=port)
    print ('Opened sapor database connection successfully')
    
    # Getting input of admin groups

    input_string = \
        input('Enter admin groups to be configure in separated by comma:: '
              )
    perform_migration(input_string)
    
