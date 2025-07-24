/**
 * Claude Code TypeScript/React Template
 * Copy this structure when creating new components
 */
import { useState, useEffect, useCallback } from 'react';
import type { FC, ReactNode } from 'react';

// Define interfaces for all props and state
interface ExampleComponentProps {
  title: string;
  onAction: (id: string) => void;
  children?: ReactNode;
}

interface ItemData {
  id: string;
  name: string;
  status: 'active' | 'inactive';
}

/**
 * Example component with proper TypeScript annotations
 */
export const ExampleComponent: FC<ExampleComponentProps> = ({
  title,
  onAction,
  children,
}) => {
  // State with explicit types
  const [items, setItems] = useState<ItemData[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Memoized callback with proper types
  const handleItemClick = useCallback(
    (item: ItemData): void => {
      onAction(item.id);
    },
    [onAction]
  );

  // Effect with cleanup
  useEffect(() => {
    let mounted = true;

    const fetchData = async (): Promise<void> => {
      try {
        setLoading(true);
        const response = await fetch('/api/items');
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data: ItemData[] = await response.json();
        
        if (mounted) {
          setItems(data);
          setError(null);
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : 'Unknown error');
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    void fetchData();

    return () => {
      mounted = false;
    };
  }, []);

  // Early return for loading/error states
  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  if (error) {
    return <div className="error">Error: {error}</div>;
  }

  // Main render
  return (
    <div className="example-component">
      <h2>{title}</h2>
      <ul>
        {items.map((item) => (
          <li
            key={item.id}
            onClick={() => handleItemClick(item)}
            className={`item item--${item.status}`}
          >
            {item.name}
          </li>
        ))}
      </ul>
      {children}
    </div>
  );
};