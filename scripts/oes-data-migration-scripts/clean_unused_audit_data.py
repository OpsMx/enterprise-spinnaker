import logging
import sys
import psycopg2


def delete_unused_audit_data():
    audit_ids_to_be_retained = []
    step = audit_cursor.itersize

    print('Fetching audit data started.')
    logging.info('Fetching audit data started.')
    try:
        audit_cursor.execute('select id, data from audit_events;')
        i = 0

        for row in audit_cursor:
            audit_data_dict = row[1]
            i += 1

            if 'eventType' in audit_data_dict:
                audit_ids_to_be_retained.append(row[0])
                continue
            if 'details' in audit_data_dict:
                details_dict = audit_data_dict['details']
                if 'type' in details_dict:
                    details_type = details_dict['type']
                    if details_type in used_pipeline_execution_events:
                        audit_ids_to_be_retained.append(row[0])
                        continue

            if 'content' in audit_data_dict:
                content_dict = audit_data_dict['content']
                if 'execution' in content_dict:
                    execution_dict = content_dict['execution']
                    if 'stages' in execution_dict:
                        stages_list = execution_dict['stages']
                        for stages_dict in stages_list:
                            if 'type' in stages_dict:
                                stage_type = stages_dict['type']
                                if stage_type in app_onboarding_events:
                                    audit_ids_to_be_retained.append(row[0])
                                    break

            if i % step == 0:
                print('Number of rows Processed ', str(i))
                logging.info('Number of rows Processed ' + str(i))

        print('Successfully fetched and identified the unused rows for deletion.')
        logging.info('Successfully fetched and identified the unused rows for deletion.')

        logging.info('Audit events ids which are to be retained ' + '\n' + ''.join(str(audit_ids_to_be_retained)))

        print('Removing unused audit data started.')
        logging.info('Removing unused audit data started.')

        audit_del_cursor = audit_conn.cursor()
        query = 'DELETE FROM audit_events WHERE NOT (id = ANY(%s)) RETURNING id;'
        audit_del_cursor.execute(query, (audit_ids_to_be_retained,))
        result = audit_del_cursor.fetchall()

        logging.info('Audit event ids which got deleted ' + '\n' + ''.join(str(result)))

        logging.info('The number of ids that are to be retained is ' + str(len(audit_ids_to_be_retained)))
        logging.info('The number of ids that got deleted is ' + str(len(result)))

        audit_conn.commit()
        print('The number of records deleted is ', str(len(result)))
        print('*********** Successfully cleaned unused audit data ******************')
        logging.info('*********** Successfully cleaned unused audit data ******************')

    except Exception as e:
        audit_conn.rollback()
        print('Exception occurred while cleaning audit data ', e)
        logging.error("Exception occurred while cleaning audit data : ", exc_info=True)
        raise Exception("FAILURE: Audit db clean up script failed. Please contact the support team")
    finally:
        audit_conn.close()


if __name__ == '__main__':
    n = len(sys.argv)

    if n != 6:
        print("Please pass valid 5 arguments <audit_db-name> <db-username> <db-password> <audit-db-host> <db-port>")
        exit(1)

    logging.basicConfig(filename='/tmp/cleanup_needless_audit_data.log', filemode='w',
                        format="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s", datefmt='%H:%M:%S',
                        level=logging.INFO)

    audit_db = sys.argv[1]
    db_username = sys.argv[2]
    db_password = sys.argv[3]
    audit_host = sys.argv[4]
    port = sys.argv[5]

    # Establishing the audit db connection
    audit_conn = psycopg2.connect(database=audit_db, user=db_username, password=db_password, host=audit_host,
                                  port=port)
    print('Audit database connection established successfully')
    logging.info('Audit database connection established successfully')

    used_pipeline_execution_events = ['orca:stage:starting', 'orca:stage:complete', 'orca:stage:failed',
                                      'orca:pipeline:failed', 'orca:pipeline:complete', 'orca:pipeline:starting']

    app_onboarding_events = ['createApplication', 'updateApplication', 'deleteApplication', 'savePipeline',
                             'updatePipeline', 'deletePipeline']

    audit_cursor = audit_conn.cursor('audit_cur')
    audit_cursor.itersize = 5000

    delete_unused_audit_data()
