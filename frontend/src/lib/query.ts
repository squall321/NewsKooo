import { QueryClient } from "@tanstack/react-query";

/** Shared TanStack Query client. Tuned for a live-news UI: short stale times,
 * background refetch on focus, and no aggressive retries (the api client already
 * falls back to mocks on failure). */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      gcTime: 5 * 60_000,
      refetchOnWindowFocus: false,
      retry: 1,
    },
    mutations: {
      retry: 0,
    },
  },
});
