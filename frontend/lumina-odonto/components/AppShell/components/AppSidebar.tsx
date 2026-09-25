import BrandLogo from "@/components/shared/BrandLogo";
import type { AppShellViewModel } from "../AppShell.viewmodel";
import LogoutButton from "./LogoutButton";
import SidebarNav from "./SidebarNav";
import UserCard from "./UserCard";

export default function AppSidebar({
  user,
  initials,
  navItems,
  onLogout,
}: AppShellViewModel) {
  return (
    <aside className="sticky top-0 flex h-screen w-[264px] shrink-0 flex-col gap-10 border-r border-[#E2E7ED] bg-white px-5 py-8">
      <BrandLogo tone="dark" className="px-3 text-2xl" />
      <div className="flex-1">
        <SidebarNav items={navItems} />
      </div>
      {user && (
        <div className="flex flex-col gap-4 border-t border-[#E2E7ED] pt-5">
          <UserCard user={user} initials={initials} />
          <LogoutButton onLogout={onLogout} />
        </div>
      )}
    </aside>
  );
}
