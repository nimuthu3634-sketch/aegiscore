import {
  createContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type PropsWithChildren,
} from "react";

import { useAuth } from "@/hooks/useAuth";
import { API_BASE_URL } from "@/services/api";
import type { AlertApiRecord } from "@/types/domain";

type ConnectionStatus = "connecting" | "connected" | "disconnected";

type LiveAlertToast = {
  count: number;
  latestAlert: AlertApiRecord;
};

type RealtimeContextValue = {
  connectionStatus: ConnectionStatus;
  refreshVersion: number;
  liveAlertToast: LiveAlertToast | null;
  liveAlertCount: number;
  dismissLiveAlertToast: () => void;
};

type AlertStreamReadyMessage = {
  event: "alerts_stream_ready";
  message: string;
  latest_alert: AlertApiRecord | null;
};

type AlertCreatedMessage = {
  event: "alert_created";
  message: string;
  alert: AlertApiRecord;
};

type RealtimeMessage = AlertStreamReadyMessage | AlertCreatedMessage;

const REFRESH_DEBOUNCE_MS = 750;
const TOAST_DISMISS_MS = 5000;
const RECONNECT_DELAY_MS = 2500;

export const RealtimeContext = createContext<RealtimeContextValue | undefined>(undefined);

function buildAlertsWebSocketUrl() {
  const configuredWebSocketUrl = import.meta.env.VITE_WS_URL;
  if (configuredWebSocketUrl) {
    return configuredWebSocketUrl;
  }

  const sanitizedBaseUrl = API_BASE_URL.replace(/\/$/, "");
  const websocketBaseUrl = sanitizedBaseUrl.replace(/^http/i, "ws");
  return `${websocketBaseUrl}/ws/alerts`;
}

export function RealtimeProvider({ children }: PropsWithChildren) {
  const { token } = useAuth();
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>("disconnected");
  const [refreshVersion, setRefreshVersion] = useState(0);
  const [liveAlertToast, setLiveAlertToast] = useState<LiveAlertToast | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<number | null>(null);
  const refreshTimerRef = useRef<number | null>(null);
  const dismissTimerRef = useRef<number | null>(null);
  const lastAlertIdRef = useRef<string | null>(null);

  useEffect(() => {
    if (!token) {
      if (reconnectTimerRef.current) {
        window.clearTimeout(reconnectTimerRef.current);
      }
      if (refreshTimerRef.current) {
        window.clearTimeout(refreshTimerRef.current);
      }
      if (dismissTimerRef.current) {
        window.clearTimeout(dismissTimerRef.current);
      }
      if (socketRef.current) {
        socketRef.current.close();
      }

      socketRef.current = null;
      setConnectionStatus("disconnected");
      setLiveAlertToast(null);
      return;
    }

    let isActive = true;

    const cleanupTimers = () => {
      if (reconnectTimerRef.current) {
        window.clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      if (refreshTimerRef.current) {
        window.clearTimeout(refreshTimerRef.current);
        refreshTimerRef.current = null;
      }
      if (dismissTimerRef.current) {
        window.clearTimeout(dismissTimerRef.current);
        dismissTimerRef.current = null;
      }
    };

    const queueRefresh = () => {
      if (refreshTimerRef.current) {
        window.clearTimeout(refreshTimerRef.current);
      }

      refreshTimerRef.current = window.setTimeout(() => {
        setRefreshVersion((currentValue) => currentValue + 1);
        refreshTimerRef.current = null;
      }, REFRESH_DEBOUNCE_MS);
    };

    const scheduleToastDismiss = () => {
      if (dismissTimerRef.current) {
        window.clearTimeout(dismissTimerRef.current);
      }

      dismissTimerRef.current = window.setTimeout(() => {
        setLiveAlertToast(null);
        dismissTimerRef.current = null;
      }, TOAST_DISMISS_MS);
    };

    const handleAlertCreated = (alert: AlertApiRecord) => {
      if (lastAlertIdRef.current === alert.id) {
        return;
      }

      lastAlertIdRef.current = alert.id;
      setLiveAlertToast((currentToast) => ({
        count: currentToast ? currentToast.count + 1 : 1,
        latestAlert: alert,
      }));
      scheduleToastDismiss();
      queueRefresh();
    };

    const connect = () => {
      if (!isActive) {
        return;
      }

      setConnectionStatus("connecting");
      const websocket = new WebSocket(buildAlertsWebSocketUrl());
      socketRef.current = websocket;

      websocket.onopen = () => {
        if (!isActive) {
          websocket.close();
          return;
        }

        setConnectionStatus("connected");
      };

      websocket.onmessage = (event) => {
        if (!isActive) {
          return;
        }

        try {
          const payload = JSON.parse(event.data) as RealtimeMessage;

          if (payload.event === "alerts_stream_ready") {
            setConnectionStatus("connected");
            return;
          }

          if (payload.event === "alert_created") {
            handleAlertCreated(payload.alert);
          }
        } catch {
          setConnectionStatus("disconnected");
        }
      };

      websocket.onerror = () => {
        websocket.close();
      };

      websocket.onclose = () => {
        if (socketRef.current === websocket) {
          socketRef.current = null;
        }

        if (!isActive) {
          return;
        }

        setConnectionStatus("disconnected");
        reconnectTimerRef.current = window.setTimeout(() => {
          connect();
        }, RECONNECT_DELAY_MS);
      };
    };

    connect();

    return () => {
      isActive = false;
      cleanupTimers();
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
    };
  }, [token]);

  const dismissLiveAlertToast = () => {
    if (dismissTimerRef.current) {
      window.clearTimeout(dismissTimerRef.current);
      dismissTimerRef.current = null;
    }

    setLiveAlertToast(null);
  };

  const value = useMemo<RealtimeContextValue>(
    () => ({
      connectionStatus,
      refreshVersion,
      liveAlertToast,
      liveAlertCount: liveAlertToast?.count ?? 0,
      dismissLiveAlertToast,
    }),
    [connectionStatus, liveAlertToast, refreshVersion],
  );

  return <RealtimeContext.Provider value={value}>{children}</RealtimeContext.Provider>;
}
