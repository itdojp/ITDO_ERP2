/**
 * Feature Flags API Service
 * Provides client-side methods for managing and evaluating feature flags
 */

import { apiClient } from "./api";

export interface FeatureFlagContext {
  userId?: string;
  organizationId?: string;
  userRoles?: string[];
  environment?: string;
  customAttributes?: Record<string, any>;
}

export interface FeatureFlagEvaluation {
  key: string;
  enabled: boolean;
  variant?: string;
  evaluationContext: Record<string, any>;
  timestamp: string;
}

export interface FeatureFlag {
  key: string;
  name: string;
  description?: string;
  enabled: boolean;
  strategy: string;
  rules?: any[];
  environments?: Record<string, any>;
  createdAt?: string;
  updatedAt?: string;
  createdBy?: string;
  updatedBy?: string;
}

export interface CreateFeatureFlagRequest {
  key: string;
  name: string;
  description?: string;
  enabled: boolean;
  strategy: string;
  percentage?: number;
  userIds?: string[];
  organizationIds?: string[];
  roles?: string[];
  environments?: Record<string, Record<string, any>>;
}

export interface UpdateFeatureFlagRequest {
  name?: string;
  description?: string;
  enabled?: boolean;
  strategy?: string;
  percentage?: number;
  userIds?: string[];
  organizationIds?: string[];
  roles?: string[];
  environments?: Record<string, Record<string, any>>;
}

class FeatureFlagsService {
  /**
   * Evaluate a single feature flag
   */
  async evaluateFlag(
    key: string,
    context: FeatureFlagContext = {},
  ): Promise<FeatureFlagEvaluation> {
    const response = await apiClient.post<FeatureFlagEvaluation>(
      "/api/v1/feature-flags/evaluate",
      {
        key,
        ...context,
      },
    );
    return response.data;
  }

  /**
   * Bulk evaluate multiple feature flags
   */
  async evaluateFlags(
    keys: string[],
    context: FeatureFlagContext = {},
  ): Promise<FeatureFlagEvaluation[]> {
    const response = await apiClient.post<FeatureFlagEvaluation[]>(
      "/api/v1/feature-flags/bulk-evaluate",
      {
        flag_keys: keys,
        context,
      },
    );
    return response.data;
  }

  /**
   * Get A/B testing variant
   */
  async getVariant(
    key: string,
    variants: string[] = ["A", "B"],
    context: FeatureFlagContext = {},
  ): Promise<{ key: string; variant: string; userId: string }> {
    const response = await apiClient.post("/api/v1/feature-flags/variant", {
      key,
      variants,
      ...context,
    });
    return response.data;
  }

  /**
   * List all feature flags (admin only)
   */
  async listFlags(): Promise<FeatureFlag[]> {
    const response = await apiClient.get<FeatureFlag[]>(
      "/api/v1/feature-flags/flags",
    );
    return response.data;
  }

  /**
   * Get detailed status of a feature flag (admin only)
   */
  async getFlagStatus(key: string): Promise<any> {
    const response = await apiClient.get(`/api/v1/feature-flags/flags/${key}`);
    return response.data;
  }

  /**
   * Create a new feature flag (admin only)
   */
  async createFlag(
    request: CreateFeatureFlagRequest,
  ): Promise<{ message: string }> {
    const response = await apiClient.post(
      "/api/v1/feature-flags/flags",
      request,
    );
    return response.data;
  }

  /**
   * Update an existing feature flag (admin only)
   */
  async updateFlag(
    key: string,
    request: UpdateFeatureFlagRequest,
  ): Promise<{ message: string }> {
    const response = await apiClient.put(
      `/api/v1/feature-flags/flags/${key}`,
      request,
    );
    return response.data;
  }

  /**
   * Delete a feature flag (admin only)
   */
  async deleteFlag(key: string): Promise<{ message: string }> {
    const response = await apiClient.delete(
      `/api/v1/feature-flags/flags/${key}`,
    );
    return response.data;
  }

