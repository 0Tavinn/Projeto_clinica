"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useSession } from "@/providers/session/session.context";
import {
  resolveGuestRoute,
  resolveProtectedRoute,
  type GuardDecision,
} from "./AuthGuard.model";

function useRedirect(decision: GuardDecision) {
  const router = useRouter();
  const target = decision.kind === "redirect" ? decision.to : null;

  useEffect(() => {
    if (target) router.replace(target);
  }, [router, target]);
}

export function useProtectedRouteViewModel(): GuardDecision {
  const { status, user } = useSession();
  const pathname = usePathname();
  const decision = resolveProtectedRoute(status, user, pathname);
  useRedirect(decision);
  return decision;
}

export function useGuestRouteViewModel(): GuardDecision {
  const { status, user } = useSession();
  const decision = resolveGuestRoute(status, user);
  useRedirect(decision);
  return decision;
}
