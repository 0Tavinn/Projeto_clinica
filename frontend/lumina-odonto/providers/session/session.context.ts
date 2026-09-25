"use client";

import { createContext, useContext } from "react";
import type { AuthUser } from "@/types/auth";

export type SessionStatus = "loading" | "authenticated" | "unauthenticated";

export type SessionContextValue = {
  status: SessionStatus;
  user: AuthUser | null;
  setUser: (user: AuthUser) => void;
  logout: () => void;
};

export const SessionContext = createContext<SessionContextValue | null>(null);

export function useSession(): SessionContextValue {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error("useSession precisa estar dentro de <SessionProvider>.");
  }
  return context;
}
