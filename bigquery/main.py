import json

from pymysqlreplication import BinLogStreamReader
from pymysqlreplication.row_event import (
  DeleteRowsEvent,
  UpdateRowsEvent,
  WriteRowsEvent,
)

from utils import concat_sql_from_binlog_event
import pymysql
import os
import sys
import logging
from google.cloud import bigquery

# Logging
logging.basicConfig(
    #filename='/tmp/snowflake_python_connector.log',
    stream=sys.stdout,
    level=logging.INFO,
    format="%(levelname)s %(message)s")

def main(mysqlConfigs, redshiftConfigs):
  SCHEMA = [
      bigquery.SchemaField('id', 'INTEGER', mode='REQUIRED'),
      bigquery.SchemaField('name', 'STRING', mode='REQUIRED'),
  ]

  project_id = os.getenv('PROJECT_ID')
  dataset_id = 'testdb'
  table_id = 'testtbl'

  client = bigquery.Client()

  
  client.delete_dataset(client.dataset(dataset_id), delete_contents=True)

  dataset = bigquery.Dataset(client.dataset(dataset_id))
  dataset = client.create_dataset(dataset)
  dataset.location = 'US'

  table = bigquery.Table(dataset.table(table_id), schema=SCHEMA)
  table = client.create_table(table)

  query = "SELECT * FROM `{}`.`{}`.`{}` limit 100".format(project_id, dataset_id, table_id)


  client = bigquery.Client()
  table_ref = client.dataset(dataset_id).table(table_id)
  '''  
  table = client.get_table(table_ref)
  rows_to_insert = [
      ('Phred Phlyntstone', 32),
      ('Wylma Phlyntstone', 1),
  ]
  errors = client.insert_rows(table, rows_to_insert)
  print(errors)
  assert errors == []
  '''

  query_job = client.query(query, location='US')
  for row in query_job:
      print(row)
  conn = pymysql.connect(**mysqlConfigs)


  stream = BinLogStreamReader(
    connection_settings = mysqlConfigs,
    server_id=100,
    blocking=True,
    resume_stream=True,
    only_events=[DeleteRowsEvent, WriteRowsEvent, UpdateRowsEvent])

  cursor = conn.cursor()
  for binlogevent in stream:
    e_start_pos, last_pos = stream.log_pos, stream.log_pos
    #print([a for a in dir(binlogevent) if not a.startswith('__')])
    for row in binlogevent.rows:
      event = {"schema": binlogevent.schema,
      "table": binlogevent.table,
      "type": type(binlogevent).__name__,
      "row": row
      }

      #if isinstance(binlog_event, QueryEvent) and binlog_event.query == 'BEGIN':
      #  e_start_pos = last_pos
      #print(json.dumps(event))
      binlog2sql = concat_sql_from_binlog_event(cursor=cursor, binlog_event=binlogevent, row=row, e_start_pos=e_start_pos).replace('`', "").replace('testtbl', '`testdb.testtbl`')
      print(binlog2sql)

      query_job = client.query(binlog2sql, location='US')
      result = query_job.result()
      #print("Total rows affected: ", query_job.num_dml_affected_rows)
      
      #query_job = client.query(query, location='US')
      #for row in query_job:
      #    print(row)

if __name__ == "__main__":
  mysqlConfigs = {
      "host": os.getenv('MYSQL_HOST'),
      "port": int(os.getenv('MYSQL_PORT')),
      "user": os.getenv('MYSQL_USER'),
      "passwd": os.getenv('MYSQL_PASSWORD'),
      'db': os.getenv('MYSQL_DATABASE'),
  }
  bigqueryConfigs = {
    'dataset': 'testdb'
  }
  main(mysqlConfigs, bigqueryConfigs)