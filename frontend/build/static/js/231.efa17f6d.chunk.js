"use strict";(self.webpackChunkSales_tracking_app=self.webpackChunkSales_tracking_app||[]).push([[231],{1231:(e,t,r)=>{r.r(t),r.d(t,{default:()=>D});var a=r(5043),o=r(5865),i=r(1906),s=r(4449),n=r(2110),l=r(5795),d=r(7561),c=r(9190),u=r(4469),p=r(8387),m=r(8610),h=r(6596),g=r(1475),v=r(1192),x=r(6870),y=r(8249),A=r(1347),j=r(408),f=r(5013),b=r(5849),C=r(2532);const w=(0,C.A)("MuiDivider",["root","absolute","fullWidth","inset","middle","flexItem","light","vertical","withChildren","withChildrenVertical","textAlignRight","textAlignLeft","wrapper","wrapperVertical"]);const S=(0,C.A)("MuiListItemIcon",["root","alignItemsFlexStart"]);const $=(0,C.A)("MuiListItemText",["root","multiline","dense","inset","primary","secondary"]);var k=r(552);function I(e){return(0,k.Ay)("MuiMenuItem",e)}const M=(0,C.A)("MuiMenuItem",["root","focusVisible","dense","disabled","divider","gutters","selected"]);var N=r(579);const O=(0,v.Ay)(j.A,{shouldForwardProp:e=>(0,g.A)(e)||"classes"===e,name:"MuiMenuItem",slot:"Root",overridesResolver:(e,t)=>{const{ownerState:r}=e;return[t.root,r.dense&&t.dense,r.divider&&t.divider,!r.disableGutters&&t.gutters]}})((0,x.A)((e=>{let{theme:t}=e;return{...t.typography.body1,display:"flex",justifyContent:"flex-start",alignItems:"center",position:"relative",textDecoration:"none",minHeight:48,paddingTop:6,paddingBottom:6,boxSizing:"border-box",whiteSpace:"nowrap","&:hover":{textDecoration:"none",backgroundColor:(t.vars||t).palette.action.hover,"@media (hover: none)":{backgroundColor:"transparent"}},[`&.${M.selected}`]:{backgroundColor:t.vars?`rgba(${t.vars.palette.primary.mainChannel} / ${t.vars.palette.action.selectedOpacity})`:(0,h.X4)(t.palette.primary.main,t.palette.action.selectedOpacity),[`&.${M.focusVisible}`]:{backgroundColor:t.vars?`rgba(${t.vars.palette.primary.mainChannel} / calc(${t.vars.palette.action.selectedOpacity} + ${t.vars.palette.action.focusOpacity}))`:(0,h.X4)(t.palette.primary.main,t.palette.action.selectedOpacity+t.palette.action.focusOpacity)}},[`&.${M.selected}:hover`]:{backgroundColor:t.vars?`rgba(${t.vars.palette.primary.mainChannel} / calc(${t.vars.palette.action.selectedOpacity} + ${t.vars.palette.action.hoverOpacity}))`:(0,h.X4)(t.palette.primary.main,t.palette.action.selectedOpacity+t.palette.action.hoverOpacity),"@media (hover: none)":{backgroundColor:t.vars?`rgba(${t.vars.palette.primary.mainChannel} / ${t.vars.palette.action.selectedOpacity})`:(0,h.X4)(t.palette.primary.main,t.palette.action.selectedOpacity)}},[`&.${M.focusVisible}`]:{backgroundColor:(t.vars||t).palette.action.focus},[`&.${M.disabled}`]:{opacity:(t.vars||t).palette.action.disabledOpacity},[`& + .${w.root}`]:{marginTop:t.spacing(1),marginBottom:t.spacing(1)},[`& + .${w.inset}`]:{marginLeft:52},[`& .${$.root}`]:{marginTop:0,marginBottom:0},[`& .${$.inset}`]:{paddingLeft:36},[`& .${S.root}`]:{minWidth:36},variants:[{props:e=>{let{ownerState:t}=e;return!t.disableGutters},style:{paddingLeft:16,paddingRight:16}},{props:e=>{let{ownerState:t}=e;return t.divider},style:{borderBottom:`1px solid ${(t.vars||t).palette.divider}`,backgroundClip:"padding-box"}},{props:e=>{let{ownerState:t}=e;return!t.dense},style:{[t.breakpoints.up("sm")]:{minHeight:"auto"}}},{props:e=>{let{ownerState:t}=e;return t.dense},style:{minHeight:32,paddingTop:4,paddingBottom:4,...t.typography.body2,[`& .${S.root} svg`]:{fontSize:"1.25rem"}}}]}}))),P=a.forwardRef((function(e,t){const r=(0,y.b)({props:e,name:"MuiMenuItem"}),{autoFocus:o=!1,component:i="li",dense:s=!1,divider:n=!1,disableGutters:l=!1,focusVisibleClassName:d,role:c="menuitem",tabIndex:u,className:h,...g}=r,v=a.useContext(A.A),x=a.useMemo((()=>({dense:s||v.dense||!1,disableGutters:l})),[v.dense,s,l]),j=a.useRef(null);(0,f.A)((()=>{o&&j.current&&j.current.focus()}),[o]);const C={...r,dense:x.dense,divider:n,disableGutters:l},w=(e=>{const{disabled:t,dense:r,divider:a,disableGutters:o,selected:i,classes:s}=e,n={root:["root",r&&"dense",t&&"disabled",!o&&"gutters",a&&"divider",i&&"selected"]},l=(0,m.A)(n,I,s);return{...s,...l}})(r),S=(0,b.A)(j,t);let $;return r.disabled||($=void 0!==u?u:-1),(0,N.jsx)(A.A.Provider,{value:x,children:(0,N.jsx)(O,{ref:S,role:c,tabIndex:$,component:i,focusVisibleClassName:(0,p.A)(w.focusVisible,d),className:(0,p.A)(w.root,h),...g,ownerState:C,classes:w})})}));var _=r(7417),E=r(3519),B=r(1072),G=r(8602),R=r(4196),V=r(8861),F=r(6579),L=r(7929),T=r(9621);const D=e=>{var t;let{showToast:r}=e;const[p,m]=(0,a.useState)([]),[h,g]=(0,a.useState)(!0),[v,x]=(0,a.useState)(!1),[y,A]=(0,a.useState)(!1),[j,f]=(0,a.useState)(null),[b,C]=(0,a.useState)("add"),[w,S]=(0,a.useState)({name:"",category:"",group:""}),[$,k]=(0,a.useState)(1),[I,M]=(0,a.useState)(1),O=JSON.parse(localStorage.getItem("user")),D=parseInt(null===O||void 0===O?void 0:O.role_id)||(null===O||void 0===O||null===(t=O.role)||void 0===t?void 0:t.id);(0,a.useEffect)((()=>{(async()=>{g(!0);try{const e=await T.A.get(`/impact_products/?sort_by=created_at&per_page=10&page=${$}`);m(e.data.products),M(Math.ceil(e.data.total/10))}catch(e){console.error("Error fetching products:",e),r("error","Failed to fetch products. Please try again later.","Error")}finally{g(!1)}})()}),[r,$]);const W=function(e){let t=arguments.length>1&&void 0!==arguments[1]?arguments[1]:null;C(e),"edit"===e&&t?(f(t),S({name:t.name,category:t.category.name,group:t.group})):S({name:"",category:"",group:""}),x(!0)},H=()=>{x(!1),f(null)};return h?(0,N.jsx)(_.A,{animation:"border"}):(0,N.jsxs)(E.A,{className:"mt-4",children:[(0,N.jsx)(B.A,{children:(0,N.jsx)(G.A,{md:12,children:(0,N.jsx)(o.A,{variant:"h4",gutterBottom:!0,children:"Product Management"})})}),(0,N.jsx)(B.A,{children:(0,N.jsx)(G.A,{md:12,children:(2===D||3===D)&&(0,N.jsxs)(i.A,{variant:"contained",color:"primary",onClick:()=>W("add"),children:[(0,N.jsx)(F.g,{icon:L.QLR})," Add New Product"]})})}),(0,N.jsx)(B.A,{className:"mt-4",children:(0,N.jsxs)(G.A,{md:12,children:[(0,N.jsxs)(R.A,{striped:!0,bordered:!0,hover:!0,children:[(0,N.jsx)("thead",{children:(0,N.jsxs)("tr",{children:[(0,N.jsx)("th",{children:"Name"}),(0,N.jsx)("th",{children:"Category"}),(0,N.jsx)("th",{children:"Group"}),(0,N.jsx)("th",{children:"Actions"})]})}),(0,N.jsx)("tbody",{children:p.map((e=>(0,N.jsxs)("tr",{children:[(0,N.jsx)("td",{children:e.name}),(0,N.jsx)("td",{children:e.category.name}),(0,N.jsx)("td",{children:e.group}),(0,N.jsx)("td",{children:(2===D||3===D)&&(0,N.jsxs)(N.Fragment,{children:[(0,N.jsxs)(i.A,{variant:"contained",color:"secondary",onClick:()=>W("edit",e),className:"me-2",children:[(0,N.jsx)(F.g,{icon:L.MT7})," Edit"]}),(0,N.jsxs)(i.A,{variant:"contained",color:"error",onClick:()=>(e=>{e&&(f(e),A(!0))})(e),children:[(0,N.jsx)(F.g,{icon:L.BeE})," Delete"]})]})})]},e.id)))})]}),(0,N.jsx)(V.A,{children:Array.from({length:I},((e,t)=>(0,N.jsx)(V.A.Item,{active:t+1===$,onClick:()=>k(t+1),children:t+1},t+1)))})]})}),(0,N.jsx)(s.A,{open:v,onClose:H,style:{overflow:"auto"},children:(0,N.jsxs)(n.A,{style:{width:"50%",margin:"5% auto",padding:"20px",maxHeight:"80vh",overflowY:"auto"},children:[(0,N.jsx)(o.A,{variant:"h5",gutterBottom:!0,children:"add"===b?"Add New Product":"Edit Product"}),(0,N.jsx)(l.A,{fullWidth:!0,label:"Product Name",value:w.name,onChange:e=>S({...w,name:e.target.value}),margin:"normal"}),(0,N.jsxs)(d.A,{fullWidth:!0,margin:"normal",children:[(0,N.jsx)(c.A,{children:"Category"}),(0,N.jsx)(u.A,{value:w.category,onChange:e=>S({...w,category:e.target.value}),children:["Retail","Corporate","Micro"].map((e=>(0,N.jsx)(P,{value:e,children:e},e)))})]}),(0,N.jsxs)(d.A,{fullWidth:!0,margin:"normal",children:[(0,N.jsx)(c.A,{children:"Group"}),(0,N.jsx)(u.A,{value:w.group,onChange:e=>S({...w,group:e.target.value}),children:["risk","investment","hybrid"].map((e=>(0,N.jsx)(P,{value:e,children:e},e)))})]}),(0,N.jsxs)(B.A,{className:"mt-3",children:[(0,N.jsx)(G.A,{md:6,children:(0,N.jsx)(i.A,{variant:"contained",color:"primary",onClick:async()=>{try{if("add"===b){const e=await T.A.post("/impact_products/",w);m((t=>[...t,e.data])),r("success","Product added successfully.","Success")}else if("edit"===b&&j){const e=await T.A.put(`/impact_products/${j.id}`,w);m((t=>t.map((t=>t.id===j.id?e.data:t)))),r("success","Product updated successfully.","Success")}H()}catch(e){console.error("Error saving product:",e),r("error","Failed to save product. Please try again later.","Error")}},children:"Save"})}),(0,N.jsx)(G.A,{md:6,children:(0,N.jsx)(i.A,{variant:"outlined",color:"secondary",onClick:H,children:"Cancel"})})]})]})}),(0,N.jsx)(s.A,{open:y,onClose:()=>A(!1),style:{display:"flex",alignItems:"center",justifyContent:"center"},children:(0,N.jsxs)(n.A,{style:{padding:"20px"},children:[(0,N.jsx)(o.A,{variant:"h6",gutterBottom:!0,children:"Are you sure you want to delete this product?"}),(0,N.jsxs)(B.A,{className:"mt-3",children:[(0,N.jsx)(G.A,{md:6,children:(0,N.jsx)(i.A,{variant:"contained",color:"error",onClick:async()=>{if(j)try{await T.A.delete(`/impact_products/${j.id}`),m((e=>e.filter((e=>e.id!==j.id)))),r("success","Product deleted successfully.","Success"),A(!1),f(null)}catch(e){console.error("Error deleting product:",e),r("error","Failed to delete product. Please try again later.","Error")}else r("error","No product selected for deletion.","Error")},children:"Delete"})}),(0,N.jsx)(G.A,{md:6,children:(0,N.jsx)(i.A,{variant:"outlined",color:"secondary",onClick:()=>A(!1),children:"Cancel"})})]})]})})]})}}}]);
//# sourceMappingURL=231.efa17f6d.chunk.js.map