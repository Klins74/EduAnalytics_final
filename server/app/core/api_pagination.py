"""
Unified API pagination, filtering, and versioning system.

Provides consistent pagination, filtering, sorting, and versioning
across all API endpoints.
"""

import logging
import math
from typing import Dict, Any, List, Optional, Union, Type, Generic, TypeVar
from datetime import datetime, date
from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel, Field, validator
from sqlalchemy import select, func, desc, asc, text, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)

T = TypeVar('T')


class SortDirection(str, Enum):
    """Sort direction enumeration."""
    ASC = "asc"
    DESC = "desc"


class FilterOperator(str, Enum):
    """Filter operator enumeration."""
    EQ = "eq"          # equals
    NE = "ne"          # not equals
    GT = "gt"          # greater than
    GTE = "gte"        # greater than or equal
    LT = "lt"          # less than
    LTE = "lte"        # less than or equal
    LIKE = "like"      # contains (case insensitive)
    ILIKE = "ilike"    # contains (case sensitive)
    IN = "in"          # in list
    NOT_IN = "not_in"  # not in list
    IS_NULL = "is_null"    # is null
    IS_NOT_NULL = "is_not_null"  # is not null
    BETWEEN = "between"    # between two values


@dataclass
class FilterSpec:
    """Filter specification."""
    field: str
    operator: FilterOperator
    value: Union[str, int, float, bool, List[Any], None]
    table_alias: Optional[str] = None


@dataclass
class SortSpec:
    """Sort specification."""
    field: str
    direction: SortDirection
    table_alias: Optional[str] = None


class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    @property
    def offset(self) -> int:
        """Calculate offset for SQL query."""
        return (self.page - 1) * self.per_page


class FilterParams(BaseModel):
    """Base filter parameters."""
    search: Optional[str] = Field(None, description="Global search term")
    created_after: Optional[datetime] = Field(None, description="Filter by creation date after")
    created_before: Optional[datetime] = Field(None, description="Filter by creation date before")
    updated_after: Optional[datetime] = Field(None, description="Filter by update date after")
    updated_before: Optional[datetime] = Field(None, description="Filter by update date before")
    
    def to_filter_specs(self) -> List[FilterSpec]:
        """Convert to filter specifications."""
        specs = []
        
        if self.created_after:
            specs.append(FilterSpec("created_at", FilterOperator.GTE, self.created_after))
        
        if self.created_before:
            specs.append(FilterSpec("created_at", FilterOperator.LTE, self.created_before))
        
        if self.updated_after:
            specs.append(FilterSpec("updated_at", FilterOperator.GTE, self.updated_after))
        
        if self.updated_before:
            specs.append(FilterSpec("updated_at", FilterOperator.LTE, self.updated_before))
        
        return specs


class SortParams(BaseModel):
    """Sort parameters."""
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_dir: SortDirection = Field(SortDirection.ASC, description="Sort direction")
    
    def to_sort_spec(self) -> Optional[SortSpec]:
        """Convert to sort specification."""
        if self.sort_by:
            return SortSpec(self.sort_by, self.sort_dir)
        return None


