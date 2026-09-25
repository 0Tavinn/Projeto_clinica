import AppSidebar from "./components/AppSidebar";
import type { AppShellViewModel } from "./AppShell.viewmodel";

export default function AppShellView({
  children,
  ...viewModel
}: AppShellViewModel & { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen w-full bg-[#F8FAFC]">
      <AppSidebar {...viewModel} />
      <main className="flex-1 px-12 py-10">
        <div className="mx-auto w-full max-w-[1080px]">{children}</div>
      </main>
    </div>
  );
}
