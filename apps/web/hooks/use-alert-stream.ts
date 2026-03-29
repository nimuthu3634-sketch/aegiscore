"use client";

import { useEffect, useState } from "react";

import { getToken } from "@/lib/auth";
import { appConfig } from "@/lib/config";

export function useAlertStream(enabled = true) {
  const [lastEvent, setLastEvent] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    if (!enabled) {
      return;
    }
    const token = getToken();
    if (!token) {
      return;
    }

    const socket = new WebSocket(`${appConfig.wsBaseUrl.replace(/^http/, "ws")}/ws/alerts?token=${token}`);
    socket.onmessage = (event) => {
      try {
        setLastEvent(JSON.parse(event.data));
      } catch {
        setLastEvent(null);
      }
    };

    return () => socket.close();
  }, [enabled]);

  return lastEvent;
}
