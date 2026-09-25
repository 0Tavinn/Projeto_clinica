import { Field, FieldError, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";

type LoginTextFieldProps = Omit<React.ComponentProps<"input">, "onChange"> & {
  id: string;
  label: string;
  value: string;
  error?: string;
  onValueChange: (value: string) => void;
};

export default function LoginTextField({
  id,
  label,
  error,
  onValueChange,
  ...inputProps
}: LoginTextFieldProps) {
  const errorId = `${id}-error`;

  return (
    <Field className="gap-[11px]" data-invalid={Boolean(error)}>
      <FieldLabel htmlFor={id} className="text-[14px] font-medium text-[#1E293B]">
        {label}
      </FieldLabel>
      <Input
        id={id}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? errorId : undefined}
        onChange={(event) => onValueChange(event.target.value)}
        className="h-[52px] rounded-[10px] border-[#E2E7ED] px-4 text-[15px] placeholder:text-[#64748B] md:text-[15px]"
        {...inputProps}
      />
      <FieldError id={errorId} className="-mt-[4px] text-[13px]">
        {error}
      </FieldError>
    </Field>
  );
}
