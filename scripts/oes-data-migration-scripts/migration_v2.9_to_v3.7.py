
import datetime
import psycopg2
import sys
import uuid
import ldap3 as ldap
from ldap3 import Server, Connection, ALL, NTLM
import json


def perform_migration():
    try:
        print("performing autopilot migration from v2.9 to v3.7")
        perform_autopilot_migration()
        print("autopilot migration completed successfully")

        print("performing platform service migration")
        print("migrating applications to v3.7")
        applications = fetch_applications()
        migrate_applications(applications)

        print("Populating app_update_info table")
        populate_app_update_info(applications)

        print("migrating services to v3.7")
        services = fetch_services()
        migrate_service_details(services)
        print("services successfully migrated to v3.7")

        print("migrating datasources to v3.7")
        datasources = fetch_datasources()
        migrate_datasources(datasources)

        print("populating user_group table")
        ldap_groups = fetch_ldap_groups()
        if ldap_groups is not None and len(ldap_groups) > 0:
            delete_user_groups()
            populate_user_groups(ldap_groups)

            print("assigning read permission for all the ldap groups")
            grant_read_permissions(applications, ldap_groups)

            print("assigning write permission")
            grant_write_permissions(applications)
            grant_write_permission_to_added_group(applications)
            grant_write_permission_to_admin_groups(applications, admin_group)

        platform_conn.commit()
        autopilot_v37_conn.commit()
        print("Successfully migrated to v3.7")

    except Exception as e:
        platform_conn.rollback()
        autopilot_v37_conn.rollback()
        print("Exception occured during the migration process and hence rolling back : ", e)
        raise e
    finally:
        platform_conn.close()
        autopilot_conn.close()
        autopilot_v37_conn.close()


