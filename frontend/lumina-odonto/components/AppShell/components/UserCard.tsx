import RoleBadge from "@/components/shared/RoleBadge";
import type { AuthUser } from "@/types/auth";

export default function UserCard({
  user,
  initials,
}: {
  user: AuthUser;
  initials: string;
}) {
  return (
    <div className="flex items-center gap-3">
      <div
        aria-hidden
        className="flex size-10 shrink-0 items-center justify-center rounded-full bg-[#0EA5E9] text-sm font-semibold text-white"
      >
        {initials}
      </div>
      <div className="flex min-w-0 flex-col gap-1">
        <p className="truncate text-[14px] font-medium text-[#1E293B]" title={user.full_name}>
          {user.full_name}
        </p>
        <RoleBadge role={user.role} />
      </div>
    </div>
  );
}
