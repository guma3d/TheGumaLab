// UI controller regression without paid generation or production data changes.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('app/templates/studio_cards.js','utf8');
const nodes={},events={},writes=[];
function node(){return {dataset:{},innerHTML:'',textContent:'',value:'',checked:false,classList:{add(){}},setAttribute(){},addEventListener(name,fn){events[name]=fn}}}
const card=node();card.dataset={rec:'recommendation',idea:'product'};card.querySelector=s=>nodes[s]??=node();
const button=node();button.closest=()=>card;
let state={id:'product',versions:{'3DModel':[{number:4,status:'ready',approved_at:'approved'}],Preview:[],Video:[]},workflow:{id:'product',approved:true,running:false,buttons:[],message:'next'}};
let unblock;let gate=Promise.resolve();
const sandbox={console,Set,Promise,JSON,Object,Error,initialFlows:{recommendation:state.workflow},category:'tech',recommendationDate:'2026-10-02',
 document:{hidden:false,querySelectorAll:()=>[card],getElementById:id=>nodes[id]??=node(),addEventListener(){}},
 window:{addEventListener(){}},location:{href:'unchanged'},setInterval(){},esc:x=>x??'',safeLink:x=>x,toast(){},
 fetch:async()=>({ok:true,json:async()=>structuredClone(state)}),
 api:async(url,body)=>{writes.push({url,body});await gate;state.workflow={...state.workflow,running:true,buttons:[{stage:'Preview',status:'running',state:'생성 중',number:1,primary:true,disabled:true,regen_disabled:true,progress_message:'1/6 컷'}]};return {number:1,status:'running'}}};
vm.createContext(sandbox);vm.runInContext(source,sandbox);
(async()=>{
 await sandbox.runStage(button,'Preview',false);
 await sandbox.runStage(button,'Preview',true);
 await sandbox.runStage(button,'3DModel',false);
 await sandbox.runStage(button,'3DModel',true);
 assert.equal(writes.length,0,'preparation buttons must never invoke paid APIs');
 assert.equal(sandbox.location.href,'unchanged');
 sandbox.paint(card,{id:'product',message:'준비 중',buttons:[{stage:'Preview',status:'awaiting_review',state:'검증 중'},{stage:'3DModel',status:'ready',state:'완료'}]});
 assert.doesNotMatch(nodes['.steps'].innerHTML,/onclick=/);
 assert.match(nodes['.steps'].innerHTML,/검증 중/);
 console.log('PASS: scheduled preparation has no paid buttons or navigation');
})().catch(e=>{console.error(e);process.exitCode=1});
