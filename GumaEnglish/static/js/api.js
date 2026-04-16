export async function fetchStage(stageNumber) {
  const res = await fetch(`/api/stage/${stageNumber}`);
  if (!res.ok) throw new Error(`stage ${stageNumber} fetch failed: ${res.status}`);
  return res.json();
}
