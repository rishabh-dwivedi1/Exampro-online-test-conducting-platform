const questions = JSON.parse(document.getElementById("question-data").textContent);
const state = {};
let current = 0;
let remaining = Number(window.EXAM_SECONDS || 0);

questions.forEach(q => state[q.id] = { answer: "", marked: false, visited: false });

const qNo = document.getElementById("qNo");
const qText = document.getElementById("qText");
const options = document.getElementById("options");
const palette = document.getElementById("palette");
const timer = document.getElementById("timer");
const form = document.getElementById("examForm");
const responsesInput = document.getElementById("responsesInput");

function statusOf(q) {
  const s = state[q.id];
  if (s.marked) return "review";
  if (s.answer) return "answered";
  if (s.visited) return "not-answered";
  return "not-visited";
}

function renderPalette() {
  palette.innerHTML = "";
  const counts = { "not-visited": 0, "not-answered": 0, answered: 0, review: 0 };
  questions.forEach((q, index) => {
    const status = statusOf(q);
    counts[status]++;
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = String(index + 1).padStart(2, "0");
    b.className = `${status} ${index === current ? "active" : ""}`;
    b.onclick = () => go(index);
    palette.appendChild(b);
  });
  document.querySelector(".box.not-visited").textContent = counts["not-visited"];
  document.querySelector(".box.not-answered").textContent = counts["not-answered"];
  document.querySelector(".box.answered").textContent = counts.answered;
  document.querySelector(".box.review").textContent = counts.review;
}

function renderQuestion() {
  const q = questions[current];
  state[q.id].visited = true;
  qNo.textContent = current + 1;
  qText.textContent = q.text;
  options.innerHTML = "";
  Object.entries(q.options).forEach(([key, value]) => {
    const label = document.createElement("label");
    label.className = "option";
    label.innerHTML = `<input type="radio" name="answer" value="${key}"><b>${key}</b><span></span>`;
    label.querySelector("span").textContent = value;
    const input = label.querySelector("input");
    input.checked = state[q.id].answer === key;
    input.onchange = () => {
      state[q.id].answer = key;
      renderPalette();
    };
    options.appendChild(label);
  });
  renderPalette();
  document.querySelectorAll(".subject-jump").forEach(btn => {
    btn.classList.toggle("active-subject", btn.dataset.subject === q.subject.toUpperCase());
  });
}

function go(index) {
  current = Math.max(0, Math.min(index, questions.length - 1));
  renderQuestion();
}

function next() {
  go(current + 1);
}

document.getElementById("saveNext").onclick = () => {
  state[questions[current].id].marked = false;
  next();
};
document.getElementById("markReview").onclick = () => {
  state[questions[current].id].marked = true;
  next();
};
document.getElementById("markOnly").onclick = () => {
  state[questions[current].id].marked = true;
  next();
};
document.getElementById("clearResponse").onclick = () => {
  state[questions[current].id].answer = "";
  state[questions[current].id].marked = false;
  renderQuestion();
};
document.getElementById("prevBtn").onclick = () => go(current - 1);
document.getElementById("nextBtn").onclick = () => next();
document.querySelectorAll(".subject-jump").forEach(btn => {
  btn.onclick = () => {
    const target = questions.findIndex(q => q.subject.toUpperCase() === btn.dataset.subject);
    if (target >= 0) go(target);
  };
});

function syncAndSubmit() {
  responsesInput.value = JSON.stringify(state);
}

form.onsubmit = () => {
  syncAndSubmit();
  return true;
};

function tick() {
  const m = Math.floor(remaining / 60);
  const s = remaining % 60;
  timer.textContent = `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  if (remaining <= 0) {
    syncAndSubmit();
    form.submit();
    return;
  }
  remaining--;
}

renderQuestion();
tick();
setInterval(tick, 1000);
