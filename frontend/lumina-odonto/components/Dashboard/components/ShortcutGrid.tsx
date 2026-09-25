import type { NavItem } from "@/lib/auth/navigation";
import ShortcutCard from "./ShortcutCard";

export default function ShortcutGrid({ shortcuts }: { shortcuts: NavItem[] }) {
  return (
    <section aria-labelledby="shortcuts-title" className="flex flex-col gap-4">
      <h2 id="shortcuts-title" className="text-[17px] font-semibold text-[#1E293B]">
        Acesso rápido
      </h2>
      <div className="grid gap-5 sm:grid-cols-2">
        {shortcuts.map((shortcut) => (
          <ShortcutCard key={shortcut.href} {...shortcut} />
        ))}
      </div>
    </section>
  );
}
