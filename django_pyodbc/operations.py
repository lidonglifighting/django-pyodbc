# Copyright 2013-2017 Lionheart Software LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Copyright (c) 2008, django-pyodbc developers (see README.rst).
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#     1. Redistributions of source code must retain the above copyright notice,
#        this list of conditions and the following disclaimer.
#
#     2. Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#
#     3. Neither the name of django-sql-server nor the names of its contributors
#        may be used to endorse or promote products derived from this software
#        without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import datetime
import decimal
import time
import uuid

try:
    import pytz
except:
    pytz = None

from django.conf import settings
try:
    from django.db.backends.base.operations import BaseDatabaseOperations
except ImportError:
    # import location prior to Django 1.8
    from django.db.backends import BaseDatabaseOperations
from django.utils.dateparse import parse_date, parse_time, parse_datetime


from django_pyodbc.compat import smart_text, string_types, timezone
from django.utils import six

class DatabaseOperations(BaseDatabaseOperations):
    compiler_module = "django_pyodbc.compiler"
    def __init__(self, connection):
        super(DatabaseOperations, self).__init__(connection) 
        self.connection = connection
        self._left_sql_quote = None
        self._right_sql_quote = None

    @property
    def left_sql_quote(self):
        if self._left_sql_quote is None:
            options = self.connection.settings_dict.get('OPTIONS', {})
            q = options.get('left_sql_quote', None)
            if q is not None:
                self._left_sql_quote = q
            else:
                self._left_sql_quote = '"'
        return self._left_sql_quote

    @property
    def right_sql_quote(self):
        if self._right_sql_quote is None:
            options = self.connection.settings_dict.get('OPTIONS', {})
            q = options.get('right_sql_quote', None)
            if q is not None:
                self._right_sql_quote = q
            else:           
                self._right_sql_quote = '"'
        return self._right_sql_quote

    def date_extract_sql(self, lookup_type, field_name):
        """
        Given a lookup_type of 'year', 'month', 'day' or 'week_day', returns
        the SQL that extracts a value from the given date field field_name.
        """
        if lookup_type == 'week_day':
            # DAYOFWEEK() returns an integer, 1-7, Sunday=1.
            # Note: WEEKDAY() returns 0-6, Monday=0.
            return "DAYOFWEEK(%s)" % field_name
        elif lookup_type == 'week':
            return "WEEK(%s)" % field_name
        elif lookup_type == 'quarter':
            return "QUARTER(%s)" % field_name
        elif lookup_type == 'month':
            return "MONTH(%s)" % field_name
        elif lookup_type == 'day':
            return "DAYOFMONTH(%s)" % field_name
        elif lookup_type == 'hour':
            return "HOUR(%s)" % field_name
        elif lookup_type == 'minute':
            return "MINUTE(%s)" % field_name
        else:
            return "SECOND(%s)" % field_name
      
    def date_trunc_sql(self, lookup_type, field_name):
        if lookup_type =='year':
            return "TO_DATE(STRDATE(%s,'start of year'), 'yyyy-mm-dd')" % field_name
        if lookup_type == 'month':
            return "TO_DATE(STRDATE(%s, 'start of month'), 'yyyy-mm-dd')" % field_name
        elif lookup_type == 'quarter':
            return "MDY(YEAR(%s), (QUARTER(%s)-1)*3+1, 1)" % (field_name , field_name)
        elif lookup_type == 'week':
            return "TO_DATE(STRDATE(%s, 'start of week'), 'yyyy-mm-dd')" % field_name
        else:
            return field_name
        #return "DATEADD(%s, DATEDIFF(%s, 0, %s), 0)" % (lookup_type, lookup_type, field_name)

    def _convert_field_to_tz(self, field_name, tzname):
        if settings.USE_TZ and not tzname == 'UTC':
            offset = self._get_utcoffset(tzname)
            field_name = 'TIMESTAMPADD(%s, %d, %s)' % ('s', offset, field_name)
        return field_name

    def _get_utcoffset(self, tzname):
        """
        Returns UTC offset for given time zone in seconds
        """
        # SQL Server has no built-in support for tz database
        # see http://blogs.msdn.com/b/sqlprogrammability/archive/2008/03/18/using-time-zone-data-in-sql-server-2008.aspx
        zone = pytz.timezone(tzname)
        # no way to take DST into account at this point
        now = datetime.datetime.now()
        delta = zone.localize(now, is_dst=False).utcoffset()
        return delta.days * 86400 + delta.seconds

    def datetime_extract_sql(self, lookup_type, field_name, tzname):
        field_name = self._convert_field_to_tz(field_name, tzname)
        return self.date_extract_sql(lookup_type, field_name)
    
    def datetime_cast_date_sql(self, field_name, tzname):
        field_name = self._convert_field_to_tz(field_name, tzname)
        return 'DATEPART(%s)' % field_name
    
    def datetime_cast_time_sql(self, field_name, tzname):
        field_name = self._convert_field_to_tz(field_name, tzname)
        return "CAST(%s AS TIME)" % field_name
    
    def datetime_trunc_sql(self, lookup_type, field_name, tzname):
        field_name = self._convert_field_to_tz(field_name, tzname)
        fields = ['year', 'month', 'day', 'hour', 'minute', 'week']
        if lookup_type == 'quarter':
            return (
                "CAST(MDY((QUARTER({field_name})-1)*3+1, 1, YEAR({field_name})) AS TIMESTAMP)"
            ).format(field_name=field_name)
        if lookup_type == 'second':
            return field_name
        try:
            i = fields.index(lookup_type)
        except ValueError:
            sql = field_name
        else:
            sql = "CAST(STRDATETIME(%s, 'start of %s') AS TIMESTAMP)" % (field_name, fields[i])
        return sql
    
    def time_trunc_sql(self, lookup_type, field_name):
        fields = ['hour', 'minute']
        if lookup_type in fields:
            format_str = fields[lookup_type]
            return "CAST(STRTIME(%s, 'start of %s') AS TIME)" % (field_name, format_str)
        else:
            return "CAST(STRTIME(%s) AS TIME)" % (field_name)

    def field_cast_sql(self, db_type, internal_type=None):
        """
        Given a column type (e.g. 'BLOB', 'VARCHAR'), returns the SQL necessary
        to cast it before using it in a WHERE statement. Note that the
        resulting string should contain a '%s' placeholder for the column being
        searched against.

        TODO: verify that db_type and internal_type do not affect T-SQL CAST statement
        """
        if db_type and db_type.lower() == 'blob':
            return 'CAST(%s as nvarchar)'
        return '%s'

    def fulltext_search_sql(self, field_name):
        """
        Returns the SQL WHERE clause to use in order to perform a full-text
        search of the given field_name. Note that the resulting string should
        contain a '%s' placeholder for the value being searched against.
        """
        return 'CONTAINS(%s, %%s)' % field_name

    def last_insert_id(self, cursor, table_name, pk_name):
