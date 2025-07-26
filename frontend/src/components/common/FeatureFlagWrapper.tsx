/**
 * Feature Flag Wrapper Component
 * Conditionally renders children based on feature flag evaluation
 */

// @ts-nocheck
import React from "react";
import {
  useFeatureFlag,
  FeatureFlagContext,
} from "../../services/featureFlags";
import { Box, Typography, CircularProgress } from "@mui/material";

interface FeatureFlagWrapperProps {
  flagKey: string;
  context?: FeatureFlagContext;
  fallback?: React.ReactNode;
  loadingFallback?: React.ReactNode;
  errorFallback?: React.ReactNode;
  children: React.ReactNode;
  invert?: boolean; // Show children when flag is disabled
}

const FeatureFlagWrapper: React.FC<FeatureFlagWrapperProps> = ({
  flagKey,
  context = {},
  fallback = null,
  loadingFallback,
  errorFallback,
  children,
  invert = false,
}) => {
  const { isEnabled, isLoading, error } = useFeatureFlag(flagKey, context);

  // Show loading state
  if (isLoading) {
    if (loadingFallback) {
      return <>{loadingFallback}</>;
    }

    return (
      <Box sx={{ display: "flex", justifyContent: "center", p: 2 }}>
        <CircularProgress size={20} />
      </Box>
    );
  }

  // Show error state
  if (error) {
    if (errorFallback) {
      return <>{errorFallback}</>;
    }

    // Fail safe: show fallback or nothing
    return <>{fallback}</>;
  }

  // Determine whether to show children
  const shouldShow = invert ? !isEnabled : isEnabled;

  if (shouldShow) {
    return <>{children}</>;
  }

  return <>{fallback}</>;
};

export default FeatureFlagWrapper;

/**
 * Higher-order component for feature flag wrapping
 */
export function withFeatureFlag<P extends object>(
  Component: React.ComponentType<P>,
  flagKey: string,
  options: {
    context?: FeatureFlagContext;
    fallback?: React.ReactNode;
    invert?: boolean;
  } = {},
) {
  const WrappedComponent: React.FC<P> = (props) => {
    return (
      <FeatureFlagWrapper
        flagKey={flagKey}
        context={options.context}
        fallback={options.fallback}
        invert={options.invert}
      >
        <Component {...props} />
      </FeatureFlagWrapper>
    );
  };

  WrappedComponent.displayName = `withFeatureFlag(${Component.displayName || Component.name})`;

  return WrappedComponent;
}

/**
 * Feature Flag Toggle - renders different content based on flag state
 */
interface FeatureFlagToggleProps {
  flagKey: string;
  context?: FeatureFlagContext;
  enabled: React.ReactNode;
  disabled: React.ReactNode;
  loading?: React.ReactNode;
}

export const FeatureFlagToggle: React.FC<FeatureFlagToggleProps> = ({
  flagKey,
  context = {},
  enabled,
  disabled,
  loading,
}) => {
  const { isEnabled, isLoading, error } = useFeatureFlag(flagKey, context);

  if (isLoading) {
    return <>{loading || <CircularProgress size={20} />}</>;
  }

  if (error) {
    // Fail safe to disabled state
    return <>{disabled}</>;
  }

  return <>{isEnabled ? enabled : disabled}</>;
};

/**
 * Debug component for feature flag state
 */
interface FeatureFlagDebugProps {
  flagKey: string;
  context?: FeatureFlagContext;
}

export const FeatureFlagDebug: React.FC<FeatureFlagDebugProps> = ({
  flagKey,
  context = {},
}) => {
  const { isEnabled, isLoading, error } = useFeatureFlag(flagKey, context);

  if (process.env.NODE_ENV === "production") {
    return null;
  }

  return (
    <Box
      sx={{
        position: "fixed",
        bottom: 16,
        right: 16,
        backgroundColor: "rgba(0, 0, 0, 0.8)",
        color: "white",
        padding: 1,
        borderRadius: 1,
        fontSize: "0.75rem",
        zIndex: 9999,
        fontFamily: "monospace",
      }}
    >
      <Typography variant="caption" display="block">
        🎛️ {flagKey}
      </Typography>
      <Typography variant="caption" display="block">
        Status:{" "}
        {isLoading
          ? "Loading..."
          : error
            ? "Error"
            : isEnabled
              ? "Enabled"
              : "Disabled"}
      </Typography>
      {error && (
        <Typography variant="caption" display="block" color="error.main">
          Error: {error.message}
        </Typography>
      )}
    </Box>
  );
};
