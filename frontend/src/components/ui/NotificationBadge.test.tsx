import { render } from "@testing-library/react";
import { NotificationBadge } from "./NotificationBadge";

describe("NotificationBadge", () => {
  it("renders count correctly", () => {
    const { getByText } = render(<NotificationBadge count={5} />);
    expect(getByText("5")).toBeInTheDocument();
  });

  it('shows "+" when count exceeds maxCount', () => {
    const { getByText } = render(
      <NotificationBadge count={150} maxCount={99} />,
    );
    expect(getByText("99+")).toBeInTheDocument();
  });

  it("does not render when count is 0 and showZero is false", () => {
    const { container } = render(<NotificationBadge count={0} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders with children correctly", () => {
    const { getByText } = render(
      <NotificationBadge count={3}>
        <button>Notifications</button>
      </NotificationBadge>,
    );
    expect(getByText("Notifications")).toBeInTheDocument();
    expect(getByText("3")).toBeInTheDocument();
  });

  it("applies correct variant styles", () => {
    const { getByText } = render(
      <NotificationBadge count={1} variant="success" />,
    );
    const badge = getByText("1");
    expect(badge).toHaveClass("bg-green-500");
  });
});
