import { LayoutDashboard, UsersRound, type LucideIcon, Contact } from "lucide-react";
import type { UserRole } from "@/types/auth";
import { hasPermission, type Permission } from "./permissions";
import { ROUTES } from "./routes";

export type NavItem = {
  label: string;
  description: string;
  href: string;
  icon: LucideIcon;
  permission?: Permission;
};

const NAV_ITEMS: NavItem[] = [
  {
    label: "Início",
    description: "Visão geral da clínica.",
    href: ROUTES.dashboard,
    icon: LayoutDashboard,
  },
  {
    label: "Pacientes",
    description: "Consulte, cadastre e atualize pacientes.",
    href: ROUTES.patients,
    icon: Contact,
    permission: "viewPatients",
  },
  {
    label: "Equipe",
    description: "Gerencie os usuários da clínica.",
    href: ROUTES.team,
    icon: UsersRound,
    permission: "manageTeam",
  },
];

export function getNavItems(role: UserRole): NavItem[] {
  return NAV_ITEMS.filter(
    (item) => !item.permission || hasPermission(role, item.permission),
  );
}
