interface Props {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

export default function TextEditor({ value, onChange, placeholder }: Props) {
  return (
    <textarea
      className="text-editor"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder ?? "Your transcript will appear here..."}
      rows={12}
    />
  );
}
