"use client";

import { useRef, useState, type FormEvent } from "react";
import { useSession } from "@/providers/session/session.context";
import { authService } from "@/services/Login/Login.service";
import {
  INITIAL_LOGIN_VALUES,
  mapLoginError,
  validateLoginForm,
  type LoginField,
  type LoginFieldErrors,
} from "./Login.model";

export function useLoginViewModel() {
  const { setUser } = useSession();
  const [values, setValues] = useState(INITIAL_LOGIN_VALUES);
  const [fieldErrors, setFieldErrors] = useState<LoginFieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  // Ref evita duplo submit antes do re-render que desabilita o botão.
  const submittingRef = useRef(false);

  function setField(field: LoginField, value: string) {
    setValues((current) => ({ ...current, [field]: value }));
    setFieldErrors((current) => ({ ...current, [field]: undefined }));
    setFormError(null);
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (submittingRef.current) return;

    const validation = validateLoginForm(values);
    if (!validation.success) {
      setFieldErrors(validation.fieldErrors);
      return;
    }

    submittingRef.current = true;
    setIsSubmitting(true);
    setFormError(null);
    try {
      const user = await authService.signIn(validation.data);
      // O GuestGuard redireciona para a home do perfil assim que a sessão fica autenticada.
      setUser(user);
    } catch (error) {
      const { formError, fieldErrors } = mapLoginError(error);
      setFormError(formError);
      setFieldErrors(fieldErrors);
      setValues((current) => ({ ...current, password: "" }));
    } finally {
      submittingRef.current = false;
      setIsSubmitting(false);
    }
  }

  return { values, fieldErrors, formError, isSubmitting, setField, submit };
}

export type LoginViewModel = ReturnType<typeof useLoginViewModel>;
