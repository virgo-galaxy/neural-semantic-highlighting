interface ButtonProps {
  label: string;
  disabled?: boolean;
}

function Button({ label, disabled }: ButtonProps) {
  return (
    <button disabled={disabled} aria-label={label}>
      {label}
    </button>
  );
}
