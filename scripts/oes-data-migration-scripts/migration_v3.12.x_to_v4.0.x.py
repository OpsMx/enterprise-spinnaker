import psycopg2
import sys
import subprocess
import json
import logging
import requests
import datetime
import redis
import mysql.connector


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

class SourceDetailsEntity:
    created_at = None
    updated_at = None
    description = None
    host_url = None
    name = None
    type = None

    def __init__(self, created_at, updated_at, description, host_url, name, type):
        self.created_at = created_at
        self.updated_at = updated_at
        self.description = description
        self.host_url = host_url
        self.name = name
        self.type = type

def update_db(version):     # pre-upgrade DB Update

    try:
        logging.info('Updating databases from v3.12.x to v4.0.x')

        logging.info("Altering platform db table app_environment")
        print("Altering platform db table app_environment")
        alterAppEnvironmentTable()

        logging.info("Updating spinnaker environments details in sapor db")
        print("Updating spinnaker environments details in sapor db")
        getEnvironmentData()

        logging.info("Updating spinnaker environments Id details in app_environment table of platform db")
        print("Updating spinnaker environments Id details in app_environment table of platform db")
        environmentUpdate()
            

        logging.info("Altering platform db table service_gate")
        print("Altering platform db table service_gate")
        alterServiceGateTable()

        logging.info("Updating ref_id in service_gate table")
        print("Updating ref_id in service_gate table")
        updateRefId()

        logging.info("Altering platform db table service_deployments_current")
        print("Altering platform db table service_deployments_current")
        add_columns_in_service_deployment_current()

        logging.info("Altering autopilot db table userlogfeedback and loganalysis")
        print("Altering autopilot db table userlogfeedback and loganalysis")
        update_autopilot_constraints()

        logging.info("Updating service_deployments_current table sync column data in platform db")
        print("Updating service_deployments_current table sync column data in platform db")
        update_sync_status()
        
        logging.info("Updating Spinnaker existing gate Json in spinnaker")
        print("Updating Spinnaker existing gate Json in spinnaker")
        processPipelineJsonForExistingGates()
        logging.info("Adding schema version to platform db table db_version")
        print("Adding schema version to platform db table db_version")
        addDBVersion(version)
        
        commit_transactions()

        update_audit_db()

        logging.info("Successfully updated databases.")
        print(f"{bcolors.OKGREEN}{bcolors.BOLD}Successfully updated databases.{bcolors.ENDC}")

    except Exception as e:
        print("Exception occurred while updating databases : ", e)
        print(f"{bcolors.FAIL} {bcolors.BOLD}FAILURE: {bcolors.ENDC}{bcolors.FAIL}DB Upgrade script execution failed. Please contact the support team{bcolors.ENDC}")
        logging.error("Exception occurred while updating databases from v3.12.x to v4.0.x:", exc_info=True)
        logging.critical(e.__str__(), exc_info=True)
        rollback_transactions()
        rollback_audit_db_charts()
        exit(1)
    finally:
        close_connections()


def update_audit_db():
    print("Migrating audit source details")
    logging.info("Migrating audit source details")
    delete_records_with_source_null()
    create_table_source_details()
    add_column_source_details_id()
    sources = get_distinct_source()
    logging.info("sources" + str(sources))
    for source in sources:
        source = source[0]
        if source == 'OES':
            migrate_oes_audits()
        elif source == 'spinnaker':
            migrate_spinnaker_audits()
    relate_audit_events_and_source_details()
    add_not_null_constraint_to_source_details_id()
    drop_column_source()
    logging.info("Dropping audit db table delivery_insights_chart_counts")
    print("Dropping audit db table delivery_insights_chart_counts")
    dropDeliveryInsights()
    logging.info("Dropping audit db table area_chart_counts")
    print("Dropping audit db table area_chart_counts")
    dropAreaCharts()
    logging.info("Creating audit db table delivery_insights_chart_counts")
    print("Creating audit db table delivery_insights_chart_counts")
    createDeliveryInsights()
    logging.info("Creating audit db table area_chart_counts")
    print("Creating audit db table area_chart_counts")
    createAreaCharts()
    audit_conn.commit()


def perform_migration(version):     # post-upgrade Data Migration (to be run as a background job)
    try:
        logging.info('Migrating data from v3.12.x to v4.0.x')

        logging.info("verify schema version in platform db table db_version")
        print("verify schema version to platform db table db_version")
        verifyDBVersion(version)

        logging.info("Updating cluster and location in service_deployments_current table")
        print("Updating cluster and location in service_deployments_current table")
        pipeline_executions = fetch_pipeline_executions()
        persist_cluster_and_location(pipeline_executions)
          
        print("Migrating the navigation Url format of the pipeline executions")
        logging.info("Migrating the navigation Url format of the pipeline executions")
        if spin_db_type == 'redis':
            plKeyExecDict = get_pipeline_execution_key_dict()
            update_custom_gates_navigation_url(plKeyExecDict)
        elif spin_db_type == 'sql':
            mysqlcursor_orca = spindb_orca_sql.cursor(buffered=True)
            pi_executions = get_sql_pi_executions(mysqlcursor_orca)
            #Should not close the cursor here, it is to be kept open until the "spin_db_update_custom_gates_navigation_url" operation complete
            spin_db_update_custom_gates_navigation_url(pi_executions)
            mysqlcursor_orca.close()
        elif spin_db_type == 'postgres':
            pi_executions = get_sql_pi_executions(spindb_orca_postgres)
            spin_db_update_custom_gates_navigation_url(pi_executions)

            
        logging.info("Updating application name in audit events table")
        print("Updating application name in audit events table")
        updateApprovalGateAudit()

        commit_transactions()
        logging.info("Successfully completed the migration.")
        print(f"{bcolors.OKGREEN}{bcolors.BOLD}Successfully completed the migration.{bcolors.ENDC}")            

    except Exception as e:
        print("Exception occurred during migration from v3.12.x to v4.0.x : ", e)
        print(f"{bcolors.FAIL} {bcolors.BOLD}FAILURE: {bcolors.ENDC}{bcolors.FAIL}Data Migration script execution failed. Please contact the support team{bcolors.ENDC}")
        logging.error("Exception occurred during migration from v3.12.x to v4.0.x : ", exc_info=True)
        logging.critical(e.__str__(), exc_info=True)
        rollback_transactions()
        exit(1)
    finally:
        close_connections()



def get_pipeline_execution_key_dict():
    try:
        keys = redis_conn.keys("pipeline:*:stageIndex")
        plKeyExecDict = {}
        for key in keys:
            executions = redis_conn.lrange(key, 0, -1)
            plKey = key[:35]
            plKeyExecDict[plKey] = executions
        logging.info(f"The plKeyExecDict is: {plKeyExecDict}")
        return plKeyExecDict
    except Exception as e:
        print("Exception occurred while getting the pipeline execution key dict : ", e)
        logging.error("Exception occurred while getting the pipeline execution key dict : ", exc_info=True)
        raise e
        

