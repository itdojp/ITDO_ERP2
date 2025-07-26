/**
 * CC02 v77.0 Day 22: Frontend Performance Optimization Module
 * Enterprise-grade React frontend optimization with intelligent rendering and resource management.
 */

import React, {
  useState,
  useEffect,
  useCallback,
  useMemo,
  useRef,
  memo,
  lazy,
  Suspense,
  createContext,
  useContext,
} from "react";
import {
  VirtualizedList,
  IntersectionObserver,
  PerformanceMetrics,
  ResourceManager,
  ComponentProfiler,
} from "./performance-utils";

// Performance monitoring context
interface PerformanceContextType {
  metrics: PerformanceMetrics;
  recordMetric: (name: string, value: number) => void;
  optimizationLevel: "low" | "medium" | "high";
  resourceBudget: ResourceBudget;
}

interface ResourceBudget {
  maxBundleSize: number;
  maxRenderTime: number;
  maxMemoryUsage: number;
  targetFrameRate: number;
}

interface ComponentMetrics {
  componentName: string;
  renderTime: number;
  rerenderCount: number;
  memoryUsage: number;
  childrenCount: number;
  propsSize: number;
  lastOptimized: Date;
}

interface OptimizationStrategy {
  type:
    | "memoization"
    | "virtualization"
    | "lazy-loading"
    | "bundling"
    | "preloading";
  priority: "low" | "medium" | "high" | "critical";
  impact: number;
  cost: number;
  applicableComponents: string[];
}

// Performance context
const PerformanceContext = createContext<PerformanceContextType | null>(null);

// Performance monitoring utilities
class FrontendPerformanceMetrics {
  private metrics: Map<string, number[]> = new Map();
  private observers: PerformanceObserver[] = [];

  constructor() {
    this.initializeObservers();
  }

  private initializeObservers() {
    // Performance observer for navigation timing
    if ("PerformanceObserver" in window) {
      const navigationObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.entryType === "navigation") {
            const navEntry = entry as PerformanceNavigationTiming;
            this.recordMetric(
              "page_load_time",
              navEntry.loadEventEnd - navEntry.fetchStart,
            );
            this.recordMetric(
              "dom_content_loaded",
              navEntry.domContentLoadedEventEnd -
                navEntry.domContentLoadedEventStart,
            );
            this.recordMetric(
              "first_paint",
              navEntry.domContentLoadedEventEnd - navEntry.fetchStart,
            );
          }
        }
      });

      navigationObserver.observe({ entryTypes: ["navigation"] });
      this.observers.push(navigationObserver);

      // Performance observer for paint timing
      const paintObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.entryType === "paint") {
            this.recordMetric(entry.name.replace("-", "_"), entry.startTime);
          }
        }
      });

      paintObserver.observe({ entryTypes: ["paint"] });
      this.observers.push(paintObserver);

      // Performance observer for largest contentful paint
      const lcpObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.entryType === "largest-contentful-paint") {
            this.recordMetric("largest_contentful_paint", entry.startTime);
          }
        }
      });

      lcpObserver.observe({ entryTypes: ["largest-contentful-paint"] });
      this.observers.push(lcpObserver);
    }
  }

  recordMetric(name: string, value: number) {
    if (!this.metrics.has(name)) {
      this.metrics.set(name, []);
    }

    const values = this.metrics.get(name)!;
    values.push(value);

    // Keep only last 100 measurements
    if (values.length > 100) {
      values.shift();
    }

    // Log significant performance issues
    if (this.isSignificantIssue(name, value)) {
      console.warn(`Performance issue detected: ${name} = ${value}ms`);
    }
  }

  private isSignificantIssue(name: string, value: number): boolean {
    const thresholds: Record<string, number> = {
      page_load_time: 3000,
      largest_contentful_paint: 2500,
      first_input_delay: 100,
      cumulative_layout_shift: 0.1,
      component_render_time: 16, // 60fps target
    };

    return value > (thresholds[name] || Infinity);
  }

  getMetricSummary(name: string) {
    const values = this.metrics.get(name) || [];
    if (values.length === 0) return null;

    const sorted = [...values].sort((a, b) => a - b);
    return {
      avg: values.reduce((a, b) => a + b, 0) / values.length,
      min: Math.min(...values),
      max: Math.max(...values),
      p50: sorted[Math.floor(sorted.length * 0.5)],
      p95: sorted[Math.floor(sorted.length * 0.95)],
      p99: sorted[Math.floor(sorted.length * 0.99)],
      count: values.length,
    };
  }

  getAllMetrics() {
    const summary: Record<string, any> = {};
    for (const [name] of this.metrics) {
      summary[name] = this.getMetricSummary(name);
    }
    return summary;
  }

  cleanup() {
    this.observers.forEach((observer) => observer.disconnect());
    this.observers = [];
    this.metrics.clear();
  }
}

