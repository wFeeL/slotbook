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

  it('locks body scroll when open', () => {
    document.body.style.overflow = '';
    const { rerender } = render(
      <Sheet open={true} onClose={() => {}}>
        hi
      </Sheet>,
    );
    expect(document.body.style.overflow).toBe('hidden');
    rerender(
      <Sheet open={false} onClose={() => {}}>
        hi
      </Sheet>,
    );
    expect(document.body.style.overflow).toBe('');
  });

  it('labels the dialog with the title when provided', () => {
    render(
      <Sheet open onClose={() => {}} title="Hello">
        body
      </Sheet>,
    );
    const dialog = screen.getByRole('dialog');
    const labelId = dialog.getAttribute('aria-labelledby');
    expect(labelId).toBeTruthy();
    expect(document.getElementById(labelId!)?.textContent).toBe('Hello');
  });
});
