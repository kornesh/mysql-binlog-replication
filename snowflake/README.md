# Streaming mysql binlog replication to Snowflake
[![](https://images.microbadger.com/badges/image/servicerocket/mysql2snowflake.svg)](https://hub.docker.com/r/servicerocket/mysql2snowflake/)

In Snowflakes web interface run this query to create a database and table
```sql
CREATE OR REPLACE DATABASE testdb;
USE DATABASE testdb;
CREATE OR REPLACE TABLE testtbl(id integer, name string);
```

You can use the following python script to generate Snowflake compatible schema
```bash
 docker-compose exec python python mysql2snowsql.py
```

Clone this repo and update your Snowflake credentials in `example.env`, then
```bash
cd snowflake/
mv example.env .env
docker-compose up --build
```

> Note: If you get `Can't connect to MySQL server on 'mysql' ([Errno 111] Connection refused)` error on the first run, try running it again.

In another terminal run
```bash
docker-compose exec mysql mysql -u root -pexample -e "DROP DATABASE IF EXISTS testdb; CREATE DATABASE testdb; USE testdb; CREATE TABLE testtbl (id int, name varchar(255)); INSERT INTO testtbl VALUES (1, 'hello'), (2, 'hola'), (3, 'zdravstvuy'), (1, 'bonjour'); UPDATE testtbl SET name = 'yolo' WHERE id = 1; UPDATE testtbl SET name = 'world' WHERE id = 3; DELETE FROM testtbl WHERE id = 1; SELECT * FROM testtbl;"
```

Which will output the following to the terminal
```
+------+-------+
| id   | name  |
+------+-------+
|    2 | hola  |
|    3 | world |
+------+-------+
```

`docker-compose` daemon should output something like this
```sql
python_1  | INSERT INTO testtbl(name, id) VALUES ('hello', 1);
python_1  | INSERT INTO testtbl(name, id) VALUES ('hola', 2);
python_1  | INSERT INTO testtbl(name, id) VALUES ('zdravstvuy', 3);
python_1  | INSERT INTO testtbl(name, id) VALUES ('bonjour', 1);
python_1  | UPDATE testtbl SET name='yolo', id=1 WHERE name='hello' AND id=1;
python_1  | UPDATE testtbl SET name='yolo', id=1 WHERE name='bonjour' AND id=1;
python_1  | UPDATE testtbl SET name='world', id=3 WHERE name='zdravstvuy' AND id=3;
python_1  | DELETE FROM testtbl WHERE name='yolo' AND id=1;
python_1  | DELETE FROM testtbl WHERE name='yolo' AND id=1;
```
Executing these queries one by one is really slow. Ideally, we should batch them together.
![Snowflake History showing slow queries](https://i.imgur.com/iVXQ3Nx.png)

# References
- https://www.alooma.com/blog/mysql-to-amazon-redshift-replication
- https://aws.amazon.com/blogs/database/streaming-changes-in-a-database-with-amazon-kinesis/
- https://github.com/danfengcao/binlog2sql
- https://www.thegeekstuff.com/2017/08/mysqlbinlog-examples/



# Dumping MySQL database as CSV
[Dumping tab files](https://dev.mysql.com/doc/refman/8.0/en/mysqldump-delimited-text.html) to arbitrary directory can result in `The MySQL server is running with the --secure-file-priv option so it cannot execute this statement` error. Instead use the directory that has been configured in mysql. [source](https://stackoverflow.com/questions/32737478/how-should-i-tackle-secure-file-priv-in-mysql)
```bash
docker-compose exec mysql mysql -u root -pexample -e 'SHOW VARIABLES LIKE "secure_file_priv";'
```
```
+------------------+-----------------------+
| Variable_name    | Value                 |
+------------------+-----------------------+
| secure_file_priv | /var/lib/mysql-files/ |
+------------------+-----------------------+
```

```bash
docker-compose exec mysql bash
mysqldump -u root -pexample -T /var/lib/mysql-files/ --fields-terminated-by ',' --fields-enclosed-by '"' --fields-escaped-by '\' --no-create-info testdb
```

> Note: mysqldump uses \N to represent NULL. Though, a NULL value is typically represented by two successive delimiters, e.g. ,,, to indicate that the field contains no data; [source](https://docs.snowflake.net/manuals/user-guide/data-unload-considerations.html#empty-strings-and-null-values)

## Preprocessing CSV

```bash
cd /var/lib/mysql-files/
# Remove sql files
find . -type f -name "*.sql" -print0 | xargs -0 rm

# Fix boolean types. HACKY! I don't know how else to do this
find . -type f -name "*.txt" -print0 | xargs -0 sed -i 's/\"\x01\"/\"1\"/g'
find . -type f -name "*.txt" -print0 | xargs -0 sed -i 's/\"\x00\"/\"0\"/g'

# Fix invalid dates to epoach time
find . -type f -name "*.txt" -print0 | xargs -0 sed -i 's/\"0000-00-00 00:00:00\"/\"1970-01-01 00:00:00\"/g'
```

# Generating Snowflake schema

```bash
docker-compose exec python python mysql2snowsql.py
```

```sql
/* TABLE: testtbl */
CREATE OR REPLACE TABLE testtbl (
  id NUMBER ,
  name STRING,
)
```

# Loading CSV into Snowflake

Copy data to S3
```bash
aws s3 cp --recursive /var/lib/mysql-files/ s3://bucket-name/directory-name
```

Create [AWS IAM User Credentials](https://docs.snowflake.net/manuals/user-guide/data-load-s3-config.html#option-1-configuring-aws-iam-user-credentials) and use it to create a `Stage` (think of it as a data source).


```sql
CREATE STAGE "TESTDB"."PUBLIC".S3STAGE 
URL = 's3://bucket-name' 
CREDENTIALS = (AWS_KEY_ID = 'abcde' AWS_SECRET_KEY = 'xxxxx');
```

For convenience, create a `File Format` to specify how Snowflake should parse the csv.
```sql
CREATE FILE FORMAT "TESTDB"."PUBLIC".MYSQLDUMPCSV 
TYPE = 'CSV' 
COMPRESSION = 'NONE' 
FIELD_DELIMITER = ',' 
RECORD_DELIMITER = '\n' 
SKIP_HEADER = 0 
FIELD_OPTIONALLY_ENCLOSED_BY = '\042' 
TRIM_SPACE = FALSE 
ERROR_ON_COLUMN_COUNT_MISMATCH = TRUE 
ESCAPE = '\134' 
ESCAPE_UNENCLOSED_FIELD = 'NONE' 
DATE_FORMAT = 'AUTO' 
TIMESTAMP_FORMAT = 'AUTO' 
NULL_IF = ('\\N');
```

Finally, load data from S3 into Snowflake

```sql
COPY INTO "TESTDB"."PUBLIC"."TESTTBL" 
FROM '@"TESTDB"."PUBLIC"."S3STAGE"/directory-name/testtbl.txt' 
FILE_FORMAT = '"TESTDB"."PUBLIC"."MYSQLDUMPCSV"' 
ON_ERROR = 'ABORT_STATEMENT' 
PURGE = FALSE;
```

# Reference
- https://docs.snowflake.net/manuals/user-guide/data-load-s3.html
- https://docs.snowflake.net/manuals/user-guide/data-load-s3-create-stage.html
- https://docs.snowflake.net/manuals/user-guide/data-load-s3-copy.html