def update_custom_gates_navigation_url(plKeyExecDict):
    try:
        for plKey, executions in plKeyExecDict.items():
            for execution in executions:
                exec_str = str(execution.decode("utf-8"))
                field = "stage." + exec_str + ".outputs"
                type = "stage."+exec_str+".type"
                logging.info("The pl key is: %s", plKey)
                logging.info("The field is: %s", field)
                output = redis_conn.hget(plKey, field)
                stage_type = redis_conn.hget(plKey, type)
                logging.info("The output is: %s", output)
                output_str = str(output.decode("utf-8"))
                output_json = json.loads(output_str)
                if b'approval' == stage_type and 'navigationalURL' in output_json:
                    update_approval_gate_url(output_json, plKey, exec_str)

                elif (b'verification' == stage_type or b'testverification' == stage_type) and ('verificationURL' in output_json or 'canaryReportURL' in output_json):
                    update_verification_gate_url(output_json, plKey, exec_str)

                elif b'policy' == stage_type:
                    update_policy_gate_url(output_json, plKey, exec_str)

    except Exception as e:
        logging.error("Exception occurred while updating custom gates : ", exc_info=True)
        print("Exception occurred while updating custom gates : ", e)
        raise e


def update_approval_gate_url(json_data, pl_key, execution_str):
    try:
        navigational_url = json_data['navigationalURL']
        if navigational_url.find('fromPlugin?instanceId') < 0:
            location = json_data['location']
            words = location.split('/')
            instance_id = words[len(words) - 2]
            logging.info(f"the instance id is:  {instance_id}")
            json_data['navigationalURL'] = navigational_url + '/fromPlugin?instanceId=' + str(instance_id)
            dump = json.dumps(json_data)
            redis_conn.hset(pl_key, "stage." + execution_str + ".outputs", dump)
            logging.info(f"The output after updating approval url is:  {json_data}")
    except Exception as e:
        print("Exception occurred while updating approval gate navigation url : ", e)
        logging.error("Exception occurred while updating approval gate navigation url : ", exc_info=True)
        raise e
        


def update_verification_gate_url(json_data, pl_key, execution_str):
    try:
        if 'verificationURL' in json_data:
            json_data['canaryReportURL'] = json_data['verificationURL']
            dump = json.dumps(json_data)
            redis_conn.hset(pl_key, "stage." + execution_str + ".outputs", dump)
            logging.info(f"The output after updating verification gate url is: {json_data}")
            return

        canary_report_url = json_data['canaryReportURL']
        if canary_report_url.find('fromPlugin') < 0:
           application_name = redis_conn.hget(pl_key, 'application')
           pipeline_name = redis_conn.hget(pl_key, 'name')
           service_id = get_service_id(str(application_name.decode("utf-8")), str(pipeline_name.decode("utf-8")))
           if service_id is not None:
              json_data['canaryReportURL'] = canary_report_url + '/fromPlugin/' + str(service_id)
              dump = json.dumps(json_data)
              redis_conn.hset(pl_key, "stage." + execution_str + ".outputs", dump)
              logging.info(f"The output after updating verification gate url is: {json_data}")
    except Exception as e:
        print("Exception occurred while updating verification gate : ", e)
        logging.error("Exception occurred while updating verification gate : ", exc_info=True)
        raise e
        


def get_service_id(application_name, pipeline_name):
    try:
        data = application_name, pipeline_name
        cur_platform.execute("select s.id as service_id from service s LEFT OUTER JOIN applications a ON s.application_id = a.id LEFT OUTER JOIN service_pipeline_map spm ON spm.service_id = s.id left outer join pipeline p on spm.pipeline_id = p.id where a.name = %s and p.pipeline_name = %s", data)
        serviceId = cur_platform.fetchone()
        if serviceId is not None:
           return serviceId[0]
        else:
          logging.info("service id was not found for the  application name : %s, Pipeline name :%s", application_name, pipeline_name)
    except Exception as e:
        print("Exception occurred while getting service id : ", e)
        logging.error("Exception occurred while getting service id : ", exc_info=True)
        raise e


def get_policy_name(application_name, pipeline_name, gate_name):
    try:
        data = application_name, pipeline_name, gate_name
        cur_oesdb.execute("select policy_name from policy_gate where application_name = %s and pipeline_name = %s and gate_name = %s", data)
        policyName = cur_oesdb.fetchone()
        if  policyName is not None:
            return policyName[0]
        else:
            logging.info("Policy name was not found for the  application name : %s, Pipeline name : %s, gate name : %s", application_name, pipeline_name,gate_name)
    except Exception as e:
        print("Exception occurred while getting the policy name : ", e)
        logging.error("Exception occurred while getting the policy name : ", exc_info=True)
        raise e


def update_policy_gate_url(json_data, pl_key, execution_str):
    try:
        if 'policyName' in json_data:
            return
        application_name = redis_conn.hget(pl_key, 'application')
        pipeline_name = redis_conn.hget(pl_key, 'name')
        gate_name = redis_conn.hget(pl_key, 'stage.' + execution_str + '.name')
        policy_name = get_policy_name(str(application_name.decode("utf-8")), str(pipeline_name.decode("utf-8")), str(gate_name.decode("utf-8")))
        if policy_name is not None: 
           json_data['policyName'] = policy_name
           json_data['policyLink'] = '/policy/' + policy_name
           dump = json.dumps(json_data)
           redis_conn.hset(pl_key, "stage." + execution_str + ".outputs", dump)
           logging.info(f"The output after updating policy gate url is: {json_data}")
    except Exception as e:
        print("Exception occurred while updating policy gate url : ", e)
        logging.error("Exception occurred while updating policy gate url : ", exc_info=True)
        raise e


def get_sql_pi_executions(sqlcursor_orca):
    try:        
        sqlcursor_orca.execute("SELECT pi.application, pi.body, ps.body FROM pipeline_stages ps LEFT OUTER JOIN pipelines pi ON ps.execution_id = pi.id")
        return sqlcursor_orca.fetchall()        
    except Exception as e:
        print("Exception occurred while getting the pipeline executions : ", e)
        logging.error("Exception occurred while getting the pipeline execution : ", exc_info=True)
        raise e

def updated_stage_execution_data(pi_stage_id, updated_json):
    try:
        dump_updated = json.dumps(updated_json)
        sql = "UPDATE pipeline_stages SET body = %s WHERE id = %s"
        data = (dump_updated, pi_stage_id)
        if spin_db_type == 'sql':
           mysqlcursor_orca = spindb_orca_sql.cursor()        
           mysqlcursor_orca.execute(sql, data)
           mysqlcursor_orca.close()
        elif spin_db_type == 'postgres':
           spindb_orca_postgres.execute(sql, data)


    except Exception as e:
        logging.error("Exception occurred while updating stage execution : ", exc_info=True)
        print("Exception occurred while updating stage execution :  : ", e)
        raise e

         
