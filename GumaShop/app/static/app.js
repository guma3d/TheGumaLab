"use strict";
const $ = (q, el = document) => el.querySelector(q);
const $$ = (q, el = document) => [...el.querySelectorAll(q)];
const e = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const money = (n) => "₩" + Number(n || 0).toLocaleString("ko-KR");
const date = (v) =>
  v
    ? new Date(v).toLocaleString("ko-KR", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        timeZone: "Asia/Seoul",
      })
    : "아직 없음";
const labels = {
  dashboard: "스튜디오 홈",
  projects: "영상 프로젝트",
  characters: "우리 가족",
  assets: "이미지·영상 자산",
  products: "상품 보관함",
  costs: "제작비 관리",
  legacy: "VideoFactory 아카이브",
};
const cats = { food: "푸드", living: "리빙", tech: "테크", beauty: "뷰티" };
const paths = {
  grid: "M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z",
  film: "M4 3h16v18H4z M4 8h16 M4 16h16 M8 3v18 M16 3v18",
  family:
    "M9 9a3 3 0 1 0 0-6 3 3 0 0 0 0 6 M3 21v-4a6 6 0 0 1 12 0v4 M16 4a3 3 0 0 1 0 6 M18 14a5 5 0 0 1 3 5v2",
  image: "M3 3h18v18H3z M3 16l6-6 5 5 3-3 4 4 M15 7h.01",
  bag: "M4 7h16l1 14H3z M8 8V6a4 4 0 0 1 8 0v2",
  chart: "M4 3v18h17 M8 17v-6 M13 17V6 M18 17v-9",
  layers: "m12 3 10 5-10 5L2 8z M2 12l10 5 10-5 M2 16l10 5 10-5",
  arrow: "M4 12h16 M14 6l6 6-6 6",
  refresh: "M20 7a9 9 0 1 0 1 8 M20 2v6h-6",
  plus: "M12 5v14 M5 12h14",
  check: "m5 12 4 4L19 6",
  clock: "M12 8v5l3 2 M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0",
  upload: "M12 16V3 M7 8l5-5 5 5 M4 16v5h16v-5",
  download: "M12 3v13 M7 11l5 5 5-5 M4 17v4h16v-4",
  edit: "m14 5 5 5 M4 16 16 4a3 3 0 0 1 4 4L8 20H4z",
  folder: "M3 6h7l2 3h9v12H3z",
  star: "m12 3 3 6 7 1-5 5 1 7-6-3-6 3 1-7-5-5 7-1z",
};
const icon = (name) =>
  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${paths[name] || paths.grid}"/></svg>`;
const button = (text, act, id = "", cls = "", ic = "") =>
  `<button type="button" class="btn ${cls}" data-act="${act}" data-id="${e(id)}">${ic ? icon(ic) : ""}${e(text)}</button>`;
const catBadge = (c) =>
  `<span class="category ${e(c)}">${e(cats[c] || c)}</span>`;
const badge = (label, status = "") =>
  `<span class="badge ${e(status)}">${e(label)}</span>`;
const live = (list) => list.filter((x) => !x.archived);
let state,
  filter = "all",
  query = "",
  routeKey = "",
  dirty = false,
  lastHash = location.hash,
  renderSequence = 0;
const find = (kind, id) => state[kind].find((x) => x.id === id);
const projectCosts = (id) =>
  state.costs.filter((c) => c.project_id === id && !c.voided);
