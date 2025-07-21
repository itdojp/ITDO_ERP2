import React from 'react'
import { designTokens, componentStyles, accessibilityGuidelines } from '../design-system'
import Button from '../components/ui/Button'
import { Card, CardHeader, CardBody, CardFooter } from '../components/ui/Layout'
import { TextInput, Select, Checkbox, Radio } from '../components/ui/FormInputs'
import { Grid, Stack, Divider } from '../components/ui/Layout'
import Modal from '../components/ui/Dialog/Modal'
import ConfirmDialog from '../components/ui/Dialog/ConfirmDialog'

const DesignSystemPage: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = React.useState(false)
  const [isConfirmOpen, setIsConfirmOpen] = React.useState(false)

  const ColorPalette: React.FC<{ 
    name: string
    colors: Record<string, string> 
  }> = ({ name, colors }) => (
    <div className="mb-8">
      <h3 className="text-lg font-semibold mb-4 capitalize">{name}</h3>
      <div className="grid grid-cols-11 gap-1">
        {Object.entries(colors).map(([shade, color]) => (
          <div key={shade} className="text-center">
            <div
              className="w-full h-12 rounded mb-2 border border-gray-200"
              style={{ backgroundColor: color }}
              title={`${name}-${shade}: ${color}`}
            />
            <div className="text-xs text-gray-600">{shade}</div>
          </div>
        ))}
      </div>
    </div>
  )

  const TypographyScale: React.FC = () => (
    <div className="space-y-4">
      {Object.entries(designTokens.typography.fontSize).map(([size, [fontSize, { lineHeight }]]) => (
        <div key={size} className="flex items-baseline gap-4">
          <div className="w-16 text-sm text-gray-500">{size}</div>
          <div style={{ fontSize, lineHeight }} className="flex-1">
            The quick brown fox jumps over the lazy dog
          </div>
          <div className="text-xs text-gray-400">{fontSize} / {lineHeight}</div>
        </div>
      ))}
    </div>
  )

  const SpacingScale: React.FC = () => (
    <div className="space-y-2">
      {Object.entries(designTokens.spacing).slice(0, 20).map(([token, value]) => (
        <div key={token} className="flex items-center gap-4">
          <div className="w-16 text-sm text-gray-500">{token}</div>
          <div
            className="bg-blue-200 border border-blue-300"
            style={{ width: value, height: '16px' }}
          />
          <div className="text-xs text-gray-400">{value}</div>
        </div>
      ))}
    </div>
  )

  const ComponentShowcase: React.FC = () => (
    <div className="space-y-8">
      {/* Buttons */}
      <section>
        <h3 className="text-lg font-semibold mb-4">Buttons</h3>
        <div className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {(Object.keys(componentStyles.button.variants) as Array<keyof typeof componentStyles.button.variants>).map(variant => (
              <Button key={variant} variant={variant} size="md">
                {variant.charAt(0).toUpperCase() + variant.slice(1)}
              </Button>
            ))}
          </div>
          <div className="flex flex-wrap gap-2 items-end">
            {(Object.keys(componentStyles.button.sizes) as Array<keyof typeof componentStyles.button.sizes>).map(size => (
              <Button key={size} variant="primary" size={size}>
                Size {size}
              </Button>
            ))}
          </div>
        </div>
      </section>

      {/* Form Inputs */}
      <section>
        <h3 className="text-lg font-semibold mb-4">Form Inputs</h3>
        <div className="space-y-4 max-w-md">
          <TextInput
            label="Text Input"
            placeholder="Enter text here..."
            helpText="This is help text"
          />
          <TextInput
            label="Input with Error"
            placeholder="Invalid input"
            validation={(value) => value.length < 3 ? 'Minimum 3 characters' : null}
            defaultValue="ab"
          />
          <Select
            label="Select Input"
            options={[
              { value: 'option1', label: 'Option 1' },
              { value: 'option2', label: 'Option 2' },
              { value: 'option3', label: 'Option 3' },
            ]}
            placeholder="Choose an option..."
          />
          <div className="space-y-2">
            <Checkbox
              label="Checkbox Option"
              helpText="This is a checkbox"
            />
            <Checkbox
              label="Checked Checkbox"
              defaultChecked
            />
          </div>
          <div className="space-y-2">
            <Radio
              name="radio-example"
              label="Radio Option 1"
              value="option1"
            />
            <Radio
              name="radio-example"
              label="Radio Option 2"
              value="option2"
              defaultChecked
            />
          </div>
        </div>
      </section>

      {/* Cards */}
      <section>
        <h3 className="text-lg font-semibold mb-4">Cards</h3>
        <Grid cols={3} gap={4}>
          <Card>
            <CardHeader>
              <h4 className="font-semibold">Default Card</h4>
            </CardHeader>
            <CardBody>
              <p className="text-gray-600">This is a basic card with header, body, and footer.</p>
            </CardBody>
            <CardFooter>
              <Button variant="outline" size="sm">Cancel</Button>
              <Button variant="primary" size="sm">Confirm</Button>
            </CardFooter>
          </Card>

          <Card variant="elevated">
            <CardHeader>
              <h4 className="font-semibold">Elevated Card</h4>
            </CardHeader>
            <CardBody>
              <p className="text-gray-600">This card has elevated shadow styling.</p>
            </CardBody>
          </Card>

          <Card variant="flat">
            <CardBody>
              <h4 className="font-semibold mb-2">Flat Card</h4>
              <p className="text-gray-600">This is a flat card without shadow.</p>
            </CardBody>
          </Card>
        </Grid>
      </section>

      {/* Layout Components */}
      <section>
        <h3 className="text-lg font-semibold mb-4">Layout Components</h3>
        
        <div className="mb-6">
          <h4 className="font-medium mb-2">Grid Layout</h4>
          <Grid cols={4} gap={3}>
            {Array.from({ length: 8 }, (_, i) => (
              <div key={i} className="bg-blue-100 p-4 rounded text-center">
                Item {i + 1}
              </div>
            ))}
          </Grid>
        </div>

        <div className="mb-6">
          <h4 className="font-medium mb-2">Stack Layout</h4>
          <Stack direction="row" align="center" justify="between" spacing={4}>
            <div className="bg-green-100 p-3 rounded">Start</div>
            <div className="bg-yellow-100 p-3 rounded">Center</div>
            <div className="bg-red-100 p-3 rounded">End</div>
          </Stack>
        </div>

        <Divider />

        <div className="mt-6">
          <h4 className="font-medium mb-2">Vertical Stack</h4>
          <Stack direction="column" spacing={3} className="max-w-xs">
            <div className="bg-purple-100 p-3 rounded">First</div>
            <div className="bg-pink-100 p-3 rounded">Second</div>
            <div className="bg-indigo-100 p-3 rounded">Third</div>
          </Stack>
        </div>
      </section>

      {/* Modals */}
      <section>
        <h3 className="text-lg font-semibold mb-4">Modals & Dialogs</h3>
        <div className="flex gap-4">
          <Button variant="primary" onClick={() => setIsModalOpen(true)}>
            Open Modal
          </Button>
          <Button variant="destructive" onClick={() => setIsConfirmOpen(true)}>
            Open Confirm Dialog
          </Button>
        </div>
      </section>

      {/* Modal Components */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Example Modal"
        description="This is an example modal with various content."
        size="md"
      >
        <div className="space-y-4">
          <p>This modal demonstrates the modal component with proper focus management and accessibility features.</p>
          <TextInput label="Example Input" placeholder="Type something..." />
          <div className="flex justify-end gap-3">
            <Button variant="outline" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={() => setIsModalOpen(false)}>
              Save
            </Button>
          </div>
        </div>
      </Modal>

      <ConfirmDialog
        isOpen={isConfirmOpen}
        onClose={() => setIsConfirmOpen(false)}
        onConfirm={() => {
          setIsConfirmOpen(false)
          alert('Confirmed!')
        }}
        title="Confirm Action"
        description="Are you sure you want to perform this action? This cannot be undone."
        variant="danger"
        confirmText="Delete"
        cancelText="Keep"
      />
    </div>
  )

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-12">
      {/* Header */}
      <header className="border-b border-gray-200 pb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Design System</h1>
        <p className="text-gray-600">
          A comprehensive design system for ITDO ERP frontend components, built with React, TypeScript, and Tailwind CSS.
        </p>
      </header>

      {/* Table of Contents */}
      <nav className="bg-gray-50 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Table of Contents</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <a href="#colors" className="text-blue-600 hover:text-blue-800">Colors</a>
          <a href="#typography" className="text-blue-600 hover:text-blue-800">Typography</a>
          <a href="#spacing" className="text-blue-600 hover:text-blue-800">Spacing</a>
          <a href="#components" className="text-blue-600 hover:text-blue-800">Components</a>
          <a href="#accessibility" className="text-blue-600 hover:text-blue-800">Accessibility</a>
          <a href="#usage" className="text-blue-600 hover:text-blue-800">Usage Guidelines</a>
        </div>
      </nav>

      {/* Design Tokens */}
      <section id="colors">
        <h2 className="text-2xl font-bold mb-6">Color Palette</h2>
        <ColorPalette name="primary" colors={designTokens.colors.primary} />
        <ColorPalette name="secondary" colors={designTokens.colors.secondary} />
        <ColorPalette name="success" colors={designTokens.colors.success} />
        <ColorPalette name="warning" colors={designTokens.colors.warning} />
        <ColorPalette name="error" colors={designTokens.colors.error} />
        <ColorPalette name="neutral" colors={designTokens.colors.neutral} />
      </section>

      <section id="typography">
        <h2 className="text-2xl font-bold mb-6">Typography</h2>
        <TypographyScale />
      </section>

      <section id="spacing">
        <h2 className="text-2xl font-bold mb-6">Spacing Scale</h2>
        <SpacingScale />
      </section>

      {/* Components */}
      <section id="components">
        <h2 className="text-2xl font-bold mb-6">Components</h2>
        <ComponentShowcase />
      </section>

      {/* Accessibility */}
      <section id="accessibility">
        <h2 className="text-2xl font-bold mb-6">Accessibility Guidelines</h2>
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold">WCAG Color Contrast</h3>
            </CardHeader>
            <CardBody>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span>Normal text (AA):</span>
                  <span className="font-mono text-sm bg-gray-100 px-2 py-1 rounded">
                    {accessibilityGuidelines.colorContrast.wcag.aa.normal}:1
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Large text (AA):</span>
                  <span className="font-mono text-sm bg-gray-100 px-2 py-1 rounded">
                    {accessibilityGuidelines.colorContrast.wcag.aa.large}:1
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Normal text (AAA):</span>
                  <span className="font-mono text-sm bg-gray-100 px-2 py-1 rounded">
                    {accessibilityGuidelines.colorContrast.wcag.aaa.normal}:1
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Large text (AAA):</span>
                  <span className="font-mono text-sm bg-gray-100 px-2 py-1 rounded">
                    {accessibilityGuidelines.colorContrast.wcag.aaa.large}:1
                  </span>
                </div>
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold">Keyboard Navigation</h3>
            </CardHeader>
            <CardBody>
              <ul className="space-y-2">
                {accessibilityGuidelines.keyboardNavigation.requirements.map((req, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <span className="text-green-500 mt-1">✓</span>
                    <span>{req}</span>
                  </li>
                ))}
              </ul>
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold">Development Checklist</h3>
            </CardHeader>
            <CardBody>
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium mb-3">Development</h4>
                  <ul className="space-y-1 text-sm">
                    {accessibilityGuidelines.checklist.development.map((item, index) => (
                      <li key={index} className="flex items-start gap-2">
                        <span className="text-gray-400">{item.slice(0, 2)}</span>
                        <span>{item.slice(2)}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h4 className="font-medium mb-3">Testing</h4>
                  <ul className="space-y-1 text-sm">
                    {accessibilityGuidelines.checklist.testing.map((item, index) => (
                      <li key={index} className="flex items-start gap-2">
                        <span className="text-gray-400">{item.slice(0, 2)}</span>
                        <span>{item.slice(2)}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </CardBody>
          </Card>
        </div>
      </section>

      {/* Usage Guidelines */}
      <section id="usage">
        <h2 className="text-2xl font-bold mb-6">Usage Guidelines</h2>
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold">Getting Started</h3>
            </CardHeader>
            <CardBody>
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium mb-2">Import Design System</h4>
                  <pre className="bg-gray-100 p-3 rounded text-sm overflow-x-auto">
{`import { designTokens, componentStyles } from '@/design-system'
import { Button, Card, TextInput } from '@/components/ui'`}
                  </pre>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Using Design Tokens</h4>
                  <pre className="bg-gray-100 p-3 rounded text-sm overflow-x-auto">
{`// Access color tokens
const primaryColor = designTokens.colors.primary[500]

// Use spacing tokens
const spacing = designTokens.spacing[4]

// Typography tokens
const fontSize = designTokens.typography.fontSize.lg`}
                  </pre>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Component Styling</h4>
                  <pre className="bg-gray-100 p-3 rounded text-sm overflow-x-auto">
{`// Use component style constants
import { componentStyles } from '@/design-system'

const buttonClass = cn(
  componentStyles.button.base,
  componentStyles.button.variants.primary,
  componentStyles.button.sizes.md
)`}
                  </pre>
                </div>
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold">Best Practices</h3>
            </CardHeader>
            <CardBody>
              <ul className="space-y-3">
                <li className="flex items-start gap-3">
                  <span className="text-green-500 mt-1">✓</span>
                  <div>
                    <strong>Use design tokens consistently</strong>
                    <p className="text-gray-600 text-sm">Always reference design tokens for colors, spacing, and typography instead of hardcoding values.</p>
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-green-500 mt-1">✓</span>
                  <div>
                    <strong>Follow accessibility guidelines</strong>
                    <p className="text-gray-600 text-sm">Ensure all components meet WCAG 2.1 AA standards for accessibility.</p>
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-green-500 mt-1">✓</span>
                  <div>
                    <strong>Test keyboard navigation</strong>
                    <p className="text-gray-600 text-sm">All interactive elements should be accessible via keyboard navigation.</p>
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-green-500 mt-1">✓</span>
                  <div>
                    <strong>Use semantic HTML</strong>
                    <p className="text-gray-600 text-sm">Choose appropriate HTML elements for their semantic meaning.</p>
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-green-500 mt-1">✓</span>
                  <div>
                    <strong>Implement proper focus management</strong>
                    <p className="text-gray-600 text-sm">Handle focus states correctly, especially in modals and complex interactions.</p>
                  </div>
                </li>
              </ul>
            </CardBody>
          </Card>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-200 pt-6 text-center text-gray-600">
        <p>ITDO ERP Design System - Built with React, TypeScript, and Tailwind CSS</p>
        <p className="text-sm mt-2">
          For questions or contributions, please refer to the project documentation.
        </p>
      </footer>
    </div>
  )
}

export default DesignSystemPage