def spin_db_update_custom_gates_navigation_url(pi_executions):
    try:
        for pi_execution in pi_executions:
            application = pi_execution[0]
            pi_execution_data = pi_execution[1]
            pi_stage_execution = pi_execution[2]            
            stage_execution_json = json.loads(pi_stage_execution)
            pi_execution_json = json.loads(pi_execution_data)            
            stage_type = stage_execution_json['type']                       
            pipeline_name = pi_execution_json['name']
            if stage_type == 'approval' and 'navigationalURL' in pi_stage_execution:
               spin_db_update_approval_gate_url(stage_execution_json)
                
            elif (stage_type == 'verification' or stage_type == 'testverification') and ('verificationURL' in pi_stage_execution or 'canaryReportURL' in pi_stage_execution):
                spin_db_update_verification_gate_url(application, pipeline_name, stage_execution_json)
                
            elif stage_type =='policy':
                spin_db_update_policy_gate_url(application, pipeline_name, stage_execution_json)

    except Exception as e:
        logging.error("Exception occurred while updating custom gates : ", exc_info=True)
        print("Exception occurred while updating custom gates : ", e)
        raise e

def get_stage_id(stage_execution_json):
    try:
        return stage_execution_json['id']
    except Exception as e:
        print("Exception occurred while getting the stage id : ", e)
        logging.error("Exception occurred while getting the the stage id : ", exc_info=True)
        raise e


def get_stage_name(stage_execution_json):
    try:
        return stage_execution_json['name']
    except Exception as e:
        print("Exception occurred while getting the stage id : ", e)
        logging.error("Exception occurred while getting the the stage id : ", exc_info=True)
        raise e


def spin_db_update_approval_gate_url(json_data):
    try:
        output_json = json_data['outputs']
        navigational_url = output_json['navigationalURL']
        if navigational_url.find('fromPlugin?instanceId') < 0:
            location = output_json['location']
            words = location.split('/')
            instance_id = words[len(words) - 2]
            logging.info(f"the instance id is:  {instance_id}")
            output_json['navigationalURL'] = navigational_url + '/fromPlugin?instanceId=' + str(instance_id)
            json_data['outputs'] = output_json                               
            logging.info(f"The output after updating approval url is:  {json_data}")            
            updated_stage_execution_data(get_stage_id(json_data),json_data)

    except Exception as e:
        print("Exception occurred while updating approval gate navigation url : ", e)
        logging.error("Exception occurred while updating approval gate navigation url : ", exc_info=True)
        raise e


def spin_db_update_verification_gate_url(application_name, pipeline_name, json_data):
    try:
        output_json = json_data['outputs']
        output_dump = json.dumps(output_json)
        if 'verificationURL' in output_dump:
            output_json['canaryReportURL'] = output_json['verificationURL']            
            json_data['outputs'] = output_json           
            logging.info(f"The output after updating verification gate url is: {json_data}")           
            updated_stage_execution_data(get_stage_id(json_data),json_data)
            return
        canary_report_url = output_json['canaryReportURL']
        if canary_report_url.find('fromPlugin') < 0:
           service_id = get_service_id(application_name, pipeline_name)
           if service_id is not None:
              output_json['canaryReportURL'] = canary_report_url + '/fromPlugin/' + str(service_id)        
              json_data['outputs'] = output_json        
              logging.info(f"The output after updating verification gate url is: {json_data}")        
              updated_stage_execution_data(get_stage_id(json_data),json_data)

    except Exception as e:
        print("Exception occurred while updating verification gate : ", e)
        logging.error("Exception occurred while updating verification gate : ", exc_info=True)
        raise e


def spin_db_update_policy_gate_url(application_name, pipeline_name, json_data):
    try:
        output_json = json_data['outputs']
        output_dump = json.dumps(output_json)
        if 'policyName' in output_dump:
            return
        
        policy_name = get_policy_name(application_name, pipeline_name, get_stage_name(json_data))
        if policy_name is not None:
           output_json['policyName'] = policy_name
           output_json['policyLink'] = '/policy/' + policy_name
           json_data['outputs'] = output_json        #
           logging.info(f"The output after updating policy gate url is: {json_data}")        
           updated_stage_execution_data(get_stage_id(json_data),json_data)

    except Exception as e:
        print("Exception occurred while updating policy gate url : ", e)
        logging.error("Exception occurred while updating policy gate url : ", exc_info=True)
        raise e        


def migrate_spinnaker_audits():
    spinnaker = get_spinnaker()
    date = datetime.datetime.now()
    source_details = SourceDetailsEntity(created_at=date,
                                         updated_at=date,
                                         name=spinnaker[0],
                                         type="spinnaker",
                                         host_url=spinnaker[1],
                                         description=spinnaker[0] + "-" + spinnaker[1])
    source_details_id = insert_source_details(source_details)
    update_source_details_id(source_details_id, "spinnaker")


def migrate_oes_audits():
    date = datetime.datetime.now()
    source_details = SourceDetailsEntity(created_at=date,
                                         updated_at=date,
                                         name="isd-application",
                                         type="OES",
                                         host_url=audit_service_url,
                                         description="isd-application-"+audit_service_url)
    source_details_id = insert_source_details(source_details)
    update_source_details_id(source_details_id, "OES")


def commit_transactions():
    try:
        platform_conn.commit()
        oesdb_conn.commit()
        autopilot_conn.commit()
        audit_conn.commit()
        if spindb_orca_sql is not None and spindb_orca_sql.is_connected():
           spindb_orca_sql.commit()            
        if spindb_front50_sql is not None and spindb_front50_sql.is_connected():
           spindb_front50_sql.commit()
        if spindb_orca_postgres_conn is not None and spindb_orca_postgres_conn.is_connected():
           spindb_orca_postgres_conn.commit()            
        if spindb_front50_postgres_conn is not None and spindb_front50_postgres_conn.is_connected():
           spindb_front50_postgres_conn.commit()
        logging.info("Successfully migrated")
    except Exception as e:
        print("Exception occurred while committing transactions : ", e)
        logging.critical("Exception occurred while committing transactions : ", exc_info=True)
        raise e


