import{j as e}from"./jsx-runtime-BQ8Dm5uo.js";import{B as l}from"./Button-hbqBliJw.js";import"./iframe-CyYF4sMK.js";const s=({children:B,variant:M="default",size:E="md",rounded:I=!0,shadow:z="md",bordered:A=!1,hoverable:H=!1,clickable:T=!1,onClick:g,href:y,className:k="",headerClassName:D="",bodyClassName:F="",footerClassName:W="",imageClassName:q="",disabled:r=!1,loading:d=!1,header:R,footer:$,image:i,imageAlt:J="",imagePosition:a="top",actions:S,title:b,subtitle:j,titleClassName:L="",subtitleClassName:_="",compact:w=!1})=>{const G=()=>({default:"bg-white",outlined:"bg-white border border-gray-200",elevated:"bg-white",filled:"bg-gray-50"})[M],K=()=>w?"p-3":{sm:"p-4",md:"p-6",lg:"p-8"}[E],O=()=>({none:"",sm:"shadow-sm",md:"shadow-md",lg:"shadow-lg",xl:"shadow-xl"})[z],U=()=>r||d?"":H||T?"transition-all duration-200 hover:shadow-lg hover:-translate-y-1":"",Q=()=>I?"rounded-lg":"",C=!!(T||g||y),V=y&&!r?"a":C?"button":"div",X=t=>{if(r||d){t.preventDefault();return}g?.(t)},Y=t=>{r||d||(t.key==="Enter"||t.key===" ")&&(t.preventDefault(),g?.(t))},n={className:`
    relative overflow-hidden
    ${G()}
    ${Q()}
    ${O()}
    ${U()}
    ${A?"border border-gray-200":""}
    ${r?"opacity-50 cursor-not-allowed":""}
    ${C&&!r&&!d?"cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2":""}
    ${d?"animate-pulse cursor-wait":""}
    ${k}
  `,onClick:X,onKeyDown:Y,"data-testid":"card"};V==="a"?(n.href=y,n.role="link"):C&&(n.type="button",n.role="button",n.tabIndex=r?-1:0),r&&(n["aria-disabled"]="true"),d&&(n["aria-busy"]="true");const c=()=>{if(!i)return null;const t=typeof i=="string"?e.jsx("img",{src:i,alt:J,className:`w-full h-full object-cover ${q}`}):e.jsx("div",{className:q,children:i}),re=`
      ${a==="top"?"w-full h-48":""}
      ${a==="bottom"?"w-full h-48":""}
      ${a==="left"?"w-48 h-full flex-shrink-0":""}
      ${a==="right"?"w-48 h-full flex-shrink-0":""}
      overflow-hidden
    `;return e.jsx("div",{className:re,children:t})},Z=()=>!R&&!b&&!j?null:e.jsx("div",{className:`${w?"mb-2":"mb-4"} ${D}`,"data-testid":"card-header",children:R||e.jsxs("div",{children:[b&&e.jsx("h3",{className:`text-lg font-semibold text-gray-900 ${L}`,children:b}),j&&e.jsx("p",{className:`text-sm text-gray-500 mt-1 ${_}`,children:j})]})}),P=()=>e.jsx("div",{className:`flex-1 ${F}`,children:B}),ee=()=>!$&&!S?null:e.jsx("div",{className:`${w?"mt-2":"mt-4"} ${W}`,"data-testid":"card-footer",children:$||S}),se=()=>d?e.jsx("div",{className:"absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center",children:e.jsxs("div",{className:"flex items-center gap-2 text-gray-500",children:[e.jsx("div",{className:"w-4 h-4 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin"}),e.jsx("span",{className:"text-sm",children:"Loading..."})]})}):null,ae=`
    ${K()}
    ${a==="left"||a==="right"?"flex-1":""}
  `,te=a==="left"||a==="right";return e.jsxs(V,{...n,children:[a==="top"&&c(),e.jsxs("div",{className:te?"flex":"",children:[a==="left"&&c(),e.jsxs("div",{className:ae,children:[Z(),P(),ee()]}),a==="right"&&c()]}),a==="bottom"&&c(),se()]})};s.__docgenInfo={description:"",methods:[],displayName:"Card",props:{children:{required:!0,tsType:{name:"ReactReactNode",raw:"React.ReactNode"},description:""},variant:{required:!1,tsType:{name:"union",raw:'"default" | "outlined" | "elevated" | "filled"',elements:[{name:"literal",value:'"default"'},{name:"literal",value:'"outlined"'},{name:"literal",value:'"elevated"'},{name:"literal",value:'"filled"'}]},description:"",defaultValue:{value:'"default"',computed:!1}},size:{required:!1,tsType:{name:"union",raw:'"sm" | "md" | "lg"',elements:[{name:"literal",value:'"sm"'},{name:"literal",value:'"md"'},{name:"literal",value:'"lg"'}]},description:"",defaultValue:{value:'"md"',computed:!1}},rounded:{required:!1,tsType:{name:"boolean"},description:"",defaultValue:{value:"true",computed:!1}},shadow:{required:!1,tsType:{name:"union",raw:'"none" | "sm" | "md" | "lg" | "xl"',elements:[{name:"literal",value:'"none"'},{name:"literal",value:'"sm"'},{name:"literal",value:'"md"'},{name:"literal",value:'"lg"'},{name:"literal",value:'"xl"'}]},description:"",defaultValue:{value:'"md"',computed:!1}},bordered:{required:!1,tsType:{name:"boolean"},description:"",defaultValue:{value:"false",computed:!1}},hoverable:{required:!1,tsType:{name:"boolean"},description:"",defaultValue:{value:"false",computed:!1}},clickable:{required:!1,tsType:{name:"boolean"},description:"",defaultValue:{value:"false",computed:!1}},onClick:{required:!1,tsType:{name:"signature",type:"function",raw:"(event: React.MouseEvent) => void",signature:{arguments:[{type:{name:"ReactMouseEvent",raw:"React.MouseEvent"},name:"event"}],return:{name:"void"}}},description:""},href:{required:!1,tsType:{name:"string"},description:""},className:{required:!1,tsType:{name:"string"},description:"",defaultValue:{value:'""',computed:!1}},headerClassName:{required:!1,tsType:{name:"string"},description:"",defaultValue:{value:'""',computed:!1}},bodyClassName:{required:!1,tsType:{name:"string"},description:"",defaultValue:{value:'""',computed:!1}},footerClassName:{required:!1,tsType:{name:"string"},description:"",defaultValue:{value:'""',computed:!1}},imageClassName:{required:!1,tsType:{name:"string"},description:"",defaultValue:{value:'""',computed:!1}},disabled:{required:!1,tsType:{name:"boolean"},description:"",defaultValue:{value:"false",computed:!1}},loading:{required:!1,tsType:{name:"boolean"},description:"",defaultValue:{value:"false",computed:!1}},header:{required:!1,tsType:{name:"ReactReactNode",raw:"React.ReactNode"},description:""},footer:{required:!1,tsType:{name:"ReactReactNode",raw:"React.ReactNode"},description:""},image:{required:!1,tsType:{name:"union",raw:"string | React.ReactNode",elements:[{name:"string"},{name:"ReactReactNode",raw:"React.ReactNode"}]},description:""},imageAlt:{required:!1,tsType:{name:"string"},description:"",defaultValue:{value:'""',computed:!1}},imagePosition:{required:!1,tsType:{name:"union",raw:'"top" | "bottom" | "left" | "right"',elements:[{name:"literal",value:'"top"'},{name:"literal",value:'"bottom"'},{name:"literal",value:'"left"'},{name:"literal",value:'"right"'}]},description:"",defaultValue:{value:'"top"',computed:!1}},actions:{required:!1,tsType:{name:"ReactReactNode",raw:"React.ReactNode"},description:""},title:{required:!1,tsType:{name:"string"},description:""},subtitle:{required:!1,tsType:{name:"string"},description:""},titleClassName:{required:!1,tsType:{name:"string"},description:"",defaultValue:{value:'""',computed:!1}},subtitleClassName:{required:!1,tsType:{name:"string"},description:"",defaultValue:{value:'""',computed:!1}},compact:{required:!1,tsType:{name:"boolean"},description:"",defaultValue:{value:"false",computed:!1}}}};const ce={title:"UI/Card",component:s,parameters:{layout:"padded",docs:{description:{component:"A flexible card component with header, content, and footer sections."}}},tags:["autodocs"],argTypes:{className:{control:"text",description:"Additional CSS classes to apply"}}},o={render:()=>e.jsx(s,{className:"w-96",children:e.jsx("div",{className:"p-6",children:e.jsx("p",{children:"This is a basic card with content."})})})},m={render:()=>e.jsxs(s,{className:"w-96",children:[e.jsxs("div",{className:"px-6 pt-6 pb-4",children:[e.jsx("h3",{className:"text-lg font-semibold",children:"Card Title"}),e.jsx("p",{className:"text-sm text-gray-600",children:"This is a card description that provides more context."})]}),e.jsx("div",{className:"px-6 pb-6",children:e.jsx("p",{children:"Card content goes here. This can include any type of content you need."})})]})},p={render:()=>e.jsxs(s,{className:"w-96",children:[e.jsx("div",{className:"px-6 pt-6 pb-4",children:e.jsx("h3",{className:"text-lg font-semibold",children:"Card with Footer"})}),e.jsx("div",{className:"px-6 pb-4",children:e.jsx("p",{children:"This card includes a footer with action buttons."})}),e.jsxs("div",{className:"px-6 pb-6 flex justify-between",children:[e.jsx(l,{variant:"outline",children:"Cancel"}),e.jsx(l,{children:"Confirm"})]})]})},u={render:()=>e.jsxs(s,{className:"w-96",children:[e.jsxs("div",{className:"px-6 pt-6 pb-4",children:[e.jsx("h3",{className:"text-lg font-semibold",children:"Complete Card"}),e.jsx("p",{className:"text-sm text-gray-600",children:"A card with all sections included."})]}),e.jsx("div",{className:"px-6 pb-4",children:e.jsxs("div",{className:"space-y-4",children:[e.jsx("p",{children:"This is a complete card example with header, content, and footer."}),e.jsx("div",{className:"bg-gray-50 p-4 rounded",children:e.jsx("p",{className:"text-sm text-gray-600",children:"Additional content section"})})]})}),e.jsx("div",{className:"px-6 pb-6",children:e.jsxs("div",{className:"flex w-full justify-between",children:[e.jsx(l,{variant:"ghost",size:"sm",children:"Learn More"}),e.jsxs("div",{className:"space-x-2",children:[e.jsx(l,{variant:"outline",size:"sm",children:"Cancel"}),e.jsx(l,{size:"sm",children:"Save"})]})]})})]})},x={render:()=>e.jsx(s,{className:"w-80",children:e.jsxs("div",{className:"p-6",children:[e.jsx("div",{className:"aspect-video bg-gray-200 rounded-md mb-4 flex items-center justify-center",children:e.jsx("span",{className:"text-gray-500",children:"Product Image"})}),e.jsx("h3",{className:"text-lg font-semibold",children:"Wireless Headphones"}),e.jsx("p",{className:"text-sm text-gray-600 mb-4",children:"High-quality wireless headphones with noise cancellation"}),e.jsxs("div",{className:"space-y-2 mb-4",children:[e.jsxs("div",{className:"flex justify-between items-center",children:[e.jsx("span",{className:"font-semibold text-2xl",children:"$299.99"}),e.jsx("span",{className:"text-sm text-gray-500 line-through",children:"$399.99"})]}),e.jsxs("div",{className:"flex items-center gap-1",children:[e.jsxs("div",{className:"flex text-yellow-400",children:["★".repeat(4),"☆".repeat(1)]}),e.jsx("span",{className:"text-sm text-gray-500",children:"(24 reviews)"})]})]}),e.jsx(l,{className:"w-full",children:"Add to Cart"})]})})},h={render:()=>e.jsxs(s,{className:"w-64",children:[e.jsxs("div",{className:"p-6 pb-2",children:[e.jsx("p",{className:"text-sm text-gray-600",children:"Total Revenue"}),e.jsx("h3",{className:"text-4xl font-bold",children:"$45,231.89"})]}),e.jsx("div",{className:"px-6 pb-6",children:e.jsxs("div",{className:"text-xs text-gray-500",children:[e.jsx("span",{className:"text-green-600",children:"+20.1%"})," from last month"]})})]})},f={render:()=>e.jsx(s,{className:"w-80",children:e.jsxs("div",{className:"p-6 text-center",children:[e.jsx("div",{className:"w-16 h-16 bg-blue-500 rounded-full mx-auto mb-4 flex items-center justify-center text-white font-semibold text-xl",children:"JD"}),e.jsx("h3",{className:"text-lg font-semibold",children:"John Doe"}),e.jsx("p",{className:"text-sm text-gray-600 mb-4",children:"Software Engineer at TechCorp"}),e.jsxs("div",{className:"space-y-2 text-sm mb-4",children:[e.jsxs("div",{className:"flex justify-between",children:[e.jsx("span",{className:"text-gray-500",children:"Email:"}),e.jsx("span",{children:"john.doe@example.com"})]}),e.jsxs("div",{className:"flex justify-between",children:[e.jsx("span",{className:"text-gray-500",children:"Location:"}),e.jsx("span",{children:"San Francisco, CA"})]}),e.jsxs("div",{className:"flex justify-between",children:[e.jsx("span",{className:"text-gray-500",children:"Joined:"}),e.jsx("span",{children:"March 2023"})]})]}),e.jsxs("div",{className:"flex w-full gap-2",children:[e.jsx(l,{variant:"outline",className:"flex-1",children:"Message"}),e.jsx(l,{className:"flex-1",children:"Connect"})]})]})})},v={render:()=>e.jsxs("div",{className:"grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6",children:[e.jsx(s,{children:e.jsxs("div",{className:"p-6",children:[e.jsx("h3",{className:"text-lg font-semibold mb-2",children:"Card 1"}),e.jsx("p",{className:"text-sm text-gray-600 mb-4",children:"First card in the grid"}),e.jsx("p",{children:"Content for the first card."})]})}),e.jsx(s,{children:e.jsxs("div",{className:"p-6",children:[e.jsx("h3",{className:"text-lg font-semibold mb-2",children:"Card 2"}),e.jsx("p",{className:"text-sm text-gray-600 mb-4",children:"Second card in the grid"}),e.jsx("p",{children:"Content for the second card."})]})}),e.jsx(s,{children:e.jsxs("div",{className:"p-6",children:[e.jsx("h3",{className:"text-lg font-semibold mb-2",children:"Card 3"}),e.jsx("p",{className:"text-sm text-gray-600 mb-4",children:"Third card in the grid"}),e.jsx("p",{children:"Content for the third card."})]})})]}),parameters:{layout:"fullscreen",docs:{story:{inline:!1,height:"400px"}}}},N={render:()=>e.jsx(s,{className:"w-96 cursor-pointer transition-shadow hover:shadow-lg",children:e.jsxs("div",{className:"p-6",children:[e.jsx("h3",{className:"text-lg font-semibold mb-2",children:"Interactive Card"}),e.jsx("p",{className:"text-sm text-gray-600 mb-4",children:"This card responds to hover and click events"}),e.jsx("p",{children:"Hover over this card to see the shadow effect."}),e.jsx("p",{className:"text-sm text-gray-500 mt-2",children:"Click anywhere on the card to interact with it."})]})})};o.parameters={...o.parameters,docs:{...o.parameters?.docs,source:{originalSource:`{
  render: () => <Card className="w-96">
      <div className="p-6">
        <p>This is a basic card with content.</p>
      </div>
    </Card>
}`,...o.parameters?.docs?.source}}};m.parameters={...m.parameters,docs:{...m.parameters?.docs,source:{originalSource:`{
  render: () => <Card className="w-96">
      <div className="px-6 pt-6 pb-4">
        <h3 className="text-lg font-semibold">Card Title</h3>
        <p className="text-sm text-gray-600">This is a card description that provides more context.</p>
      </div>
      <div className="px-6 pb-6">
        <p>Card content goes here. This can include any type of content you need.</p>
      </div>
    </Card>
}`,...m.parameters?.docs?.source}}};p.parameters={...p.parameters,docs:{...p.parameters?.docs,source:{originalSource:`{
  render: () => <Card className="w-96">
      <div className="px-6 pt-6 pb-4">
        <h3 className="text-lg font-semibold">Card with Footer</h3>
      </div>
      <div className="px-6 pb-4">
        <p>This card includes a footer with action buttons.</p>
      </div>
      <div className="px-6 pb-6 flex justify-between">
        <Button variant="outline">Cancel</Button>
        <Button>Confirm</Button>
      </div>
    </Card>
}`,...p.parameters?.docs?.source}}};u.parameters={...u.parameters,docs:{...u.parameters?.docs,source:{originalSource:`{
  render: () => <Card className="w-96">
      <div className="px-6 pt-6 pb-4">
        <h3 className="text-lg font-semibold">Complete Card</h3>
        <p className="text-sm text-gray-600">A card with all sections included.</p>
      </div>
      <div className="px-6 pb-4">
        <div className="space-y-4">
          <p>This is a complete card example with header, content, and footer.</p>
          <div className="bg-gray-50 p-4 rounded">
            <p className="text-sm text-gray-600">Additional content section</p>
          </div>
        </div>
      </div>
      <div className="px-6 pb-6">
        <div className="flex w-full justify-between">
          <Button variant="ghost" size="sm">Learn More</Button>
          <div className="space-x-2">
            <Button variant="outline" size="sm">Cancel</Button>
            <Button size="sm">Save</Button>
          </div>
        </div>
      </div>
    </Card>
}`,...u.parameters?.docs?.source}}};x.parameters={...x.parameters,docs:{...x.parameters?.docs,source:{originalSource:`{
  render: () => <Card className="w-80">
      <div className="p-6">
        <div className="aspect-video bg-gray-200 rounded-md mb-4 flex items-center justify-center">
          <span className="text-gray-500">Product Image</span>
        </div>
        <h3 className="text-lg font-semibold">Wireless Headphones</h3>
        <p className="text-sm text-gray-600 mb-4">High-quality wireless headphones with noise cancellation</p>
        
        <div className="space-y-2 mb-4">
          <div className="flex justify-between items-center">
            <span className="font-semibold text-2xl">$299.99</span>
            <span className="text-sm text-gray-500 line-through">$399.99</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="flex text-yellow-400">
              {'★'.repeat(4)}{'☆'.repeat(1)}
            </div>
            <span className="text-sm text-gray-500">(24 reviews)</span>
          </div>
        </div>
        
        <Button className="w-full">Add to Cart</Button>
      </div>
    </Card>
}`,...x.parameters?.docs?.source}}};h.parameters={...h.parameters,docs:{...h.parameters?.docs,source:{originalSource:`{
  render: () => <Card className="w-64">
      <div className="p-6 pb-2">
        <p className="text-sm text-gray-600">Total Revenue</p>
        <h3 className="text-4xl font-bold">$45,231.89</h3>
      </div>
      <div className="px-6 pb-6">
        <div className="text-xs text-gray-500">
          <span className="text-green-600">+20.1%</span> from last month
        </div>
      </div>
    </Card>
}`,...h.parameters?.docs?.source}}};f.parameters={...f.parameters,docs:{...f.parameters?.docs,source:{originalSource:`{
  render: () => <Card className="w-80">
      <div className="p-6 text-center">
        <div className="w-16 h-16 bg-blue-500 rounded-full mx-auto mb-4 flex items-center justify-center text-white font-semibold text-xl">
          JD
        </div>
        <h3 className="text-lg font-semibold">John Doe</h3>
        <p className="text-sm text-gray-600 mb-4">Software Engineer at TechCorp</p>
        
        <div className="space-y-2 text-sm mb-4">
          <div className="flex justify-between">
            <span className="text-gray-500">Email:</span>
            <span>john.doe@example.com</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Location:</span>
            <span>San Francisco, CA</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Joined:</span>
            <span>March 2023</span>
          </div>
        </div>
        
        <div className="flex w-full gap-2">
          <Button variant="outline" className="flex-1">Message</Button>
          <Button className="flex-1">Connect</Button>
        </div>
      </div>
    </Card>
}`,...f.parameters?.docs?.source}}};v.parameters={...v.parameters,docs:{...v.parameters?.docs,source:{originalSource:`{
  render: () => <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <Card>
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-2">Card 1</h3>
          <p className="text-sm text-gray-600 mb-4">First card in the grid</p>
          <p>Content for the first card.</p>
        </div>
      </Card>
      <Card>
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-2">Card 2</h3>
          <p className="text-sm text-gray-600 mb-4">Second card in the grid</p>
          <p>Content for the second card.</p>
        </div>
      </Card>
      <Card>
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-2">Card 3</h3>
          <p className="text-sm text-gray-600 mb-4">Third card in the grid</p>
          <p>Content for the third card.</p>
        </div>
      </Card>
    </div>,
  parameters: {
    layout: 'fullscreen',
    docs: {
      story: {
        inline: false,
        height: '400px'
      }
    }
  }
}`,...v.parameters?.docs?.source}}};N.parameters={...N.parameters,docs:{...N.parameters?.docs,source:{originalSource:`{
  render: () => <Card className="w-96 cursor-pointer transition-shadow hover:shadow-lg">
      <div className="p-6">
        <h3 className="text-lg font-semibold mb-2">Interactive Card</h3>
        <p className="text-sm text-gray-600 mb-4">This card responds to hover and click events</p>
        <p>Hover over this card to see the shadow effect.</p>
        <p className="text-sm text-gray-500 mt-2">Click anywhere on the card to interact with it.</p>
      </div>
    </Card>
}`,...N.parameters?.docs?.source}}};const oe=["Default","WithHeader","WithFooter","Complete","ProductCard","StatsCard","ProfileCard","CardGrid","Interactive"];export{v as CardGrid,u as Complete,o as Default,N as Interactive,x as ProductCard,f as ProfileCard,h as StatsCard,p as WithFooter,m as WithHeader,oe as __namedExportsOrder,ce as default};
