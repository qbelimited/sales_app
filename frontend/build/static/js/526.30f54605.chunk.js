"use strict";(self.webpackChunkSales_tracking_app=self.webpackChunkSales_tracking_app||[]).push([[526],{6526:(e,n,r)=>{r.r(n),r.d(n,{default:()=>v});var a=r(5043),s=r(5865),t=r(1906),l=r(4449),c=r(2110),d=r(5795),i=r(7417),o=r(3519),h=r(1072),u=r(8602),x=r(4196),j=r(7491),m=r(9621),A=r(6579),g=r(7929),y=r(579);const v=e=>{var n;let{showToast:r}=e;const[v,k]=(0,a.useState)([]),[p,f]=(0,a.useState)(!0),[b,C]=(0,a.useState)(!1),[S,B]=(0,a.useState)(!1),[w,N]=(0,a.useState)(!1),[E,_]=(0,a.useState)(!1),[F,I]=(0,a.useState)(!1),[M,P]=(0,a.useState)(null),[D,$]=(0,a.useState)(null),[T,W]=(0,a.useState)("add"),[H,L]=(0,a.useState)({name:""}),[Q,R]=(0,a.useState)({name:"",sort_code:""}),[Y,J]=(0,a.useState)([]),[O,q]=(0,a.useState)(1),z=JSON.parse(localStorage.getItem("user")),G=parseInt(null===z||void 0===z?void 0:z.role_id)||(null===z||void 0===z||null===(n=z.role)||void 0===n?void 0:n.id);(0,a.useEffect)((()=>{(async()=>{f(!0);try{const e=await m.A.get("/bank/");k(e.data)}catch(e){console.error("Error fetching banks:",e),r("error","Failed to fetch banks. Please try again later.","Error")}finally{f(!1)}})()}),[r]);const K=10*O,U=K-10,V=v.slice(U,K),X=function(e){let n=arguments.length>1&&void 0!==arguments[1]?arguments[1]:null;W(e),"edit"===e&&n?(P(n),L({name:n.name})):L({name:""}),C(!0)},Z=()=>{C(!1),P(null)};return p?(0,y.jsx)(i.A,{animation:"border"}):(0,y.jsxs)(o.A,{className:"mt-4",children:[(0,y.jsx)(h.A,{children:(0,y.jsx)(u.A,{md:12,children:(0,y.jsx)(s.A,{variant:"h4",gutterBottom:!0,children:"Bank and Branch Management"})})}),2===G||3===G?(0,y.jsx)(h.A,{children:(0,y.jsx)(u.A,{md:12,children:(0,y.jsxs)(t.A,{variant:"contained",color:"primary",onClick:()=>X("add"),children:[(0,y.jsx)(A.g,{icon:g.QLR})," Add New Bank"]})})}):null,(0,y.jsx)(h.A,{className:"mt-4",children:(0,y.jsxs)(u.A,{md:12,children:[(0,y.jsxs)(x.A,{striped:!0,bordered:!0,hover:!0,children:[(0,y.jsx)("thead",{children:(0,y.jsxs)("tr",{children:[(0,y.jsx)("th",{children:"Name"}),(0,y.jsx)("th",{children:"Actions"})]})}),(0,y.jsx)("tbody",{children:V.map((e=>(0,y.jsxs)("tr",{children:[(0,y.jsx)("td",{children:e.name}),(0,y.jsxs)("td",{children:[2===G||3===G?(0,y.jsxs)(y.Fragment,{children:[(0,y.jsxs)(t.A,{variant:"contained",color:"secondary",onClick:()=>X("edit",e),className:"me-2",children:[(0,y.jsx)(A.g,{icon:g.MT7})," Edit"]}),(0,y.jsxs)(t.A,{variant:"contained",color:"error",onClick:()=>(e=>{e&&(P(e),N(!0))})(e),children:[(0,y.jsx)(A.g,{icon:g.BeE})," Delete"]})]}):null,(0,y.jsxs)(t.A,{variant:"contained",color:"info",onClick:()=>(e=>{P(e),J(e.bank_branches||[]),B(!0)})(e),className:"ms-2",children:[(0,y.jsx)(A.g,{icon:g.FFg})," Manage Branches"]})]})]},e.id)))})]}),(0,y.jsx)(j.A,{children:Array.from({length:Math.ceil(v.length/10)},((e,n)=>(0,y.jsx)(j.A.Item,{active:n+1===O,onClick:()=>q(n+1),children:n+1},n+1)))})]})}),(0,y.jsx)(l.A,{open:b,onClose:Z,style:{overflow:"auto"},children:(0,y.jsxs)(c.A,{style:{width:"50%",margin:"5% auto",padding:"20px",maxHeight:"80vh",overflowY:"auto"},children:[(0,y.jsx)(s.A,{variant:"h5",gutterBottom:!0,children:"add"===T?"Add New Bank":"Edit Bank"}),(0,y.jsx)(d.A,{fullWidth:!0,label:"Bank Name",value:H.name,onChange:e=>L({...H,name:e.target.value}),margin:"normal"}),(0,y.jsxs)(h.A,{className:"mt-3",children:[(0,y.jsx)(u.A,{md:6,children:(0,y.jsx)(t.A,{variant:"contained",color:"primary",onClick:async()=>{try{if("add"===T){const e=await m.A.post("/bank/",H);k((n=>[...n,e.data])),r("success","Bank added successfully.","Success")}else if("edit"===T&&M){const e=await m.A.put(`/bank/${M.id}`,H);k((n=>n.map((n=>n.id===M.id?e.data:n)))),r("success","Bank updated successfully.","Success")}Z()}catch(e){console.error("Error saving bank:",e),r("error","Failed to save bank. Please try again later.","Error")}},children:"Save"})}),(0,y.jsx)(u.A,{md:6,children:(0,y.jsx)(t.A,{variant:"outlined",color:"secondary",onClick:Z,children:"Cancel"})})]})]})}),(0,y.jsx)(l.A,{open:S,onClose:()=>{B(!1),R({name:"",sort_code:""})},style:{overflow:"auto"},children:(0,y.jsxs)(c.A,{style:{width:"70%",margin:"3% auto",padding:"20px",maxHeight:"80vh",overflowY:"auto"},children:[(0,y.jsxs)(s.A,{variant:"h5",gutterBottom:!0,children:["Manage Branches for ",null===M||void 0===M?void 0:M.name]}),(0,y.jsxs)(x.A,{striped:!0,bordered:!0,hover:!0,children:[(0,y.jsx)("thead",{children:(0,y.jsxs)("tr",{children:[(0,y.jsx)("th",{children:"Name"}),(0,y.jsx)("th",{children:"Sort Code"}),(0,y.jsx)("th",{children:"Actions"})]})}),(0,y.jsx)("tbody",{children:Y.map((e=>(0,y.jsxs)("tr",{children:[(0,y.jsx)("td",{children:e.name}),(0,y.jsx)("td",{children:e.sort_code}),(0,y.jsx)("td",{children:2===G||3===G?(0,y.jsxs)(y.Fragment,{children:[(0,y.jsxs)(t.A,{variant:"contained",color:"secondary",onClick:()=>(e=>{e&&(R({name:e.name,sort_code:e.sort_code,id:e.id}),$(e),W("edit"),_(!0))})(e),className:"me-2",children:[(0,y.jsx)(A.g,{icon:g.MT7})," Edit"]}),(0,y.jsxs)(t.A,{variant:"contained",color:"error",onClick:()=>(e=>{e&&($(e),I(!0))})(e),children:[(0,y.jsx)(A.g,{icon:g.BeE})," Delete"]})]}):null})]},e.id)))})]}),2===G||3===G?(0,y.jsxs)(t.A,{variant:"contained",color:"primary",onClick:()=>{R({name:"",sort_code:""}),W("add"),_(!0)},className:"mt-3",children:[(0,y.jsx)(A.g,{icon:g.QLR})," Add New Branch"]}):null]})}),(0,y.jsx)(l.A,{open:E,onClose:()=>_(!1),style:{display:"flex",alignItems:"center",justifyContent:"center"},children:(0,y.jsxs)(c.A,{style:{width:"30%",padding:"20px"},children:[(0,y.jsx)(s.A,{variant:"h5",gutterBottom:!0,children:"add"===T?"Add Branch":"Edit Branch"}),(0,y.jsx)(d.A,{fullWidth:!0,label:"Branch Name",value:Q.name,onChange:e=>R({...Q,name:e.target.value}),margin:"normal"}),(0,y.jsx)(d.A,{fullWidth:!0,label:"Sort Code",value:Q.sort_code,onChange:e=>R({...Q,sort_code:e.target.value}),margin:"normal"}),(0,y.jsxs)(h.A,{className:"mt-3",children:[(0,y.jsx)(u.A,{md:6,children:(0,y.jsx)(t.A,{variant:"contained",color:"primary",onClick:async()=>{if(M)try{if("add"===T){const e=await m.A.post("/bank/bank-branches",{bank_id:M.id,name:Q.name,sort_code:Q.sort_code,is_deleted:!1});J((n=>[...n,e.data])),r("success","Branch added successfully.","Success")}else if("edit"===T&&D){const e=await m.A.put(`/bank/bank-branches/${D.id}`,Q);J((n=>n.map((n=>n.id===D.id?e.data:n)))),r("success","Branch updated successfully.","Success")}_(!1)}catch(e){console.error("Error saving branch:",e),r("error","Failed to save branch. Please try again later.","Error")}else r("error","No bank selected for branch operation.","Error")},children:"Save"})}),(0,y.jsx)(u.A,{md:6,children:(0,y.jsx)(t.A,{variant:"outlined",color:"secondary",onClick:()=>_(!1),children:"Cancel"})})]})]})}),(0,y.jsx)(l.A,{open:F,onClose:()=>I(!1),style:{display:"flex",alignItems:"center",justifyContent:"center"},children:(0,y.jsxs)(c.A,{style:{padding:"20px"},children:[(0,y.jsx)(s.A,{variant:"h6",gutterBottom:!0,children:"Are you sure you want to delete this branch?"}),(0,y.jsxs)(h.A,{className:"mt-3",children:[(0,y.jsx)(u.A,{md:6,children:(0,y.jsx)(t.A,{variant:"contained",color:"error",onClick:async()=>{if(D)try{await m.A.delete(`/bank/bank-branches/${D.id}`),J((e=>e.filter((e=>e.id!==D.id)))),r("success","Branch deleted successfully.","Success"),I(!1),$(null)}catch(e){console.error("Error deleting branch:",e),r("error","Failed to delete branch. Please try again later.","Error")}else r("error","No branch selected for deletion.","Error")},children:"Delete"})}),(0,y.jsx)(u.A,{md:6,children:(0,y.jsx)(t.A,{variant:"outlined",color:"secondary",onClick:()=>I(!1),children:"Cancel"})})]})]})}),(0,y.jsx)(l.A,{open:w,onClose:()=>N(!1),style:{display:"flex",alignItems:"center",justifyContent:"center"},children:(0,y.jsxs)(c.A,{style:{padding:"20px"},children:[(0,y.jsx)(s.A,{variant:"h6",gutterBottom:!0,children:"Are you sure you want to delete this bank?"}),(0,y.jsxs)(h.A,{className:"mt-3",children:[(0,y.jsx)(u.A,{md:6,children:(0,y.jsx)(t.A,{variant:"contained",color:"error",onClick:async()=>{if(M)try{await m.A.delete(`/bank/${M.id}`),k((e=>e.filter((e=>e.id!==M.id)))),r("success","Bank deleted successfully.","Success"),N(!1),P(null)}catch(e){console.error("Error deleting bank:",e),r("error","Failed to delete bank. Please try again later.","Error")}else r("error","No bank selected for deletion.","Error")},children:"Delete"})}),(0,y.jsx)(u.A,{md:6,children:(0,y.jsx)(t.A,{variant:"outlined",color:"secondary",onClick:()=>N(!1),children:"Cancel"})})]})]})})]})}}}]);
//# sourceMappingURL=526.30f54605.chunk.js.map