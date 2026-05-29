import * as React from "react";
import { getOffline, onModeChange, USE_MOCKS } from "@/lib/api";

/** Reflects whether the UI is currently serving mock data (forced or fallback). */
export function useApiMode(): { offline: boolean; forced: boolean } {
  const [offline, setOffline] = React.useState(getOffline());
  React.useEffect(() => {
    const unsubscribe = onModeChange(setOffline);
    return () => {
      unsubscribe();
    };
  }, []);
  return { offline, forced: USE_MOCKS };
}
