import type { Metadata } from "next";
import PagePlaceholder from "@/components/shared/PagePlaceholder";

export const metadata: Metadata = { title: "Equipe" };

export default function TeamPage() {
  return (
    <PagePlaceholder
      title="Equipe"
      description="Gerencie os usuários e perfis de acesso da clínica."
    />
  );
}
