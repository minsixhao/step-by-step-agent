interface LoadingDotsProps {
  className?: string;
}

export default function LoadingDots({ className = '' }: LoadingDotsProps) {
  return (
    <div className={`flex gap-1 items-center ${className}`}>
      <span className="bounce-dot" />
      <span className="bounce-dot" />
      <span className="bounce-dot" />
    </div>
  );
}