#         table_name = self.quote_name(table_name)
#         cursor.execute("SELECT CAST(IDENT_CURRENT(%s) as bigint)", [table_name])
#         return cursor.fetchone()[0]
        table_name = self.quote_name(table_name)
        cursor.execute(" select LAST_SERIAL from SYSCONINFO")
#         cursor.execute("SELECT cast(count(*) as bigint) from %s" % table_name)
        return cursor.fetchone()[0]
     
    def fetch_returned_insert_id(self, cursor):
        """
        Given a cursor object that has just performed an INSERT/OUTPUT statement
        into a table that has an auto-incrementing ID, returns the newly created
        ID.
        """
        return cursor.fetchone()[0]

    def lookup_cast(self, lookup_type, internal_type=None):
        if lookup_type in ('iexact', 'icontains', 'istartswith', 'iendswith'):
            return "UPPER(%s)"
        return "%s"

    def max_name_length(self):
        return 128

    def quote_name(self, name):
        """
        Returns a quoted version of the given table, index or column name. Does
        not quote the given name if it's already been quoted.
        """
        if name.startswith(self.left_sql_quote) and name.endswith(self.right_sql_quote):
            return name # Quoting once is enough.
        return '%s%s%s' % (self.left_sql_quote, name, self.right_sql_quote)

    def random_function_sql(self):
        """
        Returns a SQL expression that returns a random value.
        """
        return "RAND()"

    def last_executed_query(self, cursor, sql, params):
        """
        Returns a string of the query last executed by the given cursor, with
        placeholders replaced with actual values.

        `sql` is the raw query containing placeholders, and `params` is the
        sequence of parameters. These are used by default, but this method
        exists for database backends to provide a better implementation
        according to their own quoting schemes.
        """
        return super(DatabaseOperations, self).last_executed_query(cursor, cursor.last_sql, cursor.last_params)

    def bulk_insert_sql(self, fields, placeholder_rows):
        placeholder_rows_sql = (", ".join(row) for row in placeholder_rows)
        values_sql = ", ".join("(%s)" % sql for sql in placeholder_rows_sql)
        return "VALUES " + values_sql

    def savepoint_commit_sql(self, sid):
       """
       Returns the SQL for committing the given savepoint.
       """
       return "REMOVE SAVEPOINT %s" % self.quote_name(sid)

    def sql_flush(self, style, tables, sequences, allow_cascade=False):
        """
        Returns a list of SQL statements required to remove all data from
        the given database tables (without actually removing the tables
        themselves).

        The `style` argument is a Style object as returned by either
        color_style() or no_style() in django.core.management.color.
        """
        if tables:
            sql = ['CALL SETSYSTEMOPTION(\'FKCHK\', \'0\');']
            for table in tables:
                sql.append('%s %s;' % (
                    style.SQL_KEYWORD('DELETE FROM '),
                    style.SQL_FIELD(self.quote_name(table)),
                ))
            sql.append('CALL SETSYSTEMOPTION(\'FKCHK\', \'1\');')
            sql.extend(self.sequence_reset_by_name_sql(style, sequences))
            return sql
        else:
            return []

    #def sequence_reset_sql(self, style, model_list):
    #    """
    #    Returns a list of the SQL statements required to reset sequences for
    #    the given models.
    #
    #    The `style` argument is a Style object as returned by either
    #    color_style() or no_style() in django.core.management.color.
    #    """
    #    from django.db import models
    #    output = []
    #    for model in model_list:
    #        for f in model._meta.local_fields:
    #            if isinstance(f, models.AutoField):
    #                output.append(...)
    #                break # Only one AutoField is allowed per model, so don't bother continuing.
    #        for f in model._meta.many_to_many:
    #            output.append(...)
    #    return output

    def start_transaction_sql(self):
        """
        Returns the SQL statement required to start a transaction.
        """
        return "BEGIN TRANSACTION"

    def sql_for_tablespace(self, tablespace, inline=False):
        """
        Returns the SQL that will be appended to tables or rows to define
        a tablespace. Returns '' if the backend doesn't use tablespaces.
        """
        return "ON %s" % self.quote_name(tablespace)

    def prep_for_like_query(self, x):
        """Prepares a value for use in a LIKE query."""
        # http://msdn2.microsoft.com/en-us/library/ms179859.aspx
        return smart_text(x).replace('%', '\%').replace('_', '\_')

    def prep_for_iexact_query(self, x):
        """
        Same as prep_for_like_query(), but called for "iexact" matches, which
        need not necessarily be implemented using "LIKE" in the backend.
        """
        return x
    
    def adapt_datetimefield_value(self, value):	
        """
        Transform a datetime value to an object compatible with what is expected
        by the backend driver for datetime columns.
        """
        if value is None:
            return None
        if self.connection._DJANGO_VERSION >= 14 and settings.USE_TZ:
            if timezone.is_aware(value):
                # pyodbc donesn't support datetimeoffset
                value = value.astimezone(timezone.utc)
        if not self.connection.features.supports_microsecond_precision:
            value = value.replace(microsecond=0)
        return value

    def adapt_timefield_value(self, value):
        """
        Transform a time value to an object compatible with what is expected
        by the backend driver for time columns.
        """
        if value is None:
            return None
        # SQL Server doesn't support microseconds
        if isinstance(value, string_types):
            return datetime.datetime(*(time.strptime(value, '%H:%M:%S')[:6]))
        return datetime.time(value.hour, value.minute, value.second)

    def year_lookup_bounds(self, value):
        """
        Returns a two-elements list with the lower and upper bound to be used
        with a BETWEEN operator to query a field value using a year lookup

        `value` is an int, containing the looked-up year.
        """
        first = '%s-01-01 00:00:00'
        # SQL Server doesn't support microseconds
        last = '%s-12-31 23:59:59'
        return [first % value, last % value]

    def adapt_decimalfield_value(self, value, max_digits, decimal_places):
        """
        Transform a decimal.Decimal value to an object compatible with what is
        expected by the backend driver for decimal (numeric) columns.
        """
        if value is None:
            return None
        if isinstance(value, decimal.Decimal):
            context = decimal.getcontext().copy()
            context.prec = max_digits
            #context.rounding = ROUND_FLOOR
            return "%.*f" % (decimal_places + 1, value.quantize(decimal.Decimal(".1") ** decimal_places, context=context))
        else:
            return "%.*f" % (decimal_places + 1, value)

    def convert_values(self, value, field):
        """
        Coerce the value returned by the database backend into a consistent
        type that is compatible with the field type.

        In our case, cater for the fact that SQL Server < 2008 has no
        separate Date and Time data types.
        TODO: See how we'll handle this for SQL Server >= 2008
        """
        if value is None:
            return None
        if field and field.get_internal_type() == 'DateTimeField':
            if isinstance(value, string_types) and value:
                value = parse_datetime(value)
            return value
        elif field and field.get_internal_type() == 'DateField':
            if isinstance(value, datetime.datetime):
                value = value.date() # extract date
            elif isinstance(value, string_types):
                value = parse_date(value)
        elif field and field.get_internal_type() == 'TimeField':
            if (isinstance(value, datetime.datetime) and value.year == 1900 and value.month == value.day == 1):
                value = value.time() # extract time
            elif isinstance(value, string_types):
                # If the value is a string, parse it using parse_time.
                value = parse_time(value)
        # Some cases (for example when select_related() is used) aren't
        # caught by the DateField case above and date fields arrive from
        # the DB as datetime instances.
        # Implement a workaround stealing the idea from the Oracle
        # backend. It's not perfect so the same warning applies (i.e. if a
        # query results in valid date+time values with the time part set
        # to midnight, this workaround can surprise us by converting them
        # to the datetime.date Python type).
        elif isinstance(value, datetime.datetime) and value.hour == value.minute == value.second == value.microsecond == 0:
            value = value.date()
        # Force floats to the correct type
        elif value is not None and field and field.get_internal_type() == 'FloatField':
            value = float(value)
        return value
    
    def get_db_converters(self, expression):
        converters = super().get_db_converters(expression)
        internal_type = expression.output_field.get_internal_type()       
        if internal_type == 'UUIDField':
            converters.append(self.convert_uuidfield_value)
        return converters
    
    def convert_uuidfield_value(self, value, expression, connection):
        if value is not None:
            value = uuid.UUID(value)
        return value
    
    def no_limit_value(self):
        return None