def close_connections():
    try:
        platform_conn.close()
        oesdb_conn.close()
        autopilot_conn.close()
        audit_conn.close()
        if audit_conn is not None:
            audit_conn.close()
        if spindb_orca_sql is not None and spindb_orca_sql.is_connected():
            spindb_orca_sql.close()
        if spindb_front50_sql is not None and spindb_front50_sql.is_connected():
            spindb_front50_sql.close()
        if spindb_orca_postgres_conn is not None and spindb_orca_postgres_conn.is_connected():
            spindb_orca_postgres_conn.close()
        if spindb_front50_postgres_conn is not None and spindb_front50_postgres_conn.is_connected():
            spindb_front50_postgres_conn.close()

    except Exception as e:
        logging.warning("Exception occurred while closing the DB connection : ", exc_info=True)


def rollback_transactions():
    try:
        platform_conn.rollback()
        oesdb_conn.rollback()
        autopilot_conn.rollback()
        if audit_conn is not None:
           audit_conn.rollback()
        if spindb_orca_sql is not None and spindb_orca_sql.is_connected():
           spindb_orca.rollback()            
        if spindb_front50_sql is not None and spindb_front50_sql.is_connected():
           spindb_front50.rollback()  
        if spindb_orca_postgres_conn is not None and spindb_orca_postgres_conn.is_connected():
            spindb_orca_postgres_conn.rollback()
        if spindb_front50_postgres_conn is not None and spindb_front50_postgres_conn.is_connected():
            spindb_front50_postgres_conn.rollback()
    except Exception as e:
        logging.critical("Exception occurred while rolling back the transactions : ", exc_info=True)
        raise e


def rollback_audit_db_charts():
    try:
        updatePrimaryKeyAreaCharts()
        updatePrimaryKeyDeliveryInsights()
        audit_conn.commit()
    except Exception as e:
        logging.critical("Exception occurred while rolling back the audit charts primary key transactions : ", exc_info=True)
        raise e


def get_distinct_source():
    try:
        cur_audit.execute("select distinct(source) from audit_events")
        return cur_audit.fetchall()
    except Exception as e:
        print("Exception occurred while getting distinct source : ", e)
        logging.critical("Exception occurred while getting distinct source : ", exc_info=True)
        raise e


def get_spinnaker():
    try:
        cur_oesdb.execute("select name, url from spinnaker order by created_at desc limit 1")
        return cur_oesdb.fetchone()
    except Exception as e:
        print("Exception occurred while getting spinnaker : ", e)
        logging.error("Exception occurred while getting spinnaker : ", exc_info=True)
        raise e


def insert_source_details(source_details):
    try:
        data = source_details.created_at, source_details.updated_at, source_details.description, source_details.host_url, source_details.name, source_details.type
        cur_audit.execute("INSERT INTO source_details (created_at, updated_at, description, host_url, name, type) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id", data)
        return cur_audit.fetchone()[0]
    except Exception as e:
        print("Exception occurred while inserting source details : ", e)
        logging.error("Exception occurred while inserting source details : ", exc_info=True)
        raise e


def update_source_details_id(source_details_id, source):
    try:
        cur_audit.execute(f"update audit_events set source_details_id = {source_details_id} where source = '{source}'")
    except Exception as e:
        print("Exception occurred while updating source_details_id : ", source_details_id)
        logging.error("Exception occurred while updating source_details_id : ", exc_info=True)
        raise e


def delete_records_with_source_null():
    try:
        cur_audit.execute("delete from pipeline_execution_audit_events where audit_events_id IN (select id from audit_events where source IS NULL)")
        cur_audit.execute("delete from audit_events where source IS NULL")
    except Exception as e:
        print("Exception occurred while deleting records by source : ", e)
        logging.error("Exception occurred while deleting records by source : ", e)
        raise e


def add_column_source_details_id():
    try:
        cur_audit.execute("ALTER TABLE audit_events ADD COLUMN IF NOT EXISTS source_details_id int4 default null")
    except Exception as e:
        print("Exception occurred while adding the source_details_id column : ", e)
        logging.error("Exception occurred while adding the source_details_id column : ", exc_info=True)
        raise e


def create_table_source_details():
    try:
        cur_audit.execute("CREATE TABLE IF NOT EXISTS source_details (id serial PRIMARY KEY,"
                          "created_at TIMESTAMPTZ,"
                          "updated_at TIMESTAMPTZ,"
                          "description character varying(255),"
                          "host_url character varying(255) NOT NULL,"
                          "name character varying(255) NOT NULL,"
                          "type character varying(255) NOT NULL)")
    except Exception as e:
        print("Exception occurred while creating source details table : ", e)
        logging.error("Exception occurred while creating source details table : ", exc_info=True)
        raise e


def add_not_null_constraint_to_source_details_id():
    try:
        cur_audit.execute("ALTER TABLE audit_events ALTER COLUMN source_details_id SET NOT NULL")
    except Exception as e:
        print("Exception occured while adding the not null constraint to source details id : ", e)
        logging.error("Exception occured while adding the not null constraint to source details id : ", exc_info=True)
        raise e

def relate_audit_events_and_source_details():
    try:
        cur_audit.execute("ALTER TABLE audit_events DROP CONSTRAINT IF EXISTS fk_source_details_audit")
        cur_audit.execute("ALTER TABLE audit_events ADD CONSTRAINT fk_source_details_audit FOREIGN KEY (source_details_id) REFERENCES source_details(id)")
    except Exception as e:
        print("Exception occurred while add foreign key constraint to source_details table : ", e)
        logging.error("Exception occurred while add foreign key constraint to source_details table : ", exc_info=True)
        raise e


def drop_column_source():
    try:
        cur_audit.execute("ALTER TABLE audit_events DROP COLUMN IF EXISTS source")
    except Exception as e:
        print("Exception occurred while dropping the column source : ", e)
        logging.error("Exception occurred while dropping the column source : ", exc_info=True)
        raise e


def add_columns_in_service_deployment_current():
    try:
        cur_platform.execute(
            "ALTER TABLE service_deployments_current ADD COLUMN IF NOT EXISTS cluster character varying DEFAULT NULL")
        cur_platform.execute(
            "ALTER TABLE service_deployments_current ADD COLUMN IF NOT EXISTS sync character varying DEFAULT NULL")
        cur_platform.execute("ALTER TABLE service_deployments_current ADD COLUMN IF NOT EXISTS location character varying DEFAULT NULL")
    except Exception as e:
        print("Exception occurred while adding columns to service_deployments_current table : ", e)
        logging.error("Exception occurred while adding columns to service_deployments_current table : ", exc_info=True)
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


