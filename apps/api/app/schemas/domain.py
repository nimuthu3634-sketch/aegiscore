1) apps/api/app/schemas/domain.py

Add these classes right after AlertUpdate:

class ResponseActionRequest(BaseModel):
    action: Literal["block_ip", "isolate_asset", "disable_user", "contain_alert"]
    reason: str | None = Field(default=None, max_length=1000)

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class ResponseActionResult(BaseModel):
    alert_id: str
    action: str
    status: Literal["recorded", "simulated"]
    message: str
    executed_at: datetime
    target: dict[str, str | None] = Field(default_factory=dict)
    follow_up: list[str] = Field(default_factory=list)
2) apps/api/app/services/domain.py

Update the import:

from app.schemas.domain import DashboardActivityItem, DashboardKpi, DashboardSummary, DashboardTrendPoint, ResponseActionResult

Replace broadcast_alert_event with this:

async def broadcast_alert_event(alert: Alert, event: str, metadata: dict | None = None) -> None:
    payload = {
        "event": event,
        "alert_id": alert.id,
        "title": alert.title,
        "severity": alert.severity,
        "status": alert.status,
        "risk_score": alert.risk_score,
        "occurred_at": alert.occurred_at.isoformat(),
        "detected_at": alert.detected_at.isoformat(),
    }
    if metadata:
        payload.update(metadata)

    await manager.broadcast("alerts", payload)

Add these helpers below it:

def _extract_response_ip(alert: Alert) -> str | None:
    parsed_payload = dict(alert.parsed_payload or {})
    raw_payload = dict(alert.raw_payload or {})
    candidates = [
        parsed_payload.get("src_ip"),
        parsed_payload.get("source_ip"),
        parsed_payload.get("indicator_ip"),
        raw_payload.get("src_ip"),
        raw_payload.get("srcip"),
        raw_payload.get("source_ip"),
        raw_payload.get("ip"),
        alert.asset.ip_address if alert.asset else None,
    ]
    for candidate in candidates:
        if candidate:
            return str(candidate).strip()
    return None


def _extract_response_user(alert: Alert) -> str | None:
    parsed_payload = dict(alert.parsed_payload or {})
    raw_payload = dict(alert.raw_payload or {})
    for container in (parsed_payload, raw_payload):
        for key in ("username", "user", "account", "principal", "target_user", "target_account"):
            value = container.get(key)
            if value:
                return str(value).strip()
    return None


