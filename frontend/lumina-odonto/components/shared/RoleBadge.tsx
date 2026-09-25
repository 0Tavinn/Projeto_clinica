import { Badge } from "@/components/ui/badge";
import { ROLE_LABELS } from "@/lib/auth/permissions";
import { cn } from "@/lib/utils";
import type { UserRole } from "@/types/auth";

const ROLE_STYLES: Record<UserRole, string> = {
  ADMINISTRATOR: "bg-[#E0F2FE] text-[#0369A1]",
  RECEPTIONIST: "bg-[#F1F5F9] text-[#334155]",
  DENTIST: "bg-[#ECFDF5] text-[#047857]",
};

export default function RoleBadge({
  role,
  className,
}: {
  role: UserRole;
  className?: string;
}) {
  return (
    <Badge className={cn(ROLE_STYLES[role], className)}>{ROLE_LABELS[role]}</Badge>
  );
}
