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

def main():
  configs = {
      "host": os.environ['MYSQL_HOST'],
      "port": int(os.environ['MYSQL_PORT']),
      "user": os.environ['MYSQL_USER'],
      "passwd": os.environ['MYSQL_PASSWORD']
  }
  conn = pymysql.connect(**configs)  
  cursor = conn.cursor()
  stream = BinLogStreamReader(
    connection_settings = configs,
    server_id=100,
    blocking=True,
    resume_stream=True,
    only_events=[DeleteRowsEvent, WriteRowsEvent, UpdateRowsEvent])

  for binlogevent in stream:
    e_start_pos, last_pos = stream.log_pos, stream.log_pos
    for row in binlogevent.rows:
      event = {"schema": binlogevent.schema,
      "table": binlogevent.table,
      "type": type(binlogevent).__name__,
      "row": row
      }
      #if isinstance(binlog_event, QueryEvent) and binlog_event.query == 'BEGIN':
      #  e_start_pos = last_pos
      print(json.dumps(event))
      print(concat_sql_from_binlog_event(cursor=cursor, binlog_event=binlogevent, row=row, e_start_pos=e_start_pos))


if __name__ == "__main__":
   main()