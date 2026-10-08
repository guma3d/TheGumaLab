const { readFileSync } = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = readFileSync('app/static/app.js', 'utf8');
// Execute render functions without browser event wiring or network bootstrap.
const context = vm.createContext({ location: { hash: '#assets/rabbit/video' } });
vm.runInContext(source.slice(0, source.indexOf('document.addEventListener(')), context);
vm.runInContext(`state = {
  characters: [{id:'rabbit',name:'엄마',reference_id:'portrait',categories:['food']}, {id:'cat',name:'딸',categories:['beauty']}],
  assets: [
    {id:'portrait', title:'엄마 그림',character_id:'rabbit',kind:'image',bytes:100,archived:false},
    {id:'clip',title:'엄마 영상',character_id:'rabbit',kind:'video',bytes:100,archived:false},
    {id:'other',title:'딸 영상',character_id:'cat',kind:'video',bytes:100,archived:false},
    {id:'old',title:'이전 엄마 영상',character_id:'rabbit',kind:'video',bytes:100,archived:true}
  ]
}`, context);
let html = vm.runInContext('assetsPage()',context);
assert.match(html,/api\/assets\/clip\/file/);
assert.doesNotMatch(html,/api\/assets\/(portrait|other|old)\/file/);
assert.match(html, /controls playsinline/);
context.location.hash = '#assets/all/image';
html = vm.runInContext('assetsPage()',context);
assert.match(html,/api\/assets\/portrait\/file/);
assert.doesNotMatch(html,/<video/);
context.location.hash = '#assets/archive/video';
html = vm.runInContext('assetsPage()',context);
assert.match(html,/api\/assets\/old\/file/);
assert.doesNotMatch(html,/api\/assets\/clip\/file/);
vm.runInContext(`query = '없는 검색어'`,context);
assert.doesNotMatch(vm.runInContext('assetsPage()',context),/api\/assets\/old\/file/);
assert.match(vm.runInContext("animal('rabbit')",context), /api\/assets\/portrait\/file/);
assert.match(vm.runInContext('familyCard(state.characters[0])',context), /#assets\/rabbit\/video/);
console.log('Gallery filters, archived assets, search, profile and family links passed.');
vm.runInContext(`state.costs=[]; state.videos=[]; state.products=[]; state.jobs=[];
state.projects=[{id:'board',title:'이미지 콘티',category:'food',concept:'35초 무대사',revision:1,
  character_ids:['rabbit'],product_id:'',approved_at:null,archived:false,budget:0,attempt_limit:3,
  cuts:[{title:'<첫 장면>',seconds:4,visual:'문을 여는 장면',asset_id:'portrait'},
        {title:'준비 중',seconds:6,visual:'두 번째 장면',asset_id:''}]}]`,context);
html=vm.runInContext("projectPage('board','images')",context);
assert.match(html,/storyboard-image-grid/);
assert.match(html,/api\/assets\/portrait\/file/);
assert.match(html,/&lt;첫 장면&gt;/);
assert.match(html,/장면 이미지 준비 중/);
assert.match(html,/#project\/board\/images/);
console.log('Storyboard image page, linked images and pending image fallback passed.');
vm.runInContext(`state.assets.push({id:'oldimage',kind:'image',archived:true}); state.storyboards=[{id:'old-board',project_id:'board',number:1,label:'<초안>',note:'이전 화면',created_at:'2026-10-08',
storyboard:{...state.projects[0],cuts:[{title:'이전 컷',seconds:4,visual:'이전 설명',asset_id:'oldimage'}]}}]`,context);
html=vm.runInContext("projectPage('board','images','old-board')",context);
assert.match(html,/api\/assets\/oldimage\/file/);
assert.doesNotMatch(html,/&lt;첫 장면&gt;/);
assert.match(html,/&lt;초안&gt;/);
assert.match(html,/이전 설명/);
html=vm.runInContext("projectPage('board','versions')",context);
assert.match(html,/#project\/board\/images\/old-board/);
assert.match(html,/버전 관리/);
assert.match(vm.runInContext("projectPage('board','images','missing')",context),/버전을 찾을 수 없어요/);
console.log('Immutable version routes, archived images, labels and missing version fallback passed.');
vm.runInContext(`state.feedback=[];state.videos=[{id:'test-film',project_id:'board',status:'review',production_status:'partial_generation',storyboard_version_number:4,storyboard_revision:9,created_at:'2026-10-08',duration:35,bytes:100,is_preview:true}];`,context);
html=vm.runInContext("videosPanel(state.projects[0])",context);
assert.match(html,/제작 중 편집본/);
assert.match(html,/콘티 v4/);
assert.doesNotMatch(html,/콘티 v9/);
console.log('Partial video label and explicit storyboard version passed.');
