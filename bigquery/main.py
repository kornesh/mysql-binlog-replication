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
import psycopg2


# Logging
logging.basicConfig(
    #filename='/tmp/snowflake_python_connector.log',
    stream=sys.stdout,
    level=logging.INFO,
    format="%(levelname)s %(message)s")

def main(mysqlConfigs, redshiftConfigs):

  rs = psycopg2.connect(**redshiftConfigs)

  conn = pymysql.connect(**mysqlConfigs)



  rs.cursor().execute("""
    DROP TABLE IF EXISTS testtbl;
    CREATE TABLE testtbl(id integer, name varchar(255));
    """)

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
      binlog2sql = concat_sql_from_binlog_event(cursor=cursor, binlog_event=binlogevent, row=row, e_start_pos=e_start_pos).replace('`', "")
      print(binlog2sql)

      try:
        rs.cursor().execute(binlog2sql)
      except psycopg2.Error as e:
        print(e)

      # cur = rs.cursor()
      # cur.execute("SELECT * FROM testtbl;")

      # for row in cur.fetchall():
      #   print(row)
      

if __name__ == "__main__":
  redshiftConfigs = {
      "host": os.getenv('REDSHIFT_HOST'),
      "port": int(os.getenv('REDSHIFT_PORT')),
      "user": os.getenv('REDSHIFT_USER'),
      "password": os.getenv('REDSHIFT_PASSWORD'),
      'dbname': os.getenv('REDSHIFT_DATABASE'),
  }
  mysqlConfigs = {
      "host": os.getenv('MYSQL_HOST'),
      "port": int(os.getenv('MYSQL_PORT')),
      "user": os.getenv('MYSQL_USER'),
      "passwd": os.getenv('MYSQL_PASSWORD'),
      'db': os.getenv('MYSQL_DATABASE'),
  }
  main(mysqlConfigs, redshiftConfigs)