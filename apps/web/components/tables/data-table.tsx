"use client";

import {
  type ColumnDef,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  type SortingState,
  useReactTable,
} from "@tanstack/react-table";
import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react";
import { useState } from "react";

import { EmptyState } from "@/components/feedback/empty-state";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { cn } from "@/lib/utils";

export function DataTable<TData>({
  columns,
  rows,
  emptyMessage,
  emptyTitle = "Nothing to show",
  className,
}: {
  columns: ColumnDef<TData>[];
  rows: TData[];
  emptyMessage: string;
  emptyTitle?: string;
  className?: string;
}) {
  const [sorting, setSorting] = useState<SortingState>([]);

  const table = useReactTable({
    data: rows,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  const headerGroups = table.getHeaderGroups();
  const rowModel = table.getRowModel();

  return (
    <div className={cn("overflow-hidden rounded-[1.5rem] border bg-white shadow-panel", className)}>
      <div className="overflow-x-auto">
        <Table>
          <THead>
            {headerGroups.map((headerGroup) => (
              <TR key={headerGroup.id} className="border-none">
                {headerGroup.headers.map((header) => {
                  const direction = header.column.getIsSorted();
                  return (
                    <TH key={header.id}>
                      {header.isPlaceholder ? null : (
                        <button
                          type="button"
                          className={cn(
                            "inline-flex items-center gap-2 text-left",
                            header.column.getCanSort() ? "cursor-pointer hover:text-[#111111]" : "cursor-default",
                          )}
                          onClick={header.column.getToggleSortingHandler()}
                        >
                          <span>{flexRender(header.column.columnDef.header, header.getContext())}</span>
                          {direction === "asc" ? (
                            <ArrowUp className="h-3.5 w-3.5" />
                          ) : direction === "desc" ? (
                            <ArrowDown className="h-3.5 w-3.5" />
                          ) : header.column.getCanSort() ? (
                            <ArrowUpDown className="h-3.5 w-3.5 opacity-60" />
                          ) : null}
                        </button>
                      )}
                    </TH>
                  );
                })}
              </TR>
            ))}
          </THead>
          <TBody>
            {rowModel.rows.length === 0 ? (
              <TR>
                <TD colSpan={columns.length} className="p-0">
                  <div className="p-6">
                    <EmptyState title={emptyTitle} description={emptyMessage} />
                  </div>
                </TD>
              </TR>
            ) : (
              rowModel.rows.map((row) => (
                <TR key={row.id} className="transition hover:bg-[#fcfcfc]">
                  {row.getVisibleCells().map((cell) => (
                    <TD key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</TD>
                  ))}
                </TR>
              ))
            )}
          </TBody>
        </Table>
      </div>
    </div>
  );
}
