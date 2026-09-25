import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";

export default function LoginSubmitButton({ isSubmitting }: { isSubmitting: boolean }) {
  return (
    <Button
      type="submit"
      disabled={isSubmitting}
      aria-busy={isSubmitting}
      className="mt-[30px] h-[56px] w-full rounded-[10px] bg-[#0EA5E9] text-[16px] font-semibold text-white"
    >
      {isSubmitting && <Spinner aria-hidden className="size-5" />}
      {isSubmitting ? "Entrando…" : "Entrar"}
    </Button>
  );
}
