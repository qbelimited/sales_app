"use strict";(self.webpackChunkfrontend=self.webpackChunkfrontend||[]).push([[379],{7379:(e,s,t)=>{t.r(s),t.d(s,{default:()=>p});var a=t(5043),l=t(1072),n=t(8602),r=t(3814),c=t(4282),d=t(7417),i=t(4196),o=t(1899),h=t.n(o),x=(t(5015),t(9621)),j=t(3204),m=t(579);const p=e=>{let{showToast:s}=e;const[t,o]=(0,a.useState)([]),[p,g]=(0,a.useState)(!0),[u,v]=(0,a.useState)(null),[y,A]=(0,a.useState)({type:"",level:"",startDate:null,endDate:null}),[N,f]=(0,a.useState)(1),[C]=(0,a.useState)(50),[S,D]=(0,a.useState)(1),k=(0,a.useCallback)((async()=>{g(!0),v(null);try{const e={page:N,per_page:C,...y.type&&{type:y.type},...y.level&&{level:y.level},...y.startDate&&{start_date:y.startDate.toISOString().split("T")[0]},...y.endDate&&{end_date:y.endDate.toISOString().split("T")[0]}},s=await x.A.get("/logs/",{params:e});o(s.data.logs||[]),D(s.data.total_pages||1)}catch(u){console.error("Error fetching logs:",u),v("Failed to fetch logs. Please try again later."),s("danger","Failed to fetch logs. Please try again later.","Error")}finally{g(!1)}}),[N,C,y,s]);(0,a.useEffect)((()=>{k()}),[k]);const E=e=>f(e),R=Math.max(1,N-Math.floor(2.5)),T=Math.min(S,R+5-1);return(0,m.jsxs)("div",{style:{marginTop:"20px",padding:"20px"},children:[(0,m.jsx)(l.A,{className:"mb-4",children:(0,m.jsx)(n.A,{children:(0,m.jsx)("h2",{children:"Logs"})})}),(0,m.jsx)(r.A,{className:"mb-4",children:(0,m.jsxs)(l.A,{className:"align-items-end",children:[(0,m.jsx)(n.A,{md:2,children:(0,m.jsxs)(r.A.Control,{as:"select",value:y.type,onChange:e=>A({...y,type:e.target.value}),children:[(0,m.jsx)("option",{value:"",children:"Log Type"}),(0,m.jsx)("option",{value:"general",children:"General"}),(0,m.jsx)("option",{value:"error",children:"Error"}),(0,m.jsx)("option",{value:"success",children:"Success"})]})}),(0,m.jsx)(n.A,{md:2,children:(0,m.jsxs)(r.A.Control,{as:"select",value:y.level,onChange:e=>A({...y,level:e.target.value}),children:[(0,m.jsx)("option",{value:"",children:"Log Level"}),(0,m.jsx)("option",{value:"INFO",children:"INFO"}),(0,m.jsx)("option",{value:"WARNING",children:"WARNING"}),(0,m.jsx)("option",{value:"ERROR",children:"ERROR"})]})}),(0,m.jsx)(n.A,{md:2,children:(0,m.jsx)(h(),{selected:y.startDate,onChange:e=>A({...y,startDate:e}),placeholderText:"Start Date",className:"form-control"})}),(0,m.jsx)(n.A,{md:2,children:(0,m.jsx)(h(),{selected:y.endDate,onChange:e=>A({...y,endDate:e}),placeholderText:"End Date",className:"form-control"})}),(0,m.jsxs)(n.A,{md:2,children:[(0,m.jsxs)(c.A,{variant:"primary",onClick:()=>{f(1),k()},children:[(0,m.jsx)(j.KSO,{})," Filter"]}),(0,m.jsxs)(c.A,{variant:"secondary",onClick:()=>{A({type:"",level:"",startDate:null,endDate:null}),f(1),k()},className:"ms-2",children:[(0,m.jsx)(j.EEI,{})," Reset"]})]})]})}),u&&(0,m.jsx)("p",{className:"text-center text-danger",children:u}),p&&(0,m.jsx)("div",{className:"text-center my-3",children:(0,m.jsx)(d.A,{animation:"border"})}),!p&&(0,m.jsxs)(i.A,{striped:!0,bordered:!0,hover:!0,responsive:!0,children:[(0,m.jsx)("thead",{children:(0,m.jsxs)("tr",{children:[(0,m.jsx)("th",{children:"#"}),(0,m.jsx)("th",{children:"Timestamp"}),(0,m.jsx)("th",{children:"Type"}),(0,m.jsx)("th",{children:"Level"}),(0,m.jsx)("th",{children:"Message"})]})}),(0,m.jsx)("tbody",{children:t.length>0?t.map(((e,s)=>(0,m.jsxs)("tr",{children:[(0,m.jsx)("td",{children:(N-1)*C+s+1}),(0,m.jsx)("td",{children:new Date(e.timestamp).toLocaleString()}),(0,m.jsx)("td",{children:e.type}),(0,m.jsx)("td",{children:e.level}),(0,m.jsx)("td",{children:e.message})]},e.id||s))):(0,m.jsx)("tr",{children:(0,m.jsx)("td",{colSpan:"5",className:"text-center",children:"No logs found"})})})]}),!p&&S>1&&(0,m.jsx)(l.A,{className:"mt-3",children:(0,m.jsxs)(n.A,{className:"text-center",children:[N>1&&(0,m.jsxs)(m.Fragment,{children:[(0,m.jsx)(c.A,{variant:"secondary",onClick:()=>E(1),className:"mx-1",children:(0,m.jsx)(j.X8f,{})}),(0,m.jsx)(c.A,{variant:"secondary",onClick:()=>E(N-1),className:"mx-1",children:(0,m.jsx)(j.QVr,{})})]}),[...Array(T-R+1).keys()].map((e=>(0,m.jsx)(c.A,{variant:N===R+e?"primary":"secondary",onClick:()=>E(R+e),className:"mx-1",children:R+e},R+e))),N<S&&(0,m.jsxs)(m.Fragment,{children:[(0,m.jsx)(c.A,{variant:"secondary",onClick:()=>E(N+1),className:"mx-1",children:(0,m.jsx)(j.Z0P,{})}),(0,m.jsx)(c.A,{variant:"secondary",onClick:()=>E(S),className:"mx-1",children:(0,m.jsx)(j.eaw,{})})]})]})})]})}}}]);
//# sourceMappingURL=379.22808341.chunk.js.map