def perform_autopilot_migration():
    try:
        print("Checking  Applications...")
        cur_2_9.execute("""select count(*) from application """)
        result = cur_2_9.fetchone()[0]
        print("Total applications count: ", result)
        if result > 0:
            cur_2_9.execute("""select  opsmx_id, opsmxcreateddate,opsmxlastupdateddate,opsmxhash,active,name,email  from application;
        """)
            rows = cur_2_9.fetchall()
            for row in rows:
                saveapplications(row)
            print("Applications Completed")

        print("Checking  userlogservicetemplate...")
        cur_2_9.execute("""select count(*) from userlogservicetemplate """)
        result = cur_2_9.fetchone()[0]
        print("Total userlogservicetemplate count: ", result)
        if result > 0:
            cur_2_9.execute("""select  opsmx_id, opsmxcreateddate,opsmxlastupdateddate,opsmxhash,active,templatename , monitoringprovider,logtemplatejson,  accountname ,  namespace,applicationid,index,kibanaindex, serviceid from userlogservicetemplate;
        """)
            rows = cur_2_9.fetchall()
            for row in rows:
                cur_2_9.execute("""select  requestedinput from canary  where  applicationid=%s  and  logtemplatename=%s;
        """, [row[10], row[5]])
                newreleasevalue = None
                baselinevalue = None
                filterkey = None
                canaryRow = cur_2_9.fetchone()
                if canaryRow is not None:

                    data = json.loads(canaryRow[0])
                    canary_logs = data['canaryDeployments'][0]['canary']
                    baseline_logs = data['canaryDeployments'][0]['baseline']

                    if isinstance(canary_logs, str) and isinstance(baseline_logs, str):
                        newreleasevalue = canary_logs
                        baselinevalue = baseline_logs

                        cur_2_9.execute("""  select credentials   from credential where  accountname=%s ;
                        """, [row[8]])
                        keywordRow = cur_2_9.fetchone()
                        if keywordRow is not None:
                            credentials = json.loads(keywordRow[0])
                            filterkey = credentials['keyword']


                    else:
                        keyslist_canary = list(canary_logs.keys())
                        keyslist_baseline = list(baseline_logs.keys())
                        if "log" in keyslist_canary and "log" in keyslist_baseline:
                            canary = canary_logs['log']
                            canary_key_object = list(canary.keys())[0]
                            baseline = baseline_logs['log']
                            baseline_key_object = list(baseline.keys())[0]
                            for key, value in canary[canary_key_object].items():
                                newreleasevalue = value
                                filterkey = key
                            for key, value in baseline[baseline_key_object].items():
                                baselinevalue = value
                                filterkey = key

                cur_2_9.execute(""" select credentials from credential   where accountname=%s ;
        """, [row[8]])
                credentialRow = cur_2_9.fetchone()
                if credentialRow is not None:
                    filterkey = credentials['keyword']

                log_template_id = saveuserlogservicetemplates(row, baselinevalue, newreleasevalue, filterkey)
                try:
                    log_template_ids = log_template_dictionary[row[13]]
                    log_template_ids.append(log_template_id)
                    log_template_dictionary[row[13]] = log_template_ids
                except KeyError as ke :
                    log_template_ids = []
                    log_template_ids.append(log_template_id)
                    log_template_dictionary[row[13]] = log_template_ids

        print("Userlogservicetemplate Completed")

        print("Checking  canaryjob (riskanalysisjob)...")
        cur_2_9.execute("""select count(*) from canaryjob """)
        result = cur_2_9.fetchone()[0]
        print("Total canaryjob count: ", result)
        if result > 0:
            cur_2_9.execute("""select  opsmx_id, opsmxcreateddate,opsmxlastupdateddate,opsmxhash,active,containerid ,canaryid , runattempts from canaryjob;
        """)
            rows = cur_2_9.fetchall()
            for row in rows:
                saveriskanalysisjobs(row)
            print("canaryjob (riskanalysisjob) Completed")

        print("Checking  riskanalysis(canary) ...")
        cur_2_9.execute("""select count(*) from canary """)
        result = cur_2_9.fetchone()[0]
        print("Total canary count: ", result)
        if result > 0:
            cur_2_9.execute("""select  opsmx_id, opsmxcreateddate,opsmxlastupdateddate,opsmxhash,active ,canaryanalysisintervalmins, begincanaryanalysisaftermins,
          buildcase,combinedcanaryresultstrategy,requestedinput,error,iscancelled,lifetimeminutes,topscore,logstatus,metricstatus,
          minimumcanaryresultscore,canaryname,canaryresultscore,applicationid,analysisname,logtemplatename,health_health,status_status,lookbackmins from canary;
        """)
            rows = cur_2_9.fetchall()
            for row in rows:
                saveriskanalysis(row)
            print("riskanalysis(canary) Completed")

        print("Checking  userservicetemplate ...")
        cur_2_9.execute("""select count(*) from userservicetemplate """)
        result = cur_2_9.fetchone()[0]
        print("Total userservicetemplate count: ", result)
        if result > 0:
            cur_2_9.execute("""    select  opsmx_id, opsmxcreateddate,opsmxlastupdateddate,opsmxhash,active ,businessname,metricdetailsjson,isnormalize,
        percent_diff_threshold,pipelineid,applicationid, serviceid     from userservicetemplate;
        """)
            rows = cur_2_9.fetchall()
            for row in rows:
                cur_2_9.execute("""select  requestedinput from canary  where  applicationid=%s  and  analysisname=%s;
        """, [row[10], row[9]])
                newreleasevalue = None
                baselinevalue = None
                filterkey = None
                canaryRow = cur_2_9.fetchone()
                if canaryRow is not None:
                    data = json.loads(canaryRow[0])

                    canary_metric = data['canaryDeployments'][0]['canary']
                    baseline_metric = data['canaryDeployments'][0]['baseline']

                    if isinstance(canary_metric, str) and isinstance(baseline_metric, str):
                        newreleasevalue = canary_metric
                        baselinevalue = baseline_metric

                    else:
                        keyslist_canary = list(canary_metric.keys())
                        keyslist_baseline = list(baseline_metric.keys())
                        if "metric" in keyslist_canary and "metric" in keyslist_baseline:
                            canary = canary_metric['metric']
                            canary_key_object = list(canary.keys())[0]
                            baseline = baseline_metric['metric']
                            baseline_key_object = list(baseline.keys())[0]
                            for key, value in canary[canary_key_object].items():
                                filterkey = key
                                newreleasevalue = value

                            for key, value in baseline[baseline_key_object].items():
                                filterkey = key
                                baselinevalue = value

                metric_template_id = saveuserservicetemplate(row, baselinevalue, newreleasevalue, filterkey)
                try:
                    metric_template_ids = metric_template_dictionary[row[11]]
                    metric_template_ids.append(metric_template_id)
                    metric_template_dictionary[row[11]] = metric_template_ids
                except KeyError as ke:
                    metric_template_ids = []
                    metric_template_ids.append(metric_template_id)
                    metric_template_dictionary[row[11]] = metric_template_ids


        print("userservicetemplate Completed")

        print("Checking  casservicemetricdetails ...")
        cur_2_9.execute("""select count(*) from casservicemetricdetails """)
        result = cur_2_9.fetchone()[0]
        print("Total casservicemetricdetails count: ", result)
        if result > 0:
            cur_2_9.execute("""    select  opsmx_id, opsmxcreateddate,opsmxlastupdateddate,opsmxhash,active,
            accountname,aggregator,aggregatortimeinterval,
          aggregatortimeintervalunit,applicationid,critical,watchlist, ignore ,
          relevance,  datainterpolationvalue,direction,displayunit,duration,groupname,range_high,range_low,rules,
          weight,label,kairosaggregator,  metrictype,metricname,riskdirection,userrelevance,metricweight, pipelineid ,application   from casservicemetricdetails;
        """)
            rows = cur_2_9.fetchall()
            for row in rows:
                cur.execute("""  select opsmx_id from userservicetemplate   where pipeline_id=%s and application_id =%s;
                        """, [row[30], row[9]])
                templateidValue = cur.fetchone()
                templateId = None
                if templateidValue is not None:
                    templateId = templateidValue[0]
                    if templateId is not None:
                        savecasservicemetricdetails(row)
            print("casservicemetricdetails Completed")

        print("Checking  service ...")
        cur_2_9.execute("""select count(*) from service """)
        result = cur_2_9.fetchone()[0]
        print("Total service count: ", result)
        if result > 0:
            cur_2_9.execute("""select  opsmx_id, opsmxcreateddate,opsmxlastupdateddate,opsmxhash,active,name,applicationid from service;
        """)
            rows = cur_2_9.fetchall()
            for row in rows:
                saveservices(row)

            print("services Completed")

        print("Checking  entropy ...")
        cur_2_9.execute("""select count(*) from entropy """)
        result = cur_2_9.fetchone()[0]
        print("Total entropy count: ", result)
        if result > 0:
            cur_2_9.execute("""select  opsmx_id, opsmxcreateddate,opsmxlastupdateddate,opsmxhash,active,canaryid , serviceid , entropydetails,logtemplatename from entropy;
        """)
            rows = cur_2_9.fetchall()
            for row in rows:
                logid = None
                appId = None
                if row[5] is not None:
                    cur_2_9.execute("""select  applicationid  from canary  where  opsmx_id=%s   """, [row[5]])
                    appRow = cur_2_9.fetchone()
                    if appRow is not None:
                        appId = appRow[0]

                if row[8] is not None and row[6] is not None:
                    cur.execute("""select  opsmx_id  from userlogservicetemplate  where  templatename=%s  and  application_id=%s;
        """, [row[8], appId])
                    templaterow = cur.fetchone()
                    if templaterow is not None:
                        logid = templaterow[0]
                    if logid is not None:
                        saveentropys(row, logid)
                    else:
                        print("entropy record is not inserted because of logtempalte id is not found for : ")
                        print(row[0])
                else:
                    print("entropy record is not inserted because of logtempalteName or opsmx_id not found for : ")
                    print(row[0])

            print("entropy Completed")

        print("Checking  canary data for loganalysis ...")
        cur_2_9.execute("""select count(*) from canary """)
        result = cur_2_9.fetchone()[0]
        print("Total canary  (loganalysis) count: ", result)
        if result > 0:
            cur_2_9.execute("""select  opsmx_id, opsmxcreateddate,opsmxlastupdateddate,opsmxhash,active,applicationid,serviceid,acceptanceinfo , algorithm ,  buildcase ,  error ,  failurecause  ,  loganalysisduration ,  logfilesinfo ,  logmetricsinfo ,  reclassificationduration ,
          isreclassified ,  topscore ,  scores ,   sensitivity ,  logstatus ,  logsv1endtime ,  baselineclusterip ,  logsv1starttime ,
          logsv2endtime ,  canaryclusterip ,  logsv2starttime,logtemplatename from canary;
        """)
            rows = cur_2_9.fetchall()
            for row in rows:
                logid = None
                if row[27] is not None:
                    cur.execute("""select  opsmx_id  from userlogservicetemplate  where  templatename=%s  and  application_id=%s;
        """, [row[27], row[5]])
                    templaterow = cur.fetchone()
                    if templaterow is not None:
                        logid = templaterow[0]
                if row[5] is not None and row[6] is not None:
                    saveloganalysis(row, logid, row[27])

            print("loganalysis  Completed")

        print("Checking   logcluster ...")
        cur_2_9.execute("""select count(*) from logcluster """)
        result = cur_2_9.fetchone()[0]
        print("Total logcluster count: ", result)
        if result > 0:
            cur_2_9.execute("""   select  opsmx_id, opsmxcreateddate,opsmxlastupdateddate,opsmxhash,active,clusterdescription,clusterid,clusteridhash,clustertemplate,
           isdownload,logdatasummary,more,scorereduction,serviceid,topic,timestamp,v1length,v2length,canaryid,
           color,version  from logcluster;
        """)
            rows = cur_2_9.fetchall()
            for row in rows:
                logid = None
                if row[18] is not None and row[13] is not None:
                    cur.execute("""select  opsmx_id  from loganalysis  where  riskanalysis_id=%s  and  service_id=%s;
            """, [canaryDictonary[row[18]], row[13]])
                    templaterow = cur.fetchone()
                    if templaterow is not None:
                        logid = templaterow[0]
                    if logid is not None:
                        savelogcluster(row, logid)
                    else:
                        print("loganalysis record not found for canaryid or serviceid : ")
                        print(row[18])
                        print(row[13])
                else:
                    print("loganalysis record not instered because of no canaryid or service id found for :")
                    print(row[0])

            print("logcluster  Completed")

        print("Checking  userlogfeedback ...")
        cur_2_9.execute("""select count(*) from userlogfeedback """)
        result = cur_2_9.fetchone()[0]
        print("Total userlogfeedback count: ", result)
        if result > 0:
            cur_2_9.execute("""   select  opsmx_id, opsmxcreateddate,opsmxlastupdateddate,opsmxhash,active ,canaryid,cluster,cluster_id,existingtopic ,
        feedbackcomment ,  feedbackstring ,  feedbacktopic ,  feedbacktype ,  originalstring ,  ratio,templatename,canaryid from userlogfeedback;
        """)
            rows = cur_2_9.fetchall()
            for row in rows:
                logid = None
                appid = None
                serviceid = None
                if row[5] is not None:
                    cur_2_9.execute("""select  applicationid ,serviceid from canary  where  opsmx_id=%s   """, [row[5]])
                    appRow = cur_2_9.fetchone()
                    if appRow is not None:
                        appid = appRow[0]
                        serviceid = appRow[1]
                if row[15] is not None and  appid is not None:
                    cur.execute(""" select  opsmx_id  from userlogservicetemplate  where  templatename=%s  and  application_id=%s;
        """, [row[15], appid])
                    logidrow = cur.fetchone()
                    if logidrow is not None:
                        logid = logidrow[0]

                if logid is not None and serviceid is not None:
                    saveuserlogfeedback(row, logid, serviceid)
            print("userlogfeedback  Completed")

        print("Checking  clusterdetail (logclusterdetails)...")
        cur_2_9.execute("""select count(*) from clusterdetail """)
        result = cur_2_9.fetchone()[0]
        print("Total clusterdetail (logclusterdetails)count: ", result)
        if result > 0:
            cur_2_9.execute("""   select  opsmx_id, opsmxcreateddate,opsmxlastupdateddate,opsmxhash,active,canaryid,serviceid,clusterid,version,
        clusterdump,cluster_data,timestamp   from clusterdetail;
        """)
            rows = cur_2_9.fetchall()
            for row in rows:
                logid = None
                if row[5] is not None and row[6] is not None:
                    cur.execute("""select  opsmx_id  from loganalysis  where  riskanalysis_id=%s  and  service_id=%s;
            """, [canaryDictonary[row[5]], row[6]])
                    templaterow = cur.fetchone()
                    if templaterow is not None:
                        logid = templaterow[0]
                    if logid is not None:
                        savelogclusterdetails(row, logid)
                    else:
                        print("loganalysis record not found for canaryid or serviceid : ")
                        print(row[5])
                        print(row[6])
                else:
                    print("loganalysis record not instered because of no canaryid or service id found for :")
                    print(row[0])

            print("clusterdetail(logclusterdetails) Completed")

        print("Checking  canaryanalysis ..")
        cur_2_9.execute("""select count(*) from canaryanalysis """)
        result = cur_2_9.fetchone()[0]
        print("Total canaryanalysis count: ", result)
        if result > 0:
            cur_2_9.execute("""   select  opsmx_id, opsmxcreateddate,opsmxlastupdateddate,opsmxhash,active,canaryid,starttime,endtime,confidence,error,finalscore,
           version2endtime,  version2starttime     from canaryanalysis;
        """)
            rows = cur_2_9.fetchall()
            for row in rows:
                canaryid = row[5]
                cur_2_9.execute("""   select  baselineclusterip,baselineclusterip,applicationid ,serviceid,analysisname ,metricstatus from canary where opsmx_id=%s;
        """, [canaryid])
                data = cur_2_9.fetchone()
                cur.execute("""  select opsmx_id from userservicetemplate   where pipeline_id=%s and application_id =%s;
        """, [data[4], data[2]])
                templateidValue = cur.fetchone()
                templateId = None
                if templateidValue is not None:
                    templateId = templateidValue[0]
                    if templateId is not None:
                        savecanaryanalysis(row, data, templateId)
            print("canaryanalysis Completed")

        print("Checking  metricscore..")
        cur_2_9.execute("""select count(*) from metricscore """)
        result = cur_2_9.fetchone()[0]
        print("Total metricscore count: ", result)
        if result > 0:
            cur_2_9.execute("""    select  parent_id ,value   from  canaryanalysis_metricscoreids;    """)
            metricrows = cur_2_9.fetchall()
            for metricrow in metricrows:
                opsmxid = metricrow[1]
                canaryanalysis_id = canaryanalysisDictonary[metricrow[0]]
                if opsmxid is not None:

                    cur_2_9.execute("""     select    opsmx_id, opsmxcreateddate,opsmxlastupdateddate,opsmxhash,active,account ,  aggregator ,  bucketscores ,  corrcoeff , 
         critical ,  description ,  error ,  graphdata ,  graphinfo,  groupscore,  iscumulative ,  label , metricname ,  metrictype ,  originalmetricname ,
         percentdiff ,  range_high ,  range_low ,  relevance , score ,   scoreper ,  scorequant ,  scorewilcox ,  tags ,  userrelevance , 
         watchlist ,  weight,version1stats_versionstats,version2stats_versionstats
          from metricscore  where  opsmx_id=%s;  
        """, [opsmxid])
                    rows = cur_2_9.fetchall()
                    for row in rows:
                        savemetricscore(row, canaryanalysis_id)
                        cur_2_9.execute("""    select  opsmx_id, opsmxcreateddate,opsmxlastupdateddate,opsmxhash,active,min ,  firstqu,  median ,  mean ,  thirdqu,  max ,  data ,  fifthqu ,  nintyfifthqu ,  bucketdata   from versionstats where opsmx_id=%s;
        """, [row[32]])
                        v1rows = cur_2_9.fetchall()
                        for v1row in v1rows:
                            saveversionstats(v1row, "version1", metricscoreDictonary[opsmxid])
                        cur_2_9.execute("""    select  opsmx_id, opsmxcreateddate,opsmxlastupdateddate,opsmxhash,active, min ,  firstqu,  median ,  mean ,  thirdqu,  max ,  data ,  fifthqu ,  nintyfifthqu ,  bucketdata   from versionstats where opsmx_id=%s;
        """, [row[33]])
                        v2rows = cur_2_9.fetchall()
                        for v2row in v2rows:
                            saveversionstats(v2row, "version2", metricscoreDictonary[opsmxid])

            print("versionstats completed")
            print("metricscore Completed")

        print("Checking  serviceriskanalysis ...")
        cur_2_9.execute("""select count(*) from canary """)
        result = cur_2_9.fetchone()[0]
        print("Total  canary for saving (serviceriskanalysis) count: ", result)
        if result > 0:
            cur_2_9.execute("""      select    opsmx_id, opsmxcreateddate,opsmxlastupdateddate,opsmxhash,active,
          serviceid,error,status_status, logtemplatename,analysisname,canaryresultscore,  minimumcanaryresultscore,topscore from canary;
            """)
            rows = cur_2_9.fetchall()
            for row in rows:
                serviceid = row[5]
                if serviceid is not None:
                    status = row[7]
                    log = row[8]
                    metric = row[9]
                    maximumscore = float(row[10])
                    minimumscore = float(row[11])
                    logscore = row[12]
                    metricscore = None
                    serviceScore = 0
                    healthstatus = None
                    analysis_type = None
                    canaryanalysis_id = None
                    loganalysis_id = None

                    if log is not None and metric is not None:
                        analysis_type = 'both'
                    if metric is not None:
                        analysis_type = 'metric'
                    if log is not None:
                        analysis_type = 'log'

                    cur_2_9.execute(""" select status  from status where opsmx_id=%s;    """, [status])
                    statusValue = cur_2_9.fetchone()

                    if analysis_type == 'both':
                        cur_2_9.execute(
                            """ select opsmx_id,  finalscore  from canaryanalysis  where  canaryid=%s;    """, [row[0]])
                        canaryAnalysis = cur_2_9.fetchone()
                        if canaryAnalysis is not None:
                            canaryanalysis_id = canaryAnalysis[0]
                            metricscore = canaryAnalysis[1]

                        cur.execute(
                            """  select opsmx_id from loganalysis where riskanalysis_id =%s  and service_id=%s;   """,
                            [canaryDictonary[row[0]], serviceid])
                        loganalysis = cur.fetchone()
                        if loganalysis is not None:
                            loganalysis_id = loganalysis[0]
                        if logscore is not None and metricscore is not None:
                            serviceScore = logscore if logscore < metricscore else metricscore
                        if logscore:
                            serviceScore = logscore
                        if metricscore:
                            serviceScore = metricscore
                        if serviceScore > minimumscore and serviceScore < maximumscore:
                            healthstatus = "Review"
                        elif serviceScore >= maximumscore:
                            healthstatus = "Success"
                        else:
                            healthstatus = "Fail"

                        saveserviceriskanalysis(row, statusValue[0], healthstatus, analysis_type, serviceScore,
                                                loganalysis_id, canaryanalysis_id)

                    if analysis_type == 'log':
                        cur.execute(
                            """  select opsmx_id from loganalysis where riskanalysis_id =%s  and service_id=%s;   """,
                            [ canaryDictonary[row[0]], serviceid])
                        loganalysis = cur.fetchone()
                        if loganalysis is not None:
                            loganalysis_id = loganalysis[0]

                        if logscore is not None:
                            serviceScore = logscore
                        else:
                            serviceScore = 0

                        if serviceScore > minimumscore and serviceScore < maximumscore:
                            healthstatus = "Review"
                        elif serviceScore >= maximumscore:
                            healthstatus = "Success"
                        else:
                            healthstatus = "Fail"

                        saveserviceriskanalysis(row, statusValue[0], healthstatus, analysis_type, serviceScore,
                                                loganalysis_id, canaryanalysis_id)

                    if analysis_type == 'metric':
                        cur_2_9.execute(
                            """ select opsmx_id,  finalscore  from canaryanalysis  where  canaryid=%s;    """, [row[0]])
                        canaryAnalysis = cur_2_9.fetchone()
                        if canaryAnalysis is not None:
                            canaryanalysis_id = canaryAnalysis[0]
                            metricscore = canaryAnalysis[1]

                        if metricscore is not None:
                            serviceScore = metricscore
                        else:
                            serviceScore = 0
                        if serviceScore > minimumscore and serviceScore < maximumscore:
                            healthstatus = "Review"
                        elif serviceScore >= maximumscore:
                            healthstatus = "Success"
                        else:
                            healthstatus = "Fail"

                        saveserviceriskanalysis(row, statusValue[0], healthstatus, analysis_type, serviceScore,
                                                loganalysis_id, canaryanalysis_id)

            print("serviceriskanalysis Completed")

        print("Checking  clustertag ...")
        cur_2_9.execute("""select count(*) from clustertag """)
        result = cur_2_9.fetchone()[0]
        print("Total clustertag count: ", result)
        if result > 0:
            cur_2_9.execute("""select  opsmx_id, opsmxcreateddate,opsmxlastupdateddate,opsmxhash,active ,clusteridhash, clusterkeywords, tag , isregex
             from clustertag;
        """)
            rows = cur_2_9.fetchall()
            for row in rows:
                saveclustertag(row)
            print("clustertag Completed")

        print("Checking  usertagfeedback (tagsfeedback)...")
        cur_2_9.execute("""select count(*) from usertagfeedback """)
        result = cur_2_9.fetchone()[0]
        print("Total usertagfeedback (tagsfeedback)count: ", result)
        if result > 0:
            cur_2_9.execute("""    select    opsmx_id, opsmxcreateddate,opsmxlastupdateddate,opsmxhash,active,
         clusteridhash, clusterid , version,  clusterdata, comment, canaryid , serviceid, tag,existingtag, templatename from usertagfeedback ;  
        """)
            rows = cur_2_9.fetchall()
            for row in rows:
                logid = None
                if row[10] is not None and row[11] is not None:
                    cur.execute("""select  log_template_opsmx_id  from loganalysis  where  riskanalysis_id=%s  and  service_id=%s;
            """, [ canaryDictonary[row[10]], row[11]])
                    templaterow = cur.fetchone()
                    if templaterow is not None:
                        logid = templaterow[0]
                    if logid is not None:
                        saveusertagfeedback(row, logid)
                    else:
                        print("templateid record not found for canaryid or serviceid : ")
                        print(row[10])
                        print(row[11])
                else:
                    print("templateid record not instered because of no canaryid or service id found for :")
                    print(row[0])

            print("usertagfeedback(tagsfeedback) Completed")

    except Exception as e:
        print("Exception occured while performing autopilot migration : ", e)
        raise e


