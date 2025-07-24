import { render } from "@testing-library/react";
import { UserAvatar } from "./UserAvatar";

describe("UserAvatar", () => {
  it("renders initials when no image provided", () => {
    const { getByText } = render(<UserAvatar name="John Doe" />);
    expect(getByText("JD")).toBeInTheDocument();
  });

  it("displays status indicator when status is provided", () => {
    const { container } = render(
      <UserAvatar name="Jane Smith" status="online" />,
    );
    const statusIndicator = container.querySelector(".bg-green-500");
    expect(statusIndicator).toBeInTheDocument();
  });

  it("applies correct size classes", () => {
    const { container } = render(<UserAvatar name="Test User" size="lg" />);
    const avatar = container.querySelector(".w-12.h-12");
    expect(avatar).toBeInTheDocument();
  });
});