// Component performance profiler
class ComponentPerformanceProfiler {
  private componentMetrics: Map<string, ComponentMetrics> = new Map();
  private renderTimes: Map<string, number> = new Map();

  startRender(componentName: string) {
    this.renderTimes.set(componentName, performance.now());
  }

  endRender(
    componentName: string,
    propsSize: number = 0,
    childrenCount: number = 0,
  ) {
    const startTime = this.renderTimes.get(componentName);
    if (!startTime) return;

    const renderTime = performance.now() - startTime;
    this.renderTimes.delete(componentName);

    // Update component metrics
    const existing = this.componentMetrics.get(componentName);
    const metrics: ComponentMetrics = {
      componentName,
      renderTime,
      rerenderCount: (existing?.rerenderCount || 0) + 1,
      memoryUsage: this.estimateMemoryUsage(propsSize, childrenCount),
      childrenCount,
      propsSize,
      lastOptimized: existing?.lastOptimized || new Date(),
    };

    this.componentMetrics.set(componentName, metrics);

    // Log slow renders
    if (renderTime > 16) {
      // > 1 frame at 60fps
      console.warn(
        `Slow render detected: ${componentName} took ${renderTime.toFixed(2)}ms`,
      );
    }
  }

  private estimateMemoryUsage(
    propsSize: number,
    childrenCount: number,
  ): number {
    // Rough estimation of component memory usage
    return propsSize * 8 + childrenCount * 100; // bytes
  }

  getComponentProfile(componentName: string): ComponentMetrics | undefined {
    return this.componentMetrics.get(componentName);
  }

  getSlowComponents(threshold: number = 16): ComponentMetrics[] {
    return Array.from(this.componentMetrics.values())
      .filter((metrics) => metrics.renderTime > threshold)
      .sort((a, b) => b.renderTime - a.renderTime);
  }

  getFrequentlyRerenderedComponents(
    threshold: number = 10,
  ): ComponentMetrics[] {
    return Array.from(this.componentMetrics.values())
      .filter((metrics) => metrics.rerenderCount > threshold)
      .sort((a, b) => b.rerenderCount - a.rerenderCount);
  }
}

// Performance optimization analyzer
class PerformanceOptimizationAnalyzer {
  private profiler: ComponentPerformanceProfiler;
  private metrics: FrontendPerformanceMetrics;

  constructor(
    profiler: ComponentPerformanceProfiler,
    metrics: FrontendPerformanceMetrics,
  ) {
    this.profiler = profiler;
    this.metrics = metrics;
  }

  analyzeOptimizationOpportunities(): OptimizationStrategy[] {
    const strategies: OptimizationStrategy[] = [];

    // Analyze slow components for memoization
    const slowComponents = this.profiler.getSlowComponents();
    if (slowComponents.length > 0) {
      strategies.push({
        type: "memoization",
        priority: "high",
        impact: this.calculateMemoizationImpact(slowComponents),
        cost: 20, // Low implementation cost
        applicableComponents: slowComponents.map((c) => c.componentName),
      });
    }

    // Analyze frequently rerendered components
    const frequentComponents =
      this.profiler.getFrequentlyRerenderedComponents();
    if (frequentComponents.length > 0) {
      strategies.push({
        type: "memoization",
        priority: "medium",
        impact: this.calculateRerenderReductionImpact(frequentComponents),
        cost: 15,
        applicableComponents: frequentComponents.map((c) => c.componentName),
      });
    }

    // Analyze bundle size optimization
    const bundleMetrics = this.metrics.getMetricSummary("page_load_time");
    if (bundleMetrics && bundleMetrics.avg > 2000) {
      strategies.push({
        type: "lazy-loading",
        priority: "high",
        impact: 70, // High impact for bundle optimization
        cost: 50, // Medium implementation cost
        applicableComponents: ["*"], // Applies to all components
      });
    }

    // Analyze virtualization opportunities
    // This would need to be detected based on component types and data sizes
    strategies.push({
      type: "virtualization",
      priority: "medium",
      impact: 60,
      cost: 40,
      applicableComponents: ["DataTable", "List", "Grid"],
    });

    return strategies.sort((a, b) => b.impact / b.cost - a.impact / a.cost);
  }

