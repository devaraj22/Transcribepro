interface Props {
  percent: number;
  visible: boolean;
  label?: string;
}

export default function ProgressBar({ percent, visible, label }: Props) {
  if (!visible) return null;
  return (
    <div className="progress-track" role="progressbar" aria-valuenow={percent} aria-valuemin={0} aria-valuemax={100}>
      <div className="progress-fill" style={{ width: `${percent}%` }} />
      <span className="progress-label">{label ?? `${Math.round(percent)}%`}</span>
    </div>
  );
}
