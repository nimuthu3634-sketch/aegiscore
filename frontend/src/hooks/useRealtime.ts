import { useContext } from "react";

import { RealtimeContext } from "@/features/realtime/RealtimeProvider";

export function useRealtime() {
  const context = useContext(RealtimeContext);

  if (!context) {
    throw new Error("useRealtime must be used within a RealtimeProvider.");
  }

  return context;
}
