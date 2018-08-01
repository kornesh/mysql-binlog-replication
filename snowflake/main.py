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
import snowflake.connector


# Logging
logging.basicConfig(
    #filename='/tmp/snowflake_python_connector.log',
    stream=sys.stdout,
    level=logging.INFO,
    format="%(levelname)s %(message)s")

def main(snowflakeConfig, mysqlConfigs):
  # Connecting to Snowflake
  sf = snowflake.connector.connect(**snowflakeConfig)

  conn = pymysql.connect(**mysqlConfigs)
  # Usually a schema is a collection of tables and a Database is a collection of schemas.
  # https://stackoverflow.com/a/19257781

  
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
      binlog2sql = concat_sql_from_binlog_event(cursor=cursor, binlog_event=binlogevent, row=row, e_start_pos=e_start_pos).replace('`', '')
      print(binlog2sql)

      try:
        sf.cursor().execute(binlog2sql)
      except snowflake.connector.errors.ProgrammingError as e:
        # default error message
        print(e)
        # customer error message
        print('Error {0} ({1}): {2} ({3})'.format(e.errno, e.sqlstate, e.msg, e.sfqid))


if __name__ == "__main__":
  # Setting your account and login information
  snowflakeConfig = {
      'account': os.getenv('SNOWFLAKE_ACCOUNT'),
      'user': os.getenv('SNOWFLAKE_USER'),
      'password': os.getenv('SNOWFLAKE_PASSWORD'),
      'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE'),
      'database': os.getenv('SNOWFLAKE_DATABASE'),
      'schema': 'PUBLIC'
  }
  mysqlConfigs = {
      "host": os.getenv('MYSQL_HOST'),
      "port": int(os.getenv('MYSQL_PORT')),
      "user": os.getenv('MYSQL_USER'),
      "passwd": os.getenv('MYSQL_PASSWORD'),
      'db': os.getenv('MYSQL_DATABASE'),
  }
  main(snowflakeConfig, mysqlConfigs)