  private calculateMemoizationImpact(components: ComponentMetrics[]): number {
    const totalRenderTime = components.reduce(
      (sum, c) => sum + c.renderTime,
      0,
    );
    const avgRerenders =
      components.reduce((sum, c) => sum + c.rerenderCount, 0) /
      components.length;

    // Estimate impact as percentage of render time that could be saved
    return Math.min(((totalRenderTime * avgRerenders) / 1000) * 10, 90);
  }

  private calculateRerenderReductionImpact(
    components: ComponentMetrics[],
  ): number {
    const totalRerenders = components.reduce(
      (sum, c) => sum + c.rerenderCount,
      0,
    );
    return Math.min((totalRerenders / 10) * 5, 70); // Rough estimation
  }
}

// High-performance optimized components
interface OptimizedListProps<T> {
  items: T[];
  renderItem: (item: T, index: number) => React.ReactNode;
  keyExtractor: (item: T, index: number) => string;
  itemHeight?: number;
  containerHeight?: number;
  overscan?: number;
}

const OptimizedList = memo(
  <T,>({
    items,
    renderItem,
    keyExtractor,
    itemHeight = 50,
    containerHeight = 400,
    overscan = 5,
  }: OptimizedListProps<T>) => {
    const [scrollTop, setScrollTop] = useState(0);
    const containerRef = useRef<HTMLDivElement>(null);

    const visibleRange = useMemo(() => {
      const startIndex = Math.max(
        0,
        Math.floor(scrollTop / itemHeight) - overscan,
      );
      const endIndex = Math.min(
        items.length - 1,
        Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan,
      );
      return { startIndex, endIndex };
    }, [scrollTop, itemHeight, containerHeight, items.length, overscan]);

    const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
      setScrollTop(e.currentTarget.scrollTop);
    }, []);

    const visibleItems = useMemo(() => {
      const result = [];
      for (let i = visibleRange.startIndex; i <= visibleRange.endIndex; i++) {
        if (items[i]) {
          result.push({
            item: items[i],
            index: i,
            key: keyExtractor(items[i], i),
          });
        }
      }
      return result;
    }, [items, visibleRange, keyExtractor]);

    return (
      <div
        ref={containerRef}
        style={{ height: containerHeight, overflow: "auto" }}
        onScroll={handleScroll}
      >
        <div
          style={{ height: items.length * itemHeight, position: "relative" }}
        >
          {visibleItems.map(({ item, index, key }) => (
            <div
              key={key}
              style={{
                position: "absolute",
                top: index * itemHeight,
                left: 0,
                right: 0,
                height: itemHeight,
              }}
            >
              {renderItem(item, index)}
            </div>
          ))}
        </div>
      </div>
    );
  },
);

OptimizedList.displayName = "OptimizedList";

// Lazy loading wrapper with preloading
interface LazyComponentWrapperProps {
  componentLoader: () => Promise<{ default: React.ComponentType<any> }>;
  fallback?: React.ReactNode;
  preload?: boolean;
  children?: React.ReactNode;
}

const LazyComponentWrapper: React.FC<LazyComponentWrapperProps> = ({
  componentLoader,
  fallback = <div>Loading...</div>,
  preload = false,
  children,
}) => {
  const LazyComponent = useMemo(() => {
    const Component = lazy(componentLoader);

    // Preload component if requested
    if (preload) {
      componentLoader().catch(console.error);
    }

    return Component;
  }, [componentLoader, preload]);

  return (
    <Suspense fallback={fallback}>
      <LazyComponent>{children}</LazyComponent>
    </Suspense>
  );
};

