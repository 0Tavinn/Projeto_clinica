import type { AppShellViewModel } from "../AppShell.viewmodel";
import SidebarNavItem from "./SidebarNavItem";

export default function SidebarNav({ items }: { items: AppShellViewModel["navItems"] }) {
  return (
    <nav aria-label="Menu principal">
      <ul className="flex flex-col gap-1">
        {items.map((item) => (
          <li key={item.href}>
            <SidebarNavItem
              href={item.href}
              label={item.label}
              icon={item.icon}
              active={item.active}
            />
          </li>
        ))}
      </ul>
    </nav>
  );
}
