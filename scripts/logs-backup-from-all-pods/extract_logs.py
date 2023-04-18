import datetime
import logging
import subprocess
import sys
import json

import psycopg2
import redis
import requests
from datetime import datetime, timedelta
import mysql.connector


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


def get_response(url, cookie):
    try:
        logging.info(url)
        headers = {'cookie': cookie}
        request = requests.get(url=url, headers=headers)
        logging.info(f"getResponse response : {request}")
        return request.json()
    except Exception as e:
        print("Exception occurred while fetching the gate response: ", e)
        logging.error("Exception occurred while fetching the gate response: ", exc_info=True)
        raise e


def get_pipelines_executed_users_count_from_redis():
    keys = redis_conn.keys("pipeline:*:stageIndex")
    names = set()
    if days.strip() != 'None':
        pl_key_exec_dict = {}
        for key in keys:
            executions = redis_conn.lrange(key, 0, -1)
            plKey = key[:35]
            pl_key_exec_dict[plKey] = executions[len(executions) - 1]
        # print("The pl_key_exec_dict is: ", pl_key_exec_dict)
        date = datetime.now() - datetime(1970, 1, 1)
        date = date - timedelta(days=int(days))
        seconds = (date.total_seconds())
        epoch_start_date = round(seconds * 1000)
        for plKey, execution in pl_key_exec_dict.items():
            exec_str = str(execution.decode("utf-8"))
            field = "stage." + exec_str + ".endTime"
            time = redis_conn.hget(plKey, field)
            # if no time then consider start_time
            if time is None:
                field = "stage." + exec_str + ".startDate"
                time = redis_conn.hget(plKey, field)
                if time is None:
                    continue
            time = str(time.decode("utf-8"))
            time = int(time)
            if epoch_start_date <= time:
                trigger_bytes = redis_conn.hget(plKey, "trigger")
                trigger_str = str(trigger_bytes.decode("utf-8"))
                trigger_json = json.loads(trigger_str)
                name = trigger_json['user']
                names.add(name)
    else:
        for key in keys:
            plKey = key[:35]
            trigger_bytes = redis_conn.hget(plKey, "trigger")
            trigger_str = str(trigger_bytes.decode("utf-8"))
            trigger_json = json.loads(trigger_str)
            name = trigger_json['user']
            names.add(name)
    print("names: ", names)
    return len(names)


def get_no_of_active_users_count():
    if days.strip() != 'None':
        sql = "SELECT count(distinct  data->'auditData'-> 'source'->> 'name') FROM audit_events WHERE data->>'eventType' @@ ' AUTHENTICATION_SUCCESSFUL_AUDIT' AND created_at >= %s"
        date = datetime.now() - timedelta(days=int(days))
        cur_audit.execute(sql, [date])
    else:
        sql = "SELECT count(distinct  data->'auditData'-> 'source'->> 'name') FROM audit_events WHERE data->>'eventType' @@ ' AUTHENTICATION_SUCCESSFUL_AUDIT'"
        cur_audit.execute(sql)
    return cur_audit.fetchone()[0]


def get_pipelines_executed_users_count_from_sql():
    names = set()
    if days.strip() != 'None':
        date = datetime.now() - datetime(1970, 1, 1)
        date = date - timedelta(days=int(days))
        seconds = (date.total_seconds())
        epoch_start_date = round(seconds * 1000)
        sqldb_orca_cursor.execute("select body from pipelines where start_time >= %s", [epoch_start_date])
        pipeline_executions = sqldb_orca_cursor.fetchall()
    else:
        sqldb_orca_cursor.execute("select body from pipelines")
        pipeline_executions = sqldb_orca_cursor.fetchall()
    for pipeline_execution in pipeline_executions:
        pi_execution_json = json.loads(pipeline_execution[0])
        trigger = pi_execution_json['trigger']
        user = trigger['user']
        names.add(user)
    return len(names)