// Intersection observer hook for lazy loading
function useIntersectionObserver(
  ref: React.RefObject<Element>,
  options: IntersectionObserverInit = {},
): boolean {
  const [isIntersecting, setIsIntersecting] = useState(false);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const observer = new IntersectionObserver(([entry]) => {
      setIsIntersecting(entry.isIntersecting);
    }, options);

    observer.observe(element);

    return () => {
      observer.disconnect();
    };
  }, [ref, options]);

  return isIntersecting;
}

// Performance monitoring hook
function usePerformanceMonitoring(componentName: string) {
  const profiler = useMemo(() => new ComponentPerformanceProfiler(), []);

  useEffect(() => {
    profiler.startRender(componentName);

    return () => {
      profiler.endRender(componentName);
    };
  });

  return {
    recordMetric: profiler.endRender.bind(profiler),
    getProfile: () => profiler.getComponentProfile(componentName),
  };
}

// Optimized image component with lazy loading
interface OptimizedImageProps {
  src: string;
  alt: string;
  width?: number;
  height?: number;
  loading?: "lazy" | "eager";
  placeholder?: string;
  className?: string;
}

const OptimizedImage = memo<OptimizedImageProps>(
  ({ src, alt, width, height, loading = "lazy", placeholder, className }) => {
    const [isLoaded, setIsLoaded] = useState(false);
    const [hasError, setHasError] = useState(false);
    const imgRef = useRef<HTMLImageElement>(null);
    const isVisible = useIntersectionObserver(imgRef, { threshold: 0.1 });

    const shouldLoad = loading === "eager" || isVisible;

    const handleLoad = useCallback(() => {
      setIsLoaded(true);
    }, []);

    const handleError = useCallback(() => {
      setHasError(true);
    }, []);

    return (
      <div
        ref={imgRef}
        className={className}
        style={{
          width,
          height,
          backgroundColor: placeholder || "#f0f0f0",
          position: "relative",
          overflow: "hidden",
        }}
      >
        {shouldLoad && !hasError && (
          <img
            src={src}
            alt={alt}
            width={width}
            height={height}
            onLoad={handleLoad}
            onError={handleError}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              opacity: isLoaded ? 1 : 0,
              transition: "opacity 0.3s ease",
            }}
          />
        )}
        {!isLoaded && !hasError && shouldLoad && (
          <div
            style={{
              position: "absolute",
              top: "50%",
              left: "50%",
              transform: "translate(-50%, -50%)",
              color: "#666",
            }}
          >
            Loading...
          </div>
        )}
        {hasError && (
          <div
            style={{
              position: "absolute",
              top: "50%",
              left: "50%",
              transform: "translate(-50%, -50%)",
              color: "#999",
            }}
          >
            Failed to load
          </div>
        )}
      </div>
    );
  },
);

OptimizedImage.displayName = "OptimizedImage";

// Performance budget monitor
interface PerformanceBudgetMonitorProps {
  budget: ResourceBudget;
  onBudgetExceeded?: (metric: string, value: number, budget: number) => void;
}

