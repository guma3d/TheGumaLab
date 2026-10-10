'use strict';
const player = document.getElementById('story-player');
document.querySelectorAll('[data-seek]').forEach(button => {
  button.addEventListener('click', () => {
    player.currentTime = Number(button.dataset.seek);
    player.scrollIntoView({behavior:'smooth', block:'center'});
    player.play().catch(() => {});
  });
});