const totalCost = (id) => projectCosts(id).reduce((s, c) => s + c.amount, 0);
const videoList = (id) => state.videos.filter((v) => v.project_id === id);
const assetURL = (id) => `api/assets/${encodeURIComponent(id)}/file`;
function status(p) {
  if (p.archived) return ["보관됨", "archived"];
  const videos = videoList(p.id).filter(
    (v) => v.storyboard_revision === p.revision,
  );
  if (videos.some((v) => v.status === "approved"))
    return ["검수 완료", "approved"];
  if (videos.some((v) => v.status === "review")) return ["검수 대기", "review"];
  if (videos.some((v) => v.status === "changes"))
    return ["수정 필요", "changes"];
  return p.approved_at
    ? ["제작 준비", "production"]
    : [p.cuts.length ? "콘티 작성" : "아이디어", "draft"];
}
function animal(id) {
  const character = state?.characters.find((c) => c.id === id);
  if (character?.reference_id)
    return `<img class="animal profile-illustration" src="${assetURL(character.reference_id)}" alt="${e(character.name)} 일러스트" loading="lazy">`;
  const colors = {
    tiger: ["#efb96e", "#ca8e53", "#597660"],
    rabbit: ["#f8f4e9", "#dfd9c9", "#a5b694"],
    pig: ["#efb8af", "#d4948d", "#9baaba"],
    cat: ["#c8becf", "#aaa0b3", "#ddd0a8"],
  };
  const [fur, edge, shirt] = colors[id] || colors.cat;
  const ears =
    id === "rabbit"
      ? `<ellipse cx="40" cy="30" rx="10" ry="27" fill="${fur}"/><ellipse cx="70" cy="30" rx="10" ry="27" fill="${fur}"/><ellipse cx="40" cy="29" rx="4" ry="18" fill="#ead6cb"/><ellipse cx="70" cy="29" rx="4" ry="18" fill="#ead6cb"/>`
      : id === "cat"
        ? `<path d="M20 52 20 17 46 33M66 33 92 17 90 54" fill="${fur}"/><path d="m25 25 2 23 13-13m43-10-2 23-13-13" fill="#dfbac2"/>`
        : id === "pig"
          ? `<path d="M25 48Q4 20 28 25L45 38M67 37l20-13q21-4-2 27" fill="${fur}"/>`
          : `<circle cx="24" cy="39" r="14" fill="${fur}"/><circle cx="86" cy="39" r="14" fill="${fur}"/><circle cx="24" cy="39" r="7" fill="${edge}"/><circle cx="86" cy="39" r="7" fill="${edge}"/>`;
  return `<svg class="animal" viewBox="0 0 110 135" role="img" aria-label="${e({ tiger: "호랑이", rabbit: "토끼", pig: "돼지", cat: "고양이" }[id])} 임시 일러스트"><ellipse cx="55" cy="128" rx="34" ry="4" fill="#687b5f12"/><path d="M19 127v-14q0-30 36-30t36 30v14" fill="${shirt}"/><path d="m43 91 12 13 12-13" fill="#ffffffb0"/>${ears}<ellipse cx="55" cy="63" rx="38" ry="35" fill="${fur}"/>${id === "tiger" ? '<path d="m42 30 8 17 5-17m7 0 2 17 8-14M18 58l14 5-14 5m73-10-14 5 14 5" fill="#b37c46"/>' : ""}<ellipse cx="55" cy="76" rx="23" ry="16" fill="${id === "pig" ? "#e6a39d" : "#faf3e5"}"/><ellipse cx="40" cy="62" rx="3" ry="3.8" fill="#4b4b40"/><ellipse cx="70" cy="62" rx="3" ry="3.8" fill="#4b4b40"/>${id === "pig" ? '<ellipse cx="55" cy="74" rx="13" ry="9" fill="#d59491"/><circle cx="50" cy="74" r="2" fill="#a67571"/><circle cx="60" cy="74" r="2" fill="#a67571"/>' : '<path d="m51 72 4 5 4-5" fill="#a98078"/>'}<path d="M48 82q7 6 14 0" stroke="#a27f6a" stroke-width="1.4" fill="none" stroke-linecap="round"/><ellipse cx="30" cy="73" rx="6" ry="3" fill="#d990822f"/><ellipse cx="80" cy="73" rx="6" ry="3" fill="#d990822f"/>${id === "tiger" ? '<g fill="none" stroke="#6e745b" stroke-width="1.8"><circle cx="39" cy="62" r="10"/><circle cx="71" cy="62" r="10"/><path d="M49 62h12M29 62H18M81 62h11"/></g>' : id === "cat" ? '<path d="m24 73 13 2m-14 4 14-1m49-5-13 2m14 4-14-1" stroke="#a094a5" fill="none"/>' : ""}<circle cx="55" cy="114" r="2" fill="#ffffffa0"/></svg>`;
}
function heading(title, sub, action = "", eyebrow = "GUMASHOP STUDIO") {
  return `<div class="page-heading"><div><p class="eyebrow">${e(eyebrow)}</p><h1>${e(title)}</h1><p class="subtitle">${e(sub)}</p></div>${action}</div>`;
}
function empty(title, desc, action = "", sym = "folder") {
  return `<div class="empty"><div class="empty-symbol">${icon(sym)}</div><h3>${e(title)}</h3><p>${e(desc)}</p>${action}</div>`;
}
function stats(items) {
  return `<div class="stats">${items.map(([name, val, unit, sym]) => `<div class="stat"><span class="stat-icon">${icon(sym)}</span><div><label>${e(name)}</label><strong>${e(val)}</strong><small>${e(unit)}</small></div></div>`).join("")}</div>`;
}
function familyCard(c, detailed = false) {
  const assets = live(state.assets).filter((a) => a.character_id === c.id);
  return `<article class="character-card"><a class="character-art ${e(c.color)}" href="#characters/${e(c.id)}">${catBadge(c.categories[0])}${c.reference_id ? `<img src="${assetURL(c.reference_id)}" alt="${e(c.name)} 기준 이미지">` : animal(c.id)}</a><div class="character-info"><h3><a href="#characters/${e(c.id)}">${e(c.name)}</a></h3><p>${e(c.role)}</p>${detailed ? `<p>${e(c.personality)}</p><p class="tiny">${e(c.room)} · 목소리 ${e(c.voice)}</p>${button("캐릭터 설정", "character", c.id, "small", "edit")}` : ""}<div class="row wrap family-assets"><a class="btn small" href="#assets/${e(c.id)}/image">일러스트 ${assets.filter((a) => a.kind === "image").length}</a><a class="btn small" href="#assets/${e(c.id)}/video">영상 ${assets.filter((a) => a.kind === "video").length}</a></div></div></article>`;
}
function projectCard(p) {
  const [label, st] = status(p);
  return `<a class="project-card" href="#project/${e(p.id)}"><div class="row between">${catBadge(p.category)}${badge(label, st)}</div><h3>${e(p.title)}</h3><p>${e(p.concept.slice(0, 85) || "가족의 새로운 이야기를 시작해보세요.")}</p><div class="row tiny muted"><span>${p.cuts.length}컷 · ${p.cuts.reduce((s, c) => s + c.seconds, 0)}초</span><span>콘티 v${storyboardVersions(p.id)[0]?.number || 1}</span></div><div class="project-bottom"><div class="mini-family">${p.character_ids.map(animal).join("")}</div><span class="tiny muted">${money(totalCost(p.id))} ${p.budget ? "/ " + money(p.budget) : ""}</span></div></a>`;
}
function dashboard() {
  const projects = live(state.projects),
    assets = live(state.assets),
    active = projects.filter((p) => status(p)[1] !== "approved");
  return (
    heading(
      "오늘도, 우리 가족답게.",
      "작은 아이디어를 우리 가족만의 이야기로 만들어보세요.",
      '<a class="btn primary" href="#assets">이미지·영상 확인</a>',
      "YOUR FAMILY, YOUR STORY",
    ) +
    `<section class="hero"><div class="hero-copy"><p class="eyebrow">MEET THE GUMA FAMILY</p><h2>작은 가족의 이야기,<br>갖고 싶은 일상이 되다.</h2><p>네 가지 개성, 하나의 세계.<br>우리 가족이 발견한 좋은 것들을 전해요.</p><a href="#characters" class="text-link">우리 가족 만나기 ${icon("arrow")}</a></div><div class="hero-art">${["tiger", "rabbit", "pig", "cat"].map(animal).join("")}<span class="art-caption">우리 가족 캐릭터 일러스트</span></div></section>` +
    `<section class="asset-shortcuts" aria-label="생성 자산 바로가기"><a href="#assets/all/image">${icon("image")}<strong>생성 일러스트</strong><span>${assets.filter((a) => a.kind === "image").length}장 보기 →</span></a><a href="#assets/all/video">${icon("film")}<strong>샘플 영상</strong><span>${assets.filter((a) => a.kind === "video").length}편 재생 →</span></a></section>` +
    stats([
      ["진행 중인 프로젝트", active.length, "개", "film"],
      ["함께하는 가족", state.characters.length, "명", "family"],
      ["쌓여가는 자산", assets.length, "개", "image"],
      [
        "누적 제작비",
        money(
          state.costs
            .filter((c) => !c.voided)
            .reduce((s, c) => s + c.amount, 0),
        ),
        "",
        "chart",
      ],
    ]) +
    `<div class="section-head"><h2>우리 가족 <span>이야기의 주인공을 만나보세요</span></h2><a class="text-link" href="#characters">전체 보기 ${icon("arrow")}</a></div><section class="family-grid">${state.characters.map((c) => familyCard(c)).join("")}</section><div class="dashboard-bottom"><section class="panel"><div class="section-head"><h2>최근 프로젝트</h2><a class="text-link" href="#projects">모두 보기 ${icon("arrow")}</a></div>${
      projects.length
        ? projects
            .slice(0, 4)
            .map(
              (p) =>
                `<a href="#project/${e(p.id)}" class="history-row"><div><h3>${e(p.title)}</h3><p>${e(cats[p.category])} · ${p.cuts.length}컷 · ${date(p.updated_at)}</p></div>${badge(...status(p))}</a>`,
            )
            .join("")
        : empty(
            "첫 번째 이야기를 기다리고 있어요",
            "상품을 고르고, 가족과 함께할 짧은 이야기를 시작해보세요.",
            button("첫 프로젝트 만들기", "new-project", "", "small", "plus"),
            "film",
          )
    }</section><section class="panel"><div class="section-head"><h2>우리 작업실 시작하기</h2>${badge("START HERE")}</div>${[
      [
        state.characters.some((c) => c.reference_id),
        "가족의 모습을 정해요",
        "기준 이미지와 성격을 등록해주세요.",
        "characters",
      ],
      [
        live(state.products).length,
        "소개할 상품을 골라요",
        "제품 특징과 확인한 출처를 모아주세요.",
        "products",
      ],
      [
        projects.length,
        "첫 이야기를 만들어요",
        "컷별 콘티와 자산을 연결해주세요.",
        "projects",
      ],
    ]
      .map(
        ([done, title, desc, target], i) =>
          `<a class="step ${done ? "done" : ""}" href="#${target}"><span class="step-number">${done ? "✓" : i + 1}</span><div><h3>${title}</h3><p>${desc}</p></div></a>`,
      )
      .join("")}</section></div>`
  );
}
function toolbar(withArchive = true) {
  return `<div class="toolbar"><div class="tabs" role="group" aria-label="카테고리 필터">${[["all", "전체"], ...Object.entries(cats), ...(withArchive ? [["archive", "보관됨"]] : [])].map(([id, label]) => `<button class="tab ${filter === id ? "active" : ""}" data-act="filter" data-id="${id}">${label}</button>`).join("")}</div><input id="search" class="search" type="search" aria-label="이름 검색" placeholder="이름으로 찾아보기" value="${e(query)}"></div>`;
}
function filtered(list) {
  return list.filter(
    (x) =>
      (filter === "archive"
        ? x.archived
        : !x.archived && (filter === "all" || x.category === filter)) &&
      x.title.toLowerCase().includes(query.toLowerCase()),
  );
}
function projectsPage() {
  const list = filtered(state.projects);
  return (
    heading(
      "영상 프로젝트",
      "아이디어에서 콘티, 제작과 검수까지 한 곳에서.",
      button("새 프로젝트", "new-project", "", "primary", "plus"),
    ) +
    toolbar() +
    `<div id="results" class="project-grid">${list.map(projectCard).join("")}</div>` +
    (!list.length
      ? empty(
          "아직 프로젝트가 없어요",
          "상품과 출연 가족을 정해 첫 번째 콘티를 만들어보세요.",
          button("프로젝트 만들기", "new-project", "", "small", "plus"),
          "film",
        )
      : "")
  );
}
function productsPage() {
  const list = filtered(state.products);
  return (
    heading(
      "상품 보관함",
      "가족이 소개할 상품의 특징과 출처를 차곡차곡.",
      button("상품 등록", "product", "", "primary", "plus"),
    ) +
    toolbar() +
    `<div class="product-grid">${list.map((p) => `<article class="product-card"><div class="row between">${catBadge(p.category)}${p.archived ? badge("보관됨") : ""}</div><h3>${e(p.title)}</h3><p>${e(p.features.slice(0, 150) || "확인한 상품 특징을 추가해주세요.")}</p>${p.url ? `<a class="source" href="${e(p.url)}" target="_blank" rel="noopener noreferrer">상품 페이지 열기 ↗</a>` : ""}<div class="row wrap">${button("정보 수정", "product", p.id, "small", "edit")}${!p.archived ? button("영상 기획", "new-project", p.id, "small", "film") : ""}${button(p.archived ? "복원" : "보관", "archive-product", p.id, "small")}</div></article>`).join("")}</div>` +
    (!list.length
      ? empty(
          "마음에 드는 상품을 모아보세요",
          "직접 등록하거나 VideoFactory의 상품 정보를 가져올 수 있어요.",
          button("상품 등록", "product", "", "small", "plus"),
          "bag",
        )
      : "")
  );
}
function charactersPage() {
  return (
    heading("우리 가족", "각자의 개성과 취향이 모여, 하나의 세계를 만들어요.") +
    `<div class="notice">프로필은 생성된 가족 일러스트를 사용해요. 각 가족의 일러스트와 샘플 영상은 아래 버튼에서 확인할 수 있어요.</div><div class="character-detail-grid">${state.characters.map((c) => familyCard(c, true)).join("")}</div>`
  );
}
function assetsPage() {
  const [, selected = "all", media = "all"] = location.hash.slice(1).split("/");
  const characterFilter = ["all", "archive", ...state.characters.map((c) => c.id)].includes(selected) ? selected : "all";
  const mediaFilter = ["image", "video"].includes(media) ? media : "all";
  let list = state.assets
    .filter((a) =>
      characterFilter === "archive"
        ? a.archived
        : !a.archived && (characterFilter === "all" || a.character_id === characterFilter),
    )
    .filter((a) => mediaFilter === "all" || a.kind === mediaFilter)
    .filter((a) => a.title.toLowerCase().includes(query.toLowerCase()));
  return (
    heading(
      "이미지·영상 자산",
      `생성된 일러스트와 샘플 영상을 확인하고 내려받으세요. 현재 ${list.length}개`,
      button("자산 올리기", "asset", "", "primary", "upload"),
    ) +
    (state.asset_audit ? `<div class="notice"><strong>최근 제작 점검 · ${e(state.asset_audit.checked_on)}</strong><p>${e(state.asset_audit.summary)}</p>${state.asset_audit.missing?.length ? `<p>미완료: ${state.asset_audit.missing.map(e).join(", ")}</p>` : ""}<p>${e(state.asset_audit.review_note)}</p></div>` : "") +
    `<div class="toolbar"><div class="tabs" aria-label="가족 필터">${[["all", "전체"], ...state.characters.map((c) => [c.id, c.name]), ["archive", "보관됨"]].map(([id, label]) => `<a class="tab ${characterFilter === id ? "active" : ""}" href="#assets/${id}/${mediaFilter}" ${characterFilter === id ? 'aria-current="true"' : ""}>${e(label)}</a>`).join("")}</div><input id="search" class="search" type="search" aria-label="자산 검색" placeholder="자산 이름 검색" value="${e(query)}"></div><div class="tabs media-tabs" aria-label="자산 종류">${[["all", "전체 자산"], ["image", "일러스트"], ["video", "영상"]].map(([id,label]) => `<a class="tab ${mediaFilter === id ? "active" : ""}" href="#assets/${characterFilter}/${id}" ${mediaFilter === id ? 'aria-current="true"' : ""}>${label}</a>`).join("")}</div><div class="asset-grid">${list.map((a) => `<article class="asset-card"><div class="asset-preview">${a.kind === "image" ? `<a class="asset-open" href="#asset/${encodeURIComponent(a.id)}" aria-label="${e(a.title)} 크게 보기"><img src="${assetURL(a.id)}" alt="${e(a.title)}" loading="lazy"></a>` : `<video src="${assetURL(a.id)}" controls playsinline preload="metadata"></video>`}</div><div class="asset-content"><h3><a href="#asset/${encodeURIComponent(a.id)}">${e(a.title)}</a></h3><p>${e(a.character_id ? find("characters", a.character_id)?.name : "공용 자산")} · ${e(a.space || "공간 미지정")}<br>${e(a.action || "행동 미지정")} · ${(a.bytes / 1048576).toFixed(1)}MB</p><div class="row"><a class="btn small" href="${assetURL(a.id)}?download=true">다운로드</a>${button(a.archived ? "복원" : "보관", "archive-asset", a.id, "small")}</div>${a.source ? `<a class="text-link tiny" href="${e(a.source)}" target="_blank" rel="noopener noreferrer">출처 보기 ↗</a>` : ""}</div></article>`).join("")}</div>` +
    (!list.length
      ? empty(
          "가족의 첫 장면을 모아보세요",
          "캐릭터 기준 이미지, 공간, 표정, 행동 영상까지 함께 보관해요.",
          button("첫 자산 올리기", "asset", "", "small", "upload"),
          "image",
        )
      : "")
  );
}
function assetPage(id) {
  const a = find("assets", id);
  if (!a)
    return heading(
      "자산을 찾을 수 없어요",
      "목록에서 다시 선택해주세요.",
      '<a class="btn" href="#assets">자산 목록</a>',
    );
  const siblings = state.assets.filter(
    (x) => !x.archived && x.character_id === a.character_id,
  );
  const index = siblings.findIndex((x) => x.id === id);
  const neighbor = (offset, label) => {
    const next = siblings[index + offset];
    return index >= 0 && next
      ? `<a class="btn small" href="#asset/${encodeURIComponent(next.id)}">${label}</a>`
      : "";
  };
  return (
    heading(
      a.title,
      `${a.character_id ? find("characters", a.character_id)?.name || "캐릭터" : "공용 자산"} · ${a.space || "공간 미지정"}`,
      '<a class="btn" href="#assets">자산 목록</a>',
    ) +
    `<div class="asset-detail"><div class="asset-stage">${a.kind === "image" ? `<a href="${assetURL(a.id)}" target="_blank" rel="noopener" aria-label="원본 이미지 새 창에서 보기"><img src="${assetURL(a.id)}" alt="${e(a.title)}"></a>` : `<video src="${assetURL(a.id)}" controls playsinline preload="metadata"></video>`}</div><aside class="panel"><h2>장면 정보</h2><p>${e(a.action || "행동 미지정")}</p>${a.approval_status === "candidate" ? '<p class="notice">검토용 시안이에요. 영상에 사용하기 전에 얼굴·무늬·의상·손을 확인해주세요.</p>' : ""}${a.review_note ? `<p>${e(a.review_note)}</p>` : ""}<p>${(a.bytes / 1048576).toFixed(1)} MB${a.duration ? ` · ${Number(a.duration).toFixed(1)}초` : ""}</p><div class="row wrap"><a class="btn primary" href="${assetURL(a.id)}?download=true">다운로드</a><a class="btn" href="${assetURL(a.id)}" target="_blank" rel="noopener">원본 보기 ↗</a></div><div class="row wrap asset-neighbors">${neighbor(-1, "← 이전")}${neighbor(1, "다음 →")}</div></aside></div>`
  );
}
function costsPage() {
  const list = state.costs,
    active = list.filter((c) => !c.voided),
    spent = active.reduce((s, c) => s + c.amount, 0),
    budget = live(state.projects).reduce((s, p) => s + p.budget, 0);
  return (
    heading(
      "제작비 관리",
      "시도한 횟수와 실제 비용을 기록해, 지속 가능한 제작을.",
      button("비용 기록", "cost", "", "primary", "plus"),
    ) +
    stats([
      ["누적 제작비", money(spent), "", "chart"],
      ["진행 프로젝트 예산", money(budget), "", "bag"],
      [
        "기록한 제작 시도",
        active.reduce((s, c) => s + c.attempts, 0),
        "회",
        "refresh",
      ],
      ["비용 기록", active.length, "건", "layers"],
    ]) +
    `<div class="notice">직접 입력한 원화 비용을 집계해요. AI 서비스의 청구 내역이나 크레딧은 자동으로 조회하지 않아요. 잘못 입력한 기록은 취소 후 다시 등록할 수 있어요.</div><section class="panel"><div class="section-head"><h2>제작비 기록</h2><span class="tiny muted">KRW · 원화 기준</span></div>${list.length ? list.map((c) => costRow(c)).join("") : empty("첫 제작비를 기록해보세요", "프로젝트별 비용과 컷별 시도 횟수를 비교할 수 있어요.")}</section>`
  );
}
function costRow(c) {
  return `<div class="ledger-row ${c.voided ? "voided" : ""}"><div><h3>${e(c.label)} ${c.voided ? "· 취소됨" : ""}</h3><p>${e(find("projects", c.project_id)?.title || "프로젝트")} · ${c.cut ? "CUT " + c.cut : "전체"} · ${c.attempts}회 · ${date(c.created_at)}</p>${c.note ? `<p>${e(c.note)}</p>` : ""}</div><div class="row"><strong>${money(c.amount)}</strong>${button(c.voided ? "복원" : "취소", "void-cost", c.id, "small")}</div></div>`;
}
function cutEditor(c, i) {
  return `<article class="cut-card" data-cut><div class="cut-header"><strong>CUT ${String(i + 1).padStart(2, "0")}</strong><input class="cut-title" name="title" aria-label="${i + 1}컷 제목" maxlength="100" required value="${e(c.title)}"><input class="cut-seconds" type="number" name="seconds" aria-label="${i + 1}컷 길이(초)" min="1" max="60" required value="${c.seconds}"><span class="tiny muted">초</span><button type="button" class="icon-button" data-act="move-cut" data-id="${i}" data-dir="-1" aria-label="${i + 1}컷 위로">↑</button><button type="button" class="icon-button" data-act="move-cut" data-id="${i}" data-dir="1" aria-label="${i + 1}컷 아래로">↓</button><button type="button" class="icon-button" data-act="remove-cut" data-id="${i}" aria-label="${i + 1}컷 삭제">×</button></div><div class="cut-body"><label class="field">화면과 행동<textarea name="visual" maxlength="3000" placeholder="누가, 어디에서, 무엇을 하나요?">${e(c.visual)}</textarea></label><label class="field">대사 · 내레이션<textarea name="narration" maxlength="1500" placeholder="실제 상품 자료에 근거해 적어주세요.">${e(c.narration)}</textarea></label><label class="field">제작 방식<select name="method">${[
    ["ai", "AI 장면 제작"],
    ["real", "실제 상품 자료"],
    ["reuse", "기존 자산 재사용"],
  ]
    .map(
      ([v, t]) =>
        `<option value="${v}" ${c.method === v ? "selected" : ""}>${t}</option>`,
    )
    .join(
      "",
    )}</select></label><label class="field">연결 자산<select name="asset_id"><option value="">자산을 선택해주세요</option>${live(
    state.assets,
  )
    .map(
      (a) =>
        `<option value="${a.id}" ${c.asset_id === a.id ? "selected" : ""}>${e(a.title)}</option>`,
    )
    .join(
      "",
    )}</select></label><label class="field wide">장면 프롬프트<textarea name="prompt" maxlength="5000" placeholder="외형, 조명, 카메라, 동작과 유지할 기준">${e(c.prompt)}</textarea></label></div></article>`;
}
const storyboardVersions = (id) => (state.storyboards || []).filter(v => v.project_id === id).sort((a,b) => b.number-a.number);
function versionPanel(id, selected) {
  const versions = storyboardVersions(id);
  return `<section class="panel version-panel"><div class="row between wrap"><label class="field">콘티 버전<select id="storyboard-version" data-project="${e(id)}"><option value="">현재 콘티</option>${versions.map(v=>`<option value="${e(v.id)}" ${selected?.id===v.id?'selected':''}>v${v.number} · ${e(v.label)}</option>`).join('')}</select></label>${button("현재 콘티를 새 버전으로 등록", "publish-storyboard", id, "small")}</div>${selected?`<p><strong>v${selected.number} · ${e(selected.label)}</strong> · ${date(selected.created_at)}</p><p class="preserve">${e(selected.note)}</p><small>보존된 버전입니다. 수정은 스토리보드 탭의 현재 콘티에서 진행하세요.</small>`:'<p>현재 편집 중인 콘티입니다. 저장된 버전을 선택하면 당시 이미지와 설명을 함께 볼 수 있어요.</p>'}</section>`;
}
function projectPage(id, tab = "board", versionId = "") {
  const current = find("projects", id);
  const versions = storyboardVersions(id);
  const selected = versionId ? versions.find(v => v.id === versionId) : null;
  if (versionId && !selected) return empty("콘티 버전을 찾을 수 없어요", "버전 목록에서 다시 선택해주세요.");
  const p = tab === "images" && selected ? selected.storyboard : current;
  if (!p)
    return empty(
      "프로젝트를 찾을 수 없어요",
      "프로젝트 목록에서 다시 선택해주세요.",
    );
  const product = p.product_id ? find("products", p.product_id) : null,
    [label, st] = status(p),
    spent = totalCost(id);
  const content =
    tab === "images"
      ? versionPanel(id, selected)+`<div class="notice">장면 이미지로 흐름을 확인하는 콘티입니다. 각 이미지를 선택하면 크게 볼 수 있어요.</div><div class="storyboard-image-grid">${p.cuts.map((c,i) => { const asset = c.asset_id ? find("assets",c.asset_id) : null; return `<article class="panel storyboard-image-card"><div class="row between"><strong>CUT ${String(i+1).padStart(2,"0")}</strong><span class="badge">${c.seconds}초</span></div>${asset?.kind === "image" ? `<a href="#asset/${encodeURIComponent(asset.id)}"><img src="${assetURL(asset.id)}" alt="${e(c.title)}" loading="lazy"></a>` : '<p class="muted">장면 이미지 준비 중</p>'}<h2>${e(c.title)}</h2><p class="preserve">${e(c.visual)}</p></article>`; }).join("")}</div>`
      : tab === "versions"
        ? `<section class="panel"><div class="section-head"><h2>콘티 버전 관리</h2>${button("새 버전 등록", "publish-storyboard", id, "small primary")}</div>${versions.map((v,i)=>`<article class="history-row"><div><h3>v${v.number} · ${e(v.label)} ${i===0?'<span class="badge">최신</span>':''}</h3><p>${date(v.created_at)} · ${v.storyboard.cuts.length}컷 · ${v.storyboard.cuts.reduce((s,c)=>s+c.seconds,0)}초</p><p class="preserve">${e(v.note)}</p></div><a class="btn small" href="#project/${e(id)}/images/${e(v.id)}">이미지 콘티 보기</a></article>`).join('')||empty("등록된 버전이 없어요","현재 콘티를 새 버전으로 등록해주세요.")}</section>`
      : tab === "videos"
      ? videosPanel(p)
      : tab === "history"
        ? '<div id="history-list" class="panel loading">콘티 기록을 불러오는 중이에요…</div>'
        : tab === "costs"
          ? `<section class="panel"><div class="section-head"><h2>프로젝트 제작비</h2>${button("비용 기록", "cost", id, "small", "plus")}</div>${
              state.costs
                .filter((c) => c.project_id === id)
                .map(costRow)
                .join("") ||
              empty(
                "아직 제작비가 없어요",
                "유료 제작을 진행했다면 실제 사용한 비용을 기록해주세요.",
              )
            }</section>`
          : `<div class="notice">화면 설명·이미지·기획을 변경해 저장하면 새 콘티 버전으로 보존됩니다. 이전 버전은 버전 관리에서 볼 수 있어요.</div><form id="board-form" data-id="${id}"><section class="panel"><label class="field">새 버전 이름<input name="version_label" maxlength="100" value="콘티 수정" required></label><label class="field">변경 내용<textarea name="version_note" maxlength="2000" placeholder="이전 버전에서 달라진 내용을 기록해주세요."></textarea></label></section><div id="cuts">${p.cuts.map(cutEditor).join("")}</div>${p.cuts.length ? "" : empty("아직 콘티가 없어요", "이야기 틀을 불러오거나 컷을 직접 추가할 수 있어요.")}<div class="row wrap">${button("컷 추가", "add-cut", id, "small", "plus")}${!p.cuts.length ? button("5컷 이야기 틀 불러오기", "template", id, "small", "layers") : ""}</div><div class="form-error" role="alert"></div><div class="sticky-actions"><small id="board-status">${p.approved_at ? "현재 콘티 제작 승인됨" : "저장 후 제작 승인해주세요"}</small><div class="row"><button class="btn primary" type="submit">콘티 저장</button>${button("제작 승인", "approve", id, "", "check")}</div></div></form>`;
  return `<div class="detail-head"><a class="back" href="#projects">${icon("arrow")} 프로젝트 목록</a>${heading(p.title, p.concept || "우리 가족의 새로운 이야기", `<div class="row">${badge(label, st)}${button("설정", "edit-project", id, "", "edit")}<a class="btn" href="api/projects/${id}/export">${icon("download")}기획 내보내기</a></div>`, "PROJECT WORKSPACE")}</div><div class="status-line"><span class="on">01 기획</span><b>→</b><span class="${p.cuts.length ? "on" : ""}">02 콘티</span><b>→</b><span class="${p.approved_at ? "on" : ""}">03 제작</span><b>→</b><span class="${videoList(id).length ? "on" : ""}">04 검수</span><b>→</b><span class="${st === "approved" ? "on" : ""}">05 검수 완료</span></div><div class="tabs">${[
    ["board", "스토리보드"],
    ["images", "이미지 콘티"],
    ["versions", "버전 관리"],
    ["videos", "영상 · 검수"],
    ["costs", "제작비"],
    ["history", "저장 기록"],
  ]
    .map(
      ([k, v]) =>
        `<a class="tab ${k === tab ? "active" : ""}" href="#project/${id}/${k}">${v}</a>`,
    )
    .join(
      "",
    )}</div><div class="detail-columns"><section>${content}</section><aside class="detail-sidebar"><section class="panel"><h3>이번 이야기의 주인공</h3><div class="mini-family">${p.character_ids.map(animal).join("")}</div><p>${p.character_ids.map((k) => e(find("characters", k)?.name)).join(" · ")}</p><hr><h3>소개할 상품</h3><p>${e(product?.title || "아직 연결하지 않았어요")}</p>${product?.url ? `<a class="text-link" href="${e(product.url)}" target="_blank" rel="noopener noreferrer">상품 페이지 ↗</a>` : ""}${product?.features ? `<p class="preserve">${e(product.features)}</p>` : ""}${product?.cautions ? `<p class="preserve">주의 · ${e(product.cautions)}</p>` : ""}</section><section class="panel"><h3>제작 예산</h3><strong class="budget-number">${money(spent)}</strong><p>예산 ${p.budget ? money(p.budget) : "미설정"}</p>${p.budget && spent > p.budget ? '<div class="notice warm">설정한 예산을 초과했어요.</div>' : ""}<p>컷별 시도 한도 ${p.attempt_limit}회</p>${p.cuts
    .map((c, i) => {
      const count = projectCosts(id)
        .filter((v) => v.cut === i + 1)
        .reduce((s, v) => s + v.attempts, 0);
      return count
        ? `<p>CUT ${i + 1} · ${count}회 ${count >= p.attempt_limit ? "— 한도 도달" : ""}</p>`
        : "";
    })
    .join(
      "",
    )}${button("비용 기록", "cost", id, "small", "plus")}</section><section class="panel"><h3>제작 연결 상태</h3><p>AI 영상 생성 · 미연결<br>YouTube 게시 · 미연결</p><p>외부에서 제작한 영상을 등록해 버전별로 검수할 수 있어요.</p></section></aside></div>`;
}
function videosPanel(p) {
  const videos = videoList(p.id),
    chronological = [...videos].reverse();
  const jobs = (state.jobs || []).filter((j) => j.project_id === p.id);
  const jobNotice = jobs.length
    ? `<div class="notice" role="status">${e(jobs[0].message)}</div>`
    : "";
  return `<div class="section-head"><h2>영상 버전 <span>${videos.length}개</span></h2><div class="row wrap">${button("콘티 프리뷰 만들기", "render", p.id, "small", "film")}${button("새 영상 등록", "video", p.id, "small primary", "upload")}</div></div>${jobNotice}<div class="notice">영상 등록에는 현재 콘티의 제작 승인이 필요해요. 검수 완료는 YouTube 업로드나 공개를 의미하지 않아요.</div>${
    videos
      .map(
        (v) =>
          `<article class="panel video-card"><div class="row between"><h3>영상 v${chronological.findIndex((x) => x.id === v.id) + 1}${v.production_status === "partial_generation" ? " · 제작 중 편집본" : v.is_preview ? " · 콘티 프리뷰" : ""}</h3>${badge({ review: "검수 대기", approved: "검수 완료", changes: "수정 필요" }[v.status], v.status)}</div><p class="tiny muted">${v.storyboard_version_number ? "콘티 v" + v.storyboard_version_number : "저장 기록 #" + v.storyboard_revision} · ${date(v.created_at)} ${p.revision !== v.storyboard_revision ? "· 이전 콘티" : ""}</p><video src="api/videos/${v.id}/file" ${v.thumbnail_asset_id ? `poster="${assetURL(v.thumbnail_asset_id)}"` : ""} controls preload="metadata"></video><div class="video-meta"><span class="tiny muted">${Math.round(v.duration)}초 · ${(v.bytes / 1048576).toFixed(1)}MB</span><a class="text-link" href="api/videos/${v.id}/file?download=true">원본 다운로드 ${icon("download")}</a></div>${v.note ? `<p class="tiny preserve">${e(v.note)}</p>` : ""}${v.review ? `<div class="notice">${e(v.review.note || "캐릭터·상품·표현 확인 완료")}<br><span class="tiny">${date(v.review.reviewed_at)}</span></div>` : button("영상 검수", "review", v.id, "small primary", "check")}<h3 class="list-heading">컷별 피드백</h3>${state.feedback
            .filter((f) => f.video_id === v.id)
            .map(
              (f) =>
                `<div class="feedback"><small>${f.cut ? "CUT " + f.cut : "영상 전체"} · ${date(f.created_at)}</small>${e(f.text)}</div>`,
            )
            .join(
              "",
            )}${button("피드백 남기기", "feedback", v.id, "small", "edit")}</article>`,
      )
      .join("") ||
    empty(
      "첫 영상을 등록해주세요",
      "외부 제작 도구에서 완성한 영상을 올리면 콘티와 함께 보존해요.",
      button("영상 등록", "video", p.id, "small", "upload"),
      "film",
    )
  }`;
}
async function api(path, options = {}) {
  const response = await fetch(
    new URL(path.replace(/^\//, ""), document.baseURI),
    {
      ...options,
      headers: {
        "X-GumaShop": "studio",
        ...(options.body instanceof FormData
          ? {}
          : { "Content-Type": "application/json" }),
        ...options.headers,
      },
    },
  );
  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error("서버 응답을 확인할 수 없어요. 잠시 후 다시 시도해주세요.");
  }
  if (!response.ok) {
    const detail = data.detail;
    throw new Error(
      Array.isArray(detail)
        ? detail
            .map((d) => `${d.loc?.slice(-1)[0] || "입력"}: ${d.msg}`)
            .join("\n")
        : detail || "요청에 실패했어요.",
    );
  }
  return data;
}
const send = (path, data, method = "POST") =>
  api(path, { method, body: JSON.stringify(data) });
function toast(message) {
  $("#toast").textContent = message;
  $("#toast").classList.add("show");
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => $("#toast").classList.remove("show"), 4200);
}
function modal(title, html, submit) {
  $("#modal-title").textContent = title;
  $("#modal-content").innerHTML = html;
  const form = $("form", $("#modal-content"));
  if (form)
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!form.reportValidity()) return;
      const button = $("[type=submit]", form);
      button.disabled = true;
      $(".form-error", form).textContent = "";
      try {
        await submit(new FormData(form), form);
        $("#modal").close();
      } catch (err) {
        $(".form-error", form).textContent = err.message;
      } finally {
        button.disabled = false;
      }
    });
  if (!$("#modal").open) $("#modal").showModal();
}
const field = (label, name, value = "", type = "text", extra = "") =>
  `<label class="field">${e(label)}<input name="${name}" type="${type}" value="${e(value)}" ${extra}></label>`;
