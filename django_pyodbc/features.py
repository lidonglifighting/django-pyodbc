from django.db.backends.base.features import BaseDatabaseFeatures

class DatabaseFeatures(BaseDatabaseFeatures):
    can_use_chunked_reads = False
    supports_microsecond_precision = False
    supports_regex_backreferencing = False
    supports_subqueries_in_group_by = False
    supports_transactions = True
    #uses_savepoints = True
    allow_sliced_subqueries = False
    supports_paramstyle_pyformat = False

    has_bulk_insert = False
    # DateTimeField doesn't support timezones, only DateTimeOffsetField
    supports_timezones = False
    supports_sequence_reset = False
    supports_tablespaces = True
    ignores_nulls_in_unique_constraints = False
    can_introspect_autofield = True


    def _supports_transactions(self):
        # keep it compatible with Django 1.3 and 1.4
        return self.supports_transactions
