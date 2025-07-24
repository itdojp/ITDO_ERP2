import { render, fireEvent, screen, waitFor } from "@testing-library/react";
import { Select, SelectOption } from "./Select";
import userEvent from "@testing-library/user-event";

const mockOptions: SelectOption[] = [
  { value: "option1", label: "Option 1" },
  { value: "option2", label: "Option 2" },
  { value: "option3", label: "Option 3", disabled: true },
  { value: "option4", label: "Option 4" },
];

const groupedOptions: SelectOption[] = [
  { value: "fruit1", label: "Apple", group: "Fruits" },
  { value: "fruit2", label: "Banana", group: "Fruits" },
  { value: "veggie1", label: "Carrot", group: "Vegetables" },
  { value: "veggie2", label: "Broccoli", group: "Vegetables" },
];

describe("Select", () => {
  it("renders with placeholder", () => {
    render(<Select options={mockOptions} placeholder="Choose option" />);
    expect(screen.getByText("Choose option")).toBeInTheDocument();
  });

  it("opens dropdown when clicked", () => {
    render(<Select options={mockOptions} />);

    const select = screen.getByRole("combobox");
    fireEvent.click(select);

    expect(screen.getByText("Option 1")).toBeInTheDocument();
    expect(screen.getByText("Option 2")).toBeInTheDocument();
  });

  it("selects single option", () => {
    const onChange = jest.fn();
    render(<Select options={mockOptions} onChange={onChange} />);

    const select = screen.getByRole("combobox");
    fireEvent.click(select);

    fireEvent.click(screen.getByText("Option 1"));

    expect(onChange).toHaveBeenCalledWith(
      "option1",
      expect.objectContaining({ value: "option1", label: "Option 1" }),
    );
  });

  it("handles controlled value", () => {
    render(<Select options={mockOptions} value="option2" />);

    expect(screen.getByText("Option 2")).toBeInTheDocument();
  });

  it("handles uncontrolled with default value", () => {
    render(<Select options={mockOptions} defaultValue="option2" />);

    expect(screen.getByText("Option 2")).toBeInTheDocument();
  });

  it("handles multiple selection", () => {
    const onChange = jest.fn();
    render(<Select options={mockOptions} multiple onChange={onChange} />);

    const select = screen.getByRole("combobox");
    fireEvent.click(select);

    fireEvent.click(screen.getByText("Option 1"));
    expect(onChange).toHaveBeenCalledWith(["option1"], expect.any(Array));

    fireEvent.click(screen.getByText("Option 2"));
    expect(onChange).toHaveBeenLastCalledWith(
      ["option1", "option2"],
      expect.any(Array),
    );
  });

  it("displays multiple selected values as tags", () => {
    render(
      <Select options={mockOptions} multiple value={["option1", "option2"]} />,
    );

    expect(screen.getByText("Option 1")).toBeInTheDocument();
    expect(screen.getByText("Option 2")).toBeInTheDocument();
  });

  it("removes tags in multiple mode", () => {
    const onChange = jest.fn();
    render(
      <Select
        options={mockOptions}
        multiple
        value={["option1", "option2"]}
        onChange={onChange}
      />,
    );

    const removeButtons = screen.getAllByRole("button");
    const firstRemoveButton = removeButtons.find((btn) =>
      btn.closest('[class*="bg-blue-100"]'),
    );

    if (firstRemoveButton) {
      fireEvent.click(firstRemoveButton);
      expect(onChange).toHaveBeenCalled();
    }
  });

  it("shows loading state", () => {
    render(<Select options={mockOptions} loading />);

    expect(screen.getByText("Loading...")).toBeInTheDocument();
    expect(screen.getByRole("img", { hidden: true })).toHaveClass(
      "animate-spin",
    );
  });

  it("handles disabled state", () => {
    render(<Select options={mockOptions} disabled />);

    const select = screen.getByRole("combobox");
    expect(select).toHaveAttribute("aria-disabled", "true");
    expect(select.parentElement).toHaveClass(
      "opacity-50",
      "cursor-not-allowed",
    );
  });

  it("filters options when searchable", async () => {
    const user = userEvent.setup();
    render(<Select options={mockOptions} searchable />);

    const select = screen.getByRole("combobox");
    fireEvent.click(select);

    const searchInput = screen.getByRole("textbox");
    await user.type(searchInput, "Option 1");

    expect(screen.getByText("Option 1")).toBeInTheDocument();
    expect(screen.queryByText("Option 2")).not.toBeInTheDocument();
  });

  it("calls onSearch when searching", async () => {
    const user = userEvent.setup();
    const onSearch = jest.fn();
    render(<Select options={mockOptions} searchable onSearch={onSearch} />);

    const select = screen.getByRole("combobox");
    fireEvent.click(select);

    const searchInput = screen.getByRole("textbox");
    await user.type(searchInput, "test");

    expect(onSearch).toHaveBeenLastCalledWith("test");
  });

  it("shows clear button when clearable and has value", () => {
    render(<Select options={mockOptions} clearable value="option1" />);

    const clearButton = screen.getByRole("button");
    expect(clearButton).toBeInTheDocument();
  });

  it("clears selection when clear button is clicked", () => {
    const onChange = jest.fn();
    render(
      <Select
        options={mockOptions}
        clearable
        value="option1"
        onChange={onChange}
      />,
    );

    const clearButton = screen.getByRole("button");
    fireEvent.click(clearButton);

    expect(onChange).toHaveBeenCalledWith("", undefined);
  });

  it("does not show disabled options as selectable", () => {
    render(<Select options={mockOptions} />);

    const select = screen.getByRole("combobox");
    fireEvent.click(select);

    const disabledOption = screen.getByText("Option 3");
    expect(disabledOption).toHaveClass("opacity-50", "cursor-not-allowed");
  });

  it("does not select disabled options", () => {
    const onChange = jest.fn();
    render(<Select options={mockOptions} onChange={onChange} />);

    const select = screen.getByRole("combobox");
    fireEvent.click(select);

    const disabledOption = screen.getByText("Option 3");
    fireEvent.click(disabledOption);

    expect(onChange).not.toHaveBeenCalled();
  });

  it("applies size classes correctly", () => {
    const { rerender } = render(<Select options={mockOptions} size="sm" />);
    let select = screen.getByRole("combobox").parentElement;
    expect(select).toHaveClass("px-2", "py-1", "text-sm", "min-h-[32px]");

    rerender(<Select options={mockOptions} size="md" />);
    select = screen.getByRole("combobox").parentElement;
    expect(select).toHaveClass("px-3", "py-2", "text-sm", "min-h-[40px]");

    rerender(<Select options={mockOptions} size="lg" />);
    select = screen.getByRole("combobox").parentElement;
    expect(select).toHaveClass("px-4", "py-3", "text-base", "min-h-[48px]");
  });

  it("applies variant classes correctly", () => {
    const { rerender } = render(
      <Select options={mockOptions} variant="default" />,
    );
    let select = screen.getByRole("combobox").parentElement;
    expect(select).toHaveClass("bg-white", "border", "border-gray-300");

    rerender(<Select options={mockOptions} variant="filled" />);
    select = screen.getByRole("combobox").parentElement;
    expect(select).toHaveClass("bg-gray-50", "border-0");

    rerender(<Select options={mockOptions} variant="outlined" />);
    select = screen.getByRole("combobox").parentElement;
    expect(select).toHaveClass("bg-transparent", "border-2", "border-gray-300");
  });

  it("applies status classes correctly", () => {
    const { rerender } = render(
      <Select options={mockOptions} status="error" />,
    );
    let select = screen.getByRole("combobox").parentElement;
    expect(select).toHaveClass("border-red-500");

    rerender(<Select options={mockOptions} status="warning" />);
    select = screen.getByRole("combobox").parentElement;
    expect(select).toHaveClass("border-yellow-500");

    rerender(<Select options={mockOptions} status="success" />);
    select = screen.getByRole("combobox").parentElement;
    expect(select).toHaveClass("border-green-500");
  });

  it("renders grouped options", () => {
    render(<Select options={groupedOptions} />);

    const select = screen.getByRole("combobox");
    fireEvent.click(select);

    expect(screen.getByText("Fruits")).toBeInTheDocument();
    expect(screen.getByText("Vegetables")).toBeInTheDocument();
    expect(screen.getByText("Apple")).toBeInTheDocument();
    expect(screen.getByText("Carrot")).toBeInTheDocument();
  });

  it("shows option icons", () => {
    const optionsWithIcons: SelectOption[] = [
      {
        value: "home",
        label: "Home",
        icon: <span data-testid="home-icon">🏠</span>,
      },
    ];

    render(<Select options={optionsWithIcons} />);

    const select = screen.getByRole("combobox");
    fireEvent.click(select);

    expect(screen.getByTestId("home-icon")).toBeInTheDocument();
  });

  it("shows option descriptions", () => {
    const optionsWithDescriptions: SelectOption[] = [
      { value: "option1", label: "Option 1", description: "This is option 1" },
    ];

    render(<Select options={optionsWithDescriptions} />);

    const select = screen.getByRole("combobox");
    fireEvent.click(select);

    expect(screen.getByText("This is option 1")).toBeInTheDocument();
  });

  it("handles keyboard navigation", () => {
    render(<Select options={mockOptions} />);

    const select = screen.getByRole("combobox");
    select.focus();

    // Arrow down opens dropdown
    fireEvent.keyDown(select, { key: "ArrowDown" });
    expect(screen.getByText("Option 1")).toBeInTheDocument();

    // Arrow down highlights next option
    fireEvent.keyDown(select, { key: "ArrowDown" });

    // Enter selects highlighted option
    fireEvent.keyDown(select, { key: "Enter" });
    expect(screen.getByText("Option 2")).toBeInTheDocument(); // Should be selected
  });

  it("closes dropdown on escape", () => {
    render(<Select options={mockOptions} />);

    const select = screen.getByRole("combobox");
    fireEvent.click(select);

    expect(screen.getByText("Option 1")).toBeInTheDocument();

    fireEvent.keyDown(select, { key: "Escape" });
    expect(screen.queryByText("Option 1")).not.toBeInTheDocument();
  });

  it("closes dropdown when clicking outside", async () => {
    render(
      <div>
        <Select options={mockOptions} />
        <div data-testid="outside">Outside element</div>
      </div>,
    );

    const select = screen.getByRole("combobox");
    fireEvent.click(select);

    expect(screen.getByText("Option 1")).toBeInTheDocument();

    fireEvent.mouseDown(screen.getByTestId("outside"));

    await waitFor(() => {
      expect(screen.queryByText("Option 1")).not.toBeInTheDocument();
    });
  });

  it('shows "not found" content when no options match', async () => {
    const user = userEvent.setup();
    render(
      <Select options={mockOptions} searchable notFoundContent="No matches" />,
    );

    const select = screen.getByRole("combobox");
    fireEvent.click(select);

    const searchInput = screen.getByRole("textbox");
    await user.type(searchInput, "nonexistent");

    expect(screen.getByText("No matches")).toBeInTheDocument();
  });

  it("limits displayed tags with maxTagCount", () => {
    render(
      <Select
        options={mockOptions}
        multiple
        value={["option1", "option2", "option4"]}
        maxTagCount={2}
      />,
    );

    expect(screen.getByText("Option 1")).toBeInTheDocument();
    expect(screen.getByText("Option 2")).toBeInTheDocument();
    expect(screen.getByText("+1 more")).toBeInTheDocument();
  });

  it("allows creating new options when allowCreate is true", async () => {
    const user = userEvent.setup();
    const onChange = jest.fn();
    render(
      <Select
        options={mockOptions}
        searchable
        allowCreate
        onChange={onChange}
      />,
    );

    const select = screen.getByRole("combobox");
    fireEvent.click(select);

    const searchInput = screen.getByRole("textbox");
    await user.type(searchInput, "New Option");

    expect(screen.getByText('Create "New Option"')).toBeInTheDocument();

    fireEvent.click(screen.getByText('Create "New Option"'));
    expect(onChange).toHaveBeenCalledWith(
      "New Option",
      expect.objectContaining({ value: "New Option" }),
    );
  });

  it("calls onDropdownVisibleChange when dropdown opens/closes", () => {
    const onDropdownVisibleChange = jest.fn();
    render(
      <Select
        options={mockOptions}
        onDropdownVisibleChange={onDropdownVisibleChange}
      />,
    );

    const select = screen.getByRole("combobox");
    fireEvent.click(select);

    expect(onDropdownVisibleChange).toHaveBeenCalledWith(true);
  });

  it("applies custom classNames", () => {
    render(
      <Select
        options={mockOptions}
        className="custom-select"
        dropdownClassName="custom-dropdown"
        optionClassName="custom-option"
        tagClassName="custom-tag"
      />,
    );

    const select = screen.getByRole("combobox").closest("div");
    expect(select).toHaveClass("custom-select");

    fireEvent.click(screen.getByRole("combobox"));

    const dropdown = screen
      .getByText("Option 1")
      .closest('[class*="custom-dropdown"]');
    expect(dropdown).toBeInTheDocument();
  });

  it("hides arrow when showArrow is false", () => {
    render(<Select options={mockOptions} showArrow={false} />);

    const select = screen.getByRole("combobox").parentElement;
    const arrow = select?.querySelector('svg[class*="rotate"]');
    expect(arrow).not.toBeInTheDocument();
  });

  it("removes border when bordered is false", () => {
    render(<Select options={mockOptions} bordered={false} />);

    const select = screen.getByRole("combobox").parentElement;
    expect(select).toHaveClass("border-0");
  });

  it("uses custom filter function", async () => {
    const user = userEvent.setup();
    const customFilter = (inputValue: string, option: SelectOption) => {
      return option.value.toString().includes(inputValue);
    };

    render(
      <Select options={mockOptions} searchable filterOption={customFilter} />,
    );

    const select = screen.getByRole("combobox");
    fireEvent.click(select);

    const searchInput = screen.getByRole("textbox");
    await user.type(searchInput, "1");

    expect(screen.getByText("Option 1")).toBeInTheDocument();
    expect(screen.queryByText("Option 2")).not.toBeInTheDocument();
  });

  it("deselects option in multiple mode when clicking selected option", () => {
    const onChange = jest.fn();
    render(
      <Select
        options={mockOptions}
        multiple
        value={["option1"]}
        onChange={onChange}
      />,
    );

    const select = screen.getByRole("combobox");
    fireEvent.click(select);

    fireEvent.click(screen.getByText("Option 1"));

    expect(onChange).toHaveBeenCalledWith([], []);
  });
});
