"use client";

import { useRealtime } from "@/components/providers/realtime-provider";

export function useAlertStream(enabled = true) {
  const realtime = useRealtime();
  if (!enabled) {
    return null;
  }
  return realtime.lastEvent;
}

export function useRealtimeStatus() {
  return useRealtime().status;
}
