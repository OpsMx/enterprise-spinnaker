import json
import psycopg2
import sys
import requests


def perform_migration():
    try:
        print('Migrating from v3.9.x to v3.10')
        url = 'https://api.github.com'
        hosturl = 'https://github.com'
        alter_approval_gate_approval()
        print("Altered table approval_gate_approval in visibilitydb")
        modifyOpsmxdb()
        print("Altered column verification_type value of table userservicetemplate in opsmdb")
        modifyGit(hosturl)
        print("Modified config data of Datasource type 'GIT'")
        modifygitname()
        print("Modified config data of Datasource type 'GIT to GITHUB'")
        modifyGithub(hosturl, url)
        print("Modified config data of Datasource type 'GITHUB'")
        platform_conn.commit()
        visibility_conn.commit()
        opsmxdb_conn.commit()
        print("Successfully migrated")
    except Exception as e:
       print('Exception occured during migration : ', e)


def getGitUsernameBytoken(token, url):
    try:
        url = url+"/user"
        headers = {'Authorization': 'token ' + token}
        login = requests.get(url=url, headers=headers).json()
        print("git username: "+login['login'])
        return login['login']
    except Exception as e:
        print("Exception occured while getting user name of datasource type GIT : ", e)
        return " "


def alter_approval_gate_approval():
    try:
        cur = visibility_conn.cursor()
        cur.execute("ALTER TABLE approval_gate_approval ALTER COLUMN approver_comment TYPE TEXT")
    except Exception as e:
        print("Exception occured while altering the approval_gate_parameter table : ", e)
        raise e


def modifyOpsmxdb():
    try:
        cur = opsmxdb_conn.cursor()
        cur.execute("select opsmx_id from userservicetemplate where verification_type = null;")
        result = cur.fetchall()
        if result != None:
            for opsmx_id in result:
                cur.execute(
                    "update userservicetemplate set verification_type = 'VERIFICATION' where opsmx_id=" + str(opsmx_id))
    except Exception as e:
        print("Exception occurred while fetching userservicetemplate data : ", e)
        raise e


def modifyGit(hosturl):
    try:
        cur = platform_conn.cursor()
        cur.execute("select id,config from datasource where datasourcetype = 'GIT';")
        result = cur.fetchall()
        if result != None:
            for data in result:
                configData = json.loads(data[1])
                jdata = {"hostUrl":hosturl,"url":configData['url'],"username":getGitUsernameBytoken(configData['token'],configData['url']),"token":configData['token']}
                updatedConfig = "'"+str(json.dumps(jdata))+"'"
                print("GIT Datasource Json data of Id:"+str(data[0])+" :"+updatedConfig)
                cur.execute('update datasource SET config ='+updatedConfig+' where id ='+ str(data[0]))
    except Exception as e:
        print("Exception occurred while modify datasource data of GIT: ", e.with_traceback())
        raise e

def modifygitname():
    try:
        cur = platform_conn.cursor()
        cur.execute("select id from datasource where datasourcetype = 'GIT';")
        result = cur.fetchall()
        if result != None:
            for id in result:
                cur.execute("update datasource set datasourcetype = 'GITHUB' where id=" + str(id[0]))
    except Exception as e:
        print("Exception occurred while modify datasource data of GIT to GITHUB : ", e)
        raise e


def modifyGithub(hosturl,url):
    try:
        cur = platform_conn.cursor()
        cur.execute("select id,config from datasource where datasourcetype = 'GITHUB';")
        result = cur.fetchall()
        if result != None:
            for data in result:
                configData = json.loads(data[1])
                updateUsername = " "
                if 'username' in configData:
                    updateUsername = configData['username']
                jdata = {"hostUrl":hosturl,"url":url,"username":updateUsername,"token":configData['token']}
                updatedConfig = "'"+str(json.dumps(jdata))+"'"
                print("GITHUB Datasource Json data of Id: "+str(data[0])+" :"+updatedConfig)
                cur.execute('update datasource SET config ='+updatedConfig+' where id=' +str(data[0]))
    except Exception as e:
        print("Exception occurred while modify datasource of tpe GITHUB: ", e)
        raise e


if __name__ == '__main__':
    n = len(sys.argv)
    if n != 7:
        print('Please pass valid 7 arguments visibilitydb <visibility-db-host> <platform_db-name> <platform_hostt> <opsmx-db-name> <opsmx-db-host> <db-port>')

    visibility_db = 'visibilitydb'
    visibility_host = sys.argv[2]
    platform_db = sys.argv[3]
    platform_host = sys.argv[4]
    opsmx_db = sys.argv[5]
    opsmx_host = sys.argv[6]
    port = sys.argv[7]

    print("Using default host url ex:https://github.com")

    # Establishing the visibility db connection
    visibility_conn = psycopg2.connect(database=visibility_db, user='postgres', password='networks123',
                                       host=visibility_host, port=port)
    print("Visibility database connection established successfully")

    # Establishing the platform db connection
    platform_conn = psycopg2.connect(database=platform_db, user='postgres', password='networks123', host=platform_host,
                                     port=port)
    print('Opened platform database connection successfully')

    # Establishing the opsmx db connection
    opsmxdb_conn = psycopg2.connect(database=opsmx_db, user='postgres', password='networks123', host=opsmx_host,
                                    port=port)
    print("opsmx database connection established successfully")

    perform_migration()