import type { ReactNode } from "react";

type TableColumn = {
  key: string;
  label: string;
  className?: string;
};

type TableRow = Record<string, ReactNode>;

type DataTableProps = {
  columns: TableColumn[];
  rows: TableRow[];
  emptyMessage?: string;
};

export function DataTable({
  columns,
  rows,
  emptyMessage = "No records available yet.",
}: DataTableProps) {
  return (
    <div className="overflow-hidden rounded-[1.25rem] border border-brand-black/5">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-brand-black/5">
          <thead className="bg-brand-light/70">
            <tr>
              {columns.map((column) => (
                <th
                  key={column.key}
                  className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-[0.2em] text-brand-black/55"
                >
                  {column.label}
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
              rows.map((row, rowIndex) => (
                <tr key={String(row.id ?? rowIndex)} className="hover:bg-brand-light/40">
                  {columns.map((column) => (
                    <td
                      key={column.key}
                      className={`px-4 py-4 align-top text-sm text-brand-black/75 ${column.className ?? ""}`}
                    >
                      {row[column.key]}
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
