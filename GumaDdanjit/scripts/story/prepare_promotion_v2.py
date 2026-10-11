"""Prepare an immutable-parent visual revision; retain unchanged v1 audio."""
import hashlib, json, shutil
from pathlib import Path

base=Path(__file__).resolve().parents[2]
storage=base/'storage/story'
parent=storage/'productions/promotion-v1'
root=storage/'productions/promotion-v2'
if (root/'image-jobs.json').exists() or (root/'final.mp4').exists():
    raise SystemExit('Existing production preserved. Use its job manifest; do not prepare this version again.')
root.mkdir(parents=True,exist_ok=True)
for name in ('script.json','timeline.json','music-selection.json','chapters.txt'):
    if not (root/name).exists():shutil.copy2(parent/name,root/name)
(root/'images').mkdir(exist_ok=True)
(root/'rejected').mkdir(exist_ok=True)

# One new illustration per illustrated paragraph. Diagrams and measured charts stay data-native.
scenes={
1:('man','Promotion celebration in a modern office: close-up of conflicted man holding a cream promotion envelope and looking at his phone; blurred colleagues clap behind him. Only the BACK of the phone faces camera, never screen and rear cameras on the same face. Warm confetti against cool office.'),
2:('man','Over-the-shoulder shot of man at office desk opening a laptop job-board interface immediately after receiving congratulations, bouquet and promotion envelope beside laptop. Abstract UI blocks only. Screen faces him, keyboard physically connected, no rear-camera phone.'),
3:('man','Wide elevator lobby at end of workday. Promoted man carries a small congratulatory bouquet but pauses at the exit with a puzzled expression, while confident colleagues head upstairs. Visual irony of moving up versus leaving, believable office geography.'),
4:('woman','Curious professional woman at a research desk pulls a survey report from a stack and uses a magnifying glass over a simple abstract questionnaire. Overhead three-quarter shot, practical lamp, no readable figures or text.'),
6:('man','Surreal editorial metaphor: man at foot of tall ladder hesitates to climb toward a luxurious empty executive chair high above. Side view of entire ladder and grounded feet, uncluttered theatrical teal backdrop, thoughtful not frightened.'),
10:('woman','Woman carefully inspects a promotion offer folder with several blank checklist rows while another person offers a shiny new office nameplate. Focus on her inquisitive expression rather than a title. Intimate desk-level close shot.'),
11:('man','Empty impressive managerial chair under a spotlight, surrounded by an absurdly large semicircle of overflowing task trays; small man stands beside it sizing up the real workload. Wide, humorous scale contrast.'),
12:('woman','Woman retrieves a clearly aged survey folder from an office archive shelf and places it beside a new folder. Dust in warm light, investigative side view, blank covers without invented years.'),
16:('man','Same man adapted for a relaxed weekend walk, cream shirt and navy trousers, mustard backpack. He enjoys a gentle wooded trail while a distant snowy technical summit with tiny mountaineers shows a different goal. Wide scenic shot, playful clear hiking analogy.'),
18:('woman','Woman in calm discussion with several distinct young adult coworkers in an airy cafe, listening to varied thoughtful expressions instead of diagnosing fear. Candid eye-level group composition, no uniform worried crowd.'),
19:('man','Man pauses one foot before a small upward office staircase blocked by neatly visible heavy archive boxes and a tangled cable; he studies the obstacles rather than looking afraid. Low side angle, literal changeable working conditions.'),
20:('man','Top-down desk reveal: a new brass nameplate with blank face sits on a desk buried under two separate mountains of old and new folders, man visible at edge with palms open in surprise. Fresh promotion ribbon is tiny beside workload.'),
21:('woman','Woman braces to lift a large transparent glass cube containing neatly visible project folders, examining its weight before accepting it. Editorial responsibility metaphor, full-body diagonal composition, credible hands, clean background.'),
23:('man','At a tense review meeting everyone turns toward the new manager at the far end of the table, man holding a thin report while several coworkers gesture toward an unfinished model project. Wide cinematic perspective, no aggressive caricatures.'),
24:('man','Clearly surreal comedic metaphor: man seated at the driver position of a stationary open-top office-like car; his steering column ends in a smooth empty socket, while a second adult standing safely outside holds the detached steering wheel. No road traffic. Show the missing control clearly, wide side view.'),
27:('man','Man is handed an enormous sealed project crate while the nearby supply cabinet is visibly empty. Offscreen hands give encouraging thumbs up, but no tools arrive. Comic medium wide shot, man gives a dry skeptical glance.'),
29:('woman','Woman at a quiet desk compares two transparent folders: one contains a small storm-cloud model, the other a disconnected mechanical lever. Thoughtful balanced expression, physical metaphor for emotion versus controllable conditions, warm close shot.'),
30:('man','Man thoughtfully weighs a small coin stack against an hourglass on a desk balance scale. Natural three-quarter close-up, sleeves rolled, practical calculator nearby, visual compensation-versus-time negotiation.'),
31:('woman','Top-down hands of woman arranging blank cream calculation cards, wooden coins and miniature clock on a teal work mat; obviously a tabletop hypothetical example, not real financial statement. No invented text or numbers.'),
36:('man','Evening home dinner table set for family; man still in office clothes stands at doorway looking at a ringing phone with ONLY its back visible. Food cooling, empty chair waiting, clock has unnumbered ticks. Warm home versus blue office light through doorway, emotionally specific.'),
38:('woman','Woman in office skirt outfit kneels beside an elderly adult relative to help with a cardigan before an evening walk, work bag and closed laptop on bench nearby. Caring adult family scene, eye-level, gentle modern home, no medical claims.'),
39:('woman','Macro foreground of a promotion folder opening to reveal many layered blank condition sheets instead of only one gold badge; woman leans in thoughtfully in background. Tactile paper, shallow depth of field, no text.'),
40:('woman','Talented designer woman at a beautiful digital drawing workstation suddenly receives a manager badge and a thick meeting planner covering her stylus. Side view captures creative tool and intrusive planner, wry expression.'),
41:('woman','Woman in teal blazer mediates between two adult coworkers arguing over different abstract design boards while her own drawing tablet sits idle in foreground. Busy real office, expressive but respectful, wide triangular staging.'),
44:('man','Man studies two distinct workstations in a training room: hands-on sales/product demonstration counter and a team-coordination table. He compares the different tools thoughtfully, investigative medium-wide composition, no map or invented statistics.'),
45:('woman','Woman beginning a new management lesson, sleeves neatly adjusted, notebook open, tentative but willing expression as she raises a hand to ask a trainer. Small realistic workshop, foreground learning materials, warm daylight.'),
46:('man','Humorous swimming analogy: same man beside indoor swimming pool, cream shirt and mustard tie, holding swim goggles in one hand and a huge pool-facility operations binder in the other. He looks from goggles to plumbing control panel, showing skill versus management. Fully clothed, wide shot.'),
49:('woman','Woman opens a polished promotion envelope and finds a blank job-description page with a large empty outlined area. Workroom behind shows several different real tasks waiting. Over-shoulder intimate detail, no readable text.'),
50:('man','Experienced adult mentor sits beside man at a bright office table and walks through a practical project model together, both actively engaged. Warm hopeful two-shot, distinct mentor face, realistic hand poses and materials.'),
51:('man','Man caught between his OLD desk overflowing with unfinished folders and a NEW manager desk loaded with team requests, standing in narrow aisle holding one folder from each. Symmetrical wide shot with clear two-workload dilemma.'),
53:('woman','Woman passes a single project folder to a receiving coworker across a shared desk with a simple calendar grid and handover checklist; clear act of transfer, hands anatomically correct. Diagonal close shot, decisive hopeful mood.'),
55:('none','Macro cinematic editorial metaphor: a cream ceramic cup already full spills water onto a teal office desk as a glass pitcher keeps pouring. A second empty cup stands nearby. No faces, no text, realistic gravity, beautiful 3D materials, one frozen splash moment.'),
58:('woman','Woman and mentor build a small safe stepping-stone path across a shallow model gap on conference table, project folders organized beside it. Concrete supported challenge metaphor, medium-wide confident teamwork.'),
60:('man','Man politely asks a question during promotion discussion, open notebook and one raised index finger; manager opposite listens attentively. Camera near listener shoulder, brave constructive curiosity, no fearful posture.'),
61:('woman','Woman at workshop crossroads: one direction leads to team meeting chairs, another to a sophisticated creative workstation. She confidently walks toward specialist work, energetic posture and purposeful choice, wide office scene.'),
63:('man','Man deeply focused solving a customer technical problem at a workstation, small grateful customer video tile abstract without readable text, meticulous notes and prototype visible. Close on concentration, visibly diligent specialist, no executive chair.'),
66:('woman','Woman leaving office at daylight after placing a neatly finished project model on a team desk; another adult stays working on a different incomplete task. Neutral balanced scene, no moral superiority, wide doorway perspective.'),
67:('none','Playful visual metaphor in rounded 3D: a modest stack of survey forms at a starting line while an oversized empty speech bubble on little wheels has raced far ahead. No letters, numbers or labels. Clear absurd leap from evidence to conclusion, cream/navy/teal.'),
69:('man','Man torn between fixing a visibly broken office mechanism on one side and performing frantic meaningless paper shuffling on the other; he looks at the real problem with a skeptical raised brow. Strong comic staging, one protagonist only.'),
70:('woman','Reverse meeting perspective from company side: woman looking at an empty team-leader chair while a team waits around the table with unfinished shared project. Sympathetic concern, broad cinematic angle, not hostile employer stereotype.'),
71:('woman','Woman coordinates a real team: calmly connects two conflicting project boards while a new adult teammate follows her explanation. All people focused, deadline clock in background without numbers, active purposeful leadership.'),
72:('man','Man takes a careful first step across a short sturdy training rope bridge with safety rails in an indoor leadership workshop, mentor nearby. Slight uncertainty and determination, literal safe learning challenge, dynamic low angle.'),
73:('woman','Woman at conference table deliberately places the final decision tile into a branching wooden project model while coworkers watch. Clear leadership judgment, close hands plus composed face, serious but positive.'),
75:('man','Man and company representative physically rearrange oversized office blocks to clear the path to a vacant manager desk. Collaborative job redesign, wide eye-level composition, before-obstacle remnants beside them, hopeful action.'),
77:('woman','Overhead negotiation table: woman and man each slide practical condition cards toward center, forming one shared plan instead of pulling apart. Show hands, teal sleeve and cream sleeve, blank cards with tiny abstract icons, no text.'),
79:('man','Inviting managerial workspace with organized support tools, a clear task tray, comfortable chair and nearby teammate help station; man surveys it with renewed interest. Warm office doorway shot, attractive because practical rather than luxurious.'),
83:('woman','Woman finishes an intricate creative prototype with satisfaction while a small peer group admires craftsmanship. Specialist growth and project completion, medium shot with prototype prominent, no manager title or trophy.'),
84:('man','Editorial office fork: man holds a favorite precision tool while looking toward a staircase topped with a coin stack and manager chair; his hands-on workstation lies along the other path. Visibly constrained choice, wide symbolic composition.'),
86:('woman','Small three-person studio: woman alternates between creative workstation and planning board while colleagues handle multiple tasks in shared compact space. Honest small-company reality, warm wide-angle, organized not magical.'),
87:('man','Man receives a transparent layered roadmap model from a company representative, next steps physically visible as small platforms rather than disappearing into fog. Tactile office model, hopeful investigative close-up.'),
88:('both','Same man coaches two coworkers at one side of a shared workspace while same woman develops a detailed prototype at another, both equally lit and valued. One unified space, complementary growth, wide harmonious composition.'),
95:('woman','Woman pins a blank pending-decision card to a specific cell of a clean calendar board while a colleague records follow-up. Concrete managing uncertainty, close-up hand and thoughtful face, no invented dates or text.'),
96:('man','Man lays down two monthly calendar cards and an old project folder during a constructive manager discussion; relaxed assertive expression, clear transition-period proposal. Desk-level wide close-up, no readable dates.'),
97:('woman','Woman asks a precise question across a conference table; attentive company representative opens a planning folder and leans forward to work through it. Open body language, human response in focus, over-shoulder camera.'),
98:('none','Two equally elegant cream promotion folders side by side on dark teal table, same small gold badge on each, one contains tangled task ribbons while the other contains organized handover folders and a small support tool. Hypothetical comparison in one physical scene, no text.'),
102:('woman','Woman demonstrates two miniature office models on a tabletop, clearly illustrating hypothetical job designs rather than a laboratory study. Friendly explanatory expression, model scale obvious, no statistics or charts.'),
103:('woman','Woman politely slides a promotion folder back across a desk, calm confident smile, personal professional sketchbook kept at her side. Respectful adult choice without defeat, intimate human two-shot.'),
104:('man','Man accepts a challenging promotion folder with thoughtful determined smile and begins sketching a practical plan on blank paper. Active agency, sunlit office, medium close-up, no easy guaranteed success imagery.'),
106:('both','Man and woman redesign a small office floorplan model together, moving task blocks and support stations instead of judging people. Bird-eye oblique shot with faces visible, hands clearly grounded, practical hopeful teamwork.'),
107:('man','Return to opening character later that evening: man on commuter train examines phone with ONLY back visible to camera, promotion envelope beside him, city light reflections. Thoughtful quiet close-up, new setting and composition, not studio reference.'),
108:('man','Man at home lays out a work calendar beside family dinner plans and personal hobby notebook, weighing next daily life. Warm overhead shoulder view, clock and closed laptop, decision-focused not exhausted.'),
109:('woman','Woman sorts four visually different blank question cards into separate trays on a research desk, avoiding muddled conclusions. Overhead tactile composition with teal sleeve, modest survey folder, no invented numerical data.'),
111:('both','Man and woman in a final constructive promotion meeting point to one unfinished blank row of a shared checklist, curious cooperative expressions. Close two-shot, clear unanswered condition, soft window light.'),
112:('man','A genuinely celebratory new managerial desk: man receives congratulations while a named-free handover folder and supportive teammate are present, relaxed authentic smile unlike opening. Wide office view, tasteful few confetti, warm rewarding conclusion.'),
114:('both','Closing cinematic scene: man and woman walk out of office into warm evening light together, still in consistent outfits, talking with curiosity about next steps. Wide hopeful city sidewalk, enough quiet foreground for concluding captions, no waving at camera or slogan.')
}
visual=json.loads((parent/'visual-plan.json').read_text(encoding='utf-8'))
masters={'man':'adult-man-01','woman':'adult-woman-01-v3'}
common=('Use case: illustration-story. One NEW cinematic 16:9 wide film still for a Korean social-issue explainer. '
 'Original warm high-quality rounded 3D animated universe, cream/navy/teal/mustard palette, dimensional fabrics, expressive acting and cinematic lighting. '
 'Input images are IDENTITY and STYLE references ONLY: preserve faces, body proportions, hairstyles, glasses and office outfits; '
 'create the specified NEW scene, pose, camera and environment. Never reproduce a studio reference portrait. '
 'Adult man: stocky, rectangular glasses, cream rolled-sleeve shirt, mustard tie, navy trousers. '
 'Adult woman: slim mature adult, no glasses, chestnut bob, teal blazer, cream blouse, navy knee-length skirt, mustard low heels. '
 'No captions, readable words, letters, statistics, watermarks, brands or logos. No collage. '
 'Keep important faces/props away from bottom 15% and upper-left logo safety area. All physical objects and hands coherent. Scene: ')
jobs=[]
for v in visual:
    if 'illustration' not in v['kind']:continue
    role,description=scenes[v['index']]
    ids=[masters['man'],masters['woman']] if role in ('both','none') else [masters[role]]
    jobs.append(dict(index=v['index'],scene=v['scene'],paragraph=v['paragraph'],headline=v['headline'],narration=v['text'],
                     reference_ids=ids,prompt=common+description,file=f"images/{v['index']:03}.png",status='pending'))
assert len(jobs)==65
(root/'image-jobs.json').write_text(json.dumps(jobs,ensure_ascii=False,indent=2),encoding='utf-8')
(root/'revision.json').write_text(json.dumps(dict(video_version=2,parent='promotion-film-v1',script_version=5,
    scope='New scene-specific ImageGen illustrations; thinner Pretendard captions; display numbers separate from spoken text',
    audio='unchanged v1 mix retained with original provenance; no new TTS requested or generated',
    parent_sha256=hashlib.sha256((parent/'final.mp4').read_bytes()).hexdigest(),
    feedback='2026-10-11: references are generation inputs, not final film scenes; remove thick captions and spelled-out numerical subtitles'),ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'images':len(jobs),'root':str(root)}))
