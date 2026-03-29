"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export function ComparisonBarChart({
  data,
  dataKey,
}: {
  data: Array<Record<string, string | number>>;
  dataKey: string;
}) {
  return (
    <div className="h-[260px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid stroke="#efefef" strokeDasharray="4 4" vertical={false} />
          <XAxis dataKey="label" tickLine={false} axisLine={false} tick={{ fill: "#7d7d7d", fontSize: 12 }} />
          <YAxis tickLine={false} axisLine={false} tick={{ fill: "#7d7d7d", fontSize: 12 }} />
          <Tooltip
            contentStyle={{ borderRadius: 16, border: "1px solid #E8E8E8", boxShadow: "0 16px 30px rgba(17,17,17,0.08)" }}
          />
          <Bar dataKey={dataKey} fill="#FF7A1A" radius={[10, 10, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
