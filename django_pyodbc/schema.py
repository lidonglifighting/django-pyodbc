from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.models import NOT_PROVIDED


class DatabaseSchemaEditor(BaseDatabaseSchemaEditor):
    
    sql_retablespace_table = "ALTER TABLE %(table)s MOVE TABLESPACE %(new_tablespace)s"
    sql_alter_column_type = "MODIFY COLUMN %(column)s TYPE TO %(type)s"
    sql_alter_column_null = "MODIFY COLUMN %(column)s NOT NULL TO NULL"
    sql_alter_column_not_null = "MODIFY COLUMN %(column)s NULL TO NOT NULL"
    sql_alter_column_default = "MODIFY COLUMN %(column)s SET DEFAULT %(default)s"
    sql_alter_column_no_default = "MODIFY COLUMN %(column)s DROP DEFAULT"
    sql_rename_column = "ALTER TABLE %(table)s MODIFY %(old_column)s NAME TO %(new_column)s"

    sql_create_check = "ALTER TABLE %(table)s ADD CONSTRAINT %(name)s CHECK (%(check)s)"
    sql_delete_check = "ALTER TABLE %(table)s MODIFY %(column)s DROP CONSTRAINT"

    sql_delete_unique = "ALTER TABLE %(table)s MODIFY %(column)s DROP CONSTRAINT"

   
    sql_create_inline_fk = None
    sql_delete_fk = "ALTER TABLE %(table)s DROP FOREIGN KEY %(name)s"
    sql_delete_pk = "ALTER TABLE %(table)s DROP PRIMARY KEY %(name)s"

    sql_rename_table = "RENAME TO %(new_table)s"
    sql_delete_index = "DROP INDEX %(name)s ON %(table)s"

    def column_sql(self, model, field, include_default=False):
        """
        Takes a field and returns its column definition.
        The field must already have had set_attributes_from_name called.
        """
        # Get the column's type and use that as the basis of the SQL
        db_params = field.db_parameters(connection=self.connection)
        sql = db_params['type']
        params = []
        # Check for fields that aren't actually columns (e.g. M2M)
        if sql is None:
            return None, None
        # Work out nullability
        null = field.null
        # If we were told to include a default value, do so
        include_default = include_default and not self.skip_default(field)
        if include_default:
            default_value = self.effective_default(field)
            if default_value is not None:
                if self.connection.features.requires_literal_defaults:
                    # Some databases can't take defaults as a parameter (oracle)
                    # If this is the case, the individual schema backend should
                    # implement prepare_default
                    sql += " DEFAULT %s" % self.prepare_default(default_value)
                else:
                    sql += " DEFAULT %s"
                    params += [default_value]
        
        if  db_params['type'].lower() not in ("serial", "bigserial", "jsoncols"):          
            if (field.empty_strings_allowed and not field.primary_key and
                self.connection.features.interprets_empty_strings_as_nulls):
                null = True
            if null and not self.connection.features.implied_column_null:
                sql += " NULL"
            elif not null:
                sql += " NOT NULL"
        # Primary key/unique outputs
        if field.primary_key:
            sql += " PRIMARY KEY"
        elif field.unique:
            sql += " UNIQUE"
        # Optionally add the tablespace if it's an implicitly indexed column
        tablespace = field.db_tablespace or model._meta.db_tablespace
        if tablespace and self.connection.features.supports_tablespaces and field.unique:
            sql += " %s" % self.connection.ops.tablespace_sql(tablespace, inline=True)
        # Return the sql
        return sql, params
    
    def add_field(self, model, field):
        super(DatabaseSchemaEditor, self).add_field(model, field)

        # Simulate the effect of a one-off default.
        # field.default may be unhashable, so a set isn't used for "in" check.
        if self.skip_default(field) and field.default not in (None, NOT_PROVIDED):
            effective_default = self.effective_default(field)
            self.execute('UPDATE %(table)s SET %(column)s = %%s' % {
                'table': self.quote_name(model._meta.db_table),
                'column': self.quote_name(field.column),
            }, [effective_default])

    def _delete_composed_index(self, model, fields, *args):
        """
        MySQL can remove an implicit FK index on a field when that field is
        covered by another index like a unique_together. "covered" here means
        that the more complex index starts like the simpler one.
        http://bugs.mysql.com/bug.php?id=37910 / Django ticket #24757
        We check here before removing the [unique|index]_together if we have to
        recreate a FK index.
        """
        first_field = model._meta.get_field(fields[0])
        if first_field.get_internal_type() == 'ForeignKey':
            constraint_names = self._constraint_names(model, [first_field.column], index=True)
            if not constraint_names:
                self.execute(self._create_index_sql(model, [first_field], suffix=""))
        return super(DatabaseSchemaEditor, self)._delete_composed_index(model, fields, *args)

    def _set_field_new_type_null_status(self, field, new_type):
        """
        Keep the null property of the old field. If it has changed, it will be
        handled separately.
        """
        if field.null:
            new_type += " NULL"
        else:
            new_type += " NOT NULL"
        return new_type

    def _alter_column_type_sql(self, table, old_field, new_field, new_type):
#        new_type = self._set_field_new_type_null_status(old_field, new_type)
        return super(DatabaseSchemaEditor, self)._alter_column_type_sql(table, old_field, new_field, new_type)

    def _rename_field_sql(self, table, old_field, new_field, new_type):
        new_type = self._set_field_new_type_null_status(old_field, new_type)
        return super(DatabaseSchemaEditor, self)._rename_field_sql(table, old_field, new_field, new_type)
