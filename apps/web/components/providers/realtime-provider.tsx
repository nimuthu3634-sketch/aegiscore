"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { usePathname } from "next/navigation";

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
  const pathname = usePathname();
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<RealtimeContextValue["status"]>("idle");
  const [lastEvent, setLastEvent] = useState<RealtimePayload>(null);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      setStatus("idle");
      setLastEvent(null);
      return;
    }

    let isActive = true;
    setStatus("connecting");
    const socket = new WebSocket(`${appConfig.wsBaseUrl.replace(/^http/, "ws")}/ws/alerts?token=${token}`);

    socket.onopen = () => {
      if (isActive) {
        setStatus("connected");
      }
    };
    socket.onclose = () => {
      if (isActive) {
        setStatus("disconnected");
      }
    };
    socket.onerror = () => {
      if (isActive) {
        setStatus("error");
      }
    };
    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data) as Record<string, unknown>;
        if (!isActive) {
          return;
        }
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
      isActive = false;
      socket.close();
    };
  }, [pathname, queryClient]);

  const value = useMemo(() => ({ status, lastEvent }), [lastEvent, status]);
  return <RealtimeContext.Provider value={value}>{children}</RealtimeContext.Provider>;
}

export function useRealtime() {
  return useContext(RealtimeContext);
}
