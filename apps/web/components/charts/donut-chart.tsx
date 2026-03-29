"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

const COLORS = ["#FF7A1A", "#111111", "#FFB067", "#CBD5E1", "#DCFCE7"];

export function DonutChart({
  data,
}: {
  data: Array<{ name: string; value: number }>;
}) {
  return (
    <div className="h-[240px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={data} dataKey="value" nameKey="name" innerRadius={62} outerRadius={96} paddingAngle={3}>
            {data.map((entry, index) => (
              <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{ borderRadius: 16, border: "1px solid #E8E8E8", boxShadow: "0 16px 30px rgba(17,17,17,0.08)" }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