const area = (label, name, value = "", max = 3000) =>
  `<label class="field">${e(label)}<textarea name="${name}" maxlength="${max}">${e(value)}</textarea></label>`;
const select = (label, name, options, value = "", extra = "") =>
  `<label class="field">${e(label)}<select name="${name}" ${extra}>${options.map(([id, title]) => `<option value="${e(id)}" ${id === value ? "selected" : ""}>${e(title)}</option>`).join("")}</select></label>`;
const actions = (label, hint = "") =>
  `<div class="form-error" role="alert"></div><div class="form-actions"><small class="form-hint">${e(hint)}</small><button class="btn primary" type="submit">${e(label)}</button></div>`;
async function reload(message) {
  state = await api("api/state");
  await render();
  if (message) toast(message);
}
function productModal(id) {
  const p = id ? find("products", id) : { category: "food" };
  modal(
    id ? "상품 정보 수정" : "새 상품 등록",
    `<form>${field("상품 이름", "title", p.title, "text", 'required maxlength="160"')}${select("카테고리", "category", Object.entries(cats), p.category)}${field("상품 링크", "url", p.url, "url", 'maxlength="2000"')}${area("확인한 상품 특징", "features", p.features, 5000)}${area("주의사항 · 확인할 내용", "cautions", p.cautions)}${field("정보 출처 링크", "source", p.source, "url", 'maxlength="2000"')}${actions("저장하기")}</form>`,
    async (fd) => {
      await send(
        "api/products" + (id ? "/" + id : ""),
        {
          ...Object.fromEntries(fd),
          revision: p.revision || null,
          archived: p.archived || false,
        },
        id ? "PUT" : "POST",
      );
      await reload("상품을 저장했어요.");
    },
  );
}
function projectModal(id, productId = "") {
  const p = id
    ? find("projects", id)
    : {
        category: find("products", productId)?.category || "food",
        product_id: productId,
        character_ids: ["rabbit", "pig"],
        budget: 0,
        attempt_limit: 3,
      };
  modal(
    id ? "프로젝트 설정" : "새로운 이야기 시작하기",
    `<form>${field("프로젝트 이름", "title", p.title, "text", 'required maxlength="160" placeholder="예: 쌀쌀한 오후, 엄마와 아들의 간식 시간"')}<div class="form-grid">${select("카테고리", "category", Object.entries(cats), p.category)}${select("소개할 상품", "product_id", [["", "나중에 연결하기"], ...live(state.products).map((p) => [p.id, p.title])], p.product_id)}</div><label class="field">출연 가족</label><div class="row wrap">${state.characters.map((c) => `<label class="check"><input type="checkbox" name="character_ids" value="${c.id}" ${p.character_ids.includes(c.id) ? "checked" : ""}>${e(c.name)}</label>`).join("")}</div>${area("이야기 아이디어", "concept", p.concept, 4000)}<div class="form-grid">${field("제작 예산 (원)", "budget", p.budget, "number", 'required min="0" max="100000000"')}${field("컷별 시도 한도", "attempt_limit", p.attempt_limit, "number", 'required min="1" max="50"')}</div>${
      id
        ? select(
            "보관 상태",
            "archived",
            [
              ["false", "진행 중"],
              ["true", "보관됨"],
            ],
            String(p.archived),
          )
        : ""
    }${actions(id ? "설정 저장" : "프로젝트 만들기", id ? "변경하면 현재 콘티의 제작 승인이 해제돼요." : "유료 AI 생성은 실행되지 않아요.")}</form>`,
    async (fd) => {
      const chars = fd.getAll("character_ids");
      if (!chars.length)
        throw new Error("출연 가족을 한 명 이상 선택해주세요.");
      const payload = {
        title: fd.get("title"),
        category: fd.get("category"),
        product_id: fd.get("product_id"),
        character_ids: chars,
        concept: fd.get("concept"),
        budget: Number(fd.get("budget")),
        attempt_limit: Number(fd.get("attempt_limit")),
        cuts: p.cuts || [],
        archived: fd.get("archived") === "true",
        revision: p.revision || null,
      };
      const result = await send(
        "api/projects" + (id ? "/" + id : ""),
        payload,
        id ? "PUT" : "POST",
      );
      await reload("프로젝트를 저장했어요.");
      location.hash = "project/" + result.id;
    },
  );
}
function characterModal(id) {
  const c = find("characters", id);
  modal(
    "캐릭터 설정",
    `<div class="modal-art">${animal(id)}<div><h3>${e(c.name)}</h3><p>${e(c.species)} · ${c.categories.map((k) => cats[k]).join(" · ")}</p><p>이 설정을 제작할 때의 기준으로 사용해요.</p></div></div><form><div class="form-grid">${field("이름", "name", c.name, "text", 'required maxlength="80"')}${field("역할", "role", c.role, "text", 'required maxlength="160"')}</div>${area("성격과 말투", "personality", c.personality)}${area("외형 · 의상 · 손발 기준", "appearance", c.appearance)}<div class="form-grid">${field("주로 머무는 공간", "room", c.room, "text", 'maxlength="120"')}${field("목소리 설정", "voice", c.voice, "text", 'maxlength="300"')}</div>${select(
      "캐릭터 기준 이미지",
      "reference_id",
      [
        ["", "미등록"],
        ...live(state.assets)
          .filter((a) => a.kind === "image")
          .map((a) => [a.id, a.title]),
      ],
      c.reference_id,
    )}${area("제작할 때 지킬 기준", "rules", c.rules)}${actions("캐릭터 저장", "기준 이미지는 자산 라이브러리에 먼저 올려주세요.")}</form>`,
    async (fd) => {
      await send(
        "api/characters/" + id,
        { ...Object.fromEntries(fd), revision: c.revision },
        "PUT",
      );
      await reload("가족 설정을 저장했어요.");
    },
  );
}
function assetModal() {
  modal(
    "자산 라이브러리에 올리기",
    `<form>${field("자산 이름", "title", "", "text", 'required maxlength="160" placeholder="예: 토끼 엄마 · 주방에서 빵 굽기"')}<div class="form-grid">${select("캐릭터", "character_id", [["", "가족 공용"], ...state.characters.map((c) => [c.id, c.name])])}${field("공간", "space", "", "text", 'maxlength="2000" placeholder="예: 주방"')}</div>${field("행동 · 표정", "action", "", "text", 'maxlength="2000" placeholder="예: 빵 굽기, 만족"')}${field("출처 링크 (선택)", "source", "", "url", 'maxlength="2000"')}${field("이미지 또는 영상", "file", "", "file", 'required accept="image/png,image/jpeg,image/webp,video/mp4,video/webm,video/quicktime"')}${actions("업로드", "PNG · JPG · WebP · MP4 · WebM · MOV, 최대 150MB")}</form>`,
    async (fd) => {
      await api("api/assets", { method: "POST", body: fd });
      await reload("자산을 보관했어요.");
    },
  );
}
function costModal(id = "") {
  if (!state.projects.length) {
    toast("프로젝트를 먼저 만들어주세요.");
    return;
  }
  modal(
    "제작비 기록",
    `<form>${select(
      "프로젝트",
      "project_id",
      state.projects.map((p) => [p.id, p.title]),
      id || state.projects[0].id,
    )}${field("사용 내역", "label", "", "text", 'required maxlength="160" placeholder="예: 주방 도입 컷 영상 생성"')}<div class="form-grid">${field("실제 사용 비용 (원)", "amount", 0, "number", 'required min="0" max="100000000"')}${field("제작 시도 횟수", "attempts", 1, "number", 'required min="1" max="1000"')}${field("컷 번호 (전체 비용은 0)", "cut", 0, "number", 'required min="0" max="20"')}</div>${area("메모", "note", "", 2000)}${actions("기록하기", "비용은 입력한 금액 그대로 집계되며 횟수를 곱하지 않아요.")}</form>`,
    async (fd) => {
      const data = Object.fromEntries(fd);
      for (const k of ["amount", "attempts", "cut"]) data[k] = Number(data[k]);
      await send("api/costs", data);
      await reload("제작비를 기록했어요.");
    },
  );
}
function videoModal(id) {
  const p = find("projects", id);
  if (!p.approved_at || p.archived) {
    toast("현재 콘티를 먼저 제작 승인해주세요.");
    return;
  }
  modal(
    "새 영상 버전 등록",
    `<div class="notice">${e(p.title)} · 저장 기록 #${p.revision}에 연결돼요.<br>기존 영상은 보존하고 새 버전으로 등록해요.</div><form>${field("영상 파일", "file", "", "file", 'required accept="video/mp4,video/webm,video/quicktime"')}${area("버전 메모", "note", "", 4000)}${actions("영상 등록", "최대 150MB · 브라우저 재생은 MP4(H.264/AAC)를 권장해요.")}</form>`,
    async (fd) => {
      fd.set("revision", p.revision);
      await api("api/projects/" + id + "/videos", { method: "POST", body: fd });
      await reload("새 영상 버전을 등록했어요.");
    },
  );
}
function reviewModal(id) {
  const v = find("videos", id);
  modal(
    "영상 검수",
    `<form><p class="subtitle">영상을 확인하고 항목별로 체크해주세요.</p>${[
      ["character_ok", "캐릭터 외형과 공간이 기준에 맞아요"],
      ["product_ok", "제품 형태·포장·사용 장면이 정확해요"],
      ["claims_ok", "대사와 표현이 실제 자료에 근거해요"],
    ]
      .map(
        ([k, t]) =>
          `<label class="check"><input type="checkbox" name="${k}">${t}</label>`,
      )
      .join("")}${select("검수 결과", "decision", [
      ["approved", "검수 완료"],
      ["changes", "수정 필요"],
    ])}${area("검수 메모", "note", "", 4000)}${actions("검수 기록", "검수 완료 후에도 자동으로 게시되지 않아요.")}</form>`,
    async (fd) => {
      await send("api/videos/" + id + "/review", {
        revision: v.revision,
        decision: fd.get("decision"),
        note: fd.get("note"),
        ...Object.fromEntries(
          ["character_ok", "product_ok", "claims_ok"].map((k) => [
            k,
            fd.has(k),
          ]),
        ),
      });
      await reload("검수 결과를 기록했어요.");
    },
  );
}
function feedbackModal(id) {
  const v = find("videos", id);
  modal(
    "컷별 피드백",
    `<form>${select("피드백할 장면", "cut", [["0", "영상 전체"], ...v.storyboard.cuts.map((c, i) => [String(i + 1), `CUT ${i + 1} · ${c.title}`])])}<label class="field">수정할 내용<textarea name="text" required maxlength="4000" placeholder="어떤 부분을 어떻게 바꾸면 좋을까요?"></textarea></label>${actions("피드백 남기기")}</form>`,
    async (fd) => {
      await send("api/videos/" + id + "/feedback", {
        cut: Number(fd.get("cut")),
        text: fd.get("text"),
      });
      await reload("피드백을 남겼어요.");
    },
  );
}
function readCuts() {
  return $$("[data-cut]").map((el) => ({
    title: $("[name=title]", el).value,
    seconds: Number($("[name=seconds]", el).value),
    visual: $("[name=visual]", el).value,
    narration: $("[name=narration]", el).value,
    prompt: $("[name=prompt]", el).value,
    method: $("[name=method]", el).value,
    asset_id: $("[name=asset_id]", el).value,
  }));
}
function updateCuts(cuts) {
  $("#cuts").innerHTML = cuts.map(cutEditor).join("");
  const emptyEl = $("#board-form>.empty");
  if (emptyEl) emptyEl.remove();
  markDirty();
}
function markDirty() {
  dirty = true;
  const status = $("#board-status");
  if (status) status.textContent = "저장하지 않은 변경사항이 있어요";
}
const projectPayload = (p) =>
  Object.fromEntries(
    [
      "title",
      "category",
      "product_id",
      "character_ids",
      "concept",
      "budget",
      "attempt_limit",
      "cuts",
      "archived",
      "revision",
    ].map((k) => [k, p[k]]),
  );