####Used for saving data to application table###
def saveapplications(queryData):
    opsmxtime = datetime.datetime.now()
    opsmxtime = str(opsmxtime)
    if not queryData[1]:
        createtime = opsmxtime;
    else:
        createtime = queryData[1]

    if not queryData[2]:
        updatetime = opsmxtime;
    else:
        updatetime = queryData[2]

    if not queryData[4]:
        active = True;
    else:
        active = queryData[4]

    returnid = executequery(
        """INSERT INTO application (opsmxcreateddate ,opsmxlastupdateddate , opsmxhash , active,id,name,email,ismonitored) values (%s,%s,%s,%s,%s,%s,%s,%s)  RETURNING opsmx_id  """,
        (createtime, updatetime, queryData[3], active, queryData[0], queryData[5], queryData[6], False))


####Used for saving data to userlogservicetemplate table###
def saveuserlogservicetemplates(queryData, baselinevalue, newreleasevalue, filterkey):
    opsmxtime = datetime.datetime.now()
    opsmxtime = str(opsmxtime)
    if not queryData[1]:
        createtime = opsmxtime;
    else:
        createtime = queryData[1]

    if not queryData[2]:
        updatetime = opsmxtime;
    else:
        updatetime = queryData[2]

    if not queryData[4]:
        active = True;
    else:
        active = queryData[4]

    returnid = executequery(
        """INSERT INTO userlogservicetemplate (opsmxcreateddate ,opsmxlastupdateddate , opsmxhash , active, templatename , monitoringprovider,logtemplatejson,  accountname ,  namespace,application_id,index,kibanaindex,scoringalgorithm,autobaseline,baselinevalue,  newreleasevalue, filterkey,  verification_type ) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)  RETURNING opsmx_id  """,
        (createtime, updatetime, queryData[3], active, queryData[5], queryData[6], queryData[7],
         queryData[8], queryData[9], queryData[10], queryData[11], queryData[12], "Canary", False, baselinevalue,
         newreleasevalue, filterkey, "VERIFICATION"))

    return returnid


####Used for saving data to riskanalysisjob table###
def saveriskanalysisjobs(queryData):
    opsmxtime = datetime.datetime.now()
    opsmxtime = str(opsmxtime)
    if not queryData[1]:
        createtime = opsmxtime;
    else:
        createtime = queryData[1]

    if not queryData[2]:
        updatetime = opsmxtime;
    else:
        updatetime = queryData[2]

    if not queryData[4]:
        active = True;
    else:
        active = queryData[4]

    returnid = executequery(
        """INSERT INTO riskanalysisjob (opsmxcreateddate ,opsmxlastupdateddate , opsmxhash , active, container_id ,riskanalysis_id , run_analysis_attempts) values (%s,%s,%s,%s,%s,%s,%s) RETURNING opsmx_id """,
        (createtime, updatetime, queryData[3], active, queryData[5], canaryDictonary[queryData[6]], queryData[7]))


