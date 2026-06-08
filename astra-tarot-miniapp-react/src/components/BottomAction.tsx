interface BottomActionProps {
  primaryLabel: string;
  secondaryLabel?: string;
  disabled?: boolean;
  onPrimary: () => void;
  onSecondary?: () => void;
}

export function BottomAction({ primaryLabel, secondaryLabel, disabled = false, onPrimary, onSecondary }: BottomActionProps) {
  return (
    <div className="bottom-action">
      {secondaryLabel && onSecondary && (
        <button className="button button--ghost" type="button" onClick={onSecondary}>
          {secondaryLabel}
        </button>
      )}
      <button className="button button--primary" type="button" disabled={disabled} onClick={onPrimary}>
        {primaryLabel}
      </button>
    </div>
  );
}