class APIParams(BaseModel):
    """Combined API parameters."""
    # Pagination
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    # Sorting
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_dir: SortDirection = Field(SortDirection.ASC, description="Sort direction")
    
    # Filtering
    search: Optional[str] = Field(None, description="Global search term")
    created_after: Optional[datetime] = Field(None, description="Filter by creation date after")
    created_before: Optional[datetime] = Field(None, description="Filter by creation date before")
    updated_after: Optional[datetime] = Field(None, description="Filter by update date after")
    updated_before: Optional[datetime] = Field(None, description="Filter by update date before")
    
    # Include/exclude fields
    include_fields: Optional[str] = Field(None, description="Comma-separated fields to include")
    exclude_fields: Optional[str] = Field(None, description="Comma-separated fields to exclude")
    
    @property
    def pagination(self) -> PaginationParams:
        """Get pagination parameters."""
        return PaginationParams(page=self.page, per_page=self.per_page)
    
    @property
    def sorting(self) -> Optional[SortSpec]:
        """Get sort specification."""
        if self.sort_by:
            return SortSpec(self.sort_by, self.sort_dir)
        return None
    
    @property
    def filters(self) -> List[FilterSpec]:
        """Get filter specifications."""
        specs = []
        
        if self.created_after:
            specs.append(FilterSpec("created_at", FilterOperator.GTE, self.created_after))
        
        if self.created_before:
            specs.append(FilterSpec("created_at", FilterOperator.LTE, self.created_before))
        
        if self.updated_after:
            specs.append(FilterSpec("updated_at", FilterOperator.GTE, self.updated_after))
        
        if self.updated_before:
            specs.append(FilterSpec("updated_at", FilterOperator.LTE, self.updated_before))
        
        return specs
    
    @property
    def field_selection(self) -> Dict[str, List[str]]:
        """Get field selection."""
        result = {"include": [], "exclude": []}
        
        if self.include_fields:
            result["include"] = [f.strip() for f in self.include_fields.split(",")]
        
        if self.exclude_fields:
            result["exclude"] = [f.strip() for f in self.exclude_fields.split(",")]
        
        return result


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response model."""
    items: List[T] = Field(description="List of items")
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    per_page: int = Field(description="Items per page")
    pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page")
    next_page: Optional[int] = Field(None, description="Next page number")
    prev_page: Optional[int] = Field(None, description="Previous page number")
    
    @classmethod
    def create(cls, items: List[T], total: int, pagination: PaginationParams) -> "PaginatedResponse[T]":
        """Create paginated response."""
        pages = math.ceil(total / pagination.per_page) if total > 0 else 1
        has_next = pagination.page < pages
        has_prev = pagination.page > 1
        
        return cls(
            items=items,
            total=total,
            page=pagination.page,
            per_page=pagination.per_page,
            pages=pages,
            has_next=has_next,
            has_prev=has_prev,
            next_page=pagination.page + 1 if has_next else None,
            prev_page=pagination.page - 1 if has_prev else None
        )


class QueryBuilder:
    """SQL query builder with pagination, filtering, and sorting."""
    
    def __init__(self, model_class: Type[DeclarativeBase], session: AsyncSession):
        self.model_class = model_class
        self.session = session
        self.query = select(model_class)
        self.count_query = select(func.count()).select_from(model_class)
    
    def apply_filters(self, filters: List[FilterSpec], search_fields: Optional[List[str]] = None) -> "QueryBuilder":
        """Apply filters to the query."""
        conditions = []
        
        for filter_spec in filters:
            condition = self._build_filter_condition(filter_spec)
            if condition is not None:
                conditions.append(condition)
        
        if conditions:
            filter_condition = and_(*conditions)
            self.query = self.query.where(filter_condition)
            self.count_query = self.count_query.where(filter_condition)
        
        return self
    
    def apply_search(self, search_term: str, search_fields: List[str]) -> "QueryBuilder":
        """Apply global search across specified fields."""
        if not search_term or not search_fields:
            return self
        
        search_conditions = []
        for field in search_fields:
            if hasattr(self.model_class, field):
                column = getattr(self.model_class, field)
                search_conditions.append(column.ilike(f"%{search_term}%"))
        
        if search_conditions:
            search_condition = or_(*search_conditions)
            self.query = self.query.where(search_condition)
            self.count_query = self.count_query.where(search_condition)
        
        return self
    
    def apply_sorting(self, sort_spec: Optional[SortSpec], default_sort: Optional[str] = "id") -> "QueryBuilder":
        """Apply sorting to the query."""
        if sort_spec and hasattr(self.model_class, sort_spec.field):
            column = getattr(self.model_class, sort_spec.field)
            if sort_spec.direction == SortDirection.DESC:
                self.query = self.query.order_by(desc(column))
            else:
                self.query = self.query.order_by(asc(column))
        elif default_sort and hasattr(self.model_class, default_sort):
            # Apply default sorting
            column = getattr(self.model_class, default_sort)
            self.query = self.query.order_by(desc(column))
        
        return self
    
    def apply_pagination(self, pagination: PaginationParams) -> "QueryBuilder":
        """Apply pagination to the query."""
        self.query = self.query.offset(pagination.offset).limit(pagination.per_page)
        return self
    
    async def execute(self) -> tuple[List[Any], int]:
        """Execute the query and return results with total count."""
        # Execute count query
        count_result = await self.session.execute(self.count_query)
        total = count_result.scalar() or 0
        
        # Execute main query
        result = await self.session.execute(self.query)
        items = result.scalars().all()
        
        return list(items), total
    
    def _build_filter_condition(self, filter_spec: FilterSpec):
        """Build filter condition for a single filter specification."""
        if not hasattr(self.model_class, filter_spec.field):
            logger.warning(f"Field {filter_spec.field} not found in {self.model_class.__name__}")
            return None
        
        column = getattr(self.model_class, filter_spec.field)
        
        if filter_spec.operator == FilterOperator.EQ:
            return column == filter_spec.value
        elif filter_spec.operator == FilterOperator.NE:
            return column != filter_spec.value
        elif filter_spec.operator == FilterOperator.GT:
            return column > filter_spec.value
        elif filter_spec.operator == FilterOperator.GTE:
            return column >= filter_spec.value
        elif filter_spec.operator == FilterOperator.LT:
            return column < filter_spec.value
        elif filter_spec.operator == FilterOperator.LTE:
            return column <= filter_spec.value
        elif filter_spec.operator == FilterOperator.LIKE:
            return column.ilike(f"%{filter_spec.value}%")
        elif filter_spec.operator == FilterOperator.ILIKE:
            return column.like(f"%{filter_spec.value}%")
        elif filter_spec.operator == FilterOperator.IN:
            return column.in_(filter_spec.value)
        elif filter_spec.operator == FilterOperator.NOT_IN:
            return ~column.in_(filter_spec.value)
        elif filter_spec.operator == FilterOperator.IS_NULL:
            return column.is_(None)
        elif filter_spec.operator == FilterOperator.IS_NOT_NULL:
            return column.is_not(None)
        elif filter_spec.operator == FilterOperator.BETWEEN:
            if isinstance(filter_spec.value, list) and len(filter_spec.value) == 2:
                return column.between(filter_spec.value[0], filter_spec.value[1])
        
        return None


class APIVersioning:
    """API versioning utilities."""
    
    SUPPORTED_VERSIONS = ["v1"]
    DEFAULT_VERSION = "v1"
    
    @classmethod
    def get_version_from_path(cls, path: str) -> str:
        """Extract API version from request path."""
        parts = path.strip("/").split("/")
        if len(parts) > 1 and parts[0] == "api" and parts[1] in cls.SUPPORTED_VERSIONS:
            return parts[1]
        return cls.DEFAULT_VERSION
    
    @classmethod
    def is_supported_version(cls, version: str) -> bool:
        """Check if API version is supported."""
        return version in cls.SUPPORTED_VERSIONS
    
    @classmethod
    def get_version_info(cls) -> Dict[str, Any]:
        """Get API version information."""
        return {
            "current_version": cls.DEFAULT_VERSION,
            "supported_versions": cls.SUPPORTED_VERSIONS,
            "version_format": "/api/{version}/",
            "deprecation_policy": "Versions are supported for 12 months after replacement"
        }


class FieldSelector:
    """Field selection utilities for API responses."""
    
    @staticmethod
    def apply_field_selection(data: Dict[str, Any], selection: Dict[str, List[str]]) -> Dict[str, Any]:
        """Apply field selection to response data."""
        include_fields = selection.get("include", [])
        exclude_fields = selection.get("exclude", [])
        
        if include_fields:
            # Only include specified fields
            return {k: v for k, v in data.items() if k in include_fields}
        elif exclude_fields:
            # Exclude specified fields
            return {k: v for k, v in data.items() if k not in exclude_fields}
        else:
            # Return all fields
            return data
    
    @staticmethod
    def apply_field_selection_to_list(items: List[Dict[str, Any]], selection: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """Apply field selection to a list of items."""
        if not selection.get("include") and not selection.get("exclude"):
            return items
        
        return [FieldSelector.apply_field_selection(item, selection) for item in items]


class APIResponseBuilder:
    """Builder for consistent API responses."""
    
    @staticmethod
    def success(data: Any = None, message: str = "Success", meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build success response."""
        response = {
            "success": True,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if data is not None:
            response["data"] = data
        
        if meta:
            response["meta"] = meta
        
        return response
    
    @staticmethod
    def error(message: str, code: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build error response."""
        response = {
            "success": False,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if code:
            response["error_code"] = code
        
        if details:
            response["details"] = details
        
        return response
    
    @staticmethod
    def paginated(items: List[Any], total: int, pagination: PaginationParams, 
                 meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build paginated response."""
        paginated_data = PaginatedResponse.create(items, total, pagination)
        
        response = APIResponseBuilder.success(
            data=paginated_data.dict(),
            message=f"Retrieved {len(items)} of {total} items"
        )
        
        if meta:
            response["meta"] = meta
        
        return response


# Utility functions for common API operations
async def paginated_query(
    model_class: Type[DeclarativeBase],
    session: AsyncSession,
    params: APIParams,
    search_fields: Optional[List[str]] = None,
    additional_filters: Optional[List[FilterSpec]] = None,
    default_sort: Optional[str] = "id"
) -> PaginatedResponse:
    """Execute a paginated query with filtering and sorting."""
    
    builder = QueryBuilder(model_class, session)
    
    # Apply filters
    filters = params.filters
    if additional_filters:
        filters.extend(additional_filters)
    
    if filters:
        builder.apply_filters(filters)
    
    # Apply search
    if params.search and search_fields:
        builder.apply_search(params.search, search_fields)
    
    # Apply sorting
    builder.apply_sorting(params.sorting, default_sort)
    
    # Apply pagination
    builder.apply_pagination(params.pagination)
    
    # Execute query
    items, total = await builder.execute()
    
    return PaginatedResponse.create(items, total, params.pagination)
