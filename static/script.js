function toggleTab(tabId) {
  document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
  document.getElementById(tabId).classList.add('active');

  if (tabId === 'history') loadHistory();
}

function generateImage() {
  const prompt = document.getElementById("prompt").value;
  if (!prompt) return alert("Please enter a prompt!");

  fetch("http://127.0.0.1:5000/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt })
  })
  .then(res => res.blob())
  .then(blob => {
    const url = URL.createObjectURL(blob);
    document.getElementById("imageContainer").innerHTML = `<img src="${url}" />`;

    // Save to history
    fetch("http://127.0.0.1:5000/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt })
    });
  });
}

function loadHistory() {
  fetch("http://127.0.0.1:5000/history")
    .then(res => res.json())
    .then(data => {
      const container = document.getElementById("historyContainer");
      container.innerHTML = data.map(item => `
        <div>
          <strong>${item.prompt}</strong>
          <img src="data:image/png;base64,${item.image}" />
        </div>
      `).join("");
    });
}

// ✅ Signup function
function signup(e) {
  e.preventDefault();

  const username = document.getElementById("signup-username").value;
  const password = document.getElementById("signup-password").value;
  const confirmPassword = document.getElementById("signup-confirm").value;

  if (password !== confirmPassword) {
    alert("Passwords do not match!");
    return;
  }

  fetch("http://127.0.0.1:5000/signup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password, confirmPassword })
  })
  .then(res => res.json())
  .then(data => {
    alert(data.message || "Signup successful!");
    if (data.success) toggleTab("login-tab");
  });
}

// ✅ Login function
function login(e) {
  e.preventDefault();

  const username = document.getElementById("login-username").value;
  const password = document.getElementById("login-password").value;

  fetch("http://127.0.0.1:5000/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      alert("Login successful!");
      toggleTab("generate-tab");
    } else {
      alert(data.message || "Login failed.");
    }
  });
}
