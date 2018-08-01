# Ripped off from https://github.com/danfengcao/binlog2sql

import os
import sys
import argparse
import datetime

if sys.version > '3':
    PY3PLUS = True
else:
    PY3PLUS = False

from pymysqlreplication.row_event import (
    WriteRowsEvent,
    UpdateRowsEvent,
    DeleteRowsEvent,
)
from pymysqlreplication.event import QueryEvent


def compare_items(items):
    # caution: if v is NULL, may need to process
    (k, v) = items
    if v is None:
        return '`%s` IS %%s' % k
    else:
        return '`%s`=%%s' % k


def fix_object(value):
    """Fixes python objects so that they can be properly inserted into SQL queries"""
    if isinstance(value, set):
        value = ','.join(value)
    if PY3PLUS and isinstance(value, bytes):
        return value.decode('utf-8')
    elif not PY3PLUS and isinstance(value, unicode):
        return value.encode('utf-8')
    else:
        return value

def concat_sql_from_binlog_event(cursor, binlog_event, row=None, e_start_pos=None, flashback=False, no_pk=False):
    if flashback and no_pk:
        raise ValueError('only one of flashback or no_pk can be True')
    if not (isinstance(binlog_event, WriteRowsEvent) or isinstance(binlog_event, UpdateRowsEvent)
            or isinstance(binlog_event, DeleteRowsEvent) or isinstance(binlog_event, QueryEvent)):
        raise ValueError('binlog_event must be WriteRowsEvent, UpdateRowsEvent, DeleteRowsEvent or QueryEvent')

    sql = ''
    if isinstance(binlog_event, WriteRowsEvent) or isinstance(binlog_event, UpdateRowsEvent) \
            or isinstance(binlog_event, DeleteRowsEvent):
        pattern = generate_sql_pattern(binlog_event, row=row, flashback=flashback, no_pk=no_pk)
        sql = cursor.mogrify(pattern['template'], pattern['values'])
        time = datetime.datetime.fromtimestamp(binlog_event.timestamp)
        #sql += ' #start %s end %s time %s' % (e_start_pos, binlog_event.packet.log_pos, time)
    elif flashback is False and isinstance(binlog_event, QueryEvent) and binlog_event.query != 'BEGIN' \
            and binlog_event.query != 'COMMIT':
        if binlog_event.schema:
            sql = 'USE {0};\n'.format(binlog_event.schema)
        sql += '{0};'.format(fix_object(binlog_event.query))

    return sql


def generate_sql_pattern(binlog_event, row=None, flashback=False, no_pk=False):
    template = ''
    values = []
    if flashback is True:
        if isinstance(binlog_event, WriteRowsEvent):
            template = 'DELETE FROM `{0}`.`{1}` WHERE {2} LIMIT 1;'.format(
                binlog_event.schema, binlog_event.table,
                ' AND '.join(map(compare_items, row['values'].items()))
            )
            values = map(fix_object, row['values'].values())
        elif isinstance(binlog_event, DeleteRowsEvent):
            template = 'INSERT INTO `{0}`.`{1}`({2}) VALUES ({3});'.format(
                binlog_event.schema, binlog_event.table,
                ', '.join(map(lambda key: '`%s`' % key, row['values'].keys())),
                ', '.join(['%s'] * len(row['values']))
            )
            values = map(fix_object, row['values'].values())
        elif isinstance(binlog_event, UpdateRowsEvent):
            template = 'UPDATE `{0}`.`{1}` SET {2} WHERE {3} LIMIT 1;'.format(
                binlog_event.schema, binlog_event.table,
                ', '.join(['`%s`=%%s' % x for x in row['before_values'].keys()]),
                ' AND '.join(map(compare_items, row['after_values'].items())))
            values = map(fix_object, list(row['before_values'].values())+list(row['after_values'].values()))
    else:
        if isinstance(binlog_event, WriteRowsEvent):
            if no_pk:
                # print binlog_event.__dict__
                # tableInfo = (binlog_event.table_map)[binlog_event.table_id]
                # if tableInfo.primary_key:
                #     row['values'].pop(tableInfo.primary_key)
                if binlog_event.primary_key:
                    row['values'].pop(binlog_event.primary_key)

            template = 'INSERT INTO `{0}`.`{1}`({2}) VALUES ({3});'.format(
                binlog_event.schema, binlog_event.table,
                ', '.join(map(lambda key: '`%s`' % key, row['values'].keys())),
                ', '.join(['%s'] * len(row['values']))
            )
            values = map(fix_object, row['values'].values())
        elif isinstance(binlog_event, DeleteRowsEvent):
            template = 'DELETE FROM `{0}`.`{1}` WHERE {2} LIMIT 1;'.format(
                binlog_event.schema, binlog_event.table, ' AND '.join(map(compare_items, row['values'].items())))
            values = map(fix_object, row['values'].values())
        elif isinstance(binlog_event, UpdateRowsEvent):
            template = 'UPDATE `{0}`.`{1}` SET {2} WHERE {3} LIMIT 1;'.format(
                binlog_event.schema, binlog_event.table,
                ', '.join(['`%s`=%%s' % k for k in row['after_values'].keys()]),
                ' AND '.join(map(compare_items, row['before_values'].items()))
            )
            values = map(fix_object, list(row['after_values'].values())+list(row['before_values'].values()))

    return {'template': template, 'values': list(values)}