####Used for saving data to riskanalysis table###
def saveriskanalysis(queryData):
    opsmxtime = datetime.datetime.now()
    opsmxtime = str(opsmxtime)
    if not queryData[1]:
        createtime = opsmxtime;
    else:
        createtime = queryData[1]

    if not queryData[2]:
        updatetime = opsmxtime;
    else:
        updatetime = queryData[2]

    if not queryData[4]:
        active = True;
    else:
        active = queryData[4]

    analysis_type = None
    health_status = None
    health_message = None
    overallStatus = None
    metricScore = None
    logscore = None
    finalScore = None

    if queryData[20] and queryData[21]:
        analysis_type = "both"
    if queryData[20]:
        analysis_type = "metric"
    if queryData[21]:
        analysis_type = "log"

    cur_2_9.execute(""" SELECT  health ,message FROM health  where opsmx_id =%s;
""", [queryData[22]])

    healthrow = cur_2_9.fetchone()
    if healthrow is not None:
        health_message = healthrow[1]
    else:
        health_message = None

    cur_2_9.execute(""" SELECT  status   FROM status where opsmx_id=%s;
""", [queryData[23]])

    overallStatusrow = cur_2_9.fetchone()
    if overallStatusrow is not None:
        overallStatus = overallStatusrow[0]

    cur_2_9.execute(""" SELECT  finalscore FROM canaryanalysis where canaryid=%s;
""", [queryData[0]])

    canaryanalysisrow = cur_2_9.fetchone()
    if canaryanalysisrow is not None:
        metricScore = canaryanalysisrow[0]

    logscore = queryData[13]
    if metricScore is not None and logscore is not None:
        finalScore = min(metricScore, logscore)
    if metricScore is not None:
        finalScore = metricScore
    if logscore is not None:
        finalScore = logscore

    resultScore = None
    minimumResultScore = None
    if queryData[18] is not None:
        resultScore = float(queryData[18])

    if queryData[16] is not None:
        minimumResultScore = float(queryData[16])

    if finalScore is not None:

        if minimumResultScore is not None and resultScore is not None:

            if finalScore > minimumResultScore and finalScore < resultScore:
                health_status = "Review"
            elif finalScore >= resultScore:
                health_status = "Success"
            else:
                health_status = "Fail"

    returnid = executequery("""INSERT INTO riskanalysis (opsmxcreateddate, opsmxlastupdateddate, opsmxhash, active , 
analysis_interval_mins , begin_analysis_after_mins ,  buildcase ,  combined_result_strategy  ,
  end_point_input ,  error ,     is_cancelled ,  lifetime_minutes ,
  log_score ,  log_status  ,  metric_status ,  minimum_result_score ,  
  owner ,  result_score ,  application_id, lookback_mins,analysis_type, health_message ,  health_status ,overall_status,metrics_score,final_score ) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING opsmx_id """,
                 (createtime, updatetime, queryData[3], active, queryData[5], queryData[6], queryData[7],
                  queryData[8], queryData[9], queryData[10],
                  queryData[11], queryData[12], queryData[13], queryData[14], queryData[15], minimumResultScore,
                  queryData[17], resultScore,
                  queryData[19], queryData[24], analysis_type, health_message, health_status, overallStatus,
                  metricScore, finalScore))
    canaryDictonary[queryData[0]] = returnid

####Used for saving data to userservicetemplate table###
def saveuserservicetemplate(queryData, baselinevalue, newreleasevalue, filterkey):
    opsmxtime = datetime.datetime.now()
    opsmxtime = str(opsmxtime)
    if not queryData[1]:
        createtime = opsmxtime;
    else:
        createtime = queryData[1]

    if not queryData[2]:
        updatetime = opsmxtime;
    else:
        updatetime = queryData[2]

    if not queryData[4]:
        active = True;
    else:
        active = queryData[4]

    returnid = executequery("""INSERT INTO userservicetemplate (opsmxcreateddate ,opsmxlastupdateddate , opsmxhash , active,business_name,metric_details_json,is_normalize,
percent_diff_threshold,pipeline_id,application_id,baselinevalue,newreleasevalue, filterkey) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)   RETURNING opsmx_id  """,
                 ( createtime, updatetime, queryData[3], active, queryData[5], queryData[6], queryData[7],
                  queryData[8], queryData[9], queryData[10], baselinevalue, newreleasevalue, filterkey))

    return returnid

####Used for saving data to casservicemetricdetails table###
def savecasservicemetricdetails(queryData):
    opsmxtime = datetime.datetime.now()
    opsmxtime = str(opsmxtime)
    if not queryData[1]:
        createtime = opsmxtime;
    else:
        createtime = queryData[1]

    if not queryData[2]:
        updatetime = opsmxtime;
    else:
        updatetime = queryData[2]

    if not queryData[4]:
        active = True;
    else:
        active = queryData[4]

    cur.execute(""" select id from application where name =%s;
""", [queryData[31]])

    appRow = cur.fetchone()
    if appRow is not None:
        appId = appRow[0]
    else:
        appId = None

    metricid = None
    if appId is not None:
        cur.execute(""" select opsmx_id from  userservicetemplate  where  pipeline_id=%s  and application_id=%s;
""", [queryData[30], appId])
        metricRow = cur.fetchone()
        if metricRow is not None:
            metricid = metricRow[0]

    if metricid is not None:
        returnid = executequery("""INSERT INTO casservicemetricdetails (opsmxcreateddate ,opsmxlastupdateddate , opsmxhash , active,account_name,
            aggregator,aggregator_time_interval,  aggregator_time_interval_unit,application_id,critical,watchlist,ignore, relevance , 
               data_interpolation_value,direction,display_unit,duration , group_name , range_high,  range_low , rules,    weight, label  ,
     kairos_aggregator,  metric_type , metric_name  ,risk_direction,user_relevance,metric_weight,pipeline_id,metric_id) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)  RETURNING opsmx_id  """,
                     (createtime, updatetime, queryData[3], active, queryData[5], queryData[6],
                      queryData[7], queryData[8], appId, queryData[10],
                      queryData[11], queryData[12], queryData[13], queryData[14], queryData[15], queryData[16],
                      queryData[17], queryData[18], queryData[19],
                      queryData[20], queryData[21], queryData[22], queryData[23], queryData[24], queryData[25],
                      queryData[26], queryData[27],
                      queryData[28], queryData[29], queryData[30], metricid))


    else:
        print(
            "Record not inserted  casservicemetricdetails  because of appId or metrictemplate id not found for opsmx_id : ")
        print(queryData[0])


####Used for saving data to service table###
def saveservices(queryData):
    opsmxtime = datetime.datetime.now()
    opsmxtime = str(opsmxtime)
    if not queryData[1]:
        createtime = opsmxtime
    else:
        createtime = queryData[1]

    if not queryData[2]:
        updatetime = opsmxtime
    else:
        updatetime = queryData[2]

    if not queryData[4]:
        active = True
    else:
        active = queryData[4]

    returnid = executequery(
        """INSERT INTO service (opsmxcreateddate ,opsmxlastupdateddate , opsmxhash , active, id ,name , application_id ) values (%s,%s,%s,%s,%s,%s,%s) RETURNING opsmx_id  """,
        (createtime, updatetime, queryData[3], active, queryData[0], queryData[5], queryData[6]))


####Used for saving data to entropy table###
def saveentropys(queryData, templateid):
    opsmxtime = datetime.datetime.now()
    opsmxtime = str(opsmxtime)
    if not queryData[1]:
        createtime = opsmxtime;
    else:
        createtime = queryData[1]

    if not queryData[2]:
        updatetime = opsmxtime;
    else:
        updatetime = queryData[2]

    if not queryData[4]:
        active = True
    else:
        active = queryData[4]

    returnid = executequery(
        """INSERT INTO entropy (opsmxcreateddate ,opsmxlastupdateddate , opsmxhash , active, riskanalysis_id,service_id,entropydetails ,logtemplate_id) values (%s,%s,%s,%s,%s,%s,%s,%s)  RETURNING opsmx_id  """,
        (createtime, updatetime, queryData[3], active, canaryDictonary[queryData[5]], queryData[6], queryData[7],
         templateid))


