import { FieldGroup } from "@/components/ui/field";
import type { LoginViewModel } from "../Login.viewmodel";
import LoginFormAlert from "./LoginFormAlert";
import LoginSubmitButton from "./LoginSubmitButton";
import LoginTextField from "./LoginTextField";

export default function LoginForm({
  values,
  fieldErrors,
  formError,
  isSubmitting,
  setField,
  submit,
}: LoginViewModel) {
  return (
    <form onSubmit={submit} noValidate className="mt-[52px]">
      <FieldGroup className="gap-[24px]">
        <LoginTextField
          id="login-email"
          name="username"
          label="E-mail"
          type="email"
          autoComplete="email"
          placeholder="seuemail@clinica.com"
          value={values.username}
          error={fieldErrors.username}
          disabled={isSubmitting}
          onValueChange={(value) => setField("username", value)}
        />
        <LoginTextField
          id="login-password"
          name="password"
          label="Senha"
          type="password"
          autoComplete="current-password"
          placeholder="••••••••••"
          value={values.password}
          error={fieldErrors.password}
          disabled={isSubmitting}
          onValueChange={(value) => setField("password", value)}
        />
      </FieldGroup>
      <LoginFormAlert message={formError} />
      <LoginSubmitButton isSubmitting={isSubmitting} />
    </form>
  );
}
