import Link from "next/link";
import { ShieldAlert } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export default function AccessDenied({ homeRoute }: { homeRoute: string }) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-[24px] bg-white px-6 py-16 text-center shadow-[0px_14px_30px_0px_rgba(15,23,42,0.06)]">
      <ShieldAlert className="size-9 text-[#0EA5E9]" aria-hidden />
      <h1 className="text-[22px] font-semibold text-[#1E293B]">Acesso negado</h1>
      <p className="max-w-sm text-[15px] text-[#64748B]">
        Seu perfil não tem permissão para acessar esta página.
      </p>
      <Link
        href={homeRoute}
        className={cn(
          buttonVariants(),
          "mt-3 h-[44px] rounded-[10px] bg-[#0EA5E9] px-5 text-[15px] font-semibold text-white hover:bg-[#0284C7]",
        )}
      >
        Voltar ao início
      </Link>
    </div>
  );
}
