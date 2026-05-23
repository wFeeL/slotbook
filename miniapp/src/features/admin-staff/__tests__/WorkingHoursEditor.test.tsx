// miniapp/src/features/admin-staff/__tests__/WorkingHoursEditor.test.tsx
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { WorkingHoursEditor } from '../WorkingHoursEditor';

describe('WorkingHoursEditor', () => {
  it('initializes with 7 rows (Mon..Sun)', () => {
    render(<WorkingHoursEditor initial={[]} onSave={() => {}} saving={false} />);
    // Look for weekday labels — at least Mon (Пн) and Sun (Вс)
    expect(screen.getByText('Пн')).toBeInTheDocument();
    expect(screen.getByText('Вс')).toBeInTheDocument();
  });

  it('hydrates from initial entries', () => {
    render(
      <WorkingHoursEditor
        initial={[{ weekday: 1, start_time: '10:00:00', end_time: '18:00:00', is_active: true }]}
        onSave={() => {}}
        saving={false}
      />,
    );
    const startInputs = screen.getAllByDisplayValue('10:00');
    expect(startInputs.length).toBeGreaterThan(0);
  });

  it('calls onSave with active rows only', async () => {
    let captured: any = null;
    render(
      <WorkingHoursEditor
        initial={[{ weekday: 1, start_time: '10:00:00', end_time: '18:00:00', is_active: true }]}
        onSave={(entries) => {
          captured = entries;
        }}
        saving={false}
      />,
    );
    await userEvent.click(screen.getByRole('button', { name: /Сохранить/ }));
    expect(captured).toBeDefined();
    expect(captured.length).toBeGreaterThan(0);
    expect(captured[0].is_active).toBe(true);
  });
});
