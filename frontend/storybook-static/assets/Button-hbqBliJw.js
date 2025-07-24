import{j as o}from"./jsx-runtime-BQ8Dm5uo.js";import{r as M,e as p}from"./iframe-CyYF4sMK.js";const g=M.forwardRef(({variant:f="primary",size:l="md",loading:a=!1,disabled:u=!1,block:i=!1,shape:d="default",icon:v,iconPosition:r="left",href:c,target:b,htmlType:s="button",className:m="",children:e,onClick:y,...x},h)=>{const N=()=>({primary:`
        bg-blue-600 text-white border border-blue-600
        hover:bg-blue-700 hover:border-blue-700
        focus:bg-blue-700 focus:border-blue-700
        active:bg-blue-800 active:border-blue-800
        disabled:bg-blue-300 disabled:border-blue-300 disabled:cursor-not-allowed
      `,secondary:`
        bg-gray-100 text-gray-900 border border-gray-300
        hover:bg-gray-200 hover:border-gray-400
        focus:bg-gray-200 focus:border-gray-400
        active:bg-gray-300 active:border-gray-500
        disabled:bg-gray-50 disabled:text-gray-400 disabled:border-gray-200 disabled:cursor-not-allowed
      `,outline:`
        bg-transparent text-blue-600 border border-blue-600
        hover:bg-blue-50 hover:text-blue-700
        focus:bg-blue-50 focus:text-blue-700
        active:bg-blue-100 active:text-blue-800
        disabled:text-blue-300 disabled:border-blue-200 disabled:cursor-not-allowed
      `,ghost:`
        bg-transparent text-gray-600 border border-transparent
        hover:bg-gray-100 hover:text-gray-700
        focus:bg-gray-100 focus:text-gray-700
        active:bg-gray-200 active:text-gray-800
        disabled:text-gray-300 disabled:cursor-not-allowed
      `,link:`
        bg-transparent text-blue-600 border border-transparent
        hover:text-blue-700 hover:underline
        focus:text-blue-700 focus:underline
        active:text-blue-800
        disabled:text-blue-300 disabled:cursor-not-allowed disabled:no-underline
      `,danger:`
        bg-red-600 text-white border border-red-600
        hover:bg-red-700 hover:border-red-700
        focus:bg-red-700 focus:border-red-700
        active:bg-red-800 active:border-red-800
        disabled:bg-red-300 disabled:border-red-300 disabled:cursor-not-allowed
      `})[f],T=()=>d==="circle"?{sm:"w-8 h-8 p-0",md:"w-10 h-10 p-0",lg:"w-12 h-12 p-0",xl:"w-14 h-14 p-0"}[l]:{sm:"px-3 py-1.5 text-sm",md:"px-4 py-2 text-sm",lg:"px-6 py-3 text-base",xl:"px-8 py-4 text-lg"}[l],q=()=>({default:"rounded-md",circle:"rounded-full",round:"rounded-full"})[d],j=t=>{if(a||u){t.preventDefault();return}y?.(t)},$=()=>o.jsx("div",{className:"flex items-center justify-center",children:o.jsx("div",{className:"w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"})}),V=()=>a?$():v,w=()=>{const t=p.Children.count(e)>0,n=V();if(d==="circle")return n||e;if(!t&&n)return n;if(!n)return e;const R=l==="sm"?"gap-1.5":l==="lg"||l==="xl"?"gap-3":"gap-2";return o.jsxs("div",{className:`flex items-center justify-center ${R}`,children:[r==="left"&&n,t&&o.jsx("span",{children:e}),r==="right"&&n]})},C=`
    inline-flex items-center justify-center font-medium transition-all duration-200
    focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500
    ${N()}
    ${T()}
    ${q()}
    ${i?"w-full":""}
    ${a?"pointer-events-none opacity-75":""}
    ${m}
  `;return c&&!u&&!a?o.jsx("a",{ref:h,href:c,target:b,className:C,role:"button",...x,children:w()}):o.jsx("button",{ref:h,type:s,disabled:u||a,onClick:j,className:C,"aria-busy":a,"aria-disabled":u||a,...x,children:w()})});g.displayName="Button";const k=({children:f,size:l,variant:a,className:u="",vertical:i=!1})=>{const d=`
    inline-flex
    ${i?"flex-col":"flex-row"}
    ${u}
  `,v=p.Children.map(f,(r,c)=>{if(p.isValidElement(r)&&r.type===g){const b=c===0,s=c===p.Children.count(f)-1,m=!b&&!s;let e="";i?b?e="rounded-b-none":s?e="rounded-t-none":m&&(e="rounded-none"):b?e="rounded-r-none":s?e="rounded-l-none":m&&(e="rounded-none");const y=i?s?"":"-mb-px":s?"":"-mr-px";return p.cloneElement(r,{...r.props,size:r.props.size||l,variant:r.props.variant||a,className:`${r.props.className||""} ${e} ${y}`.trim()})}return r});return o.jsx("div",{className:d,role:"group",children:v})};g.Group=k;g.__docgenInfo={description:"",methods:[],displayName:"Button",props:{variant:{required:!1,tsType:{name:"union",raw:'"primary" | "secondary" | "outline" | "ghost" | "link" | "danger"',elements:[{name:"literal",value:'"primary"'},{name:"literal",value:'"secondary"'},{name:"literal",value:'"outline"'},{name:"literal",value:'"ghost"'},{name:"literal",value:'"link"'},{name:"literal",value:'"danger"'}]},description:"",defaultValue:{value:'"primary"',computed:!1}},size:{required:!1,tsType:{name:"union",raw:'"sm" | "md" | "lg" | "xl"',elements:[{name:"literal",value:'"sm"'},{name:"literal",value:'"md"'},{name:"literal",value:'"lg"'},{name:"literal",value:'"xl"'}]},description:"",defaultValue:{value:'"md"',computed:!1}},loading:{required:!1,tsType:{name:"boolean"},description:"",defaultValue:{value:"false",computed:!1}},disabled:{required:!1,tsType:{name:"boolean"},description:"",defaultValue:{value:"false",computed:!1}},block:{required:!1,tsType:{name:"boolean"},description:"",defaultValue:{value:"false",computed:!1}},shape:{required:!1,tsType:{name:"union",raw:'"default" | "circle" | "round"',elements:[{name:"literal",value:'"default"'},{name:"literal",value:'"circle"'},{name:"literal",value:'"round"'}]},description:"",defaultValue:{value:'"default"',computed:!1}},icon:{required:!1,tsType:{name:"ReactReactNode",raw:"React.ReactNode"},description:""},iconPosition:{required:!1,tsType:{name:"union",raw:'"left" | "right"',elements:[{name:"literal",value:'"left"'},{name:"literal",value:'"right"'}]},description:"",defaultValue:{value:'"left"',computed:!1}},href:{required:!1,tsType:{name:"string"},description:""},target:{required:!1,tsType:{name:"string"},description:""},htmlType:{required:!1,tsType:{name:"union",raw:'"button" | "submit" | "reset"',elements:[{name:"literal",value:'"button"'},{name:"literal",value:'"submit"'},{name:"literal",value:'"reset"'}]},description:"",defaultValue:{value:'"button"',computed:!1}},className:{required:!1,tsType:{name:"string"},description:"",defaultValue:{value:'""',computed:!1}},children:{required:!1,tsType:{name:"ReactReactNode",raw:"React.ReactNode"},description:""}},composes:["Omit"]};export{g as B};