def persist_cluster_and_location(pipeline_executions):
    try:
        logging.info("Migration to update the cluster and location")
        print("Migration to update the cluster and location")
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
                        image = get_image(context)
                        outputs_manifests = context['outputs.manifests']
                        for outputs_manifest in outputs_manifests:
                            metadata = outputs_manifest['metadata']
                            annotations = metadata['annotations']
                            cluster = annotations['moniker.spinnaker.io/cluster']
                            location = annotations['artifact.spinnaker.io/location']
                            select_data = pipeline_name, app_name
                            cur_platform.execute(
                                "select a.id as application_id, p.id as pipeline_id from applications a LEFT OUTER JOIN service s ON a.id = s.application_id LEFT OUTER JOIN service_pipeline_map spm ON spm.service_id = s.id LEFT OUTER JOIN pipeline p ON spm.pipeline_id = p.id where p.pipeline_name = %s and a.name = %s",
                                select_data)
                            records = cur_platform.fetchall()
                            for record in records:
                                data = cluster, location, record[0], record[1], image
                                logging.info(f"updating cluster and location for the app and pipeline : {select_data}")
                                logging.info(f"data :  {data}")
                                cur_platform.execute("UPDATE service_deployments_current SET cluster = %s , location = %s WHERE application_id = %s and pipeline_id = %s and image = %s", data)
            except KeyError as ke:
                pass
            except Exception as ex:
                print("Exception in nested catch block : ", ex)
                logging.error("Exception in nested catch block:", exc_info=True)
                raise ex
    except Exception as e:
        print("Exception occurred while persisting the cluster and location: ", e)
        logging.error("Exception occurred while persisting the cluster and location:", exc_info=True)
        raise e


def get_image(context):
    image = ""
    try:
        manifests = context['manifests']
        for manifest in manifests:
            kind_name = manifest['kind']
            if kind_name == 'Pod':
                spec = manifest['spec']
                containers = spec['containers']
                for container in containers:
                    image = container['image']
            else:
                spec = manifest['spec']
                template = spec['template']
                template_spec = template['spec']
                containers = template_spec['containers']
                for container in containers:
                    image = container['image']
    except KeyError as ke:
        pass
    return image


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
        print("Exception occurred while updating script : ", e)
        logging.error("Exception occurred while updating script : ", exc_info=True)        
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


def dropDeliveryInsights():
    try:
        cur_audit.execute("drop TABLE IF EXISTS delivery_insights_chart_counts")
        logging.info("Successfully dropped delivery_insights_chart_counts table")
        print("Successfully dropped delivery_insights_chart_counts table")
    except Exception as e:
        print("Exception occurred in dropping delivery_insights_chart_counts while updating script : ", e)
        logging.error("Exception occurred in delivery_insights_chart_counts while updating script: ", exc_info=True)
        raise e

def dropAreaCharts():
    try:
        cur_audit.execute("drop TABLE IF EXISTS area_chart_counts")
        logging.info("Successfully dropped area_chart_counts table")
        print("Successfully dropped area_chart_counts table")
    except Exception as e:
        print("Exception occurred in dropping area_chart_counts table while updating script : ", e)
        logging.error("Exception occurred in dropping area_chart_counts table while updating script: ", exc_info=True)
        raise e

def createDeliveryInsights():
    try:
        cur_audit.execute("CREATE TABLE public.delivery_insights_chart_counts (app_pipeline_name character varying(255) NOT NULL,"
                          "days integer NOT NULL,"
                          "source_id integer NOT NULL,"
                          "app_name character varying(255) NOT NULL,"
                          "avg_execution_duration bigint,"
                          "failed_counts bigint,"
                          "last_run_duration bigint,"
                          "passed_counts bigint,"
                          "PRIMARY KEY (app_pipeline_name, days, source_id))")
        logging.info("Successfully created delivery_insights_chart_counts table")
        print("Successfully created delivery_insights_chart_counts table")
    except Exception as e:
        print("Exception occurred in creating delivery_insights_chart_counts while updating script : ", e)
        logging.error("Exception occurred in creating delivery_insights_chart_counts while updating script: ", exc_info=True)
        raise e

def createAreaCharts():
    try:
        cur_audit.execute("CREATE TABLE public.area_chart_counts (application_name character varying(255) NOT NULL,"
                          "days integer NOT NULL,"
                          "pipeline_name character varying(255) NOT NULL,"
                          "source_id integer NOT NULL,"
                          "status character varying(255) NOT NULL,"
                          "end_dates text NOT NULL, "
                          "PRIMARY KEY (application_name, days, pipeline_name, source_id, status))")
        logging.info("Successfully dropped area_chart_counts table")
        print("Successfully created area_chart_counts table")
    except Exception as e:
        print("Exception occurred in creating area_chart_counts table while updating script : ", e)
        logging.error("Exception occurred in creating area_chart_counts table while updating script: ", exc_info=True)
        raise e


def updatePrimaryKeyDeliveryInsights():
    try:
        cur_audit.execute("ALTER TABLE IF EXISTS public.delivery_insights_chart_counts DROP CONSTRAINT delivery_insights_chart_counts_pkey")
        cur_audit.execute("ALTER TABLE IF EXISTS public.delivery_insights_chart_counts ADD CONSTRAINT delivery_insights_chart_counts_pkey(app_pipeline_name, days))");
        logging.info("Successfully updated the PRIMARY KEY area_chart_counts table")
        print("Successfully updated the PRIMARY KEY delivery_insights_chart_counts table")
    except Exception as e:
        print("Exception occurred in creating delivery_insights_chart_counts table while updating script : ", e)
        logging.error("Exception occurred in creating delivery_insights_chart_counts table while updating script: ", exc_info=True)
        raise e


def updatePrimaryKeyAreaCharts():
    try:
        cur_audit.execute("ALTER TABLE IF EXISTS public.area_chart_counts DROP CONSTRAINT area_chart_counts_pkey")
        cur_audit.execute("ALTER TABLE IF EXISTS public.area_chart_counts ADD CONSTRAINT   area_chart_counts_pkey (application_name, days, pipeline_name, status))");
        logging.info("Successfully updated the PRIMARY KEY area_chart_counts table")
        print("Successfully updated the PRIMARY KEY area_chart_counts table")
    except Exception as e:
        print("Exception occurred in creating area_chart_counts table while updating script : ", e)
        logging.error("Exception occurred in creating area_chart_counts table while updating script: ", exc_info=True)
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
            "select id, pipeline_json from pipeline where not pipeline_json::jsonb ->> 'stages' = '[]'")
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


def updateApprovalGateAudit():
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
                        logging.info("GateId: {},pipelineId: {} ,applicationName: {} ,audit_events_table_id :{}".format(gateId,
                                                                                                                 pipelineId,
                                                                                                                 applicationName,
                                                                                                                 audit_events_table_id))
                        fetchJsonAndUpdate(audit_events_table_id, applicationName, jsonData)
    except Exception as e:
        print("Exception occurred while updating application name in audit events table : ", e)
        logging.error("Exception occurred updating application name in audit events table :", exc_info=True)
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