def start_extraction():
    try:
        cookie = login_to_isd()
        # get applications count
        url = isd_gate_url + "/applications"
        apps = get_response(url, cookie)
        apps_count = len(apps)
        # print("apps_count: ", apps_count)
        pipelines_count = 0
        for app in apps:
            name = app['name']
            url = isd_gate_url + "/applications/" + name + "/pipelineConfigs"
            pipelines = get_response(url, cookie)
            pipelines_count = pipelines_count + len(pipelines)
        # print("pipelines_count: ", pipelines_count)
        cookie = login_to_isd()
        url = isd_gate_url + "/credentials"
        cloud_accounts = get_response(url, cookie)
        cloud_accounts_count = len(cloud_accounts)
        # print("cloud_accounts_count: ", cloud_accounts_count)
        users = redis_conn.keys(
            "spring:session:index:org.springframework.session.FindByIndexNameSessionRepository.PRINCIPAL_NAME_INDEX_NAME:*")
        users_count = len(users)
        # print("users_count: ", users_count)
        if spin_db_type == 'sql':
            no_of_users_executed_pipelines = get_pipelines_executed_users_count_from_sql()
        else:
            no_of_users_executed_pipelines = get_pipelines_executed_users_count_from_redis()
        # print("no_of_users_executed_pipelines: ", no_of_users_executed_pipelines)
        f = open("/tmp/logdir/usage_counts.txt", "w")
        f.write("apps_count: " + str(apps_count) + "\n")
        f.write("pipelines_count: " + str(pipelines_count) + "\n")
        f.write("cloud_accounts_count: " + str(cloud_accounts_count) + "\n")
        f.write("users_count: " + str(users_count) + "\n")
        if days.strip() != 'None':
            dys = days
        else:
            dys = "all"
        f.write(
            "no_of_users_executed_pipelines: " + str(no_of_users_executed_pipelines) + " for " + dys + " days" + "\n")
        if installation_type == 'ISD':
            no_of_active_users_count = get_no_of_active_users_count()
            f.write("no_of_active_users_count: " + str(no_of_active_users_count) + " for " + dys + " days" + "\n")
            # print("no_of_active_users_count: ", no_of_active_users_count)
        f.close()
    except Exception as e:
        print("Exception occurred while computing the application counts: ", e)
        logging.error("Exception occurred while computing the application counts: ", exc_info=True)
        raise e
    finally:
        redis_conn.close()
        audit_conn.close()
        if spin_db_type == 'sql':
            sqldb_orca.close()
    pass


if __name__ == '__main__':
    n = len(sys.argv)
    if n != 18:
        print("Please pass valid 17 arguments <isd-admin-username> <isd-admin-password> <redis-host> "
              "<redis-port> <redis-password> <isd-gate-url> <days> <installation_type> <audit_db> <audit_host> <user_name> <password> <port> <spin_db_type> <spin_db_username> <spin_db_password> <spin_db_host>")
        exit(1)

    global is_error_occurred
    is_error_occurred = False

    logging.basicConfig(filename='/tmp/extract_logs.log', filemode='w',
                        format="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s", datefmt='%H:%M:%S',
                        level=logging.INFO)

    isd_admin_username = sys.argv[1]
    isd_admin_password = sys.argv[2]
    redis_host = sys.argv[3]
    redis_port = sys.argv[4]
    redis_password = sys.argv[5]
    isd_gate_url = sys.argv[6]
    days = sys.argv[7]
    installation_type = sys.argv[8]
    audit_db = sys.argv[9]
    audit_host = sys.argv[10]
    user_name = sys.argv[11]
    password = sys.argv[12]
    port = sys.argv[13]
    spin_db_type = sys.argv[14]
    spin_db_username = sys.argv[15]
    spin_db_password = sys.argv[16]
    spin_db_host = sys.argv[17]
    # Establishing the redis connection
    redis_conn = redis.Redis(host=redis_host, port=redis_port, password=redis_password)
    print("Redis connection established successfully")

    # Establishing the platform db connection
    if port == '0':
        audit_conn = psycopg2.connect(database=audit_db, user=user_name, password=password, host=audit_host)
    else:
        audit_conn = psycopg2.connect(database=audit_db, user=user_name, password=password, host=audit_host, port=port)
    sqldb_orca_cursor = None
    if spin_db_type == 'sql':
        sqldb_orca = mysql.connector.connect(database='orca', user=spin_db_username, password=spin_db_password,
                                             host=spin_db_host)
        sqldb_orca_cursor = sqldb_orca.cursor(buffered=True)
    print('Opened audit database connection successfully')
    cur_audit = audit_conn.cursor()
    start_extraction()