####Used for saving data to loganalysis table###
def saveloganalysis(queryData, logid, templatename):
    opsmxtime = datetime.datetime.now()
    opsmxtime = str(opsmxtime)
    if not queryData[1]:
        createtime = opsmxtime;
    else:
        createtime = queryData[1]

    if not queryData[2]:
        updatetime = opsmxtime;
    else:
        updatetime = queryData[2]

    if not queryData[4]:
        active = True;
    else:
        active = queryData[4]
        sensitivityValue = queryData[19]
        if sensitivityValue is not None:
            if sensitivityValue.upper() == "LOW":
                sensitivity = 0
            if sensitivityValue.upper() == "MEDIUM":
                sensitivity = 1
            if sensitivityValue.upper() == "HIGH":
                sensitivity = 2

        else:
            sensitivity = 100

        algorithmValue = queryData[8]
        if algorithmValue is not None:
            if algorithmValue.upper() == "PERL":
                algorithm = 0
            if algorithmValue.upper() == "SPELL":
                algorithm = 1
        else:
            algorithm = 100

        statusValue = queryData[20]
        if statusValue is not None:
            if statusValue.upper() == "RUNNING":
                status = 0
            if statusValue.upper() == "LOG_RETRIEVING":
                status = 1
            if statusValue.upper() == "LOG_PROCESSING":
                status = 2
            if statusValue.upper() == "INTERMEDIATE_COMPLETED":
                status = 3
            if statusValue.upper() == "METRIC_PROCESSING":
                status = 4
            if statusValue.upper() == "CANCELLED":
                status = 5
            if statusValue.upper() == "COMPLETED":
                status = 6

        else:
            status = None

    cur.execute(""" SELECT  health_status FROM riskanalysis where opsmx_id=%s;
""", [canaryDictonary[queryData[0]]])

    health_status = "Success"
    canaryrow = cur.fetchone()
    if canaryrow is not None and canaryrow[0] is not None:
        health_status = canaryrow[0]

    returnid = executequery("""INSERT INTO loganalysis (opsmxcreateddate ,opsmxlastupdateddate , opsmxhash , active, application_id,service_id,riskanalysis_id ,
        acceptanceinfo , algorithm ,  buildcase ,  error ,  failurecause  ,  loganalysisduration ,  logfilesinfo ,  logmetricsinfo , 
         reclassificationduration ,  isreclassified ,  score ,  scores ,   sensitivity ,  status ,  v1endtime ,  v1identifiers ,  v1starttime ,
  v2endtime ,  v2identifiers ,  v2starttime ,  log_template_opsmx_id , scoringalgorithm,templatename, verification_type,autobaseline) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)  RETURNING opsmx_id  """,
                 (createtime, updatetime, queryData[3], active, queryData[5], queryData[6], canaryDictonary[queryData[0]], queryData[7],
                  algorithm, queryData[9], queryData[10], queryData[11], queryData[12], queryData[13], queryData[14],
                  queryData[15], queryData[16], queryData[17], queryData[18], sensitivity, status, queryData[21],
                  queryData[22], queryData[23], queryData[24], queryData[25], queryData[26], logid, "Canary",
                  templatename, health_status.upper(), False))


####Used for saving data to logcluster table###
def savelogcluster(queryData, logid):
    opsmxtime = datetime.datetime.now()
    opsmxtime = str(opsmxtime)
    if not queryData[1]:
        createtime = opsmxtime;
    else:
        createtime = queryData[1]

    if not queryData[2]:
        updatetime = opsmxtime;
    else:
        updatetime = queryData[2]

    if not queryData[4]:
        active = True;
    else:
        active = queryData[4]
        versionValue = queryData[20]
        if versionValue is not None:
            if versionValue.upper() == "VERSION1":
                version = 0
            if versionValue.upper() == "VERSION2":
                version = 1
            if versionValue.upper() == "V1V2":
                version = 2

        else:
            version = 100

        if versionValue is not None:
            if versionValue.upper() == "VERSION1":
                presence = "v1"
            if versionValue.upper() == "VERSION2":
                presence = "v2"
            if versionValue.upper() == "V1V2":
                presence = "both"

        else:
            presence = "none"

        colorValue = queryData[19]
        if colorValue is not None:
            if colorValue.upper() == "YELLOW":
                color = 0
            if colorValue.upper() == "GREEN":
                color = 1
            if colorValue.upper() == "DARK RED":
                color = 2
            if colorValue.upper() == "RED":
                color = 3

        else:
            color = 100

    returnid = executequery("""INSERT INTO logcluster (opsmxcreateddate ,opsmxlastupdateddate , opsmxhash , active,clusterdescription,clusterid,clusteridhash,clustertemplate,
   isdownload,logdatasummary,more,scorereduction,service_id,severity,timestamp,v1length,v2length,riskanalysis_id,
   color,version,loganalysis_id,uniqueid, factor, presence) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)  RETURNING opsmx_id  """,
                 (createtime, updatetime, queryData[3], active, queryData[5], queryData[6], queryData[7], queryData[8],
                  queryData[9], queryData[10], queryData[11],
                  queryData[12], queryData[13], queryData[14], queryData[15], queryData[16], queryData[17],
                  canaryDictonary[queryData[18]], color, version, logid, "NOT AVAILABLE", 1, presence))


####Used for saving data to userlogfeedback table###
def saveuserlogfeedback(queryData, logid, serviceid):
    opsmxtime = datetime.datetime.now()
    opsmxtime = str(opsmxtime)
    if not queryData[1]:
        createtime = opsmxtime;
    else:
        createtime = queryData[1]

    if not queryData[2]:
        updatetime = opsmxtime;
    else:
        updatetime = queryData[2]

    if not queryData[4]:
        active = True;
    else:
        active = queryData[4]

    returnid = executequery("""INSERT INTO userlogfeedback (opsmxcreateddate ,opsmxlastupdateddate , opsmxhash , active,riskanalysis_id,cluster,cluster_id,existingtopic,feedbackcomment,
feedbackstring,feedbacktopic,feedbacktype,originalstring,ratio,service_id,logtemplate_id) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)  RETURNING opsmx_id  """,
                 (createtime, updatetime, queryData[3], active, canaryDictonary[queryData[5]], queryData[6], queryData[7], queryData[8],
                  queryData[9], queryData[10], queryData[11],
                  queryData[12], queryData[13], queryData[14], serviceid, logid))


####Used for saving data to logclusterdetails table###
def savelogclusterdetails(queryData, loganalysis_id):
    opsmxtime = datetime.datetime.now()
    opsmxtime = str(opsmxtime)
    if not queryData[1]:
        createtime = opsmxtime;
    else:
        createtime = queryData[1]

    if not queryData[2]:
        updatetime = opsmxtime;
    else:
        updatetime = queryData[2]

    if not queryData[4]:
        active = True;
    else:
        active = queryData[4]

    versionValue = queryData[8]
    version = 100
    if versionValue is not None:
        if versionValue.upper() == "VERSION1":
            version = 0
        if versionValue.upper() == "VERSION2":
            version = 1
        if versionValue.upper() == "V1V2":
            version = 2

    returnid = executequery("""INSERT INTO logclusterdetails (opsmxcreateddate,opsmxlastupdateddate,opsmxhash,active,riskanalysis_id,service_id,clusterid,version,
clusterdump,cluster_data,timestamp,loganalysis_id) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)  RETURNING opsmx_id  """,
                 (createtime, updatetime, queryData[3], active, canaryDictonary[queryData[5]], queryData[6], queryData[7], version,
                  queryData[9], queryData[10], queryData[11], loganalysis_id))


####Used for saving data to canaryanalysis table###
def savecanaryanalysis(queryData, data, templateid):
    opsmxtime = datetime.datetime.now()
    opsmxtime = str(opsmxtime)
    if not queryData[1]:
        createtime = opsmxtime;
    else:
        createtime = queryData[1]

    if not queryData[2]:
        updatetime = opsmxtime;
    else:
        updatetime = queryData[2]

    if not queryData[4]:
        active = True;
    else:
        active = queryData[4]

    returnid = executequery("""INSERT INTO canaryanalysis (opsmxcreateddate ,opsmxlastupdateddate , opsmxhash , active,riskanalysis_id , starttime 
 ,   endtime ,    confidence ,error,  finalscore, version2endtime,  version2starttime ,
 v1identifiers,v2identifiers,application_id,service_id,status,metric_template_opsmx_id,templatename) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING opsmx_id  """,
                 (createtime, updatetime, queryData[3], active, canaryDictonary[queryData[5]], queryData[6], queryData[7],
                  queryData[8], queryData[9]
                  , queryData[10], queryData[11], queryData[12], data[0], data[1], data[2], data[3], data[5],
                  templateid, data[4]))
    canaryanalysisDictonary[queryData[0]] = returnid

####Used for saving data to metricscore table###
def savemetricscore(queryData, canaryanalysis_id):
    opsmxtime = datetime.datetime.now()
    opsmxtime = str(opsmxtime)
    if not queryData[1]:
        createtime = opsmxtime;
    else:
        createtime = queryData[1]

    if not queryData[2]:
        updatetime = opsmxtime;
    else:
        updatetime = queryData[2]

    if not queryData[4]:
        active = True;
    else:
        active = queryData[4]

    returnid = executequery("""INSERT INTO metricscore (opsmxcreateddate ,opsmxlastupdateddate , opsmxhash , active,
account ,  aggregator ,  bucketscores ,  corrcoeff ,  critical ,  description ,  error ,  graphdata ,  graphinfo,  groupscore,
  iscumulative ,  label ,  metricname ,  metrictype ,  originalmetricname ,  percentdiff ,  range_high ,  range_low ,  relevance , score , 
  scoreper ,  scorequant ,  scorewilcox ,  tags ,  userrelevance ,  watchlist ,  weight , metricanalysis_id ) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING opsmx_id  """,
                 (createtime, updatetime, queryData[3], active, queryData[5], queryData[6], queryData[7],
                  queryData[8], queryData[9]
                  , queryData[10], queryData[11], queryData[12], queryData[13], queryData[14], queryData[15],
                  queryData[16], queryData[17], queryData[18], queryData[19],
                  queryData[20], queryData[21], queryData[22], queryData[23], queryData[24], queryData[25],
                  queryData[26], queryData[27], queryData[28],
                  queryData[29], queryData[30], queryData[31], canaryanalysis_id))


    metricscoreDictonary[queryData[0]] = returnid

####Used for saving data to versionstats table###
def saveversionstats(queryData, version, metriscoreid):
    opsmxtime = datetime.datetime.now()
    opsmxtime = str(opsmxtime)
    if not queryData[1]:
        createtime = opsmxtime;
    else:
        createtime = queryData[1]

    if not queryData[2]:
        updatetime = opsmxtime;
    else:
        updatetime = queryData[2]

    if not queryData[4]:
        active = True;
    else:
        active = queryData[4]

    returnid = executequery("""INSERT INTO versionstats (opsmxcreateddate ,opsmxlastupdateddate , opsmxhash , active, min ,  firstqu,  median ,
 mean ,  thirdqu,  max ,  data ,  fifthqu ,  nintyfifthqu ,  bucketdata , version , metricscore_id ) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING opsmx_id  """,
                 (createtime, updatetime, queryData[3], active, queryData[5], queryData[6], queryData[7],
                  queryData[8], queryData[9]
                  , queryData[10], queryData[11], queryData[12], queryData[13], queryData[14], version, metriscoreid))


####Used for saving data to serviceriskanalysis table###
def saveserviceriskanalysis(queryData, status, healthstatus, analysis_type, serviceScore, loganalysis_id,
                            canaryanalysis_id):
    opsmxtime = datetime.datetime.now()
    opsmxtime = str(opsmxtime)
    if not queryData[1]:
        createtime = opsmxtime;
    else:
        createtime = queryData[1]

    if not queryData[2]:
        updatetime = opsmxtime;
    else:
        updatetime = queryData[2]

    if not queryData[4]:
        active = True;
    else:
        active = queryData[4]

    returnid = executequery("""INSERT INTO serviceriskanalysis (opsmxcreateddate ,opsmxlastupdateddate , opsmxhash , active,service_id,errormessage,
 analysistype,  canaryanalysis_id  ,  healthstatus ,  loganalysis_id ,  score   ,  status ,  riskanalysis_id,verification_type) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)  RETURNING opsmx_id  """,
                 (createtime, updatetime, queryData[3], active, queryData[5], queryData[6], analysis_type,
                  canaryanalysis_id, healthstatus, loganalysis_id, serviceScore, status, canaryDictonary[queryData[0]], "VERIFICATION"))


####Used for saving data to tagsfeedback table###
def saveusertagfeedback(queryData, logid):
    opsmxtime = datetime.datetime.now()
    opsmxtime = str(opsmxtime)
    if not queryData[1]:
        createtime = opsmxtime;
    else:
        createtime = queryData[1]

    if not queryData[2]:
        updatetime = opsmxtime;
    else:
        updatetime = queryData[2]

    if not queryData[4]:
        active = True;
    else:
        active = queryData[4]

    returnid = executequery("""INSERT INTO tagsfeedback (opsmxcreateddate ,opsmxlastupdateddate , opsmxhash , active,clusteridhash, 
        clusterid , version,  clusterdata, comment, riskanalysis_id,service_id,newtag,oldtag,logtemplate_id) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING opsmx_id  """,
                 (createtime, updatetime, queryData[3], active, queryData[5], queryData[6], queryData[7], queryData[8],
                  queryData[9], canaryDictonary[queryData[10]], queryData[11],
                  queryData[12], queryData[13], logid))


####Used for saving data to clustertag table###
def saveclustertag(queryData):
    opsmxtime = datetime.datetime.now()
    opsmxtime = str(opsmxtime)
    if not queryData[1]:
        createtime = opsmxtime;
    else:
        createtime = queryData[1]

    if not queryData[2]:
        updatetime = opsmxtime;
    else:
        updatetime = queryData[2]

    if not queryData[4]:
        active = True;
    else:
        active = queryData[4]

    returnid = executequery("""INSERT INTO clustertag (opsmxcreateddate ,opsmxlastupdateddate , opsmxhash , active,clusteridhash, clusterkeywords, tag , isregex, userlogservicetemplate_id ,reclassified )
     values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)  RETURNING opsmx_id""",
                 (createtime, updatetime, queryData[3], active, queryData[5], queryData[6], queryData[7], queryData[8],
                  0, False))



####Query execution handling, if transaction failed, insert/update rolledback###
def executequery(query, data):
    try:
        cur.execute(query, data)
        returnid = cur.fetchone()[0]
        return returnid
    except Exception as err:
        print(err)
        raise err

def migrate_service_details(services):
    try:
        counter = 1
        for service in services:
            migrate_services(service)
            pipeline_uuid = str(uuid.uuid4())
            pipeline_id = create_pipeline(service, pipeline_uuid)
            index = 1
            map_service_pipeline(service[0], pipeline_id, index)
            counter = persist_gate_details(counter, service, pipeline_id, pipeline_uuid)
        print("pipelines created successfully")
        print("service pipeline mapping added successfully")
        if counter > 1:
            print("Gate details persisted successfully")
    except Exception as e:
        print("Exception occured while migrating service details : ", e)
        raise e


def persist_gate_details(counter, service, pipeline_id, pipeline_uuid):
    try:
        log_template_ids = []
        metric_template_ids = []
        gate_ids = []
        try:
            log_template_ids = log_template_dictionary[service[0]]
        except KeyError as ke:
            log_template_ids = []

        for log_template_id in log_template_ids:
            app_environment_id = fetch_app_environment(service[4])
            if app_environment_id is None or len(app_environment_id) <= 0:
                app_environment_id = create_app_environment(service[4])
            gate_name = "verification-gate-" + str(counter)
            gate_id = create_gate(gate_name, app_environment_id[0])
            gate_ids.append(gate_id)
            map_pipeline_gate(pipeline_id, gate_id)
            pipeline = fetch_pipeline_json(pipeline_id)
            pipeline_json = pipeline[0][1]
            json_msg = json.loads(pipeline_json)
            ref_id = 1
            requisite_stage_ref_ids = []
            stages = []
            latest_stage = get_latest_stage(pipeline_json)
            if latest_stage is not None:
                latest_ref_id = int(latest_stage['refId'])
                ref_id = latest_ref_id + 1
                requisite_stage_ref_ids.append(str(latest_ref_id))
                stages = json_msg['stages']

            pipeline_json = get_pipeline_json(pipeline_uuid, gate_name, str(ref_id), requisite_stage_ref_ids, stages)
            update_pipeline_json(pipeline_id, pipeline_json)
            create_gate_in_autopilot(service[4], gate_id, gate_name, log_template_id, None)


        try:
            metric_template_ids = metric_template_dictionary[service[0]]
        except KeyError as ke:
            metric_template_ids = []

        for metric_template_id in metric_template_ids:
            #update gate in autopilot
            if len(gate_ids) > 0:
                for gateid in gate_ids:
                    update_gate_in_autopilot(gateid, metric_template_id)
            else:
                app_environment_id = fetch_app_environment(service[4])
                if app_environment_id is None or len(app_environment_id) <= 0:
                    app_environment_id = create_app_environment(service[4])
                gate_name = "verification-gate-" + str(counter)
                gate_id = create_gate(gate_name, app_environment_id[0])
                map_pipeline_gate(pipeline_id, gate_id)
                pipeline = fetch_pipeline_json(pipeline_id)
                pipeline_json = pipeline[0][1]
                json_msg = json.loads(pipeline_json)
                ref_id = 1
                requisite_stage_ref_ids = []
                stages = []
                latest_stage = get_latest_stage(pipeline_json)
                if latest_stage is not None:
                    latest_ref_id = int(latest_stage['refId'])
                    ref_id = latest_ref_id + 1
                    requisite_stage_ref_ids.append(str(latest_ref_id))
                    stages = json_msg['stages']

                pipeline_json = get_pipeline_json(pipeline_uuid, gate_name, str(ref_id), requisite_stage_ref_ids,
                                                  stages)
                update_pipeline_json(pipeline_id, pipeline_json)
                create_gate_in_autopilot(service[4], gate_id, gate_name, None, metric_template_id)


    except Exception as e:
        print("Exception occured while persisting gate details : ", e)
        raise e
    return counter + 1


def get_latest_stage(pipeline_json):
    json_payload = json.loads(pipeline_json)
    stage = None
    if json_payload is not None and len(json_payload):
        stages = json_payload['stages']
        if stages is not None and len(stages) > 0:
            stages.sort(key=extract_ref_id, reverse=True)
            stage = stages[0]
    return stage


def extract_ref_id(stage):
    ref_id = 0
    ref_id = str(stage['refId'])
    return ref_id


def fetch_pipeline_json(pipeline_id):
    cur = platform_conn.cursor()
    cur.execute("SELECT uuid, pipeline_json FROM pipeline where id = " + str(pipeline_id))
    result = cur.fetchall()
    return result


def update_pipeline_json(pipeline_id, pipeline_json):
    try:
        cur = platform_conn.cursor()
        cur.execute(
            "UPDATE pipeline SET pipeline_json='" + json.dumps(pipeline_json) + "' where id = " + str(pipeline_id))
    except Exception as e:
        print("Exception occured while updating pipeline json : ", e)
        raise e


def get_pipeline_json(pipeline_uuid, gate_name, refId, requisiteStageRefIds, stages):
    pipeline_json = {"expectedArtifacts": None,
                     "keepWaitingPipelines": None,
                     "parameterConfig": None,
                     "lastModifiedBy": None,
                     "index": None,
                     "triggers": None,
                     "appConfig": None,
                     "limitConcurrent": None,
                     "application": None,
                     "spelEvaluator": None,
                     "name": None,
                     "stages": stages,
                     "id": pipeline_uuid,
                     "updateTs": None,
                     "notifications": None}

    stage = {"type": "Verification",
             "alias": "preconfiguredJob",
             "name": gate_name,
             "requisiteStageRefIds": requisiteStageRefIds,
             "refId": refId}

    parameters = {"gateurl": oes_gate_url + "/autopilot/api/v3/registerCanary",
                  "baselinestarttime": "",
                  "canaryresultscore": "90",
                  "canarystarttime": "",
                  "gate": gate_name,
                  "lifetime": "0.1",
                  "log": "true",
                  "metric": "true",
                  "minicanaryresult": "70",
                  "imageids": "${parameters.imageids}",
                  "comments": '''<b>Status:</b>${#stage("$stage_name")["outputs"]["overallstatus"]} \\\n<b>Overall Score:</b>${#stage("$stage_name")["outputs"]["overallscore"]} \\\n<b>Analysis Report:</b> <a href="${#stage("$stage_name")["outputs"]["canaryreporturl"]}">${#stage("$stage_name")["outputs"]["canaryreporturl"]}</a>'''}

    comments = parameters['comments']
    comments = comments.replace("$stage_name", gate_name)
    parameters['comments'] = comments
    stage['parameters'] = parameters
    stages = pipeline_json['stages']
    stages.append(stage)
    pipeline_json['stages'] = stages
    return pipeline_json