const PerformanceBudgetMonitor: React.FC<PerformanceBudgetMonitorProps> = ({
  budget,
  onBudgetExceeded,
}) => {
  const [currentMetrics, setCurrentMetrics] = useState<Record<string, number>>(
    {},
  );

  useEffect(() => {
    const interval = setInterval(() => {
      // Collect current performance metrics
      const metrics = {
        renderTime: performance.now(),
        memoryUsage: (performance as any).memory?.usedJSHeapSize || 0,
        frameRate: 60, // Would need actual frame rate measurement
      };

      setCurrentMetrics(metrics);

      // Check budget violations
      if (metrics.renderTime > budget.maxRenderTime && onBudgetExceeded) {
        onBudgetExceeded(
          "renderTime",
          metrics.renderTime,
          budget.maxRenderTime,
        );
      }

      if (metrics.memoryUsage > budget.maxMemoryUsage && onBudgetExceeded) {
        onBudgetExceeded(
          "memoryUsage",
          metrics.memoryUsage,
          budget.maxMemoryUsage,
        );
      }

      if (metrics.frameRate < budget.targetFrameRate && onBudgetExceeded) {
        onBudgetExceeded(
          "frameRate",
          metrics.frameRate,
          budget.targetFrameRate,
        );
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [budget, onBudgetExceeded]);

  return (
    <div
      style={{
        position: "fixed",
        top: 10,
        right: 10,
        background: "rgba(0,0,0,0.8)",
        color: "white",
        padding: 10,
        borderRadius: 5,
        fontSize: 12,
        fontFamily: "monospace",
        zIndex: 9999,
      }}
    >
      <div>
        Render Time: {currentMetrics.renderTime?.toFixed(2) || 0}ms /{" "}
        {budget.maxRenderTime}ms
      </div>
      <div>
        Memory: {Math.round((currentMetrics.memoryUsage || 0) / 1024 / 1024)}MB
        / {Math.round(budget.maxMemoryUsage / 1024 / 1024)}MB
      </div>
      <div>
        Frame Rate: {currentMetrics.frameRate || 0}fps /{" "}
        {budget.targetFrameRate}fps
      </div>
    </div>
  );
};

// Main performance optimization provider
interface FrontendPerformanceProviderProps {
  children: React.ReactNode;
  optimizationLevel?: "low" | "medium" | "high";
  resourceBudget?: Partial<ResourceBudget>;
  enableMonitoring?: boolean;
}

export const FrontendPerformanceProvider: React.FC<
  FrontendPerformanceProviderProps
> = ({
  children,
  optimizationLevel = "medium",
  resourceBudget = {},
  enableMonitoring = true,
}) => {
  const [metrics] = useState(() => new FrontendPerformanceMetrics());

  const defaultBudget: ResourceBudget = {
    maxBundleSize: 250 * 1024, // 250KB
    maxRenderTime: 16, // 60fps
    maxMemoryUsage: 50 * 1024 * 1024, // 50MB
    targetFrameRate: 60,
  };

  const budget = { ...defaultBudget, ...resourceBudget };

  const recordMetric = useCallback(
    (name: string, value: number) => {
      metrics.recordMetric(name, value);
    },
    [metrics],
  );

  const handleBudgetExceeded = useCallback(
    (metric: string, value: number, budgetValue: number) => {
      console.warn(
        `Performance budget exceeded: ${metric} = ${value} (budget: ${budgetValue})`,
      );
    },
    [],
  );

  const contextValue: PerformanceContextType = {
    metrics,
    recordMetric,
    optimizationLevel,
    resourceBudget: budget,
  };

  useEffect(() => {
    return () => {
      metrics.cleanup();
    };
  }, [metrics]);

  return (
    <PerformanceContext.Provider value={contextValue}>
      {enableMonitoring && (
        <PerformanceBudgetMonitor
          budget={budget}
          onBudgetExceeded={handleBudgetExceeded}
        />
      )}
      {children}
    </PerformanceContext.Provider>
  );
};

// Hook to use performance context
export function usePerformanceContext(): PerformanceContextType {
  const context = useContext(PerformanceContext);
  if (!context) {
    throw new Error(
      "usePerformanceContext must be used within FrontendPerformanceProvider",
    );
  }
  return context;
}

// Export performance optimization utilities
export {
  OptimizedList,
  OptimizedImage,
  LazyComponentWrapper,
  useIntersectionObserver,
  usePerformanceMonitoring,
  FrontendPerformanceMetrics,
  ComponentPerformanceProfiler,
  PerformanceOptimizationAnalyzer,
};

// Performance optimization HOC
export function withPerformanceOptimization<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  options: {
    memo?: boolean;
    profiling?: boolean;
    lazyLoad?: boolean;
  } = {},
) {
  const {
    memo: enableMemo = true,
    profiling = false,
    lazyLoad = false,
  } = options;

  let OptimizedComponent: React.ComponentType<P> = WrappedComponent;

  // Apply memoization
  if (enableMemo) {
    OptimizedComponent = memo(OptimizedComponent);
  }

  // Apply performance profiling
  if (profiling) {
    OptimizedComponent = (props: P) => {
      const componentName =
        WrappedComponent.displayName || WrappedComponent.name || "Unknown";
      const { recordMetric } = usePerformanceMonitoring(componentName);

      return <WrappedComponent {...props} />;
    };
  }

  // Apply lazy loading
  if (lazyLoad) {
    return lazy(() => Promise.resolve({ default: OptimizedComponent }));
  }

  return OptimizedComponent;
}
