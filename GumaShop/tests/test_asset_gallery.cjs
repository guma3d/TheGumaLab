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
