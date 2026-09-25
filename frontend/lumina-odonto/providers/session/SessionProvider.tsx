"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { authService } from "@/services/Login/Login.service";
import type { AuthUser } from "@/types/auth";
import {
  SessionContext,
  type SessionContextValue,
  type SessionStatus,
} from "./session.context";

type SessionState = { status: SessionStatus; user: AuthUser | null };

const UNAUTHENTICATED: SessionState = { status: "unauthenticated", user: null };

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<SessionState>({
    status: "loading",
    user: null,
  });

  // Tokens ficam no localStorage: a sessão só pode ser restaurada no navegador.
  useEffect(() => {
    let active = true;
    authService.restoreSession().then((user) => {
      if (!active) return;
      setState(user ? { status: "authenticated", user } : UNAUTHENTICATED);
    });
    return () => {
      active = false;
    };
  }, []);

  const setUser = useCallback((user: AuthUser) => {
    setState({ status: "authenticated", user });
  }, []);

  const logout = useCallback(() => {
    authService.logout();
    setState(UNAUTHENTICATED);
  }, []);

  const value = useMemo<SessionContextValue>(
    () => ({ ...state, setUser, logout }),
    [state, setUser, logout],
  );

  return <SessionContext value={value}>{children}</SessionContext>;
}
