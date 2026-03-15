import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { ContentCard } from "@/components/ContentCard";

type ChartDataPoint = Record<string, string | number>;

type ChartCardProps = {
  title: string;
  description: string;
  data: ChartDataPoint[];
  xKey: string;
  yKey: string;
  variant?: "area" | "bar";
};

export function ChartCard({
  title,
  description,
  data,
  xKey,
  yKey,
  variant = "area",
}: ChartCardProps) {
  return (
    <ContentCard title={title} description={description}>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          {variant === "bar" ? (
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#D9D9D9" vertical={false} />
              <XAxis dataKey={xKey} stroke="#111111" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="#111111" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip />
              <Bar dataKey={yKey} fill="#FF7A1A" radius={[10, 10, 0, 0]} />
            </BarChart>
          ) : (
            <AreaChart data={data}>
              <defs>
                <linearGradient id="trafficGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#FF7A1A" stopOpacity={0.35} />
                  <stop offset="95%" stopColor="#FF7A1A" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#D9D9D9" vertical={false} />
              <XAxis dataKey={xKey} stroke="#111111" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="#111111" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip />
              <Area
                type="monotone"
                dataKey={yKey}
                stroke="#FF7A1A"
                strokeWidth={3}
                fill="url(#trafficGradient)"
              />
            </AreaChart>
          )}
        </ResponsiveContainer>
      </div>
    </ContentCard>
  );
}
