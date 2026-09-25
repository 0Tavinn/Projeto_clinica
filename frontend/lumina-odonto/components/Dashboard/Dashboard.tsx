"use client";

import { useDashboardViewModel } from "./Dashboard.viewmodel";
import DashboardView from "./Dashboard.view";

export default function Dashboard() {
  const viewModel = useDashboardViewModel();
  if (!viewModel) return null;
  return <DashboardView {...viewModel} />;
}
