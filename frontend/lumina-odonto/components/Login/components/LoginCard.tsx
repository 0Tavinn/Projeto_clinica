import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Field, FieldLabel, FieldGroup } from "@/components/ui/field";

export default function LoginCard() {
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
          <h1 className="text-[30px] font-semibold text-[#1E293B]">
            Boas-vindas
          </h1>
          <p className="text-[15px] text-[#64748B]">
            Informe suas credenciais para continuar.
          </p>
        </div>
        <form action="" className="mt-[52px]">
          <FieldGroup className="gap-[24px]">
            <Field className="gap-[11px]">
              <FieldLabel className="text-[14px] font-medium text-[#1E293B]">
                E-mail
              </FieldLabel>
              <Input
                placeholder="seuemail@clinica.com"
                type="text"
                className="h-[52px] rounded-[10px] border-[#E2E7ED] px-4 text-[15px] placeholder:text-[#64748B] md:text-[15px]"
              />
            </Field>
            <Field className="gap-[11px]">
              <FieldLabel className="text-[14px] font-medium text-[#1E293B]">
                Senha
              </FieldLabel>
              <Input
                placeholder="••••••••••"
                type="password"
                className="h-[52px] rounded-[10px] border-[#E2E7ED] px-4 text-[15px] placeholder:text-[#64748B] md:text-[15px]"
              />
            </Field>
          </FieldGroup>
          <Button className="mt-[30px] h-[56px] w-full rounded-[10px] bg-[#0EA5E9] text-[16px] font-semibold text-white">
            Entrar
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