def processPipelineJsonForExistingGates():
    try:
        cur_platform.execute(
            "select a.id as application_id , a.name as application_name , sp.service_id, g.id as gate_id, g.gate_name, g.gate_type, gp.pipeline_id "
            "from applications a left outer join service s on a.id = s.application_id left outer join service_pipeline_map sp on s.id=sp.service_id "
            "left outer join gate_pipeline_map gp on sp.pipeline_id=gp.pipeline_id left outer join service_gate g on gp.service_gate_id=g.id where a.source = 'Spinnaker' and g.id is not null")
        records = cur_platform.fetchall()
        cookie = "no-cookie"
        userGroupsData = getApprovalGroupsDataJson()
        if spin_db_type == 'redis':
           activateSpinnakerSession()
        for record in records:
            logging.info("Record:"+str(record))
            applicationId = record[0]
            appName = record[1]
            serviceId = record[2]
            gateId = record[3]
            gateName = record[4]
            gateType = record[5]
            pipelineId = record[6]
            env_json = formEnvJson(gateId)
            payloadConstraint = formPayloadConstraint()
            stageJson = None
            if gateType.__eq__("policy"):
                stageJson = policyGateProcess(applicationId, serviceId, gateId, gateName, gateType,
                                              payloadConstraint, pipelineId, env_json)
            elif gateType.__eq__("verification"):
                stageJson = verificationGateProcess(applicationId, serviceId, gateId, gateName, gateType,
                                                    payloadConstraint, pipelineId, env_json)
            elif gateType.__eq__("approval"):
                stageJson = approvalGateProcess(applicationId, serviceId, gateId, gateName, gateType,
                                                payloadConstraint, pipelineId, env_json, userGroupsData)
            if stageJson is not None:
                stageJson["application"] = appName
                logging.info(f"StageJson is :  {stageJson}")
                pipelineJson = updatePipelineJson(pipelineId, stageJson)
                if spin_db_type == 'redis':     
                   postingGateJson(pipelineJson, cookie)
                else:            
                   postingGateJsonSQL(pipelineJson)

    except Exception as e:
        print("Exception occurred while processing the pipeline json for existing gates : ", e)
        logging.error("Exception occurred while processing the pipeline json for existing gates :", exc_info=True)
        raise e


def activateSpinnakerSession(cookie):
    try:
        empty_json = json.loads('{}')         
        api_url = sapor_host_url+"/oes/appOnboarding/spinnaker/pipeline/stage"        
        headers = {'Content-Type': 'application/json', 'x-user-cookie' : cookie,
                   'x-spinnaker-user': isd_admin_username}
        response = requests.post(url=api_url, headers=headers, data=json.dumps(empty_json)) 
        # expected api response is 401 (if session expired) or NPE (since we are passing empty json); raise exception for any other case
        if response.status_code != 401:
           logging.info("The response from dummy Sapor API call is : " + str(response.content) + '\n')
           if 'NullPointerException' not in str(response.content):
              raise Exception("Sapor API response shows failure!")
    except Exception as e:
        print("Exception activateSpinnakerSession : ", e)
        logging.error("Exception activateSpinnakerSession :  :", exc_info=True)
        raise e


def formEnvJson(gateId):
    try:
        cur_platform.execute(
            "select ae.spinnaker_environment_id , ae.environment from app_environment ae left outer join service_gate sg on ae.id=sg.app_environment_id where sg.id=" + str(
                gateId))
        spinnakerEnvironments = cur_platform.fetchone()
        spinnakerEnvironmentId = spinnakerEnvironments[0]
        spinnakerEnvironmentName = spinnakerEnvironments[1]
        env_json = [{
            "id": spinnakerEnvironmentId,
            "spinnakerEnvironment": str(spinnakerEnvironmentName)
        }]
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


def verificationParametersDataFilter(gateId, env_json_formatted, applicationId):
    try:
        logAndMetricInfoRes = getLogAndMetricName(applicationId, gateId)
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
            "logTemplate": logAndMetricInfoRes[0],
            "metricTemplate": logAndMetricInfoRes[1],
            "minicanaryresult": ""
        }
        return verification_pipeline_json
    except Exception as e:
        print("Exception occurred while processing the verification pipeline json for existing gates : ", e)
        logging.error("Exception occurred while processing the verification pipeline json for existing gates :",
                      exc_info=True)
        raise e


def getLogAndMetricName(applicationId, gateId):
    try:
        data = applicationId, gateId
        cur_autopilot.execute("select ulst.templatename, ust.pipeline_id from servicegate s left outer join userlogservicetemplate ulst on s.logtemplate_id = ulst.opsmx_id left outer join  userservicetemplate ust on s.metrictemplate_id = ust.opsmx_id where  s.application_id=%s and s.gateid=%s", data)
        result = cur_autopilot.fetchone()
        logging.info(f"getLogAndMetricName response : {result}")
        if result is not None:
           return  result
    except Exception as e:
        print("Exception occurred while fetching log and metric template name: ", e)
        logging.error("Exception occurred while fetching log and metric template name:", exc_info=True)
        raise e


def verificationGateProcess(applicationId, serviceId, gateId, gateName, gateType, payloadConstraint, pipelineId,
                            env_json_formatted):
    try:
        logging.info("process verification gate json for application Id: " + str(applicationId) + " ,serviceId: " + str(
            serviceId) + " ,gateId: " + str(gateId))
        parameters = verificationParametersDataFilter(gateId, env_json_formatted,applicationId)
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


def approvalGateProcess(applicationId, serviceId, gateId, gateName, gateType, payloadConstraint, pipelineId, env_json, userGroupsData):
    try:
        logging.info("process approval gate json for application Id: " + str(applicationId) + " ,serviceId: " + str(
            serviceId) + " ,gateId: " + str(gateId))
        parameters = approvalParametersDataFilter(gateId, env_json, payloadConstraint, userGroupsData)
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


