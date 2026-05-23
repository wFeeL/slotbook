import type { BranchRead } from '@/shared/api/types';
import { Card } from '@/shared/ui/Card';

interface Props {
  branch: BranchRead;
  onSelect: () => void;
}

export function BranchCard({ branch, onSelect }: Props) {
  return (
    <Card interactive surface="shell" onClick={onSelect} role="button" tabIndex={0}>
      <div className="flex flex-col gap-1">
        <span className="text-lg font-semibold text-ink">{branch.name}</span>
        {branch.address && (
          <span className="text-sm text-sienna-deep">{branch.address}</span>
        )}
      </div>
    </Card>
  );
}
