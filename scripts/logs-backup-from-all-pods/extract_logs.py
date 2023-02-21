import datetime
import logging
import subprocess
import sys
import json

import psycopg2
import redis
import requests
from datetime import datetime, timedelta

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
        headers = {'cookie': cookie, 'x-spinnaker-user': isd_admin_username}
        request = requests.get(url=url, headers=headers)
        logging.info(f"getResponse response : {request}")
        return request.json()
    except Exception as e:
        print("Exception occurred while fetching the gate response: ", e)
        logging.error("Exception occurred while fetching the gate response: ", exc_info=True)
        raise e


def get_pipelines_executed_users_count():
    keys = redis_conn.keys("pipeline:*:stageIndex")
    names = set()
    if days.strip() != 'None':
        pl_key_exec_dict = {}
        for key in keys:
            executions = redis_conn.lrange(key, 0, -1)
            plKey = key[:35]
            pl_key_exec_dict[plKey] = executions[len(executions) - 1]
        # print("The pl_key_exec_dict is: ", pl_key_exec_dict)
        date = datetime.datetime.now() - datetime.datetime(1970, 1, 1)
        date = date - datetime.timedelta(days=int(days))
        seconds = (date.total_seconds())
        epoch_start_date = round(seconds*1000)
        # print("epoch_start_date: ", epoch_start_date)
        for plKey, execution in pl_key_exec_dict.items():
            exec_str = str(execution.decode("utf-8"))
            field = "stage." + exec_str + ".endTime"
            time = redis_conn.hget(plKey, field)
            # if no time then consider start_time
            if time is None:
                field = "stage." + exec_str + ".startDate"
                time = redis_conn.hget(plKey, field)
                if time is None:
                    # print("No start and end dates found for ", plKey)
                    continue
            time = str(time.decode("utf-8"))
            time = int(time)
            # print("The time is: ", time)
            if epoch_start_date <= time:
                # print("Found in time execution")
                trigger_bytes = redis_conn.hget(plKey, "trigger")
                trigger_str = str(trigger_bytes.decode("utf-8"))
                trigger_json = json.loads(trigger_str)
                name = trigger_json['user']
                # print("and the user in time execution is: ", name)
                names.add(name)
    else:
        for key in keys:
            plKey = key[:35]
            trigger_bytes = redis_conn.hget(plKey, "trigger")
            trigger_str = str(trigger_bytes.decode("utf-8"))
            trigger_json = json.loads(trigger_str)
            name = trigger_json['user']
            names.add(name)
    # print("names: ", names)
    return len(names)


def get_no_of_active_users_count():
    if days.strip() != 'None':
        sql = "select count(*) from(select * from ( select q3.name, q3.created_at, q3.eventType, rank() over(PARTITION BY " \
              "q3.name order by q3.created_at desc) as rank_no from (SELECT distinct " \
              "q1.data->'auditData'->'source'->>'name' as name, created_at, data->>'eventType' as eventType FROM " \
              "audit_events q1 where q1.data->>'eventType' in ('SUCCESSFUL_USER_LOGOUT_AUDIT')  and created_at >= %s  " \
              "union select distinct q2.data->'auditData'->>'userName' as name, q2.created_at, q2.data->>'eventType' as " \
              "eventType FROM audit_events q2 where q2.data->>'eventType' in ('USER_ACTIVITY_AUDIT')  and created_at >= " \
              "%s ) as q3) as q4 where q4.rank_no = 1 order by q4.created_at desc) as q6 where q6.eventType not in (" \
              "'SUCCESSFUL_USER_LOGOUT_AUDIT')"
        date = datetime.now() - timedelta(days=int(days))
        data = date,date
        cur_audit.execute(sql, data)
    else:
        sql = "select count(*) from(select * from ( select q3.name, q3.created_at, q3.eventType, rank() over(PARTITION BY " \
              "q3.name order by q3.created_at desc) as rank_no from (SELECT distinct " \
              "q1.data->'auditData'->'source'->>'name' as name, created_at, data->>'eventType' as eventType FROM " \
              "audit_events q1 where q1.data->>'eventType' in ('SUCCESSFUL_USER_LOGOUT_AUDIT') union select distinct " \
              "q2.data->'auditData'->>'userName' as name, q2.created_at, q2.data->>'eventType' as eventType FROM " \
              "audit_events q2 where q2.data->>'eventType' in ('USER_ACTIVITY_AUDIT')) as q3) as q4 where q4.rank_no " \
              "= 1 order by q4.created_at desc) as q6 where q6.eventType not in ('SUCCESSFUL_USER_LOGOUT_AUDIT')"
        cur_audit.execute(sql)
    return cur_audit.fetchone()[0]


def start_extraction():
    try:
        cookie = login_to_isd()
        # get applications count
        url = isd_gate_url + "/applications"
        apps = get_response(url, cookie)
        apps_count = len(apps)
        print("apps_count: ", apps_count)
        pipelines_count = 0
        # for app in apps:
        #     name = app['name']
        #     url = isd_gate_url +  "/applications/" + name + "/pipelineConfigs"
        #     pipelines = get_response(url, cookie)
        #     pipelines_count = pipelines_count + len(pipelines)
        print("pipelines_count: ", pipelines_count)
        cookie = login_to_isd()
        url = isd_gate_url + "/credentials"
        cloud_accounts = get_response(url, cookie)
        cloud_accounts_count = len(cloud_accounts)
        print("cloud_accounts_count: ", cloud_accounts_count)
        users = redis_conn.keys(
            "spring:session:index:org.springframework.session.FindByIndexNameSessionRepository.PRINCIPAL_NAME_INDEX_NAME:*")
        users_count = len(users)
        print("users_count: ", users_count)
        no_of_users_executed_pipelines = 0 #get_pipelines_executed_users_count()
        print("no_of_users_executed_pipelines: ", no_of_users_executed_pipelines)
        f = open("/tmp/logdir/usage_counts.txt", "w")
        f.write("apps_count: "+ str(apps_count) + "\n")
        f.write("pipelines_count: "+ str(pipelines_count)+ "\n")
        f.write("cloud_accounts_count: "+ str(cloud_accounts_count)+ "\n")
        f.write("users_count: "+ str(users_count)+ "\n")
        if days.strip() != 'None':
            dys = days
        else:
            dys = "all"
        f.write("no_of_users_executed_pipelines: "+ str(no_of_users_executed_pipelines)+ " for " + dys + " days"+"\n")
        if installation_type == 'ISD':
            no_of_active_users_count = get_no_of_active_users_count()
            f.write("no_of_active_users_count: "+ str(no_of_active_users_count)+ " for " + dys + " days"+"\n")
            print("no_of_active_users_count: ", no_of_active_users_count)
        f.close()
    except Exception as e:
        print("Exception occurred while computing the application counts: ", e)
        logging.error("Exception occurred while computing the application counts: ", exc_info=True)
        raise e
    pass


if __name__ == '__main__':
    n = len(sys.argv)
    if n != 14:
        print("Please pass valid 8 arguments <isd-admin-username> <isd-admin-password> <redis-host> "
              "<redis-port> <redis-password> <isd-gate-url> <days> <installation_type>")
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

    # Establishing the redis connection
    redis_conn = redis.Redis(host=redis_host, port=redis_port, password=redis_password)
    print("Redis connection established successfully")

    # Establishing the platform db connection
    audit_conn = psycopg2.connect(database=audit_db, user=user_name, password=password, host=audit_host, port=port)
    print('Opened platform database connection successfully')
    cur_audit = audit_conn.cursor()
    start_extraction()
