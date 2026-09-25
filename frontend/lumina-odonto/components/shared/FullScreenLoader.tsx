import { Spinner } from "@/components/ui/spinner";

export default function FullScreenLoader({
  label = "Carregando…",
}: {
  label?: string;
}) {
  return (
    <div className="flex min-h-screen w-full flex-col items-center justify-center gap-3 text-[#64748B]">
      <Spinner className="size-6 text-[#0EA5E9]" aria-label={label} />
      <p className="text-sm">{label}</p>
    </div>
  );
}
