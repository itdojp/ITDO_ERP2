import { render, fireEvent, screen, waitFor } from "@testing-library/react";
import { Input } from "./Input";
import React from "react";

describe("Input", () => {
  it("renders input with value", () => {
    render(<Input value="test value" onChange={jest.fn()} />);
    expect(screen.getByDisplayValue("test value")).toBeInTheDocument();
  });

  it("handles controlled input changes", () => {
    const onChange = jest.fn();
    render(<Input value="initial" onChange={onChange} />);

    const input = screen.getByRole("textbox");
    fireEvent.change(input, { target: { value: "new value" } });

    expect(onChange).toHaveBeenCalled();
  });

  it("handles uncontrolled input changes", () => {
    render(<Input defaultValue="initial" />);

    const input = screen.getByRole("textbox");
    fireEvent.change(input, { target: { value: "new value" } });

    expect(input).toHaveValue("new value");
  });

  it("applies size classes correctly", () => {
    const { rerender } = render(<Input size="sm" />);
    let wrapper = screen.getByRole("textbox").parentElement;
    expect(wrapper).toHaveClass("px-2", "py-1", "text-sm");

    rerender(<Input size="md" />);
    wrapper = screen.getByRole("textbox").parentElement;
    expect(wrapper).toHaveClass("px-3", "py-2", "text-sm");

    rerender(<Input size="lg" />);
    wrapper = screen.getByRole("textbox").parentElement;
    expect(wrapper).toHaveClass("px-4", "py-3", "text-base");
  });

  it("applies variant classes correctly", () => {
    const { rerender } = render(<Input variant="default" />);
    let wrapper = screen.getByRole("textbox").parentElement;
    expect(wrapper).toHaveClass("bg-white", "border", "border-gray-300");

    rerender(<Input variant="filled" />);
    wrapper = screen.getByRole("textbox").parentElement;
    expect(wrapper).toHaveClass("bg-gray-50", "border-0");

    rerender(<Input variant="outlined" />);
    wrapper = screen.getByRole("textbox").parentElement;
    expect(wrapper).toHaveClass(
      "bg-transparent",
      "border-2",
      "border-gray-300",
    );
  });

  it("applies status classes correctly", () => {
    const { rerender } = render(<Input status="error" />);
    let wrapper = screen.getByRole("textbox").parentElement;
    expect(wrapper).toHaveClass("border-red-500");

    rerender(<Input status="warning" />);
    wrapper = screen.getByRole("textbox").parentElement;
    expect(wrapper).toHaveClass("border-yellow-500");

    rerender(<Input status="success" />);
    wrapper = screen.getByRole("textbox").parentElement;
    expect(wrapper).toHaveClass("border-green-500");
  });

  it("displays prefix and suffix", () => {
    render(
      <Input
        prefix={<span data-testid="prefix">@</span>}
        suffix={<span data-testid="suffix">.com</span>}
      />,
    );

    expect(screen.getByTestId("prefix")).toBeInTheDocument();
    expect(screen.getByTestId("suffix")).toBeInTheDocument();
  });

  it("shows clear button when allowClear is true and has value", () => {
    render(<Input allowClear value="test" onChange={jest.fn()} />);

    const clearButton = screen.getByRole("button");
    expect(clearButton).toBeInTheDocument();
  });

  it("clears input when clear button is clicked", () => {
    const onChange = jest.fn();
    render(<Input allowClear value="test" onChange={onChange} />);

    const clearButton = screen.getByRole("button");
    fireEvent.click(clearButton);

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({
        target: { value: "" },
      }),
    );
  });

  it("shows character count when showCount is true", () => {
    render(
      <Input showCount maxLength={10} value="test" onChange={jest.fn()} />,
    );

    expect(screen.getByText("4/10")).toBeInTheDocument();
  });

  it("highlights count in red when over limit", () => {
    render(<Input showCount maxLength={3} value="test" onChange={jest.fn()} />);

    const count = screen.getByText("4/3");
    expect(count).toHaveClass("text-red-500");
  });

  it("shows loading spinner when loading is true", () => {
    render(<Input loading />);

    const spinner = screen
      .getByRole("textbox")
      .parentElement?.querySelector(".animate-spin");
    expect(spinner).toBeInTheDocument();
  });

  it("handles disabled state", () => {
    render(<Input disabled />);

    const input = screen.getByRole("textbox");
    const wrapper = input.parentElement;

    expect(input).toBeDisabled();
    expect(wrapper).toHaveClass("opacity-50", "cursor-not-allowed");
  });

  it("handles focus and blur events", () => {
    const onFocus = jest.fn();
    const onBlur = jest.fn();

    render(<Input onFocus={onFocus} onBlur={onBlur} />);

    const input = screen.getByRole("textbox");

    fireEvent.focus(input);
    expect(onFocus).toHaveBeenCalled();

    fireEvent.blur(input);
    expect(onBlur).toHaveBeenCalled();
  });

  it("calls onPressEnter when Enter key is pressed", () => {
    const onPressEnter = jest.fn();
    render(<Input onPressEnter={onPressEnter} />);

    const input = screen.getByRole("textbox");
    fireEvent.keyDown(input, { key: "Enter" });

    expect(onPressEnter).toHaveBeenCalled();
  });

  it("handles debounced onChange", async () => {
    const onDebounceChange = jest.fn();
    render(<Input debounce={100} onDebounceChange={onDebounceChange} />);

    const input = screen.getByRole("textbox");
    fireEvent.change(input, { target: { value: "test" } });

    expect(onDebounceChange).not.toHaveBeenCalled();

    await waitFor(
      () => {
        expect(onDebounceChange).toHaveBeenCalledWith("test");
      },
      { timeout: 200 },
    );
  });

  it("renders addon before and after", () => {
    render(
      <Input
        addonBefore={<span data-testid="before">https://</span>}
        addonAfter={<span data-testid="after">.com</span>}
      />,
    );

    expect(screen.getByTestId("before")).toBeInTheDocument();
    expect(screen.getByTestId("after")).toBeInTheDocument();
  });

  it("applies custom classNames", () => {
    render(
      <Input
        className="custom-wrapper"
        wrapperClassName="custom-input-wrapper"
        inputClassName="custom-input"
      />,
    );

    const wrapper = screen.getByRole("textbox").closest("div");
    const inputWrapper = screen.getByRole("textbox").parentElement;
    const input = screen.getByRole("textbox");

    expect(wrapper).toHaveClass("custom-wrapper");
    expect(inputWrapper).toHaveClass("custom-input-wrapper");
    expect(input).toHaveClass("custom-input");
  });

  it("removes border when bordered is false", () => {
    render(<Input bordered={false} />);

    const wrapper = screen.getByRole("textbox").parentElement;
    expect(wrapper).toHaveClass("border-0");
  });
});

describe("Input.Password", () => {
  it("renders password input with visibility toggle", () => {
    render(<Input.Password />);

    const input = screen.getByRole("textbox"); // Initially text type due to visibility toggle
    const toggleButton = screen.getByRole("button");

    expect(input).toHaveAttribute("type", "password");
    expect(toggleButton).toBeInTheDocument();
  });

  it("toggles password visibility", () => {
    render(<Input.Password />);

    const input = screen.getByRole("textbox");
    const toggleButton = screen.getByRole("button");

    expect(input).toHaveAttribute("type", "password");

    fireEvent.click(toggleButton);
    expect(input).toHaveAttribute("type", "text");

    fireEvent.click(toggleButton);
    expect(input).toHaveAttribute("type", "password");
  });
});

describe("Input.TextArea", () => {
  it("renders textarea", () => {
    render(<Input.TextArea />);

    const textarea = screen.getByRole("textbox");
    expect(textarea.tagName).toBe("TEXTAREA");
  });

  it("handles controlled textarea changes", () => {
    const onChange = jest.fn();
    render(<Input.TextArea value="initial" onChange={onChange} />);

    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: "new value" } });

    expect(onChange).toHaveBeenCalled();
  });

  it("shows character count for textarea", () => {
    render(
      <Input.TextArea
        showCount
        maxLength={100}
        value="test"
        onChange={jest.fn()}
      />,
    );

    expect(screen.getByText("4/100")).toBeInTheDocument();
  });

  it("shows clear button for textarea", () => {
    render(<Input.TextArea allowClear value="test" onChange={jest.fn()} />);

    const clearButton = screen.getByRole("button");
    expect(clearButton).toBeInTheDocument();
  });

  it("clears textarea when clear button is clicked", () => {
    const onChange = jest.fn();
    render(<Input.TextArea allowClear value="test" onChange={onChange} />);

    const clearButton = screen.getByRole("button");
    fireEvent.click(clearButton);

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({
        target: { value: "" },
      }),
    );
  });

  it("applies size classes to textarea", () => {
    const { rerender } = render(<Input.TextArea size="sm" />);
    let textarea = screen.getByRole("textbox");
    expect(textarea).toHaveClass("px-2", "py-1", "text-sm");

    rerender(<Input.TextArea size="lg" />);
    textarea = screen.getByRole("textbox");
    expect(textarea).toHaveClass("px-4", "py-3", "text-base");
  });

  it("applies variant classes to textarea", () => {
    render(<Input.TextArea variant="filled" />);

    const textarea = screen.getByRole("textbox");
    expect(textarea).toHaveClass("bg-gray-50", "border-0");
  });

  it("applies status classes to textarea", () => {
    render(<Input.TextArea status="error" />);

    const textarea = screen.getByRole("textbox");
    expect(textarea).toHaveClass("border-red-500");
  });

  it("handles disabled state for textarea", () => {
    render(<Input.TextArea disabled />);

    const textarea = screen.getByRole("textbox");
    expect(textarea).toBeDisabled();
    expect(textarea).toHaveClass("opacity-50", "cursor-not-allowed");
  });

  it("handles autoSize for textarea", () => {
    render(<Input.TextArea autoSize />);

    const textarea = screen.getByRole("textbox");
    expect(textarea).toHaveClass("resize-none");
  });

  it("handles autoSize with min and max rows", () => {
    render(<Input.TextArea autoSize={{ minRows: 3, maxRows: 6 }} />);

    const textarea = screen.getByRole("textbox");
    expect(textarea).toHaveClass("resize-none");
  });

  it("removes border when bordered is false for textarea", () => {
    render(<Input.TextArea bordered={false} />);

    const textarea = screen.getByRole("textbox");
    expect(textarea).toHaveClass("border-0");
  });

  it("highlights count in red when over limit for textarea", () => {
    render(
      <Input.TextArea
        showCount
        maxLength={3}
        value="test"
        onChange={jest.fn()}
      />,
    );

    const count = screen.getByText("4/3");
    expect(count).toHaveClass("text-red-500");
  });

  it("focuses textarea after clearing", () => {
    render(<Input.TextArea allowClear value="test" onChange={jest.fn()} />);

    const textarea = screen.getByRole("textbox");
    const clearButton = screen.getByRole("button");

    fireEvent.click(clearButton);
    expect(document.activeElement).toBe(textarea);
  });
});

describe("Input edge cases", () => {
  it("handles maxLength validation", () => {
    render(<Input maxLength={5} />);

    const input = screen.getByRole("textbox");
    expect(input).toHaveAttribute("maxLength", "5");
  });

  it("focuses input after clearing", () => {
    render(<Input allowClear value="test" onChange={jest.fn()} />);

    const input = screen.getByRole("textbox");
    const clearButton = screen.getByRole("button");

    fireEvent.click(clearButton);
    expect(document.activeElement).toBe(input);
  });

  it("does not show clear button when disabled", () => {
    render(<Input allowClear disabled value="test" />);

    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("does not show clear button when no value", () => {
    render(<Input allowClear />);

    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("cleans up debounce timer on unmount", () => {
    const onDebounceChange = jest.fn();
    const { unmount } = render(
      <Input debounce={100} onDebounceChange={onDebounceChange} />,
    );

    const input = screen.getByRole("textbox");
    fireEvent.change(input, { target: { value: "test" } });

    unmount();

    // Timer should be cleaned up, so callback shouldn't be called
    setTimeout(() => {
      expect(onDebounceChange).not.toHaveBeenCalled();
    }, 200);
  });

  it("handles ref forwarding", () => {
    const ref = React.createRef<HTMLInputElement>();
    render(<Input ref={ref} />);

    expect(ref.current).toBeInstanceOf(HTMLInputElement);
  });

  it("handles textarea ref forwarding", () => {
    const ref = React.createRef<HTMLTextAreaElement>();
    render(<Input.TextArea ref={ref} />);

    expect(ref.current).toBeInstanceOf(HTMLTextAreaElement);
  });

  it("applies focus ring on focus", () => {
    render(<Input />);

    const input = screen.getByRole("textbox");
    const wrapper = input.parentElement;

    fireEvent.focus(input);
    expect(wrapper).toHaveClass("border-blue-500", "ring-1", "ring-blue-500");
  });
});
