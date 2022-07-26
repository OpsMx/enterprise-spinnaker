import logging
import sys
import psycopg2


def delete_unused_audit_data():
    try:
        print('Removing unused audit data query started.')
        logging.info('Removing unused audit data query started.')

        audit_cursor.execute("""DELETE FROM audit_events WHERE id NOT IN (select id from audit_events 
        where data -> 'details' ->> 'type' IN ('orca:pipeline:complete', 'orca:pipeline:failed', 'orca:stage:starting', 
        'orca:stage:complete', 'orca:stage:failed', 'orca:pipeline:starting', 'orca:orchestration:starting', 
        'orca:orchestration:complete')) and "source" = 'spinnaker' RETURNING id;""")

        result = audit_cursor.fetchall()

        logging.info('Audit event ids which got deleted ' + '\n' + ''.join(str(result)))
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

    audit_cursor = audit_conn.cursor()

    delete_unused_audit_data()
