import Link from "next/link";
import { ArrowRight } from "lucide-react";
import type { NavItem } from "@/lib/auth/navigation";

export default function ShortcutCard({ href, label, description, icon: Icon }: NavItem) {
  return (
    <Link
      href={href}
      className="group flex flex-col gap-4 rounded-[20px] bg-white p-6 shadow-[0px_14px_30px_0px_rgba(15,23,42,0.06)] transition-shadow hover:shadow-[0px_14px_30px_0px_rgba(15,23,42,0.12)] focus-visible:ring-3 focus-visible:ring-[#0EA5E9]/40 focus-visible:outline-none"
    >
      <div className="flex size-11 items-center justify-center rounded-[12px] bg-[#E0F2FE] text-[#0369A1]">
        <Icon className="size-5" aria-hidden />
      </div>
      <div className="flex flex-col gap-1">
        <p className="flex items-center gap-2 text-[17px] font-semibold text-[#1E293B]">
          {label}
          <ArrowRight
            className="size-4 text-[#0EA5E9] transition-transform group-hover:translate-x-0.5"
            aria-hidden
          />
        </p>
        <p className="text-[14px] text-[#64748B]">{description}</p>
      </div>
    </Link>
  );
}
