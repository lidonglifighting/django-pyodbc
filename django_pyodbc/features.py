from django.db.backends.base.features import BaseDatabaseFeatures

class DatabaseFeatures(BaseDatabaseFeatures):
    can_use_chunked_reads = False
    supports_microsecond_precision = False
    supports_regex_backreferencing = False
    supports_subqueries_in_group_by = False
    supports_transactions = True
    allow_sliced_subqueries = False
    supports_paramstyle_pyformat = False

    has_bulk_insert = False
    # DateTimeField doesn't support timezones, only DateTimeOffsetField
    supports_timezones = False
    supports_sequence_reset = False
    supports_tablespaces = True
    ignores_nulls_in_unique_constraints = False
    can_introspect_autofield = True
    has_case_insensitive_like = False
    requires_literal_defaults = True
#    case_whennot_not_supported = True

