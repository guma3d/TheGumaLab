const cards=[...document.querySelectorAll('.recommendation')], pending=new Set();
let reviewRequest=null, polling=false;
const stageNames=category==='tech'?{Preview:'프리뷰·클립','3DModel':'3D 모델',Video:'영상'}:{'3DModel':'자료',Preview:'프리뷰',Video:'영상'};
const generateLabels={'3DModel':category==='tech'?'Generate 3D Model':'Prepare Real Media',Preview:'Generate Preview & Clips',Video:'Create Video'};
function paint(card,flow){
    card.flow=flow;
    if(flow){card.dataset.idea=flow.id;card.querySelector('.product-title').href='/ideas/'+flow.id}
    const notice=card.querySelector('.workflow-message');notice.hidden=!flow;
    notice.innerHTML=flow?`${flow.approved?`<span class="approved-mark">✓ ${stageNames['3DModel']} 승인 완료</span>`:''}<strong>${esc(flow.message)}</strong>`:'';
    const first=category==='tech'?'Preview':'3DModel';
    const actions=flow?.buttons||Object.keys(stageNames).map(stage=>({stage,status:'empty',state:'대기',primary:stage===first,disabled:stage!==first,regen_disabled:stage!==first}));
    card.querySelector('.steps').innerHTML=actions.map((a,i)=>{
        const running=a.status==='running';
        const label=running?`${stageNames[a.stage]} 생성 중`:a.status==='ready'?`${stageNames[a.stage]} ${a.state==='승인 완료'?'승인 완료':'완료'}`:a.status==='failed'?'다시 생성':generateLabels[a.stage];
        return `<div class="stage-line"><div class="stage-caption"><span>${i+1} · ${stageNames[a.stage]}</span><span>${a.number?'v'+a.number+' · ':''}${esc(a.state)}</span></div><div class="step"><button data-stage="${a.stage}" class="${a.primary?'primary ':''}${running?'in-progress':a.status==='ready'?'stage-complete':''}" ${a.disabled||running?'disabled':''} aria-busy="${running}" onclick="runStage(this,'${a.stage}',false)">${running?'<span class="button-progress" role="progressbar" aria-label="생성 진행 중"></span>':''}<span>${esc(label)}</span></button><button class="regen" title="새 버전 생성" aria-label="${stageNames[a.stage]} 재생성" ${a.regen_disabled?'disabled':''} onclick="runStage(this,'${a.stage}',true)">↻</button></div>${running?`<small class="progress-note">${esc(a.progress_message||'작업 준비 중')}</small>`:''}</div>`;
    }).join('');
}
async function getState(card){
    const response=await fetch('/api/ideas/'+card.dataset.idea,{cache:'no-store'});
    if(!response.ok)throw Error('진행 상태를 확인하지 못했습니다.');
    return response.json();
}
async function ensureIdea(card){
    if(!card.dataset.idea){const idea=await api('/api/ideas',{recommendation_id:card.dataset.rec,date:recommendationDate});card.dataset.idea=idea.id;card.querySelector('.product-title').href='/ideas/'+idea.id}
}
async function openTitle(event,link){
    if(link.closest('.recommendation').dataset.idea)return;
    event.preventDefault();const card=link.closest('.recommendation');
    try{await ensureIdea(card);location.href=link.href}catch(e){toast(e.message)}
}
function pendingButton(button){
    button.disabled=true;button.classList.add('in-progress');button.setAttribute('aria-busy','true');
    button.innerHTML='<span class="button-progress" role="progressbar" aria-label="작업 요청 중"></span><span>…</span>';
}
async function runStage(button,stage,regen){
    const card=button.closest('.recommendation');if(pending.has(card))return;
    pending.add(card);pendingButton(button);
    try{
        await ensureIdea(card);const data=await getState(card);
        const old=data.versions[stage][0];
        if(data.workflow.running){paint(card,data.workflow);return}
        if(old?.status==='ready'&&!regen){paint(card,data.workflow);toast('완성된 결과는 제품 제목에서 확인하세요.');return}
        if(stage==='Video'){showVideoReview(card,data,regen||old?.status==='failed');return}
        const body={regenerate:regen||old?.status==='failed'};
        if(stage==='3DModel'&&category==='tech'){
            const preview=data.versions.Preview[0];
            if(preview?.status!=='ready'||!preview.needs_3d)throw Error('3D 보완이 필요한 프리뷰를 먼저 완성해주세요.');
            body.preview_version=preview.number;body.approved=true;
        }
        if(stage==='Preview'&&category!=='tech'){
            const model=data.versions['3DModel'][0];
            if(model?.status!=='ready'||!model.approved_at)throw Error('제품 제목을 눌러 모델·자료를 먼저 승인해주세요.');
            body.model_version=model.number;
        }
        await api(`/api/ideas/${data.id}/${stage}`,body);
        paint(card,(await getState(card)).workflow);
    }catch(e){toast(e.message);try{if(card.dataset.idea)paint(card,(await getState(card)).workflow);else paint(card,card.flow)}catch{paint(card,card.flow)}}
    finally{pending.delete(card);if(stage==='Video')paint(card,card.flow)}
}
function showVideoReview(card,data,regen){
    const preview=data.versions.Preview[0];
    if(preview?.status!=='ready')throw Error('완성된 프리뷰가 필요합니다.');
    reviewRequest={card,idea:data.id,preview:preview.number,regen};
    document.getElementById('review-product').textContent=`${data.title} · 프리뷰 v${preview.number}`;
    document.getElementById('review-scenes').innerHTML=preview.storyboard.scenes.map((s,i)=>`<div class="scene">${s.clip_url?`<video controls muted playsinline preload="metadata" poster="${esc(safeLink(s.image_url))}" src="${esc(safeLink(s.clip_url))}"></video>`:`<img src="${esc(safeLink(s.image_url))}" alt="컷 ${i+1}">`}<p><small>${s.visual_mode==='official_clip'?'공식 클립':s.visual_mode==='mechanism_concept'?'원리 개념도 · 실제 내부 설계 아님':s.visual_mode==='approved_model'?'승인한 제품 모델':'실사 자료'}</small></p><p><small>${esc(s.camera_movement||'')}</small></p>${s.reference_limitation?`<p><small>${esc(s.reference_limitation)}</small></p>`:''}${(s.feature_references||[]).map(r=>`<p><a href="${esc(safeLink(r.page_url))}" target="_blank" rel="noopener noreferrer">공식 참고자료</a></p>`).join('')}<label>컷 ${i+1} 대본<textarea required maxlength="1000" class="review-narration">${esc(s.narration_ko)}</textarea></label></div>`).join('');
    document.getElementById('review-url').value=data.versions.Video[0]?.product_url||'';
    document.getElementById('review-approved').checked=false;
    document.getElementById('review-error').textContent='';
    document.getElementById('video-review').showModal();
}
document.getElementById('video-review-form').addEventListener('input',event=>{
    if(event.target.id!=='review-approved')document.getElementById('review-approved').checked=false;
});
document.getElementById('video-review-form').addEventListener('submit',async event=>{
    event.preventDefault();if(!reviewRequest)return;
    const {card,idea,preview,regen}=reviewRequest;if(pending.has(card))return;
    const button=event.submitter;pending.add(card);button.disabled=true;
    try{
        await api(`/api/ideas/${idea}/Video`,{regenerate:regen,preview_version:preview,approved:document.getElementById('review-approved').checked,product_url:document.getElementById('review-url').value,narrations:[...document.querySelectorAll('.review-narration')].map(t=>t.value)});
        document.getElementById('video-review').close();paint(card,(await getState(card)).workflow);
    }catch(e){document.getElementById('review-error').textContent=e.message}
    finally{pending.delete(card);button.disabled=false}
});
async function refreshCards(){
    if(polling||document.hidden)return;polling=true;
    try{await Promise.allSettled(cards.filter(c=>c.dataset.idea&&!pending.has(c)).map(async card=>{
        const data=await getState(card);if(!pending.has(card))paint(card,data.workflow);
    }))}finally{polling=false}
}
cards.forEach(card=>paint(card,initialFlows[card.dataset.rec]));
window.addEventListener('pageshow',refreshCards);
document.addEventListener('visibilitychange',()=>{if(!document.hidden)refreshCards()});
setInterval(refreshCards,4000);
