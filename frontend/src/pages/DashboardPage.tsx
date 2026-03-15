import { ChartCard } from "@/components/ChartCard";
import { ContentCard } from "@/components/ContentCard";
import { PageHeader } from "@/components/PageHeader";
import { StatCard } from "@/components/StatCard";
import {
  alertTrendData,
  dashboardMetrics,
  recentActivity,
  sourceCoverageData
} from "@/data/mock";

export function DashboardPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="SOC dashboard"
        title="Security operations overview"
        description="A presentation-ready command surface for monitoring alerts, incidents, ingestion health, and anomaly signals across your lab environment."
        action={<button className="btn-primary">Generate briefing</button>}
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {dashboardMetrics.map((metric) => (
          <StatCard key={metric.label} {...metric} />
        ))}
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.5fr_1fr]">
        <ChartCard
          title="Alert volume trend"
          description="Placeholder telemetry for daily alert volume."
          data={alertTrendData}
          xKey="name"
          yKey="alerts"
        />

        <ChartCard
          title="Source coverage"
          description="Visual split of current lab ingestion sources."
          data={sourceCoverageData}
          xKey="name"
          yKey="value"
          variant="bar"
        />
      </div>

      <ContentCard
        title="Recent analyst activity"
        description="A lightweight activity feed for dashboard polish and later real-time updates."
      >
        <div className="space-y-3">
          {recentActivity.map((activity) => (
            <div
              key={activity.title}
              className="rounded-[1.25rem] border border-brand-black/5 bg-brand-light/50 p-4"
            >
              <p className="font-medium text-brand-black">{activity.title}</p>
              <p className="mt-1 text-sm text-brand-black/60">{activity.meta}</p>
            </div>
          ))}
        </div>
      </ContentCard>
    </div>
  );
}