  /**
   * Update rollout percentage for gradual rollout (admin only)
   */
  async updateRolloutPercentage(key: string, percentage: number): Promise<any> {
    const response = await apiClient.post(
      `/api/v1/feature-flags/flags/${key}/rollout`,
      percentage,
    );
    return response.data;
  }

  /**
   * Get current rollout percentage
   */
  async getRolloutPercentage(
    key: string,
  ): Promise<{ flagKey: string; rolloutPercentage: number }> {
    const response = await apiClient.get(
      `/api/v1/feature-flags/flags/${key}/rollout`,
    );
    return response.data;
  }
}

export const featureFlagsService = new FeatureFlagsService();

/**
 * React hook for feature flag evaluation
 */
export function useFeatureFlag(key: string, context: FeatureFlagContext = {}) {
  const [isEnabled, setIsEnabled] = React.useState<boolean>(false);
  const [isLoading, setIsLoading] = React.useState<boolean>(true);
  const [error, setError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    let mounted = true;

    const evaluateFlag = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const result = await featureFlagsService.evaluateFlag(key, context);

        if (mounted) {
          setIsEnabled(result.enabled);
        }
      } catch (err) {
        if (mounted) {
          setError(
            err instanceof Error
              ? err
              : new Error("Failed to evaluate feature flag"),
          );
          setIsEnabled(false); // Fail safe to disabled
        }
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    };

    evaluateFlag();

    return () => {
      mounted = false;
    };
  }, [key, JSON.stringify(context)]);

  return { isEnabled, isLoading, error };
}

/**
 * React hook for A/B testing variants
 */
export function useFeatureVariant(
  key: string,
  variants: string[] = ["A", "B"],
  context: FeatureFlagContext = {},
) {
  const [variant, setVariant] = React.useState<string>(variants[0]);
  const [isLoading, setIsLoading] = React.useState<boolean>(true);
  const [error, setError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    let mounted = true;

    const getVariant = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const result = await featureFlagsService.getVariant(
          key,
          variants,
          context,
        );

        if (mounted) {
          setVariant(result.variant);
        }
      } catch (err) {
        if (mounted) {
          setError(
            err instanceof Error
              ? err
              : new Error("Failed to get feature variant"),
          );
          setVariant(variants[0]); // Default to first variant
        }
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    };

    getVariant();

    return () => {
      mounted = false;
    };
  }, [key, JSON.stringify(variants), JSON.stringify(context)]);

  return { variant, isLoading, error };
}

/**
 * React hook for bulk feature flag evaluation
 */
export function useFeatureFlags(
  keys: string[],
  context: FeatureFlagContext = {},
) {
  const [flags, setFlags] = React.useState<Record<string, boolean>>({});
  const [isLoading, setIsLoading] = React.useState<boolean>(true);
  const [error, setError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    let mounted = true;

    const evaluateFlags = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const results = await featureFlagsService.evaluateFlags(keys, context);

        if (mounted) {
          const flagsMap = results.reduce(
            (acc, result) => {
              acc[result.key] = result.enabled;
              return acc;
            },
            {} as Record<string, boolean>,
          );

          setFlags(flagsMap);
        }
      } catch (err) {
        if (mounted) {
          setError(
            err instanceof Error
              ? err
              : new Error("Failed to evaluate feature flags"),
          );
          // Set all flags to false as fail-safe
          const failSafeFlags = keys.reduce(
            (acc, key) => {
              acc[key] = false;
              return acc;
            },
            {} as Record<string, boolean>,
          );
          setFlags(failSafeFlags);
        }
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    };

    if (keys.length > 0) {
      evaluateFlags();
    } else {
      setIsLoading(false);
    }

    return () => {
      mounted = false;
    };
  }, [JSON.stringify(keys), JSON.stringify(context)]);

  return { flags, isLoading, error };
}

// Import React for hooks
import React from "react";

export default featureFlagsService;
