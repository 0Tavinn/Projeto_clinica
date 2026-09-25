"use client";

import FullScreenLoader from "@/components/shared/FullScreenLoader";
import { useGuestRouteViewModel } from "./AuthGuard.viewmodel";

export default function GuestRoute({ children }: { children: React.ReactNode }) {
  const decision = useGuestRouteViewModel();

  if (decision.kind === "loading") {
    return <FullScreenLoader label="Verificando sessão…" />;
  }
  if (decision.kind === "redirect") {
    return <FullScreenLoader label="Entrando…" />;
  }
  return children;
}
