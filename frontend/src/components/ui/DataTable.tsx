import React, { useState, useMemo } from 'react';
import {
  ChevronDown,
  ChevronUp,
  ChevronsUpDown,
  Search,
  Download,
  SlidersHorizontal,
  ChevronLeft,
  ChevronRight,
  Eye,
  EyeOff,
  X
} from 'lucide-react';

export interface ColumnDef<T> {
  key: string;
  header: string;
  render?: (row: T, index: number) => React.ReactNode;
  sortable?: boolean;
  align?: 'left' | 'center' | 'right';
  className?: string;
  accessor?: (row: T) => any;
}

interface DataTableProps<T> {
  data: T[];
  columns: ColumnDef<T>[];
  keyExtractor: (row: T, index: number) => string | number;
  title?: string;
  subtitle?: string;
  searchPlaceholder?: string;
  defaultSortKey?: string;
  defaultSortDir?: 'asc' | 'desc';
  pageSizeOptions?: number[];
  defaultPageSize?: number;
  onRowClick?: (row: T) => void;
  renderRowDetail?: (row: T) => React.ReactNode;
  exportFileName?: string;
  className?: string;
  emptyMessage?: string;
}

export function DataTable<T extends Record<string, any>>({
  data,
  columns,
  keyExtractor,
  title,
  subtitle,
  searchPlaceholder = 'Search records...',
  defaultSortKey,
  defaultSortDir = 'desc',
  pageSizeOptions = [5, 10, 25, 50],
  defaultPageSize = 10,
  onRowClick,
  renderRowDetail,
  exportFileName = 'novanest_export',
  className = '',
  emptyMessage = 'No records found matching current criteria.',
}: DataTableProps<T>) {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortKey, setSortKey] = useState<string | undefined>(defaultSortKey || (columns[0]?.key ?? ''));
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>(defaultSortDir);
  const [pageSize, setPageSize] = useState<number>(defaultPageSize);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [expandedRows, setExpandedRows] = useState<Record<string, boolean>>({});
  const [visibleColumns, setVisibleColumns] = useState<Record<string, boolean>>(() => {
    const initial: Record<string, boolean> = {};
    columns.forEach((col) => {
      initial[col.key] = true;
    });
    return initial;
  });
  const [showColMenu, setShowColMenu] = useState(false);

  // Filter
  const filteredData = useMemo(() => {
    if (!searchTerm.trim()) return data;
    const term = searchTerm.toLowerCase();
    return data.filter((row) => {
      return columns.some((col) => {
        const val = col.accessor ? col.accessor(row) : row[col.key];
        if (val === null || val === undefined) return false;
        return String(val).toLowerCase().includes(term);
      });
    });
  }, [data, searchTerm, columns]);

  // Sort
  const sortedData = useMemo(() => {
    if (!sortKey) return filteredData;
    const colDef = columns.find((c) => c.key === sortKey);
    return [...filteredData].sort((a, b) => {
      let aVal = colDef?.accessor ? colDef.accessor(a) : a[sortKey];
      let bVal = colDef?.accessor ? colDef.accessor(b) : b[sortKey];

      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;

      // Numeric comparison
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortDir === 'asc' ? aVal - bVal : bVal - aVal;
      }

      // String comparison
      aVal = String(aVal).toLowerCase();
      bVal = String(bVal).toLowerCase();
      if (aVal < bVal) return sortDir === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });
  }, [filteredData, sortKey, sortDir, columns]);

  // Paginate
  const totalPages = Math.max(1, Math.ceil(sortedData.length / pageSize));
  const safeCurrentPage = Math.min(currentPage, totalPages);
  const startIndex = (safeCurrentPage - 1) * pageSize;
  const paginatedData = useMemo(() => {
    return sortedData.slice(startIndex, startIndex + pageSize);
  }, [sortedData, startIndex, pageSize]);

  const handleSort = (key: string, isSortable?: boolean) => {
    if (isSortable === false) return;
    if (sortKey === key) {
      setSortDir((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  const toggleRowDetail = (rowKey: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setExpandedRows((prev) => ({ ...prev, [rowKey]: !prev[rowKey] }));
  };

  const toggleColumn = (key: string) => {
    setVisibleColumns((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  // Export to CSV
  const exportToCSV = () => {
    const exportCols = columns.filter((c) => visibleColumns[c.key] !== false);
    const headers = exportCols.map((c) => `"${c.header.replace(/"/g, '""')}"`).join(',');
    const rows = sortedData.map((row) =>
      exportCols
        .map((c) => {
          const val = c.accessor ? c.accessor(row) : row[c.key];
          if (val === null || val === undefined) return '""';
          return `"${String(val).replace(/"/g, '""')}"`;
        })
        .join(',')
    );
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers, ...rows].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `${exportFileName}_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const displayedColumns = columns.filter((c) => visibleColumns[c.key] !== false);

  return (
    <div
      className={`rounded-2xl bg-white border border-slate-200 overflow-hidden shadow-sm ${className}`}
      role="region"
      aria-label={title || 'Data Table'}
    >
      {/* Table Header & Toolbar */}
      <div className="p-4 sm:p-5 border-b border-slate-100 flex flex-col md:flex-row md:items-center justify-between gap-3.5 bg-white">
        <div>
          {title && (
            <h3 className="text-base font-bold text-slate-800 tracking-tight flex items-center gap-2">
              <span>{title}</span>
              <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-blue-50 text-blue-600 border border-blue-200">
                {sortedData.length} records
              </span>
            </h3>
          )}
          {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
        </div>

        {/* Toolbar: Search, Column Toggle, CSV Export */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Search Box */}
          <div className="relative min-w-[200px] sm:min-w-[240px]">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" aria-hidden="true" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              placeholder={searchPlaceholder}
              className="w-full pl-9 pr-8 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-600"
              aria-label="Filter records"
            />
            {searchTerm && (
              <button
                onClick={() => setSearchTerm('')}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700"
                aria-label="Clear search"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Column Visibility Menu */}
          <div className="relative">
            <button
              onClick={() => setShowColMenu(!showColMenu)}
              className="px-2.5 py-1.5 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-xl text-xs text-slate-700 flex items-center gap-1.5 transition-colors"
              title="Toggle Columns"
              aria-label="Toggle visible columns"
              aria-expanded={showColMenu}
            >
              <SlidersHorizontal className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Columns</span>
            </button>

            {showColMenu && (
              <div
                className="absolute right-0 mt-2 w-48 bg-white border border-slate-200 rounded-xl shadow-xl p-2 z-30 animate-fadeIn"
                role="menu"
              >
                <div className="text-[11px] font-semibold text-slate-500 px-2 py-1 uppercase tracking-wider">
                  Visible Columns
                </div>
                {columns.map((col) => (
                  <button
                    key={col.key}
                    onClick={() => toggleColumn(col.key)}
                    className="w-full flex items-center justify-between px-2 py-1.5 text-xs text-slate-700 hover:bg-slate-50 rounded-lg text-left"
                    role="menuitem"
                  >
                    <span className="truncate">{col.header}</span>
                    {visibleColumns[col.key] !== false ? (
                      <Eye className="w-3.5 h-3.5 text-blue-600" />
                    ) : (
                      <EyeOff className="w-3.5 h-3.5 text-slate-400" />
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Export to CSV */}
          <button
            onClick={exportToCSV}
            className="px-2.5 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-600 border border-blue-200 rounded-xl text-xs flex items-center gap-1.5 transition-colors font-medium"
            title="Export CSV"
            aria-label="Export table data to CSV"
          >
            <Download className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Export</span>
          </button>
        </div>
      </div>

      {/* Table Surface with responsive horizontal scrolling */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs" role="table">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase tracking-wider text-[11px] font-semibold">
              {renderRowDetail && <th className="w-10 px-3 py-3" aria-label="Expand" />}
              {displayedColumns.map((col) => {
                const isSorted = sortKey === col.key;
                const isSortable = col.sortable !== false;
                const alignClass =
                  col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left';

                return (
                  <th
                    key={col.key}
                    onClick={() => handleSort(col.key, col.sortable)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        handleSort(col.key, col.sortable);
                      }
                    }}
                    tabIndex={isSortable ? 0 : undefined}
                    className={`px-4 py-3.5 ${alignClass} ${
                      isSortable ? 'cursor-pointer select-none hover:text-slate-900 transition-colors' : ''
                    } ${col.className || ''}`}
                    role="columnheader"
                    aria-sort={isSorted ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'}
                  >
                    <div className={`inline-flex items-center gap-1.5 ${col.align === 'right' ? 'justify-end' : ''}`}>
                      <span>{col.header}</span>
                      {isSortable && (
                        <span className="text-slate-400">
                          {isSorted ? (
                            sortDir === 'asc' ? (
                              <ChevronUp className="w-3.5 h-3.5 text-blue-600" />
                            ) : (
                              <ChevronDown className="w-3.5 h-3.5 text-blue-600" />
                            )
                          ) : (
                            <ChevronsUpDown className="w-3 h-3 text-slate-400 opacity-60" />
                          )}
                        </span>
                      )}
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-slate-800">
            {paginatedData.length === 0 ? (
              <tr>
                <td
                  colSpan={displayedColumns.length + (renderRowDetail ? 1 : 0)}
                  className="px-4 py-12 text-center text-slate-500"
                >
                  <p className="text-sm font-medium">{emptyMessage}</p>
                  {searchTerm && (
                    <button
                      onClick={() => setSearchTerm('')}
                      className="mt-2 text-xs text-blue-600 hover:underline"
                    >
                      Clear search filter
                    </button>
                  )}
                </td>
              </tr>
            ) : (
              paginatedData.map((row, index) => {
                const rowKey = String(keyExtractor(row, index));
                const isExpanded = !!expandedRows[rowKey];

                return (
                  <React.Fragment key={rowKey}>
                    <tr
                      onClick={() => onRowClick && onRowClick(row)}
                      className={`hover:bg-slate-50/80 transition-colors ${
                        onRowClick ? 'cursor-pointer' : ''
                      } ${isExpanded ? 'bg-blue-50/40' : ''}`}
                    >
                      {renderRowDetail && (
                        <td className="px-3 py-3 text-center">
                          <button
                            onClick={(e) => toggleRowDetail(rowKey, e)}
                            className="p-1 rounded hover:bg-slate-200/60 text-slate-400 hover:text-slate-700 transition-colors"
                            aria-label={isExpanded ? 'Collapse row details' : 'Expand row details'}
                            aria-expanded={isExpanded}
                          >
                            {isExpanded ? (
                              <ChevronUp className="w-3.5 h-3.5" />
                            ) : (
                              <ChevronDown className="w-3.5 h-3.5" />
                            )}
                          </button>
                        </td>
                      )}
                      {displayedColumns.map((col) => {
                        const alignClass =
                          col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left';
                        const cellContent = col.render
                          ? col.render(row, startIndex + index)
                          : col.accessor
                          ? col.accessor(row)
                          : row[col.key];

                        return (
                          <td key={col.key} className={`px-4 py-3 ${alignClass} ${col.className || ''}`}>
                            {cellContent ?? '—'}
                          </td>
                        );
                      })}
                    </tr>
                    {renderRowDetail && isExpanded && (
                      <tr className="bg-slate-50">
                        <td colSpan={displayedColumns.length + 1} className="px-6 py-4 border-t border-slate-100">
                          {renderRowDetail(row)}
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="p-3 sm:p-4 border-t border-slate-100 bg-slate-50 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-500">
        <div className="flex items-center gap-3">
          <span>
            Showing <strong className="text-slate-800">{sortedData.length > 0 ? startIndex + 1 : 0}</strong> to{' '}
            <strong className="text-slate-800">{Math.min(startIndex + pageSize, sortedData.length)}</strong> of{' '}
            <strong className="text-slate-800">{sortedData.length}</strong>
          </span>
          <div className="flex items-center gap-1.5">
            <label htmlFor="pageSizeSelect" className="text-slate-500 sr-only">
              Rows per page
            </label>
            <select
              id="pageSizeSelect"
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setCurrentPage(1);
              }}
              className="bg-white border border-slate-200 rounded-lg px-2 py-1 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-600"
            >
              {pageSizeOptions.map((opt) => (
                <option key={opt} value={opt}>
                  {opt} / page
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Page Navigator */}
        <div className="flex items-center gap-1.5" role="navigation" aria-label="Pagination">
          <button
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            disabled={safeCurrentPage <= 1}
            className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 disabled:opacity-30 disabled:cursor-not-allowed text-slate-600 transition-colors"
            aria-label="Previous page"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>

          <span className="px-2 text-xs text-slate-600">
            Page <strong className="text-slate-800">{safeCurrentPage}</strong> of{' '}
            <strong className="text-slate-800">{totalPages}</strong>
          </span>

          <button
            onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            disabled={safeCurrentPage >= totalPages}
            className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 disabled:opacity-30 disabled:cursor-not-allowed text-slate-600 transition-colors"
            aria-label="Next page"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
