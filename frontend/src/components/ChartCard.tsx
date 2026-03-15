import { useId } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { SectionCard } from "@/components/SectionCard";

type ChartDataPoint = Record<string, string | number>;

type ChartCardProps = {
  title: string;
  description: string;
  data: ChartDataPoint[];
  xKey: string;
  yKey: string;
  variant?: "area" | "bar";
};

type ChartTooltipProps = {
  active?: boolean;
  label?: string | number;
  payload?: Array<{
    value?: string | number;
    name?: string;
  }>;
};

const barPalette = ["#FF7A1A", "#FFB782", "#FFD6B8", "#D9D9D9", "#B8B8B8", "#8D8D8D"];

function ChartTooltip({ active, label, payload }: ChartTooltipProps) {
  if (!active || !payload?.length) {
    return null;
  }

  const metric = payload[0];
  const value = typeof metric.value === "number" ? metric.value.toLocaleString() : metric.value;

  return (
    <div className="rounded-[1.25rem] border border-brand-orange/15 bg-brand-surface/95 px-3 py-2.5 text-white shadow-premium backdrop-blur-md">
      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-brand-muted">
        {label}
      </p>
      <p className="mt-1 text-sm font-semibold text-white">
        {metric.name ?? "Value"}: {value}
      </p>
    </div>
  );
}

export function ChartCard({
  title,
  description,
  data,
  xKey,
  yKey,
  variant = "area",
}: ChartCardProps) {
  const gradientId = useId().replace(/:/g, "");

  return (
    <SectionCard title={title} description={description}>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          {variant === "bar" ? (
            <BarChart data={data} margin={{ top: 8, right: 8, left: -22, bottom: 0 }}>
              <CartesianGrid strokeDasharray="4 4" stroke="#E9E4DE" vertical={false} />
              <XAxis
                dataKey={xKey}
                stroke="#747474"
                fontSize={12}
                tickLine={false}
                axisLine={false}
                tickMargin={10}
              />
              <YAxis
                stroke="#747474"
                fontSize={12}
                tickLine={false}
                axisLine={false}
                tickMargin={10}
                allowDecimals={false}
              />
              <Tooltip content={<ChartTooltip />} cursor={{ fill: "rgba(255, 122, 26, 0.06)" }} />
              <Bar dataKey={yKey} name={title} radius={[12, 12, 4, 4]} maxBarSize={36}>
                {data.map((_, index) => (
                  <Cell key={`${title}-bar-${index}`} fill={barPalette[index % barPalette.length]} />
                ))}
              </Bar>
            </BarChart>
          ) : (
            <AreaChart data={data} margin={{ top: 8, right: 10, left: -22, bottom: 0 }}>
              <defs>
                <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#FF7A1A" stopOpacity={0.36} />
                  <stop offset="60%" stopColor="#FF7A1A" stopOpacity={0.12} />
                  <stop offset="95%" stopColor="#FF7A1A" stopOpacity={0.03} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="4 4" stroke="#E9E4DE" vertical={false} />
              <XAxis
                dataKey={xKey}
                stroke="#747474"
                fontSize={12}
                tickLine={false}
                axisLine={false}
                tickMargin={10}
              />
              <YAxis
                stroke="#747474"
                fontSize={12}
                tickLine={false}
                axisLine={false}
                tickMargin={10}
                allowDecimals={false}
              />
              <Tooltip content={<ChartTooltip />} cursor={{ stroke: "#FF7A1A", strokeOpacity: 0.2 }} />
              <Area
                type="monotone"
                dataKey={yKey}
                name={title}
                stroke="#FF7A1A"
                strokeWidth={3}
                fill={`url(#${gradientId})`}
                activeDot={{ r: 5, fill: "#FF7A1A", stroke: "#FFFFFF", strokeWidth: 2 }}
              />
            </AreaChart>
          )}
        </ResponsiveContainer>
      </div>
    </SectionCard>
  );
}
