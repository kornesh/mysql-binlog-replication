#Ported to Python 3 from https://support.snowflake.net/s/question/0D50Z00006uSiEBSA0/homebrew-mysql-to-snowflake-ddl-converter
import re
import os
import pymysql
import snowflake.connector

def apply_regex_sub(regex, expression, sub_string):
	p = re.compile(regex, re.MULTILINE)
	return re.sub(p, sub_string, expression)

def mysql_to_snowflake(mysql_ddl):
	result = apply_regex_sub(r'`', mysql_ddl, "") # Remove `
	result = apply_regex_sub(r'((--(.+)?)|(/\*(.+)))\n?', result, "") # Remove all comments fields
	result = apply_regex_sub(r'(DROP(.)+)\n', result, "") # Remove DROP Table reference
	result = apply_regex_sub(r'\sDEFAULT(.+,)', result, ",") # Remove DEFAULT
	result = apply_regex_sub(r'\s((NOT\sNULL)|NULL)', result, "") # Remove NULL
	result = apply_regex_sub(r"((enum|varchar|nvarchar|char)\(['0-9a-zA-Z,]+\))(.)+", result, "STRING,") # STRING data types
	result = apply_regex_sub(r'(tiny|big)?int\([0-9a-zA-Z,]+\)(\s(unsigned))?', result, "NUMBER") # NUMBER data types
	result = apply_regex_sub(r'datetime', result, "TIMESTAMP_LTZ") # TIMESTAMP_LTZ data types
	result = apply_regex_sub(r'\s\s(((PRIMARY)|(UNIQUE))\s)?KEY(.+)\n', result, "") # Strip KEYS
	result = apply_regex_sub(r'AUTO_INCREMENT',result,"") #Strips AUTO_INCREMENT
	result = apply_regex_sub(r'\s\s(CONSTRAINT\s)(.+)\n', result, "") # Strip CONSTRAINTS
	result = apply_regex_sub(r',?\n\)(.+)', result, "\n);") # Clean closing bracket
	result = apply_regex_sub(r'^(?:[\t ]*(?:\r?\n|\r))+', result, "") # Discard blank lines
	result = apply_regex_sub(r'bit\([0-9a-zA-Z,]+\)', result, "BOOLEAN") # BOOLEAN data types
	
	r = re.compile(r'(\s)(longblob|blob|longtext|text)(\n|\,)', re.MULTILINE)
	result = re.sub(r, r"\1STRING\3", result)

	return result

def main(mysqlConfigs):
	conn = pymysql.connect(**mysqlConfigs)
	cur = conn.cursor()
	cur.execute("SHOW TABLES")
	sf = snowflake.connector.connect(**snowflakeConfig)

	for (table_name,) in cur.fetchall():
	  print("/* TABLE:", table_name, "*/")

	  cur.execute("SHOW CREATE TABLE %s" % table_name) # WARNING: can be dangerous as this wont properly escape table_name

	  sql = cur.fetchone()[1]
	  #print(sql)

	  if sql.find('CREATE ALGORITHM') != -1:
	  	print("/* Skipping", table_name,"*/")
	  	continue
	  
	  snowsql = mysql_to_snowflake(sql).replace("CREATE TABLE", "CREATE OR REPLACE TABLE")
	  print(snowsql)
	  #sf.cursor().execute(snowsql)

if __name__ == "__main__":
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
	main(mysqlConfigs)
