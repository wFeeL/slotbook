import { Card } from '@/shared/ui/Card';
import type { StaffRead } from '@/shared/api/types';

interface Props {
  staff: StaffRead;
  onSelect: () => void;
}

export function StaffCard({ staff, onSelect }: Props) {
  return (
    <Card interactive onClick={onSelect} role="button" tabIndex={0}>
      <div className="flex items-center gap-4">
        <div
          className="w-12 h-12 rounded-full bg-sand text-ink flex items-center justify-center text-lg font-semibold"
          aria-hidden
        >
          {staff.name[0]}
        </div>
        <div className="flex flex-col">
          <span className="text-lg font-semibold text-ink">{staff.name}</span>
          {staff.description && <span className="text-sm text-sienna-deep">{staff.description}</span>}
        </div>
      </div>
    </Card>
  );
}
