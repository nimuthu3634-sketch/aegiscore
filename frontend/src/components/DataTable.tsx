import type { Key, ReactNode } from "react";

export type DataTableColumn<T> = {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
  className?: string;
  headerClassName?: string;
};

type DataTableProps<T> = {
  columns: DataTableColumn<T>[];
  rows: T[];
  rowKey: (row: T) => Key;
  emptyMessage?: string;
  compact?: boolean;
  onRowClick?: (row: T) => void;
  selectedRowKey?: Key;
};

export function DataTable<T>({
  columns,
  rows,
  rowKey,
  emptyMessage = "No records available yet.",
  compact = false,
  onRowClick,
  selectedRowKey,
}: DataTableProps<T>) {
  return (
    <div className="overflow-hidden rounded-[1.5rem] border border-brand-black/8 bg-white">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-brand-black/5">
          <thead className="bg-brand-light/70">
            <tr>
              {columns.map((column) => (
                <th
                  key={column.key}
                  className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-[0.2em] text-brand-black/55 ${column.headerClassName ?? ""}`}
                >
                  {column.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-brand-black/5 bg-white">
            {rows.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-4 py-12 text-center text-sm text-brand-black/60"
                >
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              rows.map((row) => (
                <tr
                  key={rowKey(row)}
                  className={`hover:bg-brand-light/40 ${onRowClick ? "cursor-pointer" : ""} ${selectedRowKey === rowKey(row) ? "bg-brand-orange/5" : ""}`}
                  onClick={onRowClick ? () => onRowClick(row) : undefined}
                >
                  {columns.map((column) => (
                    <td
                      key={column.key}
                      className={`align-top text-sm text-brand-black/75 ${compact ? "px-4 py-3" : "px-4 py-4"} ${column.className ?? ""}`}
                    >
                      {column.render(row)}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
