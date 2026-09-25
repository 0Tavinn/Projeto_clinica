import { LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function LogoutButton({ onLogout }: { onLogout: () => void }) {
  return (
    <Button
      type="button"
      variant="outline"
      onClick={onLogout}
      className="h-[40px] w-full justify-start gap-3 rounded-[10px] border-[#E2E7ED] px-3 text-[14px] text-[#64748B] hover:text-[#1E293B]"
    >
      <LogOut aria-hidden />
      Sair
    </Button>
  );
}
