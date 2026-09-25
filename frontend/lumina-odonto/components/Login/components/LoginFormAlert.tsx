import { CircleAlert } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

export default function LoginFormAlert({ message }: { message: string | null }) {
  if (!message) return null;

  return (
    <Alert
      variant="destructive"
      className="mt-[28px] rounded-[10px] border-[#FECACA] bg-[#FEF2F2] px-4 py-3"
    >
      <CircleAlert aria-hidden />
      <AlertDescription className="text-[14px]">{message}</AlertDescription>
    </Alert>
  );
}
