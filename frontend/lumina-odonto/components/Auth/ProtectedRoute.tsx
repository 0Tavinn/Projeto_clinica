"use client";

import AppShell from "@/components/AppShell/AppShell";
import FullScreenLoader from "@/components/shared/FullScreenLoader";
import AccessDenied from "./AccessDenied";
import { useProtectedRouteViewModel } from "./AuthGuard.viewmodel";

// Guard client-side: os tokens ficam no localStorage, fora do alcance do proxy.ts.
// A API continua sendo a autoridade (401/403).
export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const decision = useProtectedRouteViewModel();

  if (decision.kind === "loading") {
    return <FullScreenLoader label="Verificando sessão…" />;
  }
  if (decision.kind === "redirect") {
    return <FullScreenLoader label="Redirecionando…" />;
  }
  return (
    <AppShell>
      {decision.kind === "denied" ? (
        <AccessDenied homeRoute={decision.homeRoute} />
      ) : (
        children
      )}
    </AppShell>
  );
}
