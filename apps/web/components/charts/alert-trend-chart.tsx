"use client";

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export function AlertTrendChart({
  data,
}: {
  data: Array<{ label: string; critical: number; high: number; medium: number; low: number }>;
}) {
  return (
    <div className="h-[280px]">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <defs>
            <linearGradient id="criticalGradient" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor="#ff7a1a" stopOpacity={0.45} />
              <stop offset="100%" stopColor="#ff7a1a" stopOpacity={0.05} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="label" tick={{ fill: "#6b7280", fontSize: 12 }} />
          <YAxis tick={{ fill: "#6b7280", fontSize: 12 }} />
          <Tooltip />
          <Area type="monotone" dataKey="critical" stroke="#ff7a1a" fill="url(#criticalGradient)" strokeWidth={2} />
          <Area type="monotone" dataKey="high" stroke="#111111" fillOpacity={0} strokeWidth={2} />
          <Area type="monotone" dataKey="medium" stroke="#f59e0b" fillOpacity={0} strokeWidth={2} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
