#!/usr/bin/env python
import sys
import json


class ColumnInfo(object):
    data_types = {
#        'string'
        'char':'string',
        'character':'string',
        'varchar':'string',
        'tinytext':'string',
        'text':'string',
        'mediumtext':'string',
        'longtext':'string',
#        'integer'
        'tinyint':'integer',
        'smallint':'integer',
        'mediumint':'integer',
        'integer':'integer',
        'int':'integer',
        'bigint':'integer',
#        'float'
        'float':'float',
        'double':'float',
        'real':'float',
        'decimal':'float',
        'fixed':'float',
        'dec':'float',
        'numeric':'float',
#        'timestamp'
        'date':'timestamp',
        'datetime':'timestamp',
        'timestamp':'timestamp',
        'time':'timestamp',
#        'boolean'
        'bit':'boolean',
        'bool':'boolean',
        'boolean':'boolean',
    }

    def __init__(self, name, typ, nullable):
        self.name = name.lower()
        self.typ  = self.convert_type(typ)
        self.is_nullable = self.nullable(nullable)

    def schema(self):
        return { "name": self.name,
                 "type": self.typ.replace('timestamp', 'integer'),
                 "mode": self.is_nullable }

    def convert_type(self, original):
        return self.data_types.get(original.split('(')[0], None)

    def nullable(self, is_nullable):
        return 'nullable' if is_nullable in ['YES','yes'] else 'required'

    def query(self):
        if self.typ == 'timestamp':
            return '1000000*unix_timestamp(%(name)s) as %(name)s' % ({'t':self.name})
        return self.name


class SchemaParser(object):
    def __init__(self, dest):
        self.dest = dest

    def parse_schema(self, line):
        elements = line.strip().split('\t')
        info = ColumnInfo(*elements[0:3])
        return info.schema()

    def parse_query(self, line):
        elements = line.strip().split('\t')
        info = ColumnInfo(*elements[0:3])
        return info.query()

    def schema(self, fp):
        with fp:
            return json.dumps([self.parse_schema(line) for line in fp])

    def query(self, fp):
        with fp:
            return ','.join([self.parse_query(line) for line in fp])

    def run(self, fp):
        if self.dest == 'schema':
            return self.schema(fp)
        return self.query(fp)


if __name__ == '__main__':
    dest = sys.argv[1]
    fp = sys.stdin
    parser = SchemaParser(dest)
    print(parser.run(fp))
