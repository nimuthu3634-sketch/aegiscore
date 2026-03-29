import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";

type Column<T> = {
  key: string;
  header: string;
  render: (row: T) => React.ReactNode;
};

export function DataTable<T>({ columns, rows, emptyMessage }: { columns: Column<T>[]; rows: T[]; emptyMessage: string }) {
  return (
    <div className="overflow-hidden rounded-2xl border bg-white shadow-panel">
      <div className="overflow-x-auto">
        <Table>
          <THead>
            <TR>
              {columns.map((column) => (
                <TH key={column.key}>{column.header}</TH>
              ))}
            </TR>
          </THead>
          <TBody>
            {rows.length === 0 ? (
              <TR>
                <TD colSpan={columns.length} className="py-8 text-center text-[var(--muted)]">
                  {emptyMessage}
                </TD>
              </TR>
            ) : (
              rows.map((row, index) => (
                <TR key={index}>
                  {columns.map((column) => (
                    <TD key={column.key}>{column.render(row)}</TD>
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
