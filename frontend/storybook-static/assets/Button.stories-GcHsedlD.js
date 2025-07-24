import{j as e}from"./jsx-runtime-BQ8Dm5uo.js";import{B as r}from"./Button-hbqBliJw.js";import"./iframe-CyYF4sMK.js";const j={title:"UI/Button",component:r,parameters:{layout:"centered",docs:{description:{component:"A flexible button component with multiple variants, sizes, and states."}}},tags:["autodocs"],argTypes:{variant:{control:{type:"select"},options:["default","destructive","outline","secondary","ghost","link"],description:"The visual style variant of the button"},size:{control:{type:"select"},options:["default","sm","lg","icon"],description:"The size of the button"},disabled:{control:"boolean",description:"Whether the button is disabled"},loading:{control:"boolean",description:"Whether the button is in a loading state"},onClick:{action:"clicked"}},args:{onClick:()=>{}}},a={args:{children:"Default Button"}},t={args:{variant:"destructive",children:"Destructive Button"}},n={args:{variant:"outline",children:"Outline Button"}},s={args:{variant:"secondary",children:"Secondary Button"}},o={args:{variant:"ghost",children:"Ghost Button"}},i={args:{variant:"link",children:"Link Button"}},c={args:{size:"sm",children:"Small Button"}},d={args:{size:"lg",children:"Large Button"}},l={args:{size:"icon",children:"🔍"}},u={args:{disabled:!0,children:"Disabled Button"}},p={args:{loading:!0,children:"Loading Button"}},m={args:{loading:!0,children:"Please wait..."}},g={args:{children:e.jsxs(e.Fragment,{children:[e.jsx("span",{style:{marginRight:"8px"},children:"📧"}),"Send Email"]})}},h={args:{className:"w-full",children:"Full Width Button"},parameters:{layout:"padded"}},B={render:()=>e.jsxs("div",{className:"flex flex-wrap gap-4",children:[e.jsx(r,{variant:"default",children:"Default"}),e.jsx(r,{variant:"destructive",children:"Destructive"}),e.jsx(r,{variant:"outline",children:"Outline"}),e.jsx(r,{variant:"secondary",children:"Secondary"}),e.jsx(r,{variant:"ghost",children:"Ghost"}),e.jsx(r,{variant:"link",children:"Link"})]}),parameters:{layout:"padded"}},v={render:()=>e.jsxs("div",{className:"flex items-center gap-4",children:[e.jsx(r,{size:"sm",children:"Small"}),e.jsx(r,{size:"default",children:"Default"}),e.jsx(r,{size:"lg",children:"Large"}),e.jsx(r,{size:"icon",children:"🔍"})]}),parameters:{layout:"padded"}},f={render:()=>e.jsxs("div",{className:"flex gap-2",children:[e.jsx(r,{variant:"outline",children:"Cancel"}),e.jsx(r,{children:"Confirm"})]}),parameters:{layout:"padded"}},x={args:{children:"Playground Button",variant:"default",size:"default",disabled:!1,loading:!1}};a.parameters={...a.parameters,docs:{...a.parameters?.docs,source:{originalSource:`{
  args: {
    children: 'Default Button'
  }
}`,...a.parameters?.docs?.source}}};t.parameters={...t.parameters,docs:{...t.parameters?.docs,source:{originalSource:`{
  args: {
    variant: 'destructive',
    children: 'Destructive Button'
  }
}`,...t.parameters?.docs?.source}}};n.parameters={...n.parameters,docs:{...n.parameters?.docs,source:{originalSource:`{
  args: {
    variant: 'outline',
    children: 'Outline Button'
  }
}`,...n.parameters?.docs?.source}}};s.parameters={...s.parameters,docs:{...s.parameters?.docs,source:{originalSource:`{
  args: {
    variant: 'secondary',
    children: 'Secondary Button'
  }
}`,...s.parameters?.docs?.source}}};o.parameters={...o.parameters,docs:{...o.parameters?.docs,source:{originalSource:`{
  args: {
    variant: 'ghost',
    children: 'Ghost Button'
  }
}`,...o.parameters?.docs?.source}}};i.parameters={...i.parameters,docs:{...i.parameters?.docs,source:{originalSource:`{
  args: {
    variant: 'link',
    children: 'Link Button'
  }
}`,...i.parameters?.docs?.source}}};c.parameters={...c.parameters,docs:{...c.parameters?.docs,source:{originalSource:`{
  args: {
    size: 'sm',
    children: 'Small Button'
  }
}`,...c.parameters?.docs?.source}}};d.parameters={...d.parameters,docs:{...d.parameters?.docs,source:{originalSource:`{
  args: {
    size: 'lg',
    children: 'Large Button'
  }
}`,...d.parameters?.docs?.source}}};l.parameters={...l.parameters,docs:{...l.parameters?.docs,source:{originalSource:`{
  args: {
    size: 'icon',
    children: '🔍'
  }
}`,...l.parameters?.docs?.source}}};u.parameters={...u.parameters,docs:{...u.parameters?.docs,source:{originalSource:`{
  args: {
    disabled: true,
    children: 'Disabled Button'
  }
}`,...u.parameters?.docs?.source}}};p.parameters={...p.parameters,docs:{...p.parameters?.docs,source:{originalSource:`{
  args: {
    loading: true,
    children: 'Loading Button'
  }
}`,...p.parameters?.docs?.source}}};m.parameters={...m.parameters,docs:{...m.parameters?.docs,source:{originalSource:`{
  args: {
    loading: true,
    children: 'Please wait...'
  }
}`,...m.parameters?.docs?.source}}};g.parameters={...g.parameters,docs:{...g.parameters?.docs,source:{originalSource:`{
  args: {
    children: <>
        <span style={{
        marginRight: '8px'
      }}>📧</span>
        Send Email
      </>
  }
}`,...g.parameters?.docs?.source}}};h.parameters={...h.parameters,docs:{...h.parameters?.docs,source:{originalSource:`{
  args: {
    className: 'w-full',
    children: 'Full Width Button'
  },
  parameters: {
    layout: 'padded'
  }
}`,...h.parameters?.docs?.source}}};B.parameters={...B.parameters,docs:{...B.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex flex-wrap gap-4">
      <Button variant="default">Default</Button>
      <Button variant="destructive">Destructive</Button>
      <Button variant="outline">Outline</Button>
      <Button variant="secondary">Secondary</Button>
      <Button variant="ghost">Ghost</Button>
      <Button variant="link">Link</Button>
    </div>,
  parameters: {
    layout: 'padded'
  }
}`,...B.parameters?.docs?.source}}};v.parameters={...v.parameters,docs:{...v.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex items-center gap-4">
      <Button size="sm">Small</Button>
      <Button size="default">Default</Button>
      <Button size="lg">Large</Button>
      <Button size="icon">🔍</Button>
    </div>,
  parameters: {
    layout: 'padded'
  }
}`,...v.parameters?.docs?.source}}};f.parameters={...f.parameters,docs:{...f.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex gap-2">
      <Button variant="outline">Cancel</Button>
      <Button>Confirm</Button>
    </div>,
  parameters: {
    layout: 'padded'
  }
}`,...f.parameters?.docs?.source}}};x.parameters={...x.parameters,docs:{...x.parameters?.docs,source:{originalSource:`{
  args: {
    children: 'Playground Button',
    variant: 'default',
    size: 'default',
    disabled: false,
    loading: false
  }
}`,...x.parameters?.docs?.source}}};const b=["Default","Destructive","Outline","Secondary","Ghost","Link","Small","Large","Icon","Disabled","Loading","LoadingWithText","WithIcon","FullWidth","AllVariants","AllSizes","ButtonGroup","Playground"];export{v as AllSizes,B as AllVariants,f as ButtonGroup,a as Default,t as Destructive,u as Disabled,h as FullWidth,o as Ghost,l as Icon,d as Large,i as Link,p as Loading,m as LoadingWithText,n as Outline,x as Playground,s as Secondary,c as Small,g as WithIcon,b as __namedExportsOrder,j as default};
