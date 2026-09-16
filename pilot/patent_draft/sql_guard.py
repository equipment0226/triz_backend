"""Capability-limited SQL connections for the additive patent module."""
import re
from sqlalchemy import event
from sqlalchemy.schema import CreateTable, CreateIndex
from .domain import PatentError


def guarded(engine, writable=()):
    names=frozenset(writable)
    scoped=engine.execution_options(patent_sql_scope='WRITE' if names else 'READ_ONLY')

    def check(conn, statement, multiparams, params, execution_options):
        if getattr(statement,'is_select',False):
            return
        table=getattr(statement,'table',None)
        if isinstance(statement,CreateTable):
            table=statement.element
        elif isinstance(statement,CreateIndex):
            table=statement.element.table
        is_write=any(getattr(statement,k,False) for k in ('is_insert','is_update','is_delete'))
        if names and (is_write or isinstance(statement,(CreateTable,CreateIndex))) and getattr(table,'name',None) in names:
            return
        raise PatentError('LEGACY_WRITE_FORBIDDEN','특허 모듈은 원본 SQL이나 임의 SQL을 실행할 수 없습니다.',403)

    event.listen(scoped,'before_execute',check)
    def driver_check(conn,cursor,statement,parameters,context,executemany):
        if context.compiled is not None:
            return
        # Dialect reflection uses driver SQL. Permit only its read operations;
        # arbitrary driver DML/DDL must not bypass the typed-statement guard.
        sql=statement.strip()
        if re.match(r'(?is)^(SELECT\b|SHOW\b|DESCRIBE\b)',sql) and not re.search(r'(?is)\bINTO\b|;\s*\S',sql):
            return
        if re.fullmatch(r'(?is)PRAGMA\s+(?:(?:main|temp)\.)?(?:table_info|table_xinfo|index_list|index_info|index_xinfo|foreign_key_list)\s*\([^;]*\)',sql):
            return
        raise PatentError('LEGACY_WRITE_FORBIDDEN','원본 또는 임의 SQL 실행이 차단됐습니다.',403)
    event.listen(scoped,'before_cursor_execute',driver_check)
    scoped._patent_sql_guard=(check,names,driver_check)
    return scoped


def verified(engine, writable=()):
    guard=getattr(engine,'_patent_sql_guard',None)
    return bool(guard and guard[1]==frozenset(writable) and event.contains(engine,'before_execute',guard[0])
                and event.contains(engine,'before_cursor_execute',guard[2]))