def execute_alert_response(
    db: Session,
    *,
    alert: Alert,
    action: str,
    actor: User,
    ip_address: str | None,
    reason: str | None = None,
) -> tuple[Alert, ResponseActionResult]:
    action_labels = {
        "block_ip": "Block source IP",
        "isolate_asset": "Isolate asset",
        "disable_user": "Disable user",
        "contain_alert": "Contain alert",
    }
    if action not in action_labels:
        raise ValueError("Unsupported response action.")

    target: dict[str, str | None]
    follow_up: list[str]

    if action == "block_ip":
        ip_target = _extract_response_ip(alert)
        if not ip_target:
            raise ValueError("No source IP was found on this alert, so a block action cannot be recorded.")
        target = {
            "ip_address": ip_target,
            "asset_hostname": alert.asset.hostname if alert.asset else None,
        }
        message = (
            f"Recorded a defensive block request for source IP {ip_target}. "
            "This is tracked inside AegisCore for analyst follow-through or future SOAR integration."
        )
        follow_up = [
            "Apply the block in your firewall, Wazuh active response, or upstream gateway.",
            "Validate that new events from this indicator stop after containment.",
        ]
    elif action == "isolate_asset":
        if alert.asset is None:
            raise ValueError("This alert is not mapped to an asset, so host isolation cannot be recorded.")
        target = {
            "hostname": alert.asset.hostname,
            "ip_address": alert.asset.ip_address,
        }
        message = (
            f"Recorded host isolation for {alert.asset.hostname}. "
            "Use your endpoint tooling or lab workflow to disconnect the host from the network."
        )
        follow_up = [
            "Confirm the endpoint is quarantined or otherwise segmented.",
            "Capture volatile evidence before rebooting or reimaging the host.",
        ]
    elif action == "disable_user":
        username = _extract_response_user(alert)
        if not username:
            raise ValueError("No username was found on this alert, so an account disable action cannot be recorded.")
        target = {
            "username": username,
            "asset_hostname": alert.asset.hostname if alert.asset else None,
        }
        message = (
            f"Recorded an account disable request for {username}. "
            "Coordinate with your identity provider or operating system account controls to complete the step."
        )
        follow_up = [
            "Force a credential reset if compromise is suspected.",
            "Review recent authentication events tied to this identity.",
        ]
    else:
        target = {
            "alert_title": alert.title,
            "severity": alert.severity,
        }
        message = "Recorded containment handling for this alert and moved it into the active investigation workflow."
        follow_up = [
            "Assign an analyst owner and document the next investigative step.",
            "Escalate into an incident if the alert remains confirmed or recurring.",
        ]

    if alert.status not in {AlertStatus.RESOLVED, AlertStatus.SUPPRESSED}:
        alert.status = AlertStatus.INVESTIGATING

    alert.recommendations = sorted({*list(alert.recommendations or []), "Review containment outcome"})
    db.add(alert)

    reason_suffix = f" Reason: {reason}" if reason else ""
    db.add(
        AlertComment(
            alert_id=alert.id,
            author_id=actor.id,
            body=f"{action_labels[action]} recorded. {message}{reason_suffix}",
        )
    )
    db.commit()
    db.refresh(alert)

    executed_at = datetime.now(timezone.utc)
    record_audit(
        db,
        actor=actor,
        action="alert.response_executed",
        entity_type="alert",
        entity_id=alert.id,
        details={
            "response_action": action,
            "status": "simulated",
            "target": target,
            "reason": reason,
        },
        ip_address=ip_address,
    )

    return (
        alert,
        ResponseActionResult(
            alert_id=alert.id,
            action=action,
            status="simulated",
            message=message,
            executed_at=executed_at,
            target=target,
            follow_up=follow_up,
        ),
    )
3) apps/api/app/api/routes/alerts.py

Update imports:

from app.schemas.domain import (
    AlertCommentCreate,
    AlertCommentRead,
    AlertCreate,
    AlertListResponse,
    AlertRead,
    ResponseActionRequest,
    ResponseActionResult,
    AlertUpdate,
    IncidentCreate,
    IncidentRead,
)
from app.services.domain import (
    add_alert_comment,
    broadcast_alert_event,
    create_alert,
    create_incident,
    execute_alert_response,
    update_alert,
)

Add this route under the comments route:

@router.post("/{alert_id}/respond", response_model=ResponseActionResult)
async def respond_to_alert(
    alert_id: str,
    payload: ResponseActionRequest,
    ip_address: str | None = Depends(get_optional_ip),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST)),
    db: Session = Depends(get_db),
) -> ResponseActionResult:
    alert = db.query(Alert).options(joinedload(Alert.asset)).filter(Alert.id == alert_id).one_or_none()
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    try:
        updated_alert, result = execute_alert_response(
            db,
            alert=alert,
            action=payload.action,
            actor=current_user,
            ip_address=ip_address,
            reason=payload.reason,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    await broadcast_alert_event(
        updated_alert,
        "response_executed",
        {
            "response_action": result.action,
            "response_status": result.status,
        },
    )
    return result
4) apps/web/types/domain.ts

Add:

export type ResponseActionType = "block_ip" | "isolate_asset" | "disable_user" | "contain_alert";

export interface ResponseActionResult {
  alert_id: string;
  action: ResponseActionType | string;
  status: "recorded" | "simulated" | string;
  message: string;
  executed_at: string;
  target: Record<string, string | null>;
  follow_up: string[];
}
5) apps/web/app/(app)/alerts/[id]/page.tsx

