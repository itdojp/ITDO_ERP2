import React from 'react'
import { 
  LineChart, 
  Line, 
  AreaChart, 
  Area, 
  BarChart, 
  Bar, 
  PieChart, 
  Pie, 
  Cell,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  TooltipProps
} from 'recharts'
import { cn } from '../../../lib/utils'

export interface ChartData {
  [key: string]: any
}

export interface ChartSeries {
  dataKey: string
  name?: string
  color?: string
  type?: 'line' | 'area' | 'bar'
  strokeWidth?: number
  fill?: boolean
}

export interface ChartProps {
  data: ChartData[]
  type: 'line' | 'area' | 'bar' | 'pie'
  series: ChartSeries[]
  width?: number | string
  height?: number | string
  title?: string
  description?: string
  xAxis?: {
    dataKey: string
    label?: string
    hide?: boolean
    tickFormatter?: (value: any) => string
  }
  yAxis?: {
    label?: string
    hide?: boolean
    domain?: [number | 'auto', number | 'auto']
    tickFormatter?: (value: any) => string
  }
  tooltip?: {
    formatter?: (value: any, name: string, props: any) => [React.ReactNode, string]
    labelFormatter?: (label: any) => React.ReactNode
    hide?: boolean
  }
  legend?: {
    hide?: boolean
    position?: 'top' | 'bottom' | 'left' | 'right'
  }
  grid?: {
    show?: boolean
    strokeDasharray?: string
  }
  colors?: string[]
  loading?: boolean
  error?: string | null
  emptyMessage?: string
  className?: string
  containerClassName?: string
}

const defaultColors = [
  '#3B82F6', // blue-500
  '#10B981', // emerald-500
  '#F59E0B', // amber-500
  '#EF4444', // red-500
  '#8B5CF6', // violet-500
  '#06B6D4', // cyan-500
  '#84CC16', // lime-500
  '#F97316', // orange-500
  '#EC4899', // pink-500
  '#6B7280', // gray-500
]

const Chart = React.memo<ChartProps>(({
  data,
  type,
  series,
  width = '100%',
  height = 400,
  title,
  description,
  xAxis,
  yAxis,
  tooltip,
  legend,
  grid = { show: true, strokeDasharray: '3 3' },
  colors = defaultColors,
  loading = false,
  error = null,
  emptyMessage = 'No data available',
  className,
  containerClassName,
}) => {
  const chartColors = React.useMemo(() => {
    return series.map((s, index) => s.color || colors[index % colors.length])
  }, [series, colors])

  const CustomTooltip: React.FC<TooltipProps<any, any>> = React.useCallback(({ 
    active, 
    payload, 
    label 
  }) => {
    if (!active || !payload || !payload.length) return null

    return (
      <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
        {tooltip?.labelFormatter ? (
          tooltip.labelFormatter(label)
        ) : (
          <p className="text-sm font-medium text-gray-900 mb-1">{label}</p>
        )}
        {payload.map((entry, index) => (
          <div key={index} className="flex items-center gap-2">
            <div 
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-sm text-gray-700">
              {entry.name}: {' '}
              {tooltip?.formatter 
                ? tooltip.formatter(entry.value, entry.name || '', entry)
                : entry.value
              }
            </span>
          </div>
        ))}
      </div>
    )
  }, [tooltip])

  const renderChart = () => {
    const commonProps = {
      data,
      margin: { top: 5, right: 30, left: 20, bottom: 5 },
    }

    switch (type) {
      case 'line':
        return (
          <LineChart {...commonProps}>
            {grid?.show && (
              <CartesianGrid strokeDasharray={grid.strokeDasharray} />
            )}
            {xAxis && !xAxis.hide && (
              <XAxis 
                dataKey={xAxis.dataKey}
                tickFormatter={xAxis.tickFormatter}
                label={xAxis.label ? { value: xAxis.label, position: 'insideBottom', offset: -10 } : undefined}
              />
            )}
            {yAxis && !yAxis.hide && (
              <YAxis 
                domain={yAxis.domain}
                tickFormatter={yAxis.tickFormatter}
                label={yAxis.label ? { value: yAxis.label, angle: -90, position: 'insideLeft' } : undefined}
              />
            )}
            {!tooltip?.hide && <Tooltip content={<CustomTooltip />} />}
            {!legend?.hide && <Legend />}
            {series.map((s, index) => (
              <Line
                key={s.dataKey}
                type="monotone"
                dataKey={s.dataKey}
                name={s.name || s.dataKey}
                stroke={chartColors[index]}
                strokeWidth={s.strokeWidth || 2}
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
              />
            ))}
          </LineChart>
        )

      case 'area':
        return (
          <AreaChart {...commonProps}>
            {grid?.show && (
              <CartesianGrid strokeDasharray={grid.strokeDasharray} />
            )}
            {xAxis && !xAxis.hide && (
              <XAxis 
                dataKey={xAxis.dataKey}
                tickFormatter={xAxis.tickFormatter}
                label={xAxis.label ? { value: xAxis.label, position: 'insideBottom', offset: -10 } : undefined}
              />
            )}
            {yAxis && !yAxis.hide && (
              <YAxis 
                domain={yAxis.domain}
                tickFormatter={yAxis.tickFormatter}
                label={yAxis.label ? { value: yAxis.label, angle: -90, position: 'insideLeft' } : undefined}
              />
            )}
            {!tooltip?.hide && <Tooltip content={<CustomTooltip />} />}
            {!legend?.hide && <Legend />}
            {series.map((s, index) => (
              <Area
                key={s.dataKey}
                type="monotone"
                dataKey={s.dataKey}
                name={s.name || s.dataKey}
                stroke={chartColors[index]}
                fill={s.fill !== false ? chartColors[index] : 'none'}
                fillOpacity={0.6}
                strokeWidth={s.strokeWidth || 2}
              />
            ))}
          </AreaChart>
        )

      case 'bar':
        return (
          <BarChart {...commonProps}>
            {grid?.show && (
              <CartesianGrid strokeDasharray={grid.strokeDasharray} />
            )}
            {xAxis && !xAxis.hide && (
              <XAxis 
                dataKey={xAxis.dataKey}
                tickFormatter={xAxis.tickFormatter}
                label={xAxis.label ? { value: xAxis.label, position: 'insideBottom', offset: -10 } : undefined}
              />
            )}
            {yAxis && !yAxis.hide && (
              <YAxis 
                domain={yAxis.domain}
                tickFormatter={yAxis.tickFormatter}
                label={yAxis.label ? { value: yAxis.label, angle: -90, position: 'insideLeft' } : undefined}
              />
            )}
            {!tooltip?.hide && <Tooltip content={<CustomTooltip />} />}
            {!legend?.hide && <Legend />}
            {series.map((s, index) => (
              <Bar
                key={s.dataKey}
                dataKey={s.dataKey}
                name={s.name || s.dataKey}
                fill={chartColors[index]}
                radius={[2, 2, 0, 0]}
              />
            ))}
          </BarChart>
        )

      case 'pie':
        return (
          <PieChart {...commonProps}>
            {!tooltip?.hide && <Tooltip content={<CustomTooltip />} />}
            {!legend?.hide && <Legend />}
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              outerRadius={120}
              fill="#8884d8"
              dataKey={series[0]?.dataKey || 'value'}
              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={chartColors[index % chartColors.length]} />
              ))}
            </Pie>
          </PieChart>
        )

      default:
        return null
    }
  }

  if (error) {
    return (
      <div className={cn('flex items-center justify-center h-64 text-center', containerClassName)}>
        <div className="text-red-600">
          <p className="text-sm font-medium">Error loading chart</p>
          <p className="text-xs text-gray-500 mt-1">{error}</p>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className={cn('flex items-center justify-center h-64', containerClassName)}>
        <div className="flex items-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600">Loading chart...</span>
        </div>
      </div>
    )
  }

  if (!data || data.length === 0) {
    return (
      <div className={cn('flex items-center justify-center h-64 text-center', containerClassName)}>
        <div className="text-gray-500">
          <p className="text-sm">{emptyMessage}</p>
        </div>
      </div>
    )
  }

  return (
    <div className={cn('w-full', containerClassName)}>
      {(title || description) && (
        <div className="mb-4">
          {title && (
            <h3 className="text-lg font-semibold text-gray-900 mb-1">{title}</h3>
          )}
          {description && (
            <p className="text-sm text-gray-600">{description}</p>
          )}
        </div>
      )}
      
      <div className={cn('w-full', className)} style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          {renderChart()}
        </ResponsiveContainer>
      </div>
    </div>
  )
})

Chart.displayName = 'Chart'

// Chart wrapper components for convenience
export const LineChartComponent = React.memo<Omit<ChartProps, 'type'>>(props => (
  <Chart {...props} type="line" />
))

export const AreaChartComponent = React.memo<Omit<ChartProps, 'type'>>(props => (
  <Chart {...props} type="area" />
))

export const BarChartComponent = React.memo<Omit<ChartProps, 'type'>>(props => (
  <Chart {...props} type="bar" />
))

export const PieChartComponent = React.memo<Omit<ChartProps, 'type'>>(props => (
  <Chart {...props} type="pie" />
))

LineChartComponent.displayName = 'LineChart'
AreaChartComponent.displayName = 'AreaChart'
BarChartComponent.displayName = 'BarChart'
PieChartComponent.displayName = 'PieChart'

export default Chart