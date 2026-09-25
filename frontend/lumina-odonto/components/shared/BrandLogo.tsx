import { cn } from "@/lib/utils";

type BrandLogoProps = {
  tone?: "light" | "dark";
  className?: string;
};

export default function BrandLogo({ tone = "light", className }: BrandLogoProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-start text-3xl leading-none font-bold",
        tone === "light" ? "text-white" : "text-[#1E293B]",
        className,
      )}
    >
      Lumina
      <span
        className={cn(
          "mt-1 text-xs font-light tracking-wide",
          tone === "dark" && "text-[#0EA5E9]",
        )}
      >
        ODONTO
      </span>
    </div>
  );
}
