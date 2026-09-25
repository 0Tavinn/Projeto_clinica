import PageHeader from "@/components/shared/PageHeader";
import ShortcutGrid from "./components/ShortcutGrid";
import type { DashboardViewModel } from "./Dashboard.viewmodel";

export default function DashboardView({
  firstName,
  roleLabel,
  shortcuts,
}: DashboardViewModel) {
  return (
    <div className="flex flex-col gap-10">
      <PageHeader
        title={`Olá, ${firstName}`}
        description={`Você está conectado como ${roleLabel}.`}
      />
      <ShortcutGrid shortcuts={shortcuts} />
    </div>
  );
}
