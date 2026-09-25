type PageHeaderProps = {
  title: string;
  description?: string;
  actions?: React.ReactNode;
};

export default function PageHeader({ title, description, actions }: PageHeaderProps) {
  return (
    <header className="flex flex-wrap items-end justify-between gap-4">
      <div className="flex flex-col gap-1">
        <h1 className="text-[26px] font-semibold text-[#1E293B]">{title}</h1>
        {description && (
          <p className="text-[15px] text-[#64748B]">{description}</p>
        )}
      </div>
      {actions}
    </header>
  );
}