Update import:

import type { Alert, Incident, PageResult, ResponseActionResult, ResponseActionType, User } from "@/types/domain";

Add this near the top of the file:

const containmentActions: Array<{ action: ResponseActionType; label: string; description: string }> = [
  {
    action: "block_ip",
    label: "Block source IP",
    description: "Record a perimeter or host firewall block for the source indicator tied to this alert.",
  },
  {
    action: "isolate_asset",
    label: "Isolate asset",
    description: "Record host isolation for the linked endpoint so the analyst can quarantine it in tooling.",
  },
  {
    action: "disable_user",
    label: "Disable user",
    description: "Record an account disable action when the alert includes affected username context.",
  },
  {
    action: "contain_alert",
    label: "Mark contained",
    description: "Move the alert into active containment handling and document the action trail.",
  },
];

Add this mutation inside the component, above updateMutation:

const responseMutation = useMutation({
  mutationFn: (action: ResponseActionType) =>
    api.post<ResponseActionResult>(`/alerts/${params.id}/respond`, { action }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["alert", params.id] });
    queryClient.invalidateQueries({ queryKey: ["alerts"] });
    queryClient.invalidateQueries({ queryKey: ["dashboard", "summary"] });
  },
});

Then add this new card under the existing Triage controls card:

<Card>
  <CardHeader>
    <CardTitle>Containment actions</CardTitle>
  </CardHeader>
  <CardContent className="space-y-4">
    <div className="rounded-[1.25rem] border bg-[#fff7f1] p-4 text-sm leading-6 text-[#8a4e16]">
      These actions are recorded and audited inside AegisCore. They do not directly push firewall or host controls yet,
      but they create a real containment trail and prepare the app for SOAR-style execution.
    </div>

    <div className="grid gap-3">
      {containmentActions.map((item) => (
        <div key={item.action} className="rounded-[1.25rem] border bg-[#fcfcfc] p-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p className="font-semibold text-[#111111]">{item.label}</p>
              <p className="mt-1 text-sm leading-6 text-[#5f5f5f]">{item.description}</p>
            </div>
            <Button
              variant="outline"
              onClick={() => responseMutation.mutate(item.action)}
              disabled={responseMutation.isPending}
            >
              {responseMutation.isPending && responseMutation.variables === item.action ? "Recording..." : item.label}
            </Button>
          </div>
        </div>
      ))}
    </div>

    {responseMutation.data ? (
      <div className="rounded-[1.25rem] border bg-white p-4">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="high">{responseMutation.data.action}</Badge>
          <Badge tone="medium">{responseMutation.data.status}</Badge>
          <span className="text-xs uppercase tracking-[0.24em] text-[#8f8f8f]">
            {formatDate(responseMutation.data.executed_at)}
          </span>
        </div>

        <p className="mt-3 text-sm leading-6 text-[#5f5f5f]">{responseMutation.data.message}</p>

        {Object.keys(responseMutation.data.target).length ? (
          <div className="mt-4 grid gap-2">
            {Object.entries(responseMutation.data.target).map(([key, value]) => (
              <div key={key} className="flex items-center justify-between rounded-xl border px-3 py-2 text-sm">
                <span className="capitalize text-[#6f6f6f]">{key.replaceAll("_", " ")}</span>
                <span className="font-medium text-[#111111]">{value ?? "Unavailable"}</span>
              </div>
            ))}
          </div>
        ) : null}

        {responseMutation.data.follow_up.length ? (
          <div className="mt-4 space-y-2">
            {responseMutation.data.follow_up.map((item) => (
              <div key={item} className="rounded-xl border bg-[#fcfcfc] px-3 py-2 text-sm leading-6 text-[#5f5f5f]">
                {item}
              </div>
            ))}
          </div>
        ) : null}
      </div>
    ) : null}

    {responseMutation.error instanceof Error ? (
      <div className="rounded-[1.25rem] border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        {responseMutation.error.message}
      </div>
    ) : null}
  </CardContent>
</Card>