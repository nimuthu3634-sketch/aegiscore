"use client";

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export function AlertTrendChart({
  data,
}: {
  data: Array<{ label: string; critical: number; high: number; medium: number; low: number }>;
}) {
  return (
    <div className="h-[280px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <defs>
            <linearGradient id="criticalGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#FF7A1A" stopOpacity={0.32} />
              <stop offset="95%" stopColor="#FF7A1A" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="highGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#111111" stopOpacity={0.22} />
              <stop offset="95%" stopColor="#111111" stopOpacity={0} />
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
          <Area type="monotone" dataKey="critical" stackId="1" stroke="#FF7A1A" fill="url(#criticalGradient)" strokeWidth={2.4} />
          <Area type="monotone" dataKey="high" stackId="1" stroke="#111111" fill="url(#highGradient)" strokeWidth={2} />
          <Area type="monotone" dataKey="medium" stackId="1" stroke="#FFB067" fill="#FFE4CF" strokeWidth={1.5} />
          <Area type="monotone" dataKey="low" stackId="1" stroke="#B7C7B8" fill="#EDF4ED" strokeWidth={1.5} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
