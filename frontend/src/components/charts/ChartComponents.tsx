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
  ResponsiveContainer
} from 'recharts'
import { CHART_COLORS } from '../../types/dashboard'

// Base Chart Props
interface BaseChartProps {
  data: Record<string, unknown>[]
  height?: number
  className?: string
}

interface ChartTooltipProps {
  active?: boolean
  payload?: Array<{ name: string; value: string | number; color: string }>
  label?: string
}

// Custom Tooltip Component
function CustomTooltip({ active, payload, label }: ChartTooltipProps) {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
        <p className="text-sm font-medium text-gray-900">{label}</p>
        {payload.map((item, index) => (
          <p key={index} className="text-sm" style={{ color: item.color }}>
            {item.name}: {typeof item.value === 'number' ? item.value.toLocaleString() : String(item.value)}
          </p>
        ))}
      </div>
    )
  }
  return null
}

// Line Chart Component
interface LineChartProps extends BaseChartProps {
  xKey: string
  yKey: string
  lineColor?: string
  showGrid?: boolean
  showTooltip?: boolean
}

export function SimpleLineChart({
  data,
  xKey,
  yKey,
  lineColor = CHART_COLORS[0],
  height = 300,
  showGrid = true,
  showTooltip = true,
  className = ''
}: LineChartProps) {
  return (
    <div className={className}>
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />}
          <XAxis 
            dataKey={xKey} 
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: 12, fill: '#6b7280' }}
          />
          <YAxis 
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: 12, fill: '#6b7280' }}
          />
          {showTooltip && <Tooltip content={<CustomTooltip />} />}
          <Line
            type="monotone"
            dataKey={yKey}
            stroke={lineColor}
            strokeWidth={2}
            dot={{ r: 4, fill: lineColor }}
            activeDot={{ r: 6, fill: lineColor }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

// Area Chart Component
interface AreaChartProps extends BaseChartProps {
  xKey: string
  yKey: string
  fillColor?: string
  strokeColor?: string
  showGrid?: boolean
}

export function SimpleAreaChart({
  data,
  xKey,
  yKey,
  fillColor = `${CHART_COLORS[0]}20`,
  strokeColor = CHART_COLORS[0],
  height = 300,
  showGrid = true,
  className = ''
}: AreaChartProps) {
  return (
    <div className={className}>
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />}
          <XAxis 
            dataKey={xKey}
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: 12, fill: '#6b7280' }}
          />
          <YAxis 
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: 12, fill: '#6b7280' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area
            type="monotone"
            dataKey={yKey}
            stroke={strokeColor}
            fill={fillColor}
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

// Bar Chart Component
interface BarChartProps extends BaseChartProps {
  xKey: string
  yKey: string
  barColor?: string
  showGrid?: boolean
}

export function SimpleBarChart({
  data,
  xKey,
  yKey,
  barColor = CHART_COLORS[0],
  height = 300,
  showGrid = true,
  className = ''
}: BarChartProps) {
  return (
    <div className={className}>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />}
          <XAxis 
            dataKey={xKey}
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: 12, fill: '#6b7280' }}
          />
          <YAxis 
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: 12, fill: '#6b7280' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey={yKey} fill={barColor} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

// Pie Chart Component
interface PieChartProps extends BaseChartProps {
  valueKey: string
  showLabels?: boolean
  showLegend?: boolean
  colors?: string[]
}

export function SimplePieChart({
  data,
  valueKey,
  height = 300,
  showLabels = true,
  showLegend = true,
  colors = CHART_COLORS,
  className = ''
}: PieChartProps) {
  return (
    <div className={className}>
      <ResponsiveContainer width="100%" height={height}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={showLabels ? ({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%` : false}
            outerRadius={80}
            fill="#8884d8"
            dataKey={valueKey}
          >
            {data.map((_, index) => (
              <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          {showLegend && <Legend />}
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}

// Multi-Line Chart Component
interface MultiLineChartProps extends BaseChartProps {
  xKey: string
  lines: Array<{
    key: string
    color: string
    name: string
  }>
  showGrid?: boolean
  showLegend?: boolean
}

export function MultiLineChart({
  data,
  xKey,
  lines,
  height = 300,
  showGrid = true,
  showLegend = true,
  className = ''
}: MultiLineChartProps) {
  return (
    <div className={className}>
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />}
          <XAxis 
            dataKey={xKey}
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: 12, fill: '#6b7280' }}
          />
          <YAxis 
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: 12, fill: '#6b7280' }}
          />
          <Tooltip content={<CustomTooltip />} />
          {showLegend && <Legend />}
          {lines.map((line) => (
            <Line
              key={line.key}
              type="monotone"
              dataKey={line.key}
              stroke={line.color}
              strokeWidth={2}
              dot={{ r: 3, fill: line.color }}
              name={line.name}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

// Multi-Bar Chart Component
interface MultiBarChartProps extends BaseChartProps {
  xKey: string
  bars: Array<{
    key: string
    color: string
    name: string
  }>
  showGrid?: boolean
  showLegend?: boolean
}

export function MultiBarChart({
  data,
  xKey,
  bars,
  height = 300,
  showGrid = true,
  showLegend = true,
  className = ''
}: MultiBarChartProps) {
  return (
    <div className={className}>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />}
          <XAxis 
            dataKey={xKey}
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: 12, fill: '#6b7280' }}
          />
          <YAxis 
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: 12, fill: '#6b7280' }}
          />
          <Tooltip content={<CustomTooltip />} />
          {showLegend && <Legend />}
          {bars.map((bar) => (
            <Bar
              key={bar.key}
              dataKey={bar.key}
              fill={bar.color}
              name={bar.name}
              radius={[4, 4, 0, 0]}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

// Chart Container Wrapper
interface ChartContainerProps {
  title: string
  subtitle?: string
  children: React.ReactNode
  className?: string
}

export function ChartContainer({ title, subtitle, children, className = '' }: ChartContainerProps) {
  return (
    <div className={`bg-white rounded-lg border p-4 ${className}`}>
      <div className="mb-4">
        <h3 className="text-lg font-medium text-gray-900">{title}</h3>
        {subtitle && <p className="text-sm text-gray-600 mt-1">{subtitle}</p>}
      </div>
      {children}
    </div>
  )
}