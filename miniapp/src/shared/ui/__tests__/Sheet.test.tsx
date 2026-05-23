import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Sheet } from '../Sheet';

describe('Sheet', () => {
  it('does not render content when closed', () => {
    render(
      <Sheet open={false} onClose={() => {}}>
        hello
      </Sheet>,
    );
    expect(screen.queryByText('hello')).not.toBeInTheDocument();
  });

  it('renders content when open', () => {
    render(
      <Sheet open onClose={() => {}}>
        hello
      </Sheet>,
    );
    expect(screen.getByText('hello')).toBeInTheDocument();
  });

  it('calls onClose when backdrop clicked', async () => {
    const onClose = vi.fn();
    render(
      <Sheet open onClose={onClose}>
        hi
      </Sheet>,
    );
    await userEvent.click(screen.getByTestId('sheet-backdrop'));
    expect(onClose).toHaveBeenCalled();
  });
});
