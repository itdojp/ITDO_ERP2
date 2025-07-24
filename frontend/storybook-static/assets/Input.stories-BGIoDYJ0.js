import{j as e}from"./jsx-runtime-BQ8Dm5uo.js";import{r as t,e as $e}from"./iframe-CyYF4sMK.js";import{B as de}from"./Button-hbqBliJw.js";const a=t.forwardRef(({size:b="md",variant:v="default",status:S="default",prefix:I,suffix:d,addonBefore:h,addonAfter:n,allowClear:ee=!1,showCount:re=!1,maxLength:c,loading:f=!1,bordered:ae=!0,debounce:i,onDebounceChange:g,className:E="",wrapperClassName:se="",inputClassName:R="",onChange:te,onPressEnter:T,visibilityToggle:ne=!1,type:u="text",value:l,defaultValue:C,disabled:m,...x},le)=>{const[N,A]=t.useState(C||""),[w,s]=t.useState(!1),[y,j]=t.useState(!1),p=t.useRef(null),o=t.useRef(),ce=le||p,oe=l!==void 0?l:N,ie=u==="password",ye=ie&&w?"text":u,ue=()=>({sm:"px-2 py-1 text-sm",md:"px-3 py-2 text-sm",lg:"px-4 py-3 text-base"})[b],be=()=>({default:"bg-white border border-gray-300",filled:"bg-gray-50 border-0",outlined:"bg-transparent border-2 border-gray-300",borderless:"bg-transparent border-0"})[v],ve=()=>m?"border-gray-200 text-gray-400 bg-gray-50":{default:"",error:"border-red-500 focus:border-red-500 focus:ring-red-500",warning:"border-yellow-500 focus:border-yellow-500 focus:ring-yellow-500",success:"border-green-500 focus:border-green-500 focus:ring-green-500"}[S],me=()=>`${`
      relative inline-flex items-center w-full transition-colors duration-200
      ${be()}
      ${ve()}
      ${y&&S==="default"?"border-blue-500 ring-1 ring-blue-500":""}
      ${m?"opacity-50 cursor-not-allowed":"cursor-text"}
      ${ae?"":"border-0"}
      rounded-md
    `} ${se}`.trim(),Ne=r=>{const fe=r.target.value;l===void 0&&A(fe),te?.(r),i&&g&&(o.current&&clearTimeout(o.current),o.current=setTimeout(()=>{g(fe)},i))},we=()=>{const r={target:{value:""},currentTarget:{value:""}};l===void 0&&A(""),te?.(r),ce.current?.focus()},je=r=>{j(!0),x.onFocus?.(r)},Se=r=>{j(!1),x.onBlur?.(r)},Ie=r=>{r.key==="Enter"&&T?.(r),x.onKeyDown?.(r)},Ee=()=>{s(!w)},Re=ee&&oe&&!m,Te=re&&c,pe=String(oe).length;t.useEffect(()=>()=>{o.current&&clearTimeout(o.current)},[]);const Ce=()=>I?e.jsx("span",{className:"flex-shrink-0 text-gray-500 mr-2",children:I}):null,Ae=()=>{const r=[];return f&&r.push(e.jsx("div",{className:"flex-shrink-0 ml-2",children:e.jsx("div",{className:"w-4 h-4 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin"})},"loading")),Te&&r.push(e.jsxs("span",{className:`flex-shrink-0 ml-2 text-xs ${pe>c?"text-red-500":"text-gray-400"}`,children:[pe,"/",c]},"count")),Re&&r.push(e.jsx("button",{type:"button",onClick:we,className:"flex-shrink-0 ml-2 p-1 text-gray-400 hover:text-gray-600 transition-colors rounded",tabIndex:-1,children:e.jsx("svg",{className:"w-4 h-4",fill:"none",stroke:"currentColor",viewBox:"0 0 24 24",children:e.jsx("path",{strokeLinecap:"round",strokeLinejoin:"round",strokeWidth:2,d:"M6 18L18 6M6 6l12 12"})})},"clear")),ie&&ne&&r.push(e.jsx("button",{type:"button",onClick:Ee,className:"flex-shrink-0 ml-2 p-1 text-gray-400 hover:text-gray-600 transition-colors rounded",tabIndex:-1,children:w?e.jsx("svg",{className:"w-4 h-4",fill:"none",stroke:"currentColor",viewBox:"0 0 24 24",children:e.jsx("path",{strokeLinecap:"round",strokeLinejoin:"round",strokeWidth:2,d:"M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21"})}):e.jsxs("svg",{className:"w-4 h-4",fill:"none",stroke:"currentColor",viewBox:"0 0 24 24",children:[e.jsx("path",{strokeLinecap:"round",strokeLinejoin:"round",strokeWidth:2,d:"M15 12a3 3 0 11-6 0 3 3 0 016 0z"}),e.jsx("path",{strokeLinecap:"round",strokeLinejoin:"round",strokeWidth:2,d:"M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"})]})},"visibility")),d&&r.push(e.jsx("span",{className:"flex-shrink-0 ml-2 text-gray-500",children:d},"suffix")),r.length>0?e.jsx("div",{className:"flex items-center",children:r}):null},he=e.jsxs("div",{className:me(),children:[Ce(),e.jsx("input",{...x,ref:ce,type:ye,value:oe,onChange:Ne,onFocus:je,onBlur:Se,onKeyDown:Ie,maxLength:c,disabled:m,className:`
          flex-1 bg-transparent outline-none placeholder-gray-400 min-w-0
          ${m?"cursor-not-allowed":""}
          ${R}
        `}),Ae()]});return h||n?e.jsxs("div",{className:`inline-flex w-full ${E}`,children:[h&&e.jsx("span",{className:`
            inline-flex items-center px-3 border border-r-0 border-gray-300 
            bg-gray-50 text-gray-500 text-sm rounded-l-md
            ${ue()}
          `,children:h}),e.jsx("div",{className:"flex-1",children:$e.cloneElement(he,{className:`
              ${me()} 
              ${h?"rounded-l-none border-l-0":""}
              ${n?"rounded-r-none border-r-0":""}
            `})}),n&&e.jsx("span",{className:`
            inline-flex items-center px-3 border border-l-0 border-gray-300 
            bg-gray-50 text-gray-500 text-sm rounded-r-md
            ${ue()}
          `,children:n})]}):e.jsx("div",{className:E,children:he})});a.displayName="Input";const ge=t.forwardRef((b,v)=>e.jsx(a,{...b,ref:v,type:"password",visibilityToggle:!0}));ge.displayName="Input.Password";const xe=t.forwardRef(({size:b="md",variant:v="default",status:S="default",showCount:I=!1,maxLength:d,allowClear:h=!1,autoSize:n=!1,bordered:ee=!0,className:re="",onChange:c,value:f,defaultValue:ae,disabled:i,...g},E)=>{const[se,R]=t.useState(ae||""),[te,T]=t.useState(!1),ne=t.useRef(null),u=E||ne,l=f!==void 0?f:se,C=String(l).length,m=()=>({sm:"px-2 py-1 text-sm",md:"px-3 py-2 text-sm",lg:"px-4 py-3 text-base"})[b],x=()=>({default:"bg-white border border-gray-300",filled:"bg-gray-50 border-0",outlined:"bg-transparent border-2 border-gray-300",borderless:"bg-transparent border-0"})[v],le=()=>i?"border-gray-200 text-gray-400 bg-gray-50":{default:"focus:border-blue-500 focus:ring-1 focus:ring-blue-500",error:"border-red-500 focus:border-red-500 focus:ring-red-500",warning:"border-yellow-500 focus:border-yellow-500 focus:ring-yellow-500",success:"border-green-500 focus:border-green-500 focus:ring-green-500"}[S],N=()=>{if(n&&u.current){const s=u.current;s.style.height="auto";const y=typeof n=="object"?n.minRows:void 0,j=typeof n=="object"?n.maxRows:void 0;let p=s.scrollHeight;if(y){const o=parseInt(getComputedStyle(s).lineHeight);p=Math.max(p,o*y)}if(j){const o=parseInt(getComputedStyle(s).lineHeight);p=Math.min(p,o*j)}s.style.height=`${p}px`}},A=s=>{const y=s.target.value;f===void 0&&R(y),c?.(s),N()},w=()=>{const s={target:{value:""},currentTarget:{value:""}};f===void 0&&R(""),c?.(s),u.current?.focus(),N()};return t.useEffect(()=>{N()},[l,n]),e.jsxs("div",{className:`relative ${re}`,children:[e.jsx("textarea",{...g,ref:u,value:l,onChange:A,onFocus:s=>{T(!0),g.onFocus?.(s)},onBlur:s=>{T(!1),g.onBlur?.(s)},maxLength:d,disabled:i,className:`
          w-full resize-none outline-none placeholder-gray-400 transition-colors duration-200
          ${m()}
          ${x()}
          ${le()}
          ${ee?"":"border-0"}
          ${i?"opacity-50 cursor-not-allowed":""}
          rounded-md
        `}),h&&l&&!i&&e.jsx("button",{type:"button",onClick:w,className:"absolute top-2 right-2 p-1 text-gray-400 hover:text-gray-600 transition-colors rounded",tabIndex:-1,children:e.jsx("svg",{className:"w-4 h-4",fill:"none",stroke:"currentColor",viewBox:"0 0 24 24",children:e.jsx("path",{strokeLinecap:"round",strokeLinejoin:"round",strokeWidth:2,d:"M6 18L18 6M6 6l12 12"})})}),I&&d&&e.jsxs("div",{className:`absolute bottom-2 right-2 text-xs ${C>d?"text-red-500":"text-gray-400"}`,children:[C,"/",d]})]})});xe.displayName="Input.TextArea";a.Password=ge;a.TextArea=xe;a.__docgenInfo={description:"",methods:[],displayName:"Input",props:{size:{required:!1,tsType:{name:"union",raw:'"sm" | "md" | "lg"',elements:[{name:"literal",value:'"sm"'},{name:"literal",value:'"md"'},{name:"literal",value:'"lg"'}]},description:"",defaultValue:{value:'"md"',computed:!1}},variant:{required:!1,tsType:{name:"union",raw:'"default" | "filled" | "outlined" | "borderless"',elements:[{name:"literal",value:'"default"'},{name:"literal",value:'"filled"'},{name:"literal",value:'"outlined"'},{name:"literal",value:'"borderless"'}]},description:"",defaultValue:{value:'"default"',computed:!1}},status:{required:!1,tsType:{name:"union",raw:'"default" | "error" | "warning" | "success"',elements:[{name:"literal",value:'"default"'},{name:"literal",value:'"error"'},{name:"literal",value:'"warning"'},{name:"literal",value:'"success"'}]},description:"",defaultValue:{value:'"default"',computed:!1}},prefix:{required:!1,tsType:{name:"ReactReactNode",raw:"React.ReactNode"},description:""},suffix:{required:!1,tsType:{name:"ReactReactNode",raw:"React.ReactNode"},description:""},addonBefore:{required:!1,tsType:{name:"ReactReactNode",raw:"React.ReactNode"},description:""},addonAfter:{required:!1,tsType:{name:"ReactReactNode",raw:"React.ReactNode"},description:""},allowClear:{required:!1,tsType:{name:"boolean"},description:"",defaultValue:{value:"false",computed:!1}},showCount:{required:!1,tsType:{name:"boolean"},description:"",defaultValue:{value:"false",computed:!1}},maxLength:{required:!1,tsType:{name:"number"},description:""},loading:{required:!1,tsType:{name:"boolean"},description:"",defaultValue:{value:"false",computed:!1}},bordered:{required:!1,tsType:{name:"boolean"},description:"",defaultValue:{value:"true",computed:!1}},debounce:{required:!1,tsType:{name:"number"},description:""},onDebounceChange:{required:!1,tsType:{name:"signature",type:"function",raw:"(value: string) => void",signature:{arguments:[{type:{name:"string"},name:"value"}],return:{name:"void"}}},description:""},className:{required:!1,tsType:{name:"string"},description:"",defaultValue:{value:'""',computed:!1}},wrapperClassName:{required:!1,tsType:{name:"string"},description:"",defaultValue:{value:'""',computed:!1}},inputClassName:{required:!1,tsType:{name:"string"},description:"",defaultValue:{value:'""',computed:!1}},onPressEnter:{required:!1,tsType:{name:"signature",type:"function",raw:"(e: React.KeyboardEvent<HTMLInputElement>) => void",signature:{arguments:[{type:{name:"ReactKeyboardEvent",raw:"React.KeyboardEvent<HTMLInputElement>",elements:[{name:"HTMLInputElement"}]},name:"e"}],return:{name:"void"}}},description:""},visibilityToggle:{required:!1,tsType:{name:"boolean"},description:"",defaultValue:{value:"false",computed:!1}},type:{defaultValue:{value:'"text"',computed:!1},required:!1}},composes:["Omit"]};const Ve={title:"UI/Input",component:a,parameters:{layout:"padded",docs:{description:{component:"A flexible input component with various types, sizes, and addon support."}}},tags:["autodocs"],argTypes:{type:{control:{type:"select"},options:["text","email","password","number","tel","url","search"],description:"The type of input"},size:{control:{type:"select"},options:["sm","default","lg"],description:"The size of the input"},disabled:{control:"boolean",description:"Whether the input is disabled"},readOnly:{control:"boolean",description:"Whether the input is read-only"},error:{control:"boolean",description:"Whether the input has an error state"},placeholder:{control:"text",description:"Placeholder text"},value:{control:"text",description:"Input value"},onChange:{action:"changed"},onFocus:{action:"focused"},onBlur:{action:"blurred"}},args:{onChange:()=>{},onFocus:()=>{},onBlur:()=>{}}},$={args:{placeholder:"Enter text..."}},k={args:{value:"Sample text",placeholder:"Enter text..."}},L={args:{type:"email",placeholder:"Enter your email..."}},M={args:{type:"password",placeholder:"Enter password..."}},V={args:{type:"number",placeholder:"Enter number..."}},D={args:{type:"search",placeholder:"Search..."}},P={args:{size:"sm",placeholder:"Small input"}},B={args:{size:"lg",placeholder:"Large input"}},W={args:{disabled:!0,placeholder:"Disabled input",value:"Cannot edit this"}},q={args:{readOnly:!0,value:"This is read-only"}},z={args:{error:!0,placeholder:"Input with error",value:"Invalid input"}},F={args:{loading:!0,placeholder:"Loading state..."}},O={args:{leftAddon:"$",placeholder:"0.00",type:"number"}},H={args:{rightAddon:"@example.com",placeholder:"username"}},U={args:{leftAddon:"$",rightAddon:"USD",placeholder:"0.00",type:"number"}},K={args:{leftAddon:"🔍",placeholder:"Search...",type:"search"}},_={render:()=>e.jsxs("div",{className:"flex w-full max-w-sm items-center space-x-2",children:[e.jsx(a,{type:"search",placeholder:"Search...",className:"flex-1",leftAddon:"🔍"}),e.jsx(de,{type:"submit",children:"Search"})]})},Y={render:()=>e.jsxs("div",{className:"space-y-4 w-full max-w-md",children:[e.jsx(a,{type:"email",placeholder:"Enter your email",leftAddon:"📧"}),e.jsx(de,{className:"w-full",children:"Sign Up"})]})},G={render:()=>e.jsxs("div",{className:"space-y-2",children:[e.jsx("label",{className:"text-sm font-medium",children:"Price"}),e.jsx(a,{type:"number",placeholder:"0.00",leftAddon:"$",rightAddon:"USD"}),e.jsx("p",{className:"text-xs text-gray-500",children:"Enter the price in USD"})]})},J={render:()=>e.jsxs("div",{className:"space-y-4 w-full max-w-md",children:[e.jsxs("div",{children:[e.jsx("label",{className:"text-sm font-medium",children:"Name"}),e.jsx(a,{placeholder:"Your name",className:"mt-1"})]}),e.jsxs("div",{children:[e.jsx("label",{className:"text-sm font-medium",children:"Email"}),e.jsx(a,{type:"email",placeholder:"your@email.com",className:"mt-1"})]}),e.jsxs("div",{children:[e.jsx("label",{className:"text-sm font-medium",children:"Phone"}),e.jsx(a,{type:"tel",placeholder:"+1 (555) 000-0000",className:"mt-1"})]}),e.jsx(de,{className:"w-full",children:"Submit"})]})},Q={render:()=>e.jsxs("div",{className:"space-y-4",children:[e.jsxs("div",{children:[e.jsx("label",{className:"text-sm font-medium",children:"Small"}),e.jsx(a,{size:"sm",placeholder:"Small input",className:"mt-1"})]}),e.jsxs("div",{children:[e.jsx("label",{className:"text-sm font-medium",children:"Default"}),e.jsx(a,{placeholder:"Default input",className:"mt-1"})]}),e.jsxs("div",{children:[e.jsx("label",{className:"text-sm font-medium",children:"Large"}),e.jsx(a,{size:"lg",placeholder:"Large input",className:"mt-1"})]})]})},X={render:()=>e.jsxs("div",{className:"space-y-4",children:[e.jsxs("div",{children:[e.jsx("label",{className:"text-sm font-medium",children:"Normal"}),e.jsx(a,{placeholder:"Normal state",className:"mt-1"})]}),e.jsxs("div",{children:[e.jsx("label",{className:"text-sm font-medium",children:"Focused"}),e.jsx(a,{placeholder:"Focused state",className:"mt-1",autoFocus:!0})]}),e.jsxs("div",{children:[e.jsx("label",{className:"text-sm font-medium",children:"Error"}),e.jsx(a,{error:!0,placeholder:"Error state",className:"mt-1"})]}),e.jsxs("div",{children:[e.jsx("label",{className:"text-sm font-medium",children:"Disabled"}),e.jsx(a,{disabled:!0,placeholder:"Disabled state",className:"mt-1"})]}),e.jsxs("div",{children:[e.jsx("label",{className:"text-sm font-medium",children:"Read-only"}),e.jsx(a,{readOnly:!0,value:"Read-only value",className:"mt-1"})]})]})},Z={args:{placeholder:"Playground input",type:"text",size:"default",disabled:!1,readOnly:!1,error:!1,loading:!1}};$.parameters={...$.parameters,docs:{...$.parameters?.docs,source:{originalSource:`{
  args: {
    placeholder: 'Enter text...'
  }
}`,...$.parameters?.docs?.source}}};k.parameters={...k.parameters,docs:{...k.parameters?.docs,source:{originalSource:`{
  args: {
    value: 'Sample text',
    placeholder: 'Enter text...'
  }
}`,...k.parameters?.docs?.source}}};L.parameters={...L.parameters,docs:{...L.parameters?.docs,source:{originalSource:`{
  args: {
    type: 'email',
    placeholder: 'Enter your email...'
  }
}`,...L.parameters?.docs?.source}}};M.parameters={...M.parameters,docs:{...M.parameters?.docs,source:{originalSource:`{
  args: {
    type: 'password',
    placeholder: 'Enter password...'
  }
}`,...M.parameters?.docs?.source}}};V.parameters={...V.parameters,docs:{...V.parameters?.docs,source:{originalSource:`{
  args: {
    type: 'number',
    placeholder: 'Enter number...'
  }
}`,...V.parameters?.docs?.source}}};D.parameters={...D.parameters,docs:{...D.parameters?.docs,source:{originalSource:`{
  args: {
    type: 'search',
    placeholder: 'Search...'
  }
}`,...D.parameters?.docs?.source}}};P.parameters={...P.parameters,docs:{...P.parameters?.docs,source:{originalSource:`{
  args: {
    size: 'sm',
    placeholder: 'Small input'
  }
}`,...P.parameters?.docs?.source}}};B.parameters={...B.parameters,docs:{...B.parameters?.docs,source:{originalSource:`{
  args: {
    size: 'lg',
    placeholder: 'Large input'
  }
}`,...B.parameters?.docs?.source}}};W.parameters={...W.parameters,docs:{...W.parameters?.docs,source:{originalSource:`{
  args: {
    disabled: true,
    placeholder: 'Disabled input',
    value: 'Cannot edit this'
  }
}`,...W.parameters?.docs?.source}}};q.parameters={...q.parameters,docs:{...q.parameters?.docs,source:{originalSource:`{
  args: {
    readOnly: true,
    value: 'This is read-only'
  }
}`,...q.parameters?.docs?.source}}};z.parameters={...z.parameters,docs:{...z.parameters?.docs,source:{originalSource:`{
  args: {
    error: true,
    placeholder: 'Input with error',
    value: 'Invalid input'
  }
}`,...z.parameters?.docs?.source}}};F.parameters={...F.parameters,docs:{...F.parameters?.docs,source:{originalSource:`{
  args: {
    loading: true,
    placeholder: 'Loading state...'
  }
}`,...F.parameters?.docs?.source}}};O.parameters={...O.parameters,docs:{...O.parameters?.docs,source:{originalSource:`{
  args: {
    leftAddon: '$',
    placeholder: '0.00',
    type: 'number'
  }
}`,...O.parameters?.docs?.source}}};H.parameters={...H.parameters,docs:{...H.parameters?.docs,source:{originalSource:`{
  args: {
    rightAddon: '@example.com',
    placeholder: 'username'
  }
}`,...H.parameters?.docs?.source}}};U.parameters={...U.parameters,docs:{...U.parameters?.docs,source:{originalSource:`{
  args: {
    leftAddon: '$',
    rightAddon: 'USD',
    placeholder: '0.00',
    type: 'number'
  }
}`,...U.parameters?.docs?.source}}};K.parameters={...K.parameters,docs:{...K.parameters?.docs,source:{originalSource:`{
  args: {
    leftAddon: '🔍',
    placeholder: 'Search...',
    type: 'search'
  }
}`,...K.parameters?.docs?.source}}};_.parameters={..._.parameters,docs:{..._.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex w-full max-w-sm items-center space-x-2">
      <Input type="search" placeholder="Search..." className="flex-1" leftAddon="🔍" />
      <Button type="submit">Search</Button>
    </div>
}`,..._.parameters?.docs?.source}}};Y.parameters={...Y.parameters,docs:{...Y.parameters?.docs,source:{originalSource:`{
  render: () => <div className="space-y-4 w-full max-w-md">
      <Input type="email" placeholder="Enter your email" leftAddon="📧" />
      <Button className="w-full">Sign Up</Button>
    </div>
}`,...Y.parameters?.docs?.source}}};G.parameters={...G.parameters,docs:{...G.parameters?.docs,source:{originalSource:`{
  render: () => <div className="space-y-2">
      <label className="text-sm font-medium">Price</label>
      <Input type="number" placeholder="0.00" leftAddon="$" rightAddon="USD" />
      <p className="text-xs text-gray-500">Enter the price in USD</p>
    </div>
}`,...G.parameters?.docs?.source}}};J.parameters={...J.parameters,docs:{...J.parameters?.docs,source:{originalSource:`{
  render: () => <div className="space-y-4 w-full max-w-md">
      <div>
        <label className="text-sm font-medium">Name</label>
        <Input placeholder="Your name" className="mt-1" />
      </div>
      <div>
        <label className="text-sm font-medium">Email</label>
        <Input type="email" placeholder="your@email.com" className="mt-1" />
      </div>
      <div>
        <label className="text-sm font-medium">Phone</label>
        <Input type="tel" placeholder="+1 (555) 000-0000" className="mt-1" />
      </div>
      <Button className="w-full">Submit</Button>
    </div>
}`,...J.parameters?.docs?.source}}};Q.parameters={...Q.parameters,docs:{...Q.parameters?.docs,source:{originalSource:`{
  render: () => <div className="space-y-4">
      <div>
        <label className="text-sm font-medium">Small</label>
        <Input size="sm" placeholder="Small input" className="mt-1" />
      </div>
      <div>
        <label className="text-sm font-medium">Default</label>
        <Input placeholder="Default input" className="mt-1" />
      </div>
      <div>
        <label className="text-sm font-medium">Large</label>
        <Input size="lg" placeholder="Large input" className="mt-1" />
      </div>
    </div>
}`,...Q.parameters?.docs?.source}}};X.parameters={...X.parameters,docs:{...X.parameters?.docs,source:{originalSource:`{
  render: () => <div className="space-y-4">
      <div>
        <label className="text-sm font-medium">Normal</label>
        <Input placeholder="Normal state" className="mt-1" />
      </div>
      <div>
        <label className="text-sm font-medium">Focused</label>
        <Input placeholder="Focused state" className="mt-1" autoFocus />
      </div>
      <div>
        <label className="text-sm font-medium">Error</label>
        <Input error placeholder="Error state" className="mt-1" />
      </div>
      <div>
        <label className="text-sm font-medium">Disabled</label>
        <Input disabled placeholder="Disabled state" className="mt-1" />
      </div>
      <div>
        <label className="text-sm font-medium">Read-only</label>
        <Input readOnly value="Read-only value" className="mt-1" />
      </div>
    </div>
}`,...X.parameters?.docs?.source}}};Z.parameters={...Z.parameters,docs:{...Z.parameters?.docs,source:{originalSource:`{
  args: {
    placeholder: 'Playground input',
    type: 'text',
    size: 'default',
    disabled: false,
    readOnly: false,
    error: false,
    loading: false
  }
}`,...Z.parameters?.docs?.source}}};const De=["Default","WithValue","Email","Password","Number","Search","Small","Large","Disabled","ReadOnly","Error","Loading","WithLeftAddon","WithRightAddon","WithBothAddons","WithIconAddon","SearchWithButton","EmailSignup","PriceInput","ContactForm","AllSizes","InputStates","Playground"];export{Q as AllSizes,J as ContactForm,$ as Default,W as Disabled,L as Email,Y as EmailSignup,z as Error,X as InputStates,B as Large,F as Loading,V as Number,M as Password,Z as Playground,G as PriceInput,q as ReadOnly,D as Search,_ as SearchWithButton,P as Small,U as WithBothAddons,K as WithIconAddon,O as WithLeftAddon,H as WithRightAddon,k as WithValue,De as __namedExportsOrder,Ve as default};
