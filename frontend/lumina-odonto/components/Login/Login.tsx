import LoginCard from "./components/LoginCard";

export default function Login() {
  return (
    <>
      <section className="w-full h-screen flex">
        <div className="bg-[#0EA5E9] w-1/2 p-28 flex flex-col relative overflow-hidden">
          <div
            aria-hidden
            className="pointer-events-none absolute left-[70px] top-[85px] size-[360px] rounded-full bg-[#C7EBFA] opacity-25"
          />
          <div
            aria-hidden
            className="pointer-events-none absolute left-[330px] top-[470px] size-[420px] rounded-full bg-white opacity-[0.13]"
          />
          <div className="relative z-10 ">
            <h1 className="flex flex-col items-start text-3xl font-bold text-white">
              Lumina
              <span className="text-xs font-light">ODONTO</span>
            </h1>
          </div>
          <div className="relative z-10 flex flex-col gap-[20px] text-white mt-[140px]">
            <h1 className="text-5xl font-bold">
              Cuidado inteligente para cada sorriso.
            </h1>
            <p className="text-md font-light">
              Gestão simples, segura e próxima da sua clínica.
            </p>
          </div>
        </div>
        <div className="w-1/2 flex flex-col items-center justify-center">
          <LoginCard />
        </div>
      </section>
    </>
  );
}
