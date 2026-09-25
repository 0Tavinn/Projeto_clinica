"use client";

import { useAppShellViewModel } from "./AppShell.viewmodel";
import AppShellView from "./AppShell.view";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const viewModel = useAppShellViewModel();
  return <AppShellView {...viewModel}>{children}</AppShellView>;
}