def fetch_applications():
    cur = autopilot_conn.cursor()
    cur.execute(
        "SELECT opsmx_id, opsmxcreateddate, opsmxlastupdateddate, description, email, name, userid, groupname FROM application where active = 't'")
    result = cur.fetchall()
    return result


def migrate_applications(applications):
    try:
        cur = platform_conn.cursor()
        for app in applications:
            data = app[1], app[2], app[3], app[4], app[5], 'OES'
            cur.execute(
                "INSERT INTO applications (created_at, updated_at, description, email, name, source) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                data)
        platform_id = cur.fetchone()[0]
        update_application_id_in_autopilot(app[0], platform_id)
        print("applications successfully migrated to v3.7")
    except Exception as e:
        print("Exception occured while migrating applications to v3.7 : ", e)
        raise e


def update_application_id_in_autopilot(opsmx_id, platform_id):
    try:
        cur = autopilot_v37_conn.cursor()
        cur.execute("UPDATE application SET id = "+str(platform_id) + " WHERE id = "+str(opsmx_id))
        cur.execute("UPDATE service SET application_id = "+str(platform_id) + " WHERE application_id = "+str(opsmx_id))
        cur.execute("UPDATE canaryanalysis SET application_id = "+str(platform_id) + " WHERE application_id = "+ str(opsmx_id))
        cur.execute("UPDATE casservicemetricdetails SET application_id = " + str(platform_id) + " WHERE application_id = " + str(opsmx_id))
        cur.execute("UPDATE loganalysis SET application_id = " + str(platform_id) + " WHERE application_id = " + str(opsmx_id))
        cur.execute("UPDATE riskanalysis SET application_id = " + str(platform_id) + " WHERE application_id = " + str(opsmx_id))
        cur.execute("UPDATE riskanalysis SET application_id = " + str(platform_id) + " WHERE application_id = " + str(opsmx_id))
        cur.execute("UPDATE servicegate SET application_id = " + str(platform_id) + " WHERE application_id = " + str(opsmx_id))
        cur.execute("UPDATE userlogservicetemplate SET application_id = " + str(platform_id) + " WHERE application_id = " + str(opsmx_id))
        cur.execute("UPDATE userservicetemplate SET application_id = " + str(platform_id) + " WHERE application_id = " + str(opsmx_id))
        cur.execute("UPDATE tags SET application_id = " + str(platform_id) + " WHERE application_id = " + str(opsmx_id))
    except Exception as e:
        print("Exception occured while updating autopilot with the new application id : ", e)
        raise e


def populate_app_update_info(applications):
    try:
        cur = platform_conn.cursor()
        for app in applications:
            date_time = datetime.datetime.now()
            data = date_time, date_time, app[2], app[0]
            cur.execute(
                "INSERT INTO app_update_info (created_at, updated_at, updated_time, application_id) VALUES (%s, %s, %s, %s)",
                data)
        print("Successfully populated app_update_info table")
    except Exception as e:
        print("Exception occured while populating app_update_info : ", e)
        raise e


def fetch_services():
    cur = autopilot_conn.cursor()
    cur.execute(
        "SELECT opsmx_id, opsmxcreateddate, opsmxlastupdateddate, name, applicationid FROM service where active = 't'")
    result = cur.fetchall()
    return result


def migrate_services(service):
    try:
        cur = platform_conn.cursor()
        data = service[1], service[2], service[3], service[4], False, False
        cur.execute(
            "INSERT INTO service (created_at, updated_at, name, application_id, is_hidden, is_imported) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
            data)
        platform_id = cur.fetchone()[0]
        update_service_id_in_autopilot(service[0], platform_id)
    except Exception as e:
        print("Exception occured while migrating services to v3.7 : ", e)
        raise e


def update_service_id_in_autopilot(opsmx_id, platform_id):
    try:
        cur = autopilot_v37_conn.cursor()
        cur.execute("UPDATE service SET id = " + str(platform_id) + " WHERE id = " + str(opsmx_id))
        cur.execute("UPDATE canaryanalysis SET service_id = " + str(platform_id) + " WHERE service_id = " + str(opsmx_id))
        cur.execute("UPDATE entropy SET service_id = " + str(platform_id) + " WHERE service_id = " + str(opsmx_id))
        cur.execute("UPDATE loganalysis SET service_id = " + str(platform_id) + " WHERE service_id = " + str(opsmx_id))
        cur.execute("UPDATE logcluster SET service_id = " + str(platform_id) + " WHERE service_id = " + str(opsmx_id))
        cur.execute("UPDATE logclusterdetails SET service_id = " + str(platform_id) + " WHERE service_id = " + str(opsmx_id))
        cur.execute("UPDATE servicegate SET service_id = " + str(platform_id) + " WHERE service_id = " + str(opsmx_id))
        cur.execute("UPDATE serviceriskanalysis SET service_id = " + str(platform_id) + " WHERE service_id = " + str(opsmx_id))
        cur.execute("UPDATE userlogfeedback SET service_id = " + str(platform_id) + " WHERE service_id = " + str(opsmx_id))
        cur.execute("UPDATE tagsfeedback SET service_id = " + str(platform_id) + " WHERE service_id = " + str(opsmx_id))
    except Exception as e:
        print("Exception occured while updating autopilot with the new service id : ", e)
        raise e


def create_pipeline(service, pipeline_uuid):
    try:
        cur = platform_conn.cursor()
        data = service[1], service[2], True, '{}', service[3], pipeline_uuid
        cur.execute(
            "INSERT INTO pipeline (created_at, updated_at, is_default, pipeline_json, pipeline_name, uuid) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
            data)
        pipelineId = cur.fetchone()[0]
    except Exception as e:
        print("Exception occured while creating pipelines : ", e)
        raise e
    return pipelineId


def map_service_pipeline(service_id, pipeline_id, index):
    try:
        cur = platform_conn.cursor()
        date_time = str(datetime.datetime.now())
        data = date_time, date_time, index, pipeline_id, service_id
        cur.execute(
            "INSERT INTO service_pipeline_map (created_at, updated_at, index, pipeline_id, service_id) VALUES (%s, %s, %s, %s, %s)",
            data)
    except Exception as e:
        print("Exception occured while mapping service and pipeline : ", e)
        raise e


def fetch_app_environment(application_id):
    cur = platform_conn.cursor()
    cur.execute("SELECT id FROM app_environment where application_id = " + str(application_id))
    result = cur.fetchall()
    return result


def create_app_environment(application_id):
    try:
        cur = platform_conn.cursor()
        date_time = str(datetime.datetime.now())
        data = date_time, date_time, 'default', application_id
        cur.execute(
            "INSERT INTO app_environment (created_at, updated_at, environment, application_id) VALUES (%s, %s, %s, %s) RETURNING id",
            data)
        app_environment_id = cur.fetchone()
    except Exception as e:
        print("Exception occured while creating app environment : ", e)
        raise e
    return app_environment_id


def create_gate(gate_name, app_environment_id):
    try:
        cur = platform_conn.cursor()
        date_time = str(datetime.datetime.now())
        data = date_time, date_time, gate_name, 'verification', app_environment_id
        cur.execute(
            "INSERT INTO service_gate (created_at, updated_at, gate_name, gate_type, app_environment_id) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            data)
        gate_id = cur.fetchone()[0]
    except Exception as e:
        print("Exception occured while creating gate : ", e)
        raise e
    return gate_id


def map_pipeline_gate(pipeline_id, gate_id):
    try:
        cur = platform_conn.cursor()
        date_time = str(datetime.datetime.now())
        data = date_time, date_time, pipeline_id, gate_id
        cur.execute(
            "INSERT INTO gate_pipeline_map (created_at, updated_at, pipeline_id, service_gate_id) VALUES (%s, %s, %s, %s)",
            data)
    except Exception as e:
        print("Exception occured while gate pipeline map : ", e)
        raise e


def create_gate_in_autopilot(application_id, gate_id, gate_name, logtemplate_id, metrictemplate_id):
    try:
        cur = autopilot_v37_conn.cursor()
        date_time = str(datetime.datetime.now())
        if logtemplate_id is not None and metrictemplate_id is not None:
            data = True, date_time, date_time, application_id, gate_id, gate_name, logtemplate_id, metrictemplate_id
            cur.execute(
                "INSERT INTO servicegate (active, opsmxcreateddate, opsmxlastupdateddate, application_id, gateid, gatename, logtemplate_id, metrictemplate_id) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", data)

        elif logtemplate_id is not None and metrictemplate_id is None:
            data = True, date_time, date_time, application_id, gate_id, gate_name, logtemplate_id
            cur.execute(
                "INSERT INTO servicegate (active, opsmxcreateddate, opsmxlastupdateddate, application_id, gateid, gatename, logtemplate_id) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)", data)

        elif logtemplate_id is None and metrictemplate_id is not None:
            data = True, date_time, date_time, application_id, gate_id, gate_name, metrictemplate_id
            cur.execute(
                "INSERT INTO servicegate (active, opsmxcreateddate, opsmxlastupdateddate, application_id, gateid, gatename, metrictemplate_id) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)", data)


    except Exception as e:
        print("Exception occured while creating gate in autopilot : ", e)
        raise e


def update_gate_in_autopilot(gate_id, metrictemplate_id):
    try:
        cur = autopilot_v37_conn.cursor()
        cur.execute("UPDATE servicegate SET metrictemplate_id = "+metrictemplate_id + " WHERE gateid = "+gate_id)
    except Exception as e:
        print("Exception occured while updating metric template in servicegate : ", e)
        raise e



def fetch_datasources():
    try:
        cur = autopilot_conn.cursor()
        cur.execute(
            "SELECT opsmxcreateddate, opsmxlastupdateddate, accountname, sourcetype, credentials FROM credential")
        result = cur.fetchall()
        return result
    except Exception as e:
        print("Exception occured while fetching datasources : ", e)
        raise e


def migrate_datasources(datasources):
    try:
        cur = platform_conn.cursor()
        for datasource in datasources:
            if datasource[0] is None or len(str(datasource[0])) <= 0:
                opsmx_created_time = datetime.datetime.now()
                opsmx_created_time = str(opsmx_created_time)
            else:
                opsmx_created_time = datasource[0]

            if datasource[1] is None or len(str(datasource[1])) <= 0:
                opsmx_updated_time = datetime.datetime.now()
                opsmx_updated_time = str(opsmx_updated_time)
            else:
                opsmx_updated_time = datasource[1]

            datasource_config = json.loads(datasource[4])
            datasource_type = str(datasource[3]).upper()
            data = opsmx_created_time, opsmx_updated_time, True, datasource[2], datasource_type, json.dumps(
                datasource_config)
            cur.execute(
                "INSERT INTO datasource (created_at, updated_at, active, name, datasourcetype, config) VALUES (%s, %s, %s, %s, %s, %s)",
                data)
        print("datasources successfully migrated to v3.7")

    except Exception as e:
        print("Exception occured while migrating datasources : ", e)
        raise e


def fetch_ldap_groups():
    groups = []
    try:
        ldap_conn.search(search_base='dc=example,dc=com', search_scope=ldap.SUBTREE,
                         search_filter='(objectclass=groupOfNames)', attributes=ldap.ALL_ATTRIBUTES)
        ldap_groups = ldap_conn.entries
        for group in ldap_groups:
            groups.append(str(group['cn']))
        print("ldap groups : ", groups)
        return groups
    except Exception as e:
        print("Exception occured while fetching all ldap groups : ", e)
        raise e
    finally:
        ldap_conn.unbind()


def delete_user_groups():
    try:
        cur = platform_conn.cursor()
        cur.execute("DELETE FROM user_group")
    except Exception as e:
        print("Exception occured while deleting user groups : ", e)
        raise e


def populate_user_groups(ldap_groups):
    try:
        cur = platform_conn.cursor()
        for ldap_group in ldap_groups:
            opsmxtime = datetime.datetime.now()
            opsmxtime = str(opsmxtime)
            data = opsmxtime, opsmxtime, ldap_group
            cur.execute("INSERT INTO user_group (created_at, updated_at, name) VALUES (%s, %s, %s)",
                        data)
        print("user_group table populated successfully")
    except Exception as e:
        print("Exception occured while populating user_group : ", e)
        raise e


def grant_read_permissions(applications, ldap_groups):
    try:
        cur = platform_conn.cursor()
        for app in applications:
            for ldap_group in ldap_groups:
                opsmxtime = datetime.datetime.now()
                opsmxtime = str(opsmxtime)
                object_id = app[0]
                object_type = "APP"
                permission_id = "read"
                cur.execute("SELECT id FROM user_group WHERE name='" + ldap_group + "'")
                group_id = cur.fetchone()[0]
                data = opsmxtime, opsmxtime, object_id, object_type, permission_id, group_id
                cur.execute(
                    "INSERT INTO user_group_permission (created_at, updated_at, object_id, object_type, permission_id, group_id) VALUES (%s, %s, %s, %s, %s, %s)",
                    data)
        print("all the ldap groups assigned with read permissions")
    except Exception as e:
        print("Exception occured while assigning read permissions : ", e)
        raise e


def grant_write_permissions(applications):
    try:
        ap_cur = autopilot_conn.cursor()
        platfor_cur = platform_conn.cursor()
        for app in applications:
            user_id = app[6]
            object_id = app[0]
            object_type = "APP"
            permission_id = "write"
            ap_cur.execute("SELECT ldapgroups from userlogindetails where opsmx_id = " + str(user_id))
            ldap_groups = ap_cur.fetchone()[0]
            if ldap_groups is not None and len(ldap_groups) > 0:
                ldap_groups_json = json.loads(ldap_groups)
                for ldap_group in ldap_groups_json:
                    opsmxtime = datetime.datetime.now()
                    opsmxtime = str(opsmxtime)
                    platfor_cur.execute("SELECT id FROM user_group WHERE name='" + ldap_group + "'")
                    group_id = platfor_cur.fetchone()[0]
                    data = opsmxtime, opsmxtime, object_id, object_type, permission_id, group_id
                    platfor_cur.execute(
                        "INSERT INTO user_group_permission (created_at, updated_at, object_id, object_type, permission_id, group_id) VALUES (%s, %s, %s, %s, %s, %s)",
                        data)
            else:
                print("application : " + app[
                    5] + " is not created by an ldap user and hence not assigning write permission")
        print("successfully granted write permissions to all the ldap groups that the user belongs to")

    except Exception as e:
        print("Exception occured while assigning write permission : ", e)
        raise e


def grant_write_permission_to_added_group(applications):
    try:
        platfor_cur = platform_conn.cursor()
        for app in applications:
            group = app[7]
            object_id = app[0]
            object_type = "APP"
            permission_id = "write"
            platfor_cur.execute("SELECT id FROM user_group WHERE name='" + group + "'")
            group_id = platfor_cur.fetchone()
            if group_id is not None:
                group_id = group_id[0]
                platfor_cur.execute(
                    "SELECT COUNT(*) FROM user_group_permission WHERE group_id = {0} AND object_id = {1} AND object_type = {2}".format(
                        group_id, object_id, "'APP'"))
                count = platfor_cur.fetchone()[0]
                if (count <= 0):
                    opsmxtime = datetime.datetime.now()
                    opsmxtime = str(opsmxtime)
                    data = opsmxtime, opsmxtime, object_id, object_type, permission_id, group_id
                    platfor_cur.execute(
                        "INSERT INTO user_group_permission (created_at, updated_at, object_id, object_type, permission_id, group_id) VALUES (%s, %s, %s, %s, %s, %s)",
                        data)
            else:
                print("Group : " + group + " is not an LDAP group and hence not assigning write permission")
        print("successfully granted write permission to the added groups")
    except Exception as e:
        print("Exception occured while granting write permission to added groups : ", e)
        raise e


def grant_write_permission_to_admin_groups(applications, group):
    try:
        platfor_cur = platform_conn.cursor()
        platfor_cur.execute("SELECT id FROM user_group WHERE name='" + group + "'")
        group_id = platfor_cur.fetchone()
        if group_id is not None:
            group_id = group_id[0]
            for app in applications:
                object_id = app[0]
                object_type = "APP"
                permission_id = "write"
                platfor_cur.execute(
                    "SELECT COUNT(*) FROM user_group_permission WHERE group_id = {0} AND object_id = {1} AND object_type = {2}".format(
                        group_id, object_id, "'APP'"))
                count = platfor_cur.fetchone()[0]
                if (count <= 0):
                    opsmxtime = datetime.datetime.now()
                    opsmxtime = str(opsmxtime)
                    data = opsmxtime, opsmxtime, object_id, object_type, permission_id, group_id
                    platfor_cur.execute(
                        "INSERT INTO user_group_permission (created_at, updated_at, object_id, object_type, permission_id, group_id) VALUES (%s, %s, %s, %s, %s, %s)",
                        data)
        else:
            print("Group : " + group + " is not a valid admin group")
        print("successfully granted write permission to the admin groups")
    except Exception as e:
        print("Exception occured while granting write permission to admin groups : ", e)
        raise e


if __name__ == '__main__':
    n = len(sys.argv)
    if n != 13:
        print('Please pass valid 12 arguments with <autopilot-v2.9-db-name> <autopilot-v3.7-db-name> <autopilot-v3.7-db-host> <autopilot-v2.9-db-host> <platform-db-host>  <db-port> <ldap-host> <ldap-port> <ldap-user-name> <ldap-password> <ldap-admin-group> <oes-gate-url>')
        exit(0)

    ###DB Config####
    autopilot_db = sys.argv[1]
    autopilot_v37_db = sys.argv[2]
    autopilot_v37_host = sys.argv[3]
    host = sys.argv[4]
    platform_host = sys.argv[5]
    port = sys.argv[6]
    ldap_host = sys.argv[7]
    ldap_port = int(sys.argv[8])
    ldap_username = sys.argv[9]
    ldap_password = sys.argv[10]
    admin_group = sys.argv[11]
    oes_gate_url = sys.argv[12]

    canaryDictonary = {}
    canaryanalysisDictonary = {}
    metricscoreDictonary = {}
    log_template_dictionary = {}
    metric_template_dictionary = {}
    # ldap_username = "cn=admin,dc=example,dc=com"
    # ldap_password = "adminroot123"

    platform_db = 'platformdb'
    # Establishing the platform db connection
    platform_conn = psycopg2.connect(database=platform_db, user="postgres", password="networks123", host=platform_host,
                                     port=port)
    print("Opened platform database connection successfully")

    # Establishing the opsmx db connection
    autopilot_conn = psycopg2.connect(database=autopilot_db, user="postgres", password="networks123", host=host,
                                      port=port)
    print("Opened opsmx v2.9 database connection successfully")

    # Establishing the opsmx db connection
    autopilot_v37_conn = psycopg2.connect(database=autopilot_v37_db, user="postgres", password="networks123",
                                          host=autopilot_v37_host, port=port)
    print("Opened opsmx v3.7 database connection successfully")

    # Establishing the LDAP connection
    server = Server(host=ldap_host, port=ldap_port, use_ssl=False, get_info=ALL)
    ldap_conn = Connection(server, ldap_username, ldap_password, auto_bind=True)
    print("LDAP connection established")

    cur = autopilot_v37_conn.cursor()
    cur_2_9 = autopilot_conn.cursor()

    perform_migration()