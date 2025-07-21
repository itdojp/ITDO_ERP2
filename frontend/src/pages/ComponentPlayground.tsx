import React from 'react'
import { componentDocumentation, getComponentsByCategory, getAllCategories } from '../design-system/component-docs'
import Button from '../components/ui/Button'
import { Card, CardHeader, CardBody, CardFooter } from '../components/ui/Layout'
import { TextInput, Select } from '../components/ui/FormInputs'
import { Stack } from '../components/ui/Layout'
import { cn } from '../lib/utils'

interface PlaygroundProps {
  [key: string]: any
}

const ComponentPlayground: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = React.useState<string>('Form')
  const [selectedComponent, setSelectedComponent] = React.useState<string>('Button')
  const [componentProps, setComponentProps] = React.useState<PlaygroundProps>({
    variant: 'primary',
    size: 'md',
    loading: false,
    disabled: false,
    rounded: false,
    fullWidth: false,
    children: 'Button Text'
  })
  const [code, setCode] = React.useState<string>('')

  const categories = getAllCategories()
  const componentsInCategory = getComponentsByCategory(selectedCategory as any)
  const currentDoc = componentDocumentation[selectedComponent]

  React.useEffect(() => {
    if (currentDoc) {
      // Initialize props with default values
      const initialProps: PlaygroundProps = {}
      currentDoc.props.forEach(prop => {
        if (prop.defaultValue !== undefined) {
          const value = prop.defaultValue === 'true' ? true 
                      : prop.defaultValue === 'false' ? false 
                      : prop.defaultValue.replace(/'/g, '')
          initialProps[prop.name] = value
        } else if (prop.name === 'children') {
          initialProps[prop.name] = selectedComponent + ' Text'
        }
      })
      setComponentProps(initialProps)
    }
  }, [selectedComponent, currentDoc])

  React.useEffect(() => {
    generateCode()
  }, [componentProps, selectedComponent])

  const generateCode = () => {
    const props = Object.entries(componentProps)
      .filter(([key, value]) => {
        if (key === 'children') return true
        const prop = currentDoc?.props.find(p => p.name === key)
        return prop && value !== prop.defaultValue?.replace(/'/g, '')
      })
      .map(([key, value]) => {
        if (key === 'children') {
          return typeof value === 'string' ? value : '{children}'
        }
        if (typeof value === 'boolean') {
          return value ? key : null
        }
        if (typeof value === 'string') {
          return `${key}="${value}"`
        }
        return `${key}={${JSON.stringify(value)}}`
      })
      .filter(Boolean)

    const propsString = props.filter(p => p !== componentProps.children).join(' ')
    const childrenString = props.find(p => p === componentProps.children) || ''
    
    setCode(`<${selectedComponent}${propsString ? ' ' + propsString : ''}${
      childrenString ? `>${childrenString}</${selectedComponent}>` : ' />'
    }`)
  }

  const updateProp = (propName: string, value: any) => {
    setComponentProps(prev => ({
      ...prev,
      [propName]: value
    }))
  }

  const renderPropControl = (prop: any) => {
    const value = componentProps[prop.name]

    if (prop.type === 'boolean') {
      return (
        <label key={prop.name} className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={value || false}
            onChange={(e) => updateProp(prop.name, e.target.checked)}
            className="rounded border-gray-300"
          />
          <span className="text-sm">{prop.name}</span>
          {prop.required && <span className="text-red-500">*</span>}
        </label>
      )
    }

    if (prop.options) {
      return (
        <div key={prop.name}>
          <label className="block text-sm font-medium mb-1">
            {prop.name}
            {prop.required && <span className="text-red-500">*</span>}
          </label>
          <Select
            options={prop.options.map(opt => ({ value: opt, label: opt }))}
            value={value || prop.defaultValue?.replace(/'/g, '') || ''}
            onChange={(selectedValue) => updateProp(prop.name, selectedValue)}
            placeholder={`Select ${prop.name}...`}
          />
        </div>
      )
    }

    if (prop.type.includes('string') || prop.name === 'children') {
      return (
        <div key={prop.name}>
          <label className="block text-sm font-medium mb-1">
            {prop.name}
            {prop.required && <span className="text-red-500">*</span>}
          </label>
          <TextInput
            value={value || ''}
            onChange={(e) => updateProp(prop.name, e.target.value)}
            placeholder={prop.description}
          />
        </div>
      )
    }

    if (prop.type.includes('number')) {
      return (
        <div key={prop.name}>
          <label className="block text-sm font-medium mb-1">
            {prop.name}
            {prop.required && <span className="text-red-500">*</span>}
          </label>
          <TextInput
            type="number"
            value={value || ''}
            onChange={(e) => updateProp(prop.name, Number(e.target.value))}
            placeholder={prop.description}
          />
        </div>
      )
    }

    return null
  }

  const renderComponentPreview = () => {
    try {
      switch (selectedComponent) {
        case 'Button':
          return (
            <Button
              variant={componentProps.variant}
              size={componentProps.size}
              loading={componentProps.loading}
              disabled={componentProps.disabled}
              rounded={componentProps.rounded}
              fullWidth={componentProps.fullWidth}
            >
              {componentProps.children || 'Button'}
            </Button>
          )

        case 'TextInput':
          return (
            <div className="max-w-sm">
              <TextInput
                label={componentProps.label || 'Example Input'}
                type={componentProps.type}
                placeholder={componentProps.placeholder}
                helpText={componentProps.helpText}
                required={componentProps.required}
                disabled={componentProps.disabled}
              />
            </div>
          )

        case 'Card':
          return (
            <Card variant={componentProps.variant} className="max-w-sm">
              <CardHeader>
                <h3 className="font-semibold">Card Title</h3>
              </CardHeader>
              <CardBody>
                <p>This is the card content. You can put any content here.</p>
              </CardBody>
              <CardFooter>
                <Button variant="outline" size="sm">Cancel</Button>
                <Button variant="primary" size="sm">Confirm</Button>
              </CardFooter>
            </Card>
          )

        default:
          return (
            <div className="p-8 border-2 border-dashed border-gray-300 rounded-lg text-center text-gray-500">
              Preview not available for {selectedComponent}
            </div>
          )
      }
    } catch (error) {
      return (
        <div className="p-8 border-2 border-dashed border-red-300 rounded-lg text-center text-red-500">
          Error rendering preview: {error instanceof Error ? error.message : 'Unknown error'}
        </div>
      )
    }
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Component Playground</h1>
        <p className="text-gray-600">
          Interactive playground for testing and experimenting with design system components.
        </p>
      </header>

      <div className="grid lg:grid-cols-4 gap-6">
        {/* Component Selection Sidebar */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <h2 className="text-lg font-semibold">Components</h2>
            </CardHeader>
            <CardBody className="space-y-4">
              {/* Category Filter */}
              <div>
                <label className="block text-sm font-medium mb-2">Category</label>
                <Select
                  options={categories.map(cat => ({ value: cat, label: cat }))}
                  value={selectedCategory}
                  onChange={setSelectedCategory}
                />
              </div>

              {/* Component List */}
              <div>
                <label className="block text-sm font-medium mb-2">Component</label>
                <div className="space-y-1">
                  {componentsInCategory.map(comp => (
                    <button
                      key={comp.name}
                      className={cn(
                        "w-full text-left px-3 py-2 rounded text-sm transition-colors",
                        selectedComponent === comp.name
                          ? "bg-blue-100 text-blue-700"
                          : "hover:bg-gray-100"
                      )}
                      onClick={() => setSelectedComponent(comp.name)}
                    >
                      {comp.name}
                      <div className="text-xs text-gray-500 mt-1">
                        {comp.status === 'beta' && '(Beta)'}
                        {comp.status === 'deprecated' && '(Deprecated)'}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </CardBody>
          </Card>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-3 space-y-6">
          {/* Component Info */}
          {currentDoc && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-semibold">{currentDoc.name}</h2>
                  <div className="flex items-center gap-2">
                    <span className={cn(
                      "px-2 py-1 text-xs rounded-full",
                      currentDoc.status === 'stable' && "bg-green-100 text-green-800",
                      currentDoc.status === 'beta' && "bg-yellow-100 text-yellow-800",
                      currentDoc.status === 'deprecated' && "bg-red-100 text-red-800"
                    )}>
                      {currentDoc.status}
                    </span>
                    <span className="text-xs text-gray-500">v{currentDoc.version}</span>
                  </div>
                </div>
              </CardHeader>
              <CardBody>
                <p className="text-gray-600 mb-4">{currentDoc.description}</p>
                <div className="text-sm text-gray-500">
                  <strong>Category:</strong> {currentDoc.category}
                </div>
              </CardBody>
            </Card>
          )}

          <div className="grid lg:grid-cols-2 gap-6">
            {/* Props Panel */}
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold">Props</h3>
              </CardHeader>
              <CardBody>
                <div className="space-y-4">
                  {currentDoc?.props
                    .filter(prop => !['onClick', 'onClose', 'onConfirm', 'isOpen'].includes(prop.name))
                    .map(renderPropControl)}
                </div>
              </CardBody>
            </Card>

            {/* Preview Panel */}
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold">Preview</h3>
              </CardHeader>
              <CardBody>
                <div className="p-6 bg-gray-50 rounded-lg">
                  {renderComponentPreview()}
                </div>
              </CardBody>
            </Card>
          </div>

          {/* Generated Code */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">Generated Code</h3>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigator.clipboard.writeText(code)}
                >
                  Copy Code
                </Button>
              </div>
            </CardHeader>
            <CardBody>
              <pre className="bg-gray-100 p-4 rounded text-sm overflow-x-auto">
                <code>{code}</code>
              </pre>
            </CardBody>
          </Card>

          {/* API Documentation */}
          {currentDoc && (
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold">API Documentation</h3>
              </CardHeader>
              <CardBody>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-2 px-3">Prop</th>
                        <th className="text-left py-2 px-3">Type</th>
                        <th className="text-left py-2 px-3">Required</th>
                        <th className="text-left py-2 px-3">Default</th>
                        <th className="text-left py-2 px-3">Description</th>
                      </tr>
                    </thead>
                    <tbody>
                      {currentDoc.props.map(prop => (
                        <tr key={prop.name} className="border-b">
                          <td className="py-2 px-3 font-mono text-sm">{prop.name}</td>
                          <td className="py-2 px-3 font-mono text-xs text-gray-600">{prop.type}</td>
                          <td className="py-2 px-3">
                            {prop.required ? (
                              <span className="text-red-500">✓</span>
                            ) : (
                              <span className="text-gray-400">-</span>
                            )}
                          </td>
                          <td className="py-2 px-3 font-mono text-xs text-gray-600">
                            {prop.defaultValue || '-'}
                          </td>
                          <td className="py-2 px-3 text-gray-700">{prop.description}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardBody>
            </Card>
          )}

          {/* Examples */}
          {currentDoc && currentDoc.examples.length > 0 && (
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold">Examples</h3>
              </CardHeader>
              <CardBody>
                <div className="space-y-6">
                  {currentDoc.examples.map((example, index) => (
                    <div key={index}>
                      <h4 className="font-medium mb-2">{example.title}</h4>
                      <p className="text-gray-600 text-sm mb-3">{example.description}</p>
                      <pre className="bg-gray-100 p-4 rounded text-sm overflow-x-auto">
                        <code>{example.code}</code>
                      </pre>
                    </div>
                  ))}
                </div>
              </CardBody>
            </Card>
          )}

          {/* Accessibility */}
          {currentDoc && currentDoc.accessibility.length > 0 && (
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold">Accessibility</h3>
              </CardHeader>
              <CardBody>
                <div className="space-y-4">
                  {currentDoc.accessibility.map((note, index) => (
                    <div key={index} className="border-l-4 border-blue-200 pl-4">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                          {note.type}
                        </span>
                      </div>
                      <p className="text-gray-700 text-sm mb-2">{note.description}</p>
                      {note.implementation && (
                        <pre className="bg-gray-100 p-2 rounded text-xs overflow-x-auto">
                          <code>{note.implementation}</code>
                        </pre>
                      )}
                    </div>
                  ))}
                </div>
              </CardBody>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}

export default ComponentPlayground