import type { Metadata } from "next";
import PagePlaceholder from "@/components/shared/PagePlaceholder";

export const metadata: Metadata = { title: "Pacientes" };

export default function PatientsPage() {
  return (
    <PagePlaceholder
      title="Pacientes"
      description="Consulte, cadastre e atualize os pacientes da clínica."
    />
  );
}
