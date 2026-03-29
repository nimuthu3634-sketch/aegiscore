"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { getToken } from "@/lib/auth";
import { appConfig } from "@/lib/config";

type RealtimePayload = Record<string, unknown> | null;

type RealtimeContextValue = {
  status: "idle" | "connecting" | "connected" | "disconnected" | "error";
  lastEvent: RealtimePayload;
};

const RealtimeContext = createContext<RealtimeContextValue>({
  status: "idle",
  lastEvent: null,
});

export function RealtimeProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<RealtimeContextValue["status"]>("idle");
  const [lastEvent, setLastEvent] = useState<RealtimePayload>(null);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      setStatus("idle");
      return;
    }

    setStatus("connecting");
    const socket = new WebSocket(`${appConfig.wsBaseUrl.replace(/^http/, "ws")}/ws/alerts?token=${token}`);

    socket.onopen = () => setStatus("connected");
    socket.onclose = () => setStatus("disconnected");
    socket.onerror = () => setStatus("error");
    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data) as Record<string, unknown>;
        setLastEvent(payload);
        queryClient.invalidateQueries({ queryKey: ["dashboard", "summary"] });
        queryClient.invalidateQueries({ queryKey: ["alerts"] });
        queryClient.invalidateQueries({ queryKey: ["assets"] });
        if (typeof payload.alert_id === "string") {
          queryClient.invalidateQueries({ queryKey: ["alert", payload.alert_id] });
        }
      } catch {
        setLastEvent(null);
      }
    };

    return () => {
      socket.close();
    };
  }, [queryClient]);

  const value = useMemo(() => ({ status, lastEvent }), [lastEvent, status]);
  return <RealtimeContext.Provider value={value}>{children}</RealtimeContext.Provider>;
}

export function useRealtime() {
  return useContext(RealtimeContext);
}
