"""Public, cross-artist publication search. No private project data is queried."""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
import re

PAGE_SIZE = 48
MAX_PAGE = 100
SORTS = {
    'recent': 'p.created_at DESC, p.token DESC',
    'oldest': 'p.created_at ASC, p.token ASC',
    'az': 'p.title COLLATE NOCASE ASC, p.created_at DESC, p.token DESC',
    'za': 'p.title COLLATE NOCASE DESC, p.created_at DESC, p.token DESC',
    'artist': 'u.username COLLATE NOCASE ASC, p.created_at DESC, p.token DESC',
}
PERIODS = ('all', 'today', 'week', 'month')
DATE_RE = re.compile(r'\d{4}-\d{2}-\d{2}\Z')

@dataclass(frozen=True)
class Filters:
    q: str = ''
    sort: str = 'recent'
    period: str = 'all'
    date_from: str = ''
    date_to: str = ''
    page: int = 1


def normalized(params) -> Filters:
    q = str(params.get('q', ''))[:100].strip()
    sort = str(params.get('sort', 'recent'))
    period = str(params.get('period', 'all'))
    def date(value):
        value = str(value or '')
        if not DATE_RE.fullmatch(value): return ''
        try: datetime.strptime(value, '%Y-%m-%d')
        except ValueError: return ''
        return value
    try: page = int(params.get('page', '1'))
    except (ValueError, TypeError): page = 1
    return Filters(q=q,sort=sort if sort in SORTS else 'recent',
                   period=period if period in PERIODS else 'all',
                   date_from=date(params.get('from')),
                   date_to=date(params.get('to')),
                   page=max(1, min(MAX_PAGE,page)))


def search(connection, filters: Filters, now=None, *, owner_id=None, include_hidden=False):
    """Return public records, total matches, and 1-based page, newest by default."""
    today = (now or datetime.now(timezone.utc)).date()
    clauses = []
    values = []
    if not include_hidden: clauses.append('p.is_visible=1')
    if owner_id is not None:
        clauses.append('p.owner_id=?')
        values.append(owner_id)
    if filters.q:
        # instr treats %, _, and backslash as literal search characters, not wildcards.
        clauses.append('(instr(lower(p.title),lower(?)) > 0 OR instr(lower(u.username),lower(?)) > 0)')
        values += [filters.q,filters.q]
    start = {'today':0, 'week':6, 'month':29}.get(filters.period)
    if start is not None:
        clauses.append('p.created_at >= ?')
        values.append((today-timedelta(days=start)).isoformat())
    if filters.date_from:
        clauses.append('substr(p.created_at,1,10) >= ?')
        values.append(filters.date_from)
    if filters.date_to:
        clauses.append('substr(p.created_at,1,10) <= ?')
        values.append(filters.date_to)
    condition = (' WHERE '+' AND '.join(clauses)) if clauses else ''
    tables = ' FROM publications p JOIN users u ON u.id=p.owner_id'
    total = connection.execute('SELECT COUNT(*)'+tables+condition,values).fetchone()[0]
    page = min(filters.page,max(1,(total+PAGE_SIZE-1)//PAGE_SIZE))
    rows=connection.execute('SELECT p.token,p.title,p.file_name,p.created_at,p.is_visible,u.username'+tables+condition+
        ' ORDER BY '+SORTS[filters.sort]+' LIMIT ? OFFSET ?',
        [*values,PAGE_SIZE,(page-1)*PAGE_SIZE]).fetchall()
    return rows,total,page
