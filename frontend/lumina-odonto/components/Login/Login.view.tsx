import LoginCard from "./components/LoginCard";
import LoginForm from "./components/LoginForm";
import LoginHero from "./components/LoginHero";
import type { LoginViewModel } from "./Login.viewmodel";

export default function LoginView(viewModel: LoginViewModel) {
  return (
    <section className="w-full h-screen flex">
      <LoginHero />
      <div className="w-1/2 flex flex-col items-center justify-center">
        <LoginCard>
          <LoginForm {...viewModel} />
        </LoginCard>
      </div>
    </section>
  );
}
