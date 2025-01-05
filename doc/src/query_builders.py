# /home/administrator/cobol-analyzer/src/db/query_builders.py

from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

@dataclass
class QueryCondition:
    """クエリ条件"""
    field: str
    operator: str
    value: Any

class QueryBuilder:
    """SQLクエリビルダー"""
    def __init__(self):
        self.select_fields: List[str] = []
        self.from_table: str = ""
        self.where_conditions: List[QueryCondition] = []
        self.order_by: List[str] = []
        self.limit: Optional[int] = None
        self.offset: Optional[int] = None

    def select(self, *fields: str) -> 'QueryBuilder':
        """SELECT句の設定"""
        self.select_fields.extend(fields)
        return self

    def from_table(self, table: str) -> 'QueryBuilder':
        """FROM句の設定"""
        self.from_table = table
        return self

    def where(self, field: str, operator: str, value: Any) -> 'QueryBuilder':
        """WHERE条件の追加"""
        self.where_conditions.append(
            QueryCondition(field, operator, value)
        )
        return self

    def order_by(self, *fields: str) -> 'QueryBuilder':
        """ORDER BY句の設定"""
        self.order_by.extend(fields)
        return self

    def set_limit(self, limit: int) -> 'QueryBuilder':
        """LIMIT句の設定"""
        self.limit = limit
        return self

    def set_offset(self, offset: int) -> 'QueryBuilder':
        """OFFSET句の設定"""
        self.offset = offset
        return self

    def build(self) -> tuple[str, List[Any]]:
        """クエリの構築"""
        query_parts = []
        params = []

        # SELECT句
        select_clause = "SELECT "
        select_clause += ", ".join(self.select_fields) if self.select_fields else "*"
        query_parts.append(select_clause)

        # FROM句
        query_parts.append(f"FROM {self.from_table}")

        # WHERE句
        if self.where_conditions:
            conditions = []
            for i, condition in enumerate(self.where_conditions, start=1):
                conditions.append(f"{condition.field} {condition.operator} ${i}")
                params.append(condition.value)
            query_parts.append("WHERE " + " AND ".join(conditions))

        # ORDER BY句
        if self.order_by:
            query_parts.append("ORDER BY " + ", ".join(self.order_by))

        # LIMIT句
        if self.limit is not None:
            query_parts.append(f"LIMIT {self.limit}")

        # OFFSET句
        if self.offset is not None:
            query_parts.append(f"OFFSET {self.offset}")

        return " ".join(query_parts), params

class InsertQueryBuilder:
    """INSERT文のクエリビルダー"""
    def __init__(self, table: str):
        self.table = table
        self.fields: List[str] = []
        self.values: List[Any] = []

    def add_field(self, field: str, value: Any) -> 'InsertQueryBuilder':
        """フィールドと値の追加"""
        self.fields.append(field)
        self.values.append(value)
        return self

    def build(self) -> tuple[str, List[Any]]:
        """INSERT文の構築"""
        placeholders = [f"${i+1}" for i in range(len(self.fields))]
        query = f"""
            INSERT INTO {self.table} (
                {', '.join(self.fields)}
            ) VALUES (
                {', '.join(placeholders)}
            )
        """
        return query, self.values

class UpdateQueryBuilder:
    """UPDATE文のクエリビルダー"""
    def __init__(self, table: str):
        self.table = table
        self.fields: List[str] = []
        self.values: List[Any] = []
        self.where_conditions: List[QueryCondition] = []

    def set_field(self, field: str, value: Any) -> 'UpdateQueryBuilder':
        """更新フィールドの設定"""
        self.fields.append(field)
        self.values.append(value)
        return self

    def where(self, field: str, operator: str, value: Any) -> 'UpdateQueryBuilder':
        """WHERE条件の追加"""
        self.where_conditions.append(
            QueryCondition(field, operator, value)
        )
        return self

    def build(self) -> tuple[str, List[Any]]:
        """UPDATE文の構築"""
        set_expressions = [
            f"{field} = ${i+1}"
            for i, field in enumerate(self.fields)
        ]
        
        query_parts = [
            f"UPDATE {self.table}",
            "SET " + ", ".join(set_expressions)
        ]

        params = self.values.copy()
        
        if self.where_conditions:
            conditions = []
            for i, condition in enumerate(self.where_conditions):
                param_index = len(params) + i + 1
                conditions.append(
                    f"{condition.field} {condition.operator} ${param_index}"
                )
                params.append(condition.value)
            query_parts.append("WHERE " + " AND ".join(conditions))

        return " ".join(query_parts), params