async function render() {
  const sequence = ++renderSequence;
  const [page = "dashboard", id, tab, versionId] = location.hash.slice(1).split("/");
  const key =
    page === "project" ? "projects" : page === "asset" ? "assets" : page;
  if (routeKey !== key) {
    filter = "all";
    query = "";
    routeKey = key;
  }
  $("#breadcrumb").textContent = labels[key] || labels.dashboard;
  $$("[data-nav]").forEach((el) =>
    el.classList.toggle("active", el.dataset.nav === key),
  );
  $("#project-count").textContent = live(state.projects).length;
  const views = {
    dashboard,
    projects: projectsPage,
    characters: charactersPage,
    products: productsPage,
    assets: assetsPage,
    costs: costsPage,
  };
  if (page === "legacy") {
    $("#main").innerHTML =
      heading(
        "VideoFactory 아카이브",
        "기존 작업실의 상품을 이어받아, 가족의 새 이야기로.",
        `<a class="btn" href="https://videofactory.guma3d.com/" target="_blank" rel="noopener">기존 작업실 ↗</a>`,
      ) +
      `<div class="notice">원본은 읽기 전용으로 연결돼요. 상품 정보를 가져오면 GumaShop에서 독립적으로 편집할 수 있어요. 기존 영상과 승인 기록은 원래 작업실에서 확인해주세요.</div><div id="legacy-list" class="loading">기존 제작물을 불러오는 중이에요…</div>`;
    try {
      const data = await api("api/legacy");
      if (sequence !== renderSequence) return;
      $("#legacy-list").className = "product-grid";
      $("#legacy-list").innerHTML =
        data.items
          .map(
            (p) =>
              `<article class="product-card">${catBadge(p.category)}<h3>${e(p.title)}</h3><p>기존 영상 버전 ${p.videos}개</p><div class="row wrap">${button(state.products.some((x) => x.legacy_id === p.id) ? "가져온 상품 열기" : "상품 정보 가져오기", "import", p.id, "small primary", "download")}<a class="btn small" href="${e(p.source_url)}" target="_blank" rel="noopener noreferrer">원본 보기 ↗</a></div></article>`,
          )
          .join("") ||
        empty(
          data.available
            ? "가져올 항목이 없어요"
            : "아카이브가 연결되지 않았어요",
          "기존 제작물이 있으면 이곳에 표시돼요.",
        );
    } catch (err) {
      if (sequence === renderSequence)
        $("#legacy-list").innerHTML =
          `<div class="error">${e(err.message)}</div>`;
    }
  } else {
    $("#main").innerHTML =
      page === "project"
        ? projectPage(id, tab, versionId)
        : page === "asset"
          ? assetPage(id)
          : (views[page] || dashboard)();
    if (page === "characters" && id && find("characters", id))
      characterModal(id);
    if (page === "project" && tab === "history" && $("#history-list")) {
      try {
        const items = await api("api/projects/" + id + "/history");
        if (sequence !== renderSequence) return;
        $("#history-list").className = "panel";
        $("#history-list").innerHTML =
          "<h2>보존된 콘티 기록</h2>" +
          items
            .map(
              (p) =>
                `<div class="history-row"><div><h3>저장 기록 #${p.revision} · ${e(p.title)}</h3><p>${date(p.updated_at)} · ${p.cuts.length}컷 · ${p.approved_at ? "제작 승인됨" : "작성 중"}</p></div>${button("기록 보기", "history", p.id + ":" + p.revision, "small")}</div>`,
            )
            .join("");
      } catch (err) {
        if (sequence === renderSequence)
          $("#history-list").innerHTML = e(err.message);
      }
    }
  }
  const board = $("#board-form");
  const versionSelect = $("#storyboard-version");
  if (versionSelect) versionSelect.addEventListener("change",()=>{
    location.hash = `project/${versionSelect.dataset.project}/images${versionSelect.value?'/'+versionSelect.value:''}`;
  });
  if (board) {
    board.addEventListener("input", markDirty);
    board.addEventListener("change", markDirty);
    board.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!board.reportValidity()) return;
      const btn = $("[type=submit]", board);
      btn.disabled = true;
      try {
        const p = find("projects", board.dataset.id);
        await send(
          "api/projects/" + p.id,
          { ...projectPayload(p), cuts: readCuts(), version_label: board.elements.version_label.value, version_note: board.elements.version_note.value },
          "PUT",
        );
        dirty = false;
        await reload("새 콘티 버전을 저장했어요.");
      } catch (err) {
        $(".form-error", board).textContent = err.message;
      } finally {
        btn.disabled = false;
      }
    });
  }
  const search = $("#search");
  if (search)
    search.addEventListener("input", () => {
      query = search.value;
      const position = search.selectionStart;
      render().then(() => {
        const el = $("#search");
        if (el) {
          el.focus();
          el.setSelectionRange(position, position);
        }
      });
    });
}
const handlers = {
  render: (id) => {
    const p = find("projects", id);
    if (!p.approved_at) {
      toast("콘티를 먼저 제작 승인해주세요.");
      return;
    }
    modal(
      "콘티 프리뷰 만들기",
      `<form><div class="notice">연결된 이미지와 클립을 컷 순서대로 조합해요.<br>720×1280 세로 영상 · 무음 · 최대 180초</div><p class="subtitle">장면 길이와 순서를 확인하는 프리뷰예요. 음성·자막·AI 동작 생성은 포함되지 않으며 외부 AI 비용은 발생하지 않아요.</p>${actions("프리뷰 제작 시작")}</form>`,
      async () => {
        await send("api/projects/" + id + "/render", { revision: p.revision });
        await reload("프리뷰 제작을 시작했어요.");
      },
    );
  },
  "new-project": (id) => projectModal("", id),
  "edit-project": (id) => {
    if (dirty) {
      toast("콘티를 먼저 저장해주세요.");
      return;
    }
    projectModal(id);
  },
  product: productModal,
  character: characterModal,
  asset: assetModal,
  cost: costModal,
  video: videoModal,
  review: reviewModal,
  feedback: feedbackModal,
  filter: async (id) => {
    filter = id;
    await render();
  },
  "archive-product": async (id) => {
    const p = find("products", id);
    const body = Object.fromEntries(
      [
        "title",
        "category",
        "url",
        "features",
        "cautions",
        "source",
        "revision",
      ].map((k) => [k, p[k]]),
    );
    await send("api/products/" + id, { ...body, archived: !p.archived }, "PUT");
    await reload(p.archived ? "상품을 복원했어요." : "상품을 보관했어요.");
  },
  "archive-asset": async (id) => {
    const a = find("assets", id);
    await send("api/assets/" + id + "/archive", { revision: a.revision });
    await reload(a.archived ? "자산을 복원했어요." : "자산을 보관했어요.");
  },
  "void-cost": async (id) => {
    const c = find("costs", id);
    await send("api/costs/" + id + "/void", { revision: c.revision });
    await reload("비용 기록을 갱신했어요.");
  },
  "add-cut": () => {
    const cuts = readCuts();
    if (cuts.length >= 20) {
      toast("최대 20컷까지 작성할 수 있어요.");
      return;
    }
    updateCuts([
      ...cuts,
      {
        title: "새 장면",
        seconds: 6,
        visual: "",
        narration: "",
        prompt: "",
        asset_id: "",
        method: "ai",
      },
    ]);
  },
  "remove-cut": (id) =>
    updateCuts(readCuts().filter((_, i) => i !== Number(id))),
  "move-cut": (id, el) => {
    const cuts = readCuts(),
      i = Number(id),
      j = i + Number(el.dataset.dir);
    if (j < 0 || j >= cuts.length) return;
    [cuts[i], cuts[j]] = [cuts[j], cuts[i]];
    updateCuts(cuts);
  },
  template: (id) => {
    const p = find("projects", id),
      names = p.character_ids.map((k) => find("characters", k).name).join(", ");
    updateCuts(
      [
        "가족의 작은 사건",
        "해결을 위한 시도",
        "상품과의 만남",
        "특징을 가까이",
        "가족의 짧은 반응",
      ].map((title, i) => ({
        title,
        seconds: 6,
        visual: [
          `${names}의 일상 속 작은 불편이나 바람을 보여주세요.`,
          "캐릭터의 성격이 드러나는 행동으로 해결을 시도해요.",
          "실제 상품의 포장과 크기를 정확하게 보여주세요.",
          "실제 자료로 확인한 상품의 특징을 보여주세요.",
          "가족다운 짧은 반응으로 이야기를 마무리해요.",
        ][i],
        narration: "",
        prompt: "",
        asset_id: "",
        method: [2, 3].includes(i) ? "real" : "ai",
      })),
    );
    toast("기본 이야기 틀을 불러왔어요. 상품에 맞게 편집 후 저장해주세요.");
  },
  approve: async (id) => {
    if (dirty) {
      toast("변경한 콘티를 먼저 저장해주세요.");
      return;
    }
    const p = find("projects", id);
    if (p.approved_at) {
      toast("이미 제작 승인된 콘티예요.");
      return;
    }
    modal(
      "현재 콘티 제작 승인",
      `<form><div class="notice">${e(p.title)} · 저장 기록 #${p.revision}<br>${p.cuts.length}컷 · ${p.cuts.reduce((s, c) => s + c.seconds, 0)}초</div><p class="subtitle">상품 정보와 컷별 화면을 확인했다면 승인해주세요. 승인은 기록만 남기며 유료 생성은 실행하지 않아요.</p>${actions("이 콘티 제작 승인")}</form>`,
      async () => {
        await send("api/projects/" + id + "/approve", { revision: p.revision });
        await reload("콘티를 제작 승인했어요.");
      },
    );
  },
  import: async (id) => {
    const p = await send("api/legacy/" + id + "/import", {});
    await reload("상품 정보를 불러왔어요.");
    productModal(p.id);
  },
  history: async (id) => {
    const [key, revision] = id.split(":");
    const list = await api("api/projects/" + key + "/history"),
      p = list.find((p) => p.revision === Number(revision));
    modal(
      "저장 기록 #" + revision,
      `<p class="subtitle">${date(p.updated_at)} · 이전 버전 읽기 전용</p>${p.cuts.map((c, i) => `<section class="panel"><h3>CUT ${i + 1} · ${e(c.title)} · ${c.seconds}초</h3><p class="tiny preserve">${e(c.visual)}</p><p class="tiny preserve">대사 · ${e(c.narration || "미작성")}</p><p class="tiny preserve">프롬프트 · ${e(c.prompt || "미작성")}</p></section>`).join("") || empty("작성된 컷이 없어요", "이 버전은 기획 단계의 기록이에요.")}`,
    );
  },
  "publish-storyboard": async (id) => {
    const p = find("projects", id);
    modal("새 콘티 버전 등록", `<form>${field("버전 이름", "label", "새 콘티", "text", 'required maxlength="100"')}${area("변경 내용", "note", "", 2000)}<p>현재 콘티의 이미지와 설명을 보존합니다. 이전 버전도 계속 볼 수 있어요.</p>${actions("버전 등록")}</form>`, async (data) => {
      const result = await send(`api/projects/${id}/storyboards`, {revision:p.revision,label:data.get("label"),note:data.get("note")});
      location.hash = `project/${id}/images/${result.id}`;
      await reload(`콘티 v${result.number}을 등록했어요.`);
    });
  },
};
document.addEventListener("click", async (event) => {
  const el = event.target.closest("[data-act]");
  if (!el) return;
  if (
    dirty &&
    ![
      "add-cut",
      "remove-cut",
      "move-cut",
      "template",
      "approve",
      "filter",
    ].includes(el.dataset.act)
  ) {
    toast("콘티를 먼저 저장해주세요.");
    return;
  }
  const handler = handlers[el.dataset.act];
  if (!handler) return;
  el.disabled = true;
  try {
    await handler(el.dataset.id, el);
  } catch (err) {
    toast(err.message);
  } finally {
    el.disabled = false;
  }
});
$("#modal-close").addEventListener("click", () => $("#modal").close());
$("#refresh").addEventListener("click", async () => {
  if (
    dirty &&
    !confirm("저장하지 않은 콘티 변경사항이 사라져요. 새로고침할까요?")
  )
    return;
  dirty = false;
  try {
    await reload("작업실을 새로고침했어요.");
  } catch (err) {
    toast(err.message);
  }
});
window.addEventListener("beforeunload", (event) => {
  if (dirty) {
    event.preventDefault();
    event.returnValue = "";
  }
});
window.addEventListener("hashchange", async () => {
  if (
    dirty &&
    !confirm("저장하지 않은 콘티 변경사항이 사라져요. 이동할까요?")
  ) {
    history.replaceState(null, "", lastHash || "#dashboard");
    return;
  }
  dirty = false;
  lastHash = location.hash;
  $("#modal").close();
  if (state) {
    await render();
    window.scrollTo(0, 0);
  }
});
$$("[data-icon]").forEach((el) => (el.innerHTML = icon(el.dataset.icon)));
reload().catch((err) => {
  $("#main").innerHTML =
    `<div class="error">${e(err.message)}<p><a href="${e(document.baseURI)}">페이지 다시 열기</a></p></div>`;
});

let polling = false;
setInterval(async () => {
  if (
    polling ||
    !state ||
    dirty ||
    $("#modal").open ||
    !(state.jobs || []).some((j) => ["queued", "running"].includes(j.status))
  )
    return;
  polling = true;
  try {
    const next = await api("api/state");
    const changed = JSON.stringify(next.jobs) !== JSON.stringify(state.jobs);
    state = next;
    if (
      changed &&
      location.hash.endsWith("/videos") &&
      !$$("video").some((v) => !v.paused)
    )
      await render();
  } catch {
  } finally {
    polling = false;
  }
}, 3000);
