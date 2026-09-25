import { Construction } from "lucide-react";
import PageHeader from "./PageHeader";

type PagePlaceholderProps = {
  title: string;
  description: string;
};

// Página ainda não implementada nesta sprint.
export default function PagePlaceholder({ title, description }: PagePlaceholderProps) {
  return (
    <div className="flex flex-col gap-8">
      <PageHeader title={title} description={description} />
      <div className="flex flex-col items-center gap-3 rounded-[24px] border border-dashed border-[#E2E7ED] bg-white px-6 py-16 text-center">
        <Construction className="size-8 text-[#0EA5E9]" aria-hidden />
        <p className="text-[15px] font-medium text-[#1E293B]">Em construção</p>
        <p className="max-w-sm text-sm text-[#64748B]">
          Esta tela chega nas próximas entregas.
        </p>
      </div>
    </div>
  );
}