def approvalParametersDataFilter(gateId, env_json_formatted, payloadConstraint, userGroupsData):
    try:
        approvalGroupsData = getApprovalGroupsDataFilter(gateId, userGroupsData)
        automatedApproval = getAutomatedApproval(gateId)
        isAutomatedApproval = len(automatedApproval) > 0
        approvalGateId = getApprovalGateId(gateId)
        selectedConnectors = getSelectedConnectors(approvalGateId)
        approval_pipeline_json = {
            "approvalGroups": approvalGroupsData,
            "automatedApproval": automatedApproval,
            "isAutomatedApproval":isAutomatedApproval,
            "connectors": "",
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


def getApprovalGateId(gateId):
    try:
        cur_visibility.execute("select approval_gate_id From approval_service_gate_map where service_gate_id =" + str(gateId))
        result = cur_visibility.fetchone()
        if result is not None:
            return result[0]
    except Exception as e:
        print("Exception occurred while fetching approval gate Id by service gate Id: ", e)
        logging.error("Exception occurred while fetching approval gate Id by service gate Id", exc_info=True)
        raise e


def getApprovalGroupsName(gateId):
    try:
        data = gateId
        cur_platform.execute( "SELECT ug.name FROM user_group_permission_3_12 ugp LEFT OUTER JOIN user_group ug ON ugp.group_id = ug.id  where ugp.object_type ='APPROVAL_GATE' and ugp.object_id=%s",[data])
        return cur_platform.fetchall()        
    except Exception as e:
        print("Exception occurred while fetching usergroups permission resources: ", e)
        logging.error("Exception occurred while fetching usergroups permission resources:", exc_info=True)
        raise e

def getApprovalGroupsDataJson():
    try:
        URL = platform_host_url + "/platformservice/v2/usergroups"
        logging.info(URL)
        response = requests.get(url=URL)
        return response.json()
    except Exception as e:
        print("Exception occurred while fetching approval groups data : ", e)
        logging.error("Exception occurred while fetching approval groups data:", exc_info=True)
        raise e


def getApprovalGroupsDataFilter(gateId, userGroupsData):
    dataList = []
    approvalGroupList = getApprovalGroupsName(gateId)
    for approvalGroupName in approvalGroupList:
        groupDetails = getApprovalGroupData(approvalGroupName[0], userGroupsData)
        if groupDetails is not None:
           dataList.append(groupDetails)
    logging.info("Fetched approval groups data for gateId- " + str(gateId) + str(dataList))
    return dataList
    
    
def getApprovalGroupData(groupName, userGroupsData):
    for userGroup in userGroupsData:
        if groupName == userGroup['userGroupName']:
           return userGroup

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


def getConnectorsConfiguredNames(approvalGateId):
    try:
        connectors = []
        data = approvalGateId 
        cur_visibility.execute("select datasource_name from approval_gate_tool_connector where approval_gate_id=%s", [data])
        connectorsNames = cur_visibility.fetchall()
        if connectorsNames is not None:
           for connectorName in connectorsNames:            
               connectorTypeAndName = getConnectorData(connectorName[0]) 
               connectorData = {
                    "connector": connectorTypeAndName[0],
                    "account": connectorTypeAndName[1]
               }
               connectors.append(connectorData)
        logging.info("Gate Id :%s, Connectors :%s",str(approvalGateId), str(connectors))
        return  connectors
    except Exception as e:
        print("Exception occurred while fetching connector configured names : ", e)
        logging.error("Exception occurred while fetching connector configured names:", exc_info=True)
        raise e
def getConnectorData(connectorName):
    try:
        data = connectorName 
        cur_platform.execute("SELECT datasourcetype, name FROM datasource WHERE name=%s ", [data])
        return cur_platform.fetchone()
    except Exception as e:
        print("Exception occurred while fetching connector configured names : ", e)
        logging.error("Exception occurred while fetching connector configured names:", exc_info=True)
        raise e


def getSelectedConnectors(approvalGateId):
    try:
        logging.info("Formatting selected connectors for gateId: " + str(approvalGateId))
        mainData = getConnectorsConfiguredNames(approvalGateId)
        defaultData = [{
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
            ],
            "values": []
        }]
        defaultData[0]["values"] = mainData
        return defaultData
    except Exception as e:
        print(
            "Exception occurred while processing the approval supported parameter pipeline json for existing gates : ",
            e)
        logging.error(
            "Exception occurred while processing the approval supported parameter pipeline json for existing gates ",
            exc_info=True)
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

                        if newsPipelineGateType.__eq__("approval"):
                            stageJson["parameters"]["connectors"] = stage["parameters"]["connectors"]
                        stage = stageJson
                except KeyError as ke:
                    print("Exception occurred while formatting pipeline Json to update in db: ")
                    logging.error("Exception occurred while formatting pipeline Json to update in db: ", exc_info=True)
                    raise ke
                updated_stages.append(stage)

            dbPipelineJson["stages"] = updated_stages
            try:
                dbPipelineJson["index"] = int(dbPipelineJson["index"])
            except KeyError as ke:
                pass
            return dbPipelineJson
    except Exception as e:
        print("Exception occurred while formatting pipeline Json to update in db: ", e)
        logging.error("Exception occurred while formatting pipeline Json to update in db", exc_info=True)
        raise e


def postingGateJsonSQL(pipelineJson):
    try:
        pipeline_id = pipelineJson['id']
        update_data = json.dumps(pipelineJson), isd_admin_username, pipeline_id        
        sql = "UPDATE pipelines SET body = %s, last_modified_by = %s WHERE id = %s"        
        if spin_db_type == 'sql':
           mysqlcursor_front50 = spindb_front50_sql.cursor()
           mysqlcursor_front50.execute(sql, update_data)
           mysqlcursor_front50.close()
        elif spin_db_type == 'postgres':
           spindb_front50_postgres.execute(sql, update_data)

    except Exception as e:
        print("Exception occurred while posting gate: ", e)
        logging.error("Exception occurred while posting gate", exc_info=True)
        raise e

def postingGateJson(pipelineJson, cookie):
    try:
        api_url = sapor_host_url+"/oes/appOnboarding/spinnaker/pipeline/stage"
        logging.info(api_url)
        headers = {'Content-Type': 'application/json', 'x-user-cookie' : cookie,
                   'x-spinnaker-user': isd_admin_username}
        response = requests.post(url=api_url, headers=headers, data=json.dumps(pipelineJson))
        logging.info("The response status is: " + str(response.status_code))
        if (response.status_code == 200 | response.status_code == 201):
            logging.info("Successfully added stage")
        else:
            print("Failed to add stage; The response is: "+str(response.content))
            logging.info("Failed to add stage; The response is:\n" + str(response.content) + '\n')
            raise Exception("Sapor API response shows failure!")
    except Exception as e:
        print("Exception occurred while posting gate: ", e)
        logging.error("Exception occurred while posting gate", exc_info=True)
        raise e


def get_redis_conn():
    if spin_db_type == 'redis':   
        #Establishing the redis connection       
        redis = redis.Redis(host=redis_host, port=redis_port, password=redis_password)
        print("Redis connection established successfully")
        return redis


def get_sql_orca_db_conn():
    sqldb_orca = None
    if spin_db_type == 'sql':
        #Establishing the spinnaker orca sql database connection
        if migrate_data_flag == 'true':
            sqldb_orca = mysql.connector.connect(database='orca', user=spin_db_username, password=spin_db_password, host=spin_db_host, autocommit = True)
        else:
            sqldb_orca = mysql.connector.connect(database='orca', user=spin_db_username, password=spin_db_password, host=spin_db_host)
        print("Spinnaker orca database connection established successfully")         
        return sqldb_orca

