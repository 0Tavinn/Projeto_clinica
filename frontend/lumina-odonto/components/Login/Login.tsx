"use client";

import { useLoginViewModel } from "./Login.viewmodel";
import LoginView from "./Login.view";

export default function Login() {
  const viewModel = useLoginViewModel();
  return <LoginView {...viewModel} />;
}
