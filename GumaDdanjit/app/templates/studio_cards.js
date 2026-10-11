const cards=[...document.querySelectorAll('.recommendation')];
function paint(card,flow){
 card.flow=flow;if(flow){card.dataset.idea=flow.id;card.querySelector('.product-title').href='/ideas/'+flow.id}
 const notice=card.querySelector('.workflow-message');notice.hidden=!flow;notice.textContent=flow?.message||'';
 card.querySelector('.steps').innerHTML=(flow?.buttons||[]).map(a=>`<div class="stage-line"><span>${a.stage==='Preview'?'컷씬':'영상'} · ${esc(a.state)}</span><p class="muted">${esc(a.progress_message)}</p></div>`).join('');
}
async function openTitle(event,link){if(link.closest('.recommendation').dataset.idea)return;event.preventDefault();const card=link.closest('.recommendation');try{const d=await api('/api/ideas',{recommendation_id:card.dataset.rec,date:recommendationDate});location.href='/ideas/'+d.id}catch(e){toast(e.message)}}
cards.forEach(c=>paint(c,initialFlows[c.dataset.rec]));
setInterval(async()=>{if(document.hidden)return;await Promise.allSettled(cards.filter(c=>c.dataset.idea).map(async c=>{const r=await fetch('/api/ideas/'+c.dataset.idea);if(r.ok)paint(c,(await r.json()).workflow)}))},5000);
