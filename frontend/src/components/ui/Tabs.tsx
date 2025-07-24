import React, { useState, useRef, useEffect } from "react";

export interface Tab {
  id: string;
  label: string;
  content: React.ReactNode;
  disabled?: boolean;
  icon?: React.ReactNode;
  badge?: string | number;
  closable?: boolean;
}

interface TabsProps {
  tabs: Tab[];
  activeTab?: string;
  onTabChange?: (tabId: string) => void;
  onTabClose?: (tabId: string) => void;
  variant?: "default" | "pills" | "underline" | "bordered";
  orientation?: "horizontal" | "vertical";
  size?: "sm" | "md" | "lg";
  className?: string;
  tabListClassName?: string;
  tabClassName?: string;
  contentClassName?: string;
  allowCloseTabs?: boolean;
  scrollable?: boolean;
  centered?: boolean;
  lazy?: boolean;
}

export const Tabs: React.FC<TabsProps> = ({
  tabs,
  activeTab,
  onTabChange,
  onTabClose,
  variant = "default",
  orientation = "horizontal",
  size = "md",
  className = "",
  tabListClassName = "",
  tabClassName = "",
  contentClassName = "",
  allowCloseTabs = false,
  scrollable = false,
  centered = false,
  lazy = false,
}) => {
  const [internalActiveTab, setInternalActiveTab] = useState(() => {
    return (
      activeTab || tabs.find((tab) => !tab.disabled)?.id || tabs[0]?.id || ""
    );
  });

  const tabListRef = useRef<HTMLDivElement>(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);
  const [renderedTabs, setRenderedTabs] = useState<Set<string>>(
    new Set([internalActiveTab]),
  );

  const currentActiveTab =
    activeTab !== undefined ? activeTab : internalActiveTab;

  const getSizeClasses = () => {
    const sizeMap = {
      sm: "text-sm px-3 py-1.5",
      md: "text-sm px-4 py-2",
      lg: "text-base px-6 py-3",
    };
    return sizeMap[size];
  };

  const getVariantClasses = (isActive: boolean, isDisabled: boolean) => {
    const baseClasses = `
      inline-flex items-center gap-2 font-medium transition-all duration-200
      ${getSizeClasses()}
      ${isDisabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}
    `;

    switch (variant) {
      case "pills":
        return `${baseClasses} rounded-lg ${
          isActive
            ? "bg-blue-100 text-blue-700"
            : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
        }`;
      case "underline":
        return `${baseClasses} border-b-2 ${
          isActive
            ? "border-blue-500 text-blue-600"
            : "border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300"
        }`;
      case "bordered":
        return `${baseClasses} border border-gray-300 ${
          isActive
            ? "bg-white border-blue-500 text-blue-600 -mb-px"
            : "bg-gray-50 text-gray-600 hover:text-gray-900 hover:bg-gray-100"
        }`;
      default:
        return `${baseClasses} ${
          isActive
            ? "text-blue-600 bg-blue-50"
            : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
        }`;
    }
  };

  const handleTabClick = (tabId: string, disabled?: boolean) => {
    if (disabled) return;

    if (activeTab === undefined) {
      setInternalActiveTab(tabId);
    }
    onTabChange?.(tabId);

    if (lazy) {
      setRenderedTabs((prev) => new Set([...prev, tabId]));
    }
  };

  const handleTabClose = (event: React.MouseEvent, tabId: string) => {
    event.stopPropagation();
    onTabClose?.(tabId);
  };

  const handleKeyDown = (event: React.KeyboardEvent, tabId: string) => {
    const enabledTabs = tabs.filter((tab) => !tab.disabled);
    const currentIndex = enabledTabs.findIndex(
      (tab) => tab.id === currentActiveTab,
    );

    switch (event.key) {
      case "ArrowRight":
      case "ArrowDown":
        event.preventDefault();
        const nextIndex = (currentIndex + 1) % enabledTabs.length;
        handleTabClick(enabledTabs[nextIndex].id);
        break;
      case "ArrowLeft":
      case "ArrowUp":
        event.preventDefault();
        const prevIndex =
          currentIndex > 0 ? currentIndex - 1 : enabledTabs.length - 1;
        handleTabClick(enabledTabs[prevIndex].id);
        break;
      case "Home":
        event.preventDefault();
        handleTabClick(enabledTabs[0].id);
        break;
      case "End":
        event.preventDefault();
        handleTabClick(enabledTabs[enabledTabs.length - 1].id);
        break;
      case "Enter":
      case " ":
        event.preventDefault();
        handleTabClick(tabId);
        break;
    }
  };

  const scrollTabs = (direction: "left" | "right") => {
    const container = tabListRef.current;
    if (!container) return;

    const scrollAmount = 200;
    const newScrollLeft =
      direction === "left"
        ? container.scrollLeft - scrollAmount
        : container.scrollLeft + scrollAmount;

    container.scrollTo({ left: newScrollLeft, behavior: "smooth" });
  };

  const updateScrollButtons = () => {
    const container = tabListRef.current;
    if (!container) return;

    setCanScrollLeft(container.scrollLeft > 0);
    setCanScrollRight(
      container.scrollLeft < container.scrollWidth - container.clientWidth - 1,
    );
  };

  useEffect(() => {
    if (!scrollable) return;

    const container = tabListRef.current;
    if (!container) return;

    updateScrollButtons();

    const handleScroll = () => updateScrollButtons();
    container.addEventListener("scroll", handleScroll);

    const resizeObserver = new ResizeObserver(() => updateScrollButtons());
    resizeObserver.observe(container);

    return () => {
      container.removeEventListener("scroll", handleScroll);
      resizeObserver.disconnect();
    };
  }, [scrollable, tabs]);

  useEffect(() => {
    if (lazy && currentActiveTab) {
      setRenderedTabs((prev) => new Set([...prev, currentActiveTab]));
    }
  }, [currentActiveTab, lazy]);

  const activeTabContent = tabs.find((tab) => tab.id === currentActiveTab);

  const tabListClasses = `
    ${orientation === "horizontal" ? "flex" : "flex flex-col"}
    ${scrollable && orientation === "horizontal" ? "overflow-x-auto scrollbar-hide" : ""}
    ${centered ? "justify-center" : ""}
    ${variant === "bordered" ? "border-b border-gray-300" : ""}
    ${tabListClassName}
  `;

  const containerClasses = `
    ${orientation === "horizontal" ? "flex flex-col" : "flex gap-6"}
    ${className}
  `;

  return (
    <div className={containerClasses}>
      <div
        className={`relative ${orientation === "horizontal" ? "" : "w-48 flex-shrink-0"}`}
      >
        {scrollable && orientation === "horizontal" && (
          <>
            {canScrollLeft && (
              <button
                onClick={() => scrollTabs("left")}
                className="absolute left-0 top-0 z-10 h-full bg-white shadow-md px-2 flex items-center"
                aria-label="Scroll tabs left"
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 19l-7-7 7-7"
                  />
                </svg>
              </button>
            )}
            {canScrollRight && (
              <button
                onClick={() => scrollTabs("right")}
                className="absolute right-0 top-0 z-10 h-full bg-white shadow-md px-2 flex items-center"
                aria-label="Scroll tabs right"
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5l7 7-7 7"
                  />
                </svg>
              </button>
            )}
          </>
        )}

        <div
          ref={tabListRef}
          role="tablist"
          aria-orientation={orientation}
          className={tabListClasses}
        >
          {tabs.map((tab, index) => {
            const isActive = tab.id === currentActiveTab;

            return (
              <button
                key={tab.id}
                role="tab"
                tabIndex={isActive ? 0 : -1}
                aria-selected={isActive}
                aria-controls={`tabpanel-${tab.id}`}
                id={`tab-${tab.id}`}
                disabled={tab.disabled}
                className={`
                  ${getVariantClasses(isActive, tab.disabled || false)}
                  ${variant === "bordered" && index > 0 ? "ml-0" : ""}
                  ${tabClassName}
                `}
                onClick={() => handleTabClick(tab.id, tab.disabled)}
                onKeyDown={(e) => handleKeyDown(e, tab.id)}
              >
                {tab.icon && <span className="flex-shrink-0">{tab.icon}</span>}
                <span className="truncate">{tab.label}</span>
                {tab.badge && (
                  <span className="bg-red-500 text-white text-xs px-1.5 py-0.5 rounded-full min-w-[1.25rem] h-5 flex items-center justify-center">
                    {tab.badge}
                  </span>
                )}
                {tab.closable && allowCloseTabs && (
                  <button
                    onClick={(e) => handleTabClose(e, tab.id)}
                    className="ml-2 text-gray-400 hover:text-gray-600 transition-colors"
                    aria-label={`Close ${tab.label} tab`}
                  >
                    <svg
                      className="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                  </button>
                )}
              </button>
            );
          })}
        </div>
      </div>

      <div className={`flex-1 ${contentClassName}`}>
        {tabs.map((tab) => {
          const isActive = tab.id === currentActiveTab;
          const shouldRender = !lazy || renderedTabs.has(tab.id);

          if (!shouldRender) return null;

          return (
            <div
              key={tab.id}
              role="tabpanel"
              tabIndex={0}
              aria-labelledby={`tab-${tab.id}`}
              id={`tabpanel-${tab.id}`}
              className={isActive ? "block" : "hidden"}
            >
              {tab.content}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default Tabs;
