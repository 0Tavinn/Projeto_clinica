import Link from "next/link";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

type SidebarNavItemProps = {
  href: string;
  label: string;
  icon: LucideIcon;
  active: boolean;
};

export default function SidebarNavItem({
  href,
  label,
  icon: Icon,
  active,
}: SidebarNavItemProps) {
  return (
    <Link
      href={href}
      aria-current={active ? "page" : undefined}
      className={cn(
        "flex h-[44px] items-center gap-3 rounded-[10px] px-3 text-[15px] font-medium transition-colors",
        active
          ? "bg-[#E0F2FE] text-[#0369A1]"
          : "text-[#64748B] hover:bg-[#F1F5F9] hover:text-[#1E293B]",
      )}
    >
      <Icon className="size-[18px]" aria-hidden />
      {label}
    </Link>
  );
}
