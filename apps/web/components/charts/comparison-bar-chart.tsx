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
          <defs>
            <linearGradient id="comparisonBarGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#FF8A36" />
              <stop offset="100%" stopColor="#FF7A1A" />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="rgba(17,17,17,0.08)" strokeDasharray="4 4" vertical={false} />
          <XAxis dataKey="label" tickLine={false} axisLine={false} tick={{ fill: "#7d746d", fontSize: 12 }} />
          <YAxis tickLine={false} axisLine={false} tick={{ fill: "#7d746d", fontSize: 12 }} />
          <Tooltip
            contentStyle={{
              borderRadius: 18,
              border: "1px solid rgba(255,255,255,0.08)",
              background: "#171311",
              color: "#fff",
              boxShadow: "0 18px 40px rgba(17,17,17,0.22)",
            }}
          />
          <Bar dataKey={dataKey} fill="url(#comparisonBarGradient)" radius={[10, 10, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
