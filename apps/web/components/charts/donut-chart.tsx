"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

const COLORS = ["#FF7A1A", "#111111", "#FFB067", "#D2C4B4", "#DDEBDC"];

export function DonutChart({
  data,
}: {
  data: Array<{ name: string; value: number }>;
}) {
  return (
    <div className="h-[240px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={data} dataKey="value" nameKey="name" innerRadius={62} outerRadius={96} paddingAngle={3} stroke="none">
            {data.map((entry, index) => (
              <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              borderRadius: 18,
              border: "1px solid rgba(255,255,255,0.08)",
              background: "#171311",
              color: "#fff",
              boxShadow: "0 18px 40px rgba(17,17,17,0.22)",
            }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