def get_sql_front50_db_conn():
    sqldb_front50 = None
    if spin_db_type == 'sql':
        #Establishing the spinnaker front50 sql database connection
        if migrate_data_flag == 'true':
            sqldb_front50 = mysql.connector.connect(database='front50', user=spin_db_username, password=spin_db_password, host=spin_db_host, autocommit = True)
        else:
            sqldb_front50 = mysql.connector.connect(database='front50', user=spin_db_username, password=spin_db_password, host=spin_db_host)
        print("Spinnaker front50 database connection established successfully")         
        return sqldb_front50

def get_postgres_orca_db_conn():
    if spin_db_type == 'postgres':
        #Establishing the spinnaker orca postgres database connection       
        postgresdb_orca = psycopg2.connect(database='orca', user=spin_db_username, password=spin_db_password, host=spin_db_host,port=spin_db_port)
        if migrate_data_flag == 'true':
           postgresdb_orca.autocommit = True
        print("Spinnaker orca database connection established successfully")         
        return postgresdb_orca

def get_postgres_front50_db_conn():
    if spin_db_type == 'postgres':
        #Establishing the spinnaker front50 postgres database connection       
        postgresdb_front50 = psycopg2.connect(database='front50', user=spin_db_username, password=spin_db_password, host=spin_db_host,port=spin_db_port)
        if migrate_data_flag == 'true':
           postgresdb_front50.autocommit = True
        print("Spinnaker front50 database connection established successfully")         
        return postgresdb_front50

def addDBVersion(version):
    try:
        # create db_version table if not exists
        cur_platform.execute("CREATE TABLE IF NOT EXISTS db_version (id serial PRIMARY KEY,"
                             "version_no character varying(20) NOT NULL,"
                             "created_at TIMESTAMPTZ,"
                             "updated_at TIMESTAMPTZ)")
        # set db version
        date = datetime.datetime.now()        
        data = version,date,date
        cur_platform.execute("DELETE FROM  db_version WHERE version_no ="+str(version))
        cur_platform.execute("INSERT INTO db_version (version_no, created_at, updated_at) VALUES (%s, %s, %s)",data)
    except Exception as e:
        print("Exception occurred while adding db version : ", e)
        logging.error("Exception occurred while adding db version  : ", exc_info=True)
        raise e
def verifyDBVersion(version):
    try:
        # fetch db_version from platform db
        cur_platform.execute("select version_no from db_version order by updated_at desc limit 1")
        db_version = cur_platform.fetchone()
        if db_version is not None: 
           if db_version[0] != version:
              raise Exception("Version mismatch! Cannot proceed with the data migration. Expected db version :"+version+" found db version : "+db_version[0])
           else:
              logging.info("Verified schema version. Schema version is : "+ db_version[0])  
        else:
           logging.info("Failed fetch the ISD Schema version from Platform DB")       
           raise Exception("Failed fetch the ISD Schema version from Platform DB")
    except Exception as e:
        print("Exception occurred while fetching db version : ", e)
        logging.error("Exception occurred while fetching db version  : ", exc_info=True)
        raise e

if __name__ == '__main__':
    n = len(sys.argv)

    if n != 26:
        print(
            "Please pass valid 25 arguments <platform_db-name> <platform_host> <oes-db-name> <oes-db-host> <autopilot-db-name> <autopilot-db-host> <audit_db-name> <audit-db-host> <visibility_db-name> <visibility-db-host> "
            "<db-port> <user-name> <password> <isd-gate-url> <isd-admin-username> <isd-admin-password> <sapor-host-url> <audit-service-url> <redis/sql/postgres> <redis-host/sql-host/postgres-host> <redis-port/sql-port/postgres-port> <redis-username/sql-username/postgres-username> <redis-password/sql-password/postgres-password> <migration-flag> <isd-platform-url>")
        exit(1)


    logging.basicConfig(filename='/tmp/migration_v3.12.x_to_v4.0.x.log', filemode='w',
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
    sapor_host_url = sys.argv[17]
    audit_service_url = sys.argv[18]
    spin_db_type = sys.argv[19]

    global redis_host
    global redis_port
    global redis_username
    global redis_password

    global spin_db_host
    global spin_db_port
    global spin_db_username
    global spin_db_password
    if spin_db_type == 'redis':     
       redis_host = sys.argv[20]
       redis_port = sys.argv[21]
       redis_username = sys.argv[22]
       redis_password = sys.argv[23]
    else:
       spin_db_host = sys.argv[20]
       spin_db_port = sys.argv[21]
       spin_db_username = sys.argv[22]
       spin_db_password = sys.argv[23]

    migrate_data_flag = sys.argv[24]
    platform_host_url = sys.argv[25]

    # Establishing the platform db connection
    platform_conn = psycopg2.connect(database=platform_db, user=user_name, password=password, host=platform_host,port=port)
    print('Opened platform database connection successfully')

    # Establishing the oesdb db connection
    oesdb_conn = psycopg2.connect(database=oes_db, user=user_name, password=password, host=oes_host, port=port)
    print("Sapor database connection established successfully")

    # Establishing the opsmx db connection
    autopilot_conn = psycopg2.connect(database=autopilot_db, user=user_name, password=password, host=autopilot_host, port=port)
    print("autopilot database connection established successfully")

    # Establishing the audit db connection
    audit_conn = psycopg2.connect(database=audit_db, user=user_name, password=password, host=audit_host, port=port)
    print('Opened audit database connection successfully')

    # Establishing the visibility db connection
    visibility_conn = psycopg2.connect(database=visibility_db, user=user_name, password=password, host=visibility_host, port=port)
    print("Visibility database connection established successfully")
     

    redis_conn = get_redis_conn()
    cur_platform = platform_conn.cursor()
    cur_oesdb = oesdb_conn.cursor()
    cur_autopilot = autopilot_conn.cursor()
    cur_audit = audit_conn.cursor()
    cur_visibility = visibility_conn.cursor()
    spindb_orca_sql = get_sql_orca_db_conn()
    spindb_front50_sql = get_sql_front50_db_conn()    
    spindb_orca_postgres_conn = get_postgres_orca_db_conn()
    spindb_front50_postgres_conn = get_postgres_front50_db_conn()
    spindb_orca_postgres =  None   
    spindb_front50_postgres = None
    if spindb_orca_postgres_conn is not None:
       spindb_orca_postgres =  spindb_orca_postgres_conn.cursor()
    if spindb_front50_postgres_conn is not None:
       spindb_front50_postgres = spindb_front50_postgres_conn.cursor()    


   #check if it is pre-upgrade DB Update or post-upgrade Data Migration     
    if migrate_data_flag == 'false':        
        update_db("4.0.3")      # Note: version here should be updated for each ISD release
    elif migrate_data_flag == 'true':        
        audit_conn.autocommit = True
        platform_conn.autocommit = True
        perform_migration("4.0.3")       # pass the ISD version we are performing data migration for (Note: version here should be updated for each ISD release)

