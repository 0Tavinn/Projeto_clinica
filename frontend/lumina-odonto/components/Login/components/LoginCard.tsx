import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";

export default function LoginCard({ children }: { children: React.ReactNode }) {
  return (
    <Card className="w-[440px] gap-0 rounded-[24px] border-0 pt-[52px] pb-[20px] ring-0 shadow-[0px_14px_30px_0px_rgba(15,23,42,0.09)] [--card-spacing:44px]">
      <CardHeader className="gap-[9px]">
        <CardTitle className="text-[26px] font-semibold text-[#1E293B]">
          Lumina Odonto
        </CardTitle>
        <CardDescription className="text-[15px] text-[#64748B]">
          Acesse a gestão da sua clínica
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-[54px]">
        <div className="flex flex-col gap-[8px]">
          <h2 className="text-[30px] font-semibold text-[#1E293B]">
            Boas-vindas
          </h2>
          <p className="text-[15px] text-[#64748B]">
            Informe suas credenciais para continuar.
          </p>
        </div>
        {children}
      </CardContent>
    </Card>
  );
}
