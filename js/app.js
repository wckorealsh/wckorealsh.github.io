import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import {
  getAuth, onAuthStateChanged, GoogleAuthProvider, signInWithPopup,
  signInWithEmailAndPassword, createUserWithEmailAndPassword, signOut,
} from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";
import {
  getFirestore, collection, doc, onSnapshot, setDoc, deleteDoc, updateDoc, increment, serverTimestamp,
} from "https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js";
import { firebaseConfig } from "./firebase-config.js";

const $ = (s, r = document) => r.querySelector(s);
const configured = !String(firebaseConfig.apiKey).startsWith("PASTE");

// ---------- DOM ----------
const authBtn = $("#auth-btn"), userBox = $("#user-box"), userName = $("#user-name"), signOutBtn = $("#signout-btn");
const cartBtn = $("#cart-btn"), cartCount = $("#cart-count"), drawer = $("#cart"), cartList = $("#cart-list"),
      cartEmpty = $("#cart-empty"), cartTotal = $("#cart-total"), cartClose = $("#cart-close"), backdrop = $("#backdrop");
const dlg = $("#auth-dialog"), authForm = $("#auth-form"), authErr = $("#auth-error"), authTitle = $("#auth-title"),
      authSubmit = $("#auth-submit"), authToggle = $("#auth-toggle"), googleBtn = $("#google-btn");

if (!configured) {
  $("#setup-banner").hidden = false;
}

const app = configured ? initializeApp(firebaseConfig) : null;
const auth = configured ? getAuth(app) : null;
const db = configured ? getFirestore(app) : null;

let user = null, cart = new Map(), unsubCart = null, mode = "signin";

// ---------- auth UI ----------
function openAuth(msg = "") {
  if (!configured) { alert("Accounts are not set up yet — Firebase config is missing."); return; }
  authErr.textContent = msg;
  dlg.showModal();
}
authBtn.addEventListener("click", () => openAuth());
$("#auth-cancel").addEventListener("click", () => dlg.close());
authToggle.addEventListener("click", () => {
  mode = mode === "signin" ? "signup" : "signin";
  authTitle.textContent = mode === "signin" ? "Sign in" : "Create account";
  authSubmit.textContent = mode === "signin" ? "Sign in" : "Create account";
  authToggle.textContent = mode === "signin" ? "New here? Create an account" : "Have an account? Sign in";
  authErr.textContent = "";
});
authForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = authForm.email.value.trim(), pw = authForm.password.value;
  try {
    if (mode === "signin") await signInWithEmailAndPassword(auth, email, pw);
    else await createUserWithEmailAndPassword(auth, email, pw);
    dlg.close(); authForm.reset();
  } catch (err) { authErr.textContent = friendly(err); }
});
googleBtn.addEventListener("click", async () => {
  try { await signInWithPopup(auth, new GoogleAuthProvider()); dlg.close(); }
  catch (err) { authErr.textContent = friendly(err); }
});
signOutBtn.addEventListener("click", () => signOut(auth));

function friendly(err) {
  const m = { "auth/invalid-credential": "Wrong email or password.", "auth/user-not-found": "No account with that email.",
    "auth/wrong-password": "Wrong password.", "auth/email-already-in-use": "That email already has an account — sign in instead.",
    "auth/weak-password": "Password needs at least 6 characters.", "auth/invalid-email": "That doesn't look like an email.",
    "auth/popup-closed-by-user": "Google sign-in was cancelled.", "auth/unauthorized-domain": "This domain isn't authorised in Firebase Auth settings." };
  return m[err.code] || err.message;
}

if (configured) onAuthStateChanged(auth, (u) => {
  user = u;
  authBtn.hidden = !!u; userBox.hidden = !u;
  if (u) {
    userName.textContent = u.displayName || u.email;
    unsubCart = onSnapshot(collection(db, "users", u.uid, "cart"), (snap) => {
      cart = new Map(snap.docs.map((d) => [d.id, d.data()]));
      renderCart();
    });
  } else {
    if (unsubCart) unsubCart(); unsubCart = null;
    cart = new Map(); renderCart();
  }
});

// ---------- cart ----------
const won = (n) => "₩" + n.toLocaleString("en-US");
const minPrice = (s) => parseInt(String(s).replace(/[^\d–-]/g, "").split(/[–-]/)[0], 10) || 0;

function renderCart() {
  const qty = [...cart.values()].reduce((a, i) => a + (i.qty || 0), 0);
  cartCount.textContent = qty; cartCount.hidden = qty === 0;
  cartList.innerHTML = "";
  cartEmpty.hidden = cart.size > 0;
  let total = 0;
  for (const [id, it] of cart) {
    total += minPrice(it.price) * it.qty;
    const li = document.createElement("li");
    li.innerHTML = `<img src="${it.img}" alt=""><div><p class="brand">${it.brand}</p><h4>${it.name}</h4><p class="price">${it.price}</p></div>
      <div class="qty"><button data-d="-1" aria-label="less">−</button><span>${it.qty}</span><button data-d="1" aria-label="more">+</button></div>
      <button class="rm" aria-label="remove">×</button>`;
    li.querySelectorAll(".qty button").forEach((b) => b.addEventListener("click", () => changeQty(id, +b.dataset.d)));
    li.querySelector(".rm").addEventListener("click", () => deleteDoc(doc(db, "users", user.uid, "cart", id)));
    cartList.appendChild(li);
  }
  cartTotal.textContent = cart.size ? `from ${won(total)}` : "";
}
async function changeQty(id, d) {
  const it = cart.get(id); if (!it) return;
  if (it.qty + d <= 0) return deleteDoc(doc(db, "users", user.uid, "cart", id));
  return updateDoc(doc(db, "users", user.uid, "cart", id), { qty: increment(d) });
}
async function addToCart(card, n = 1) {
  if (!user) return openAuth("Sign in to save items to your cart.");
  const id = card.dataset.id;
  const ref = doc(db, "users", user.uid, "cart", id);
  if (cart.has(id)) await updateDoc(ref, { qty: increment(n) });
  else await setDoc(ref, { name: card.dataset.name, brand: card.dataset.brand, price: card.dataset.price, img: card.dataset.img, qty: n, addedAt: serverTimestamp() });
  const btn = card.querySelector(".add"), label = btn.textContent;
  btn.classList.add("done"); btn.textContent = "Added ✓";
  setTimeout(() => { btn.classList.remove("done"); btn.textContent = label; }, 1200);
  openDrawer();
}
document.addEventListener("click", (e) => {
  const b = e.target.closest("button.add"); if (!b) return;
  const box = b.closest("[data-id]"), qty = box.querySelector("input#qty");
  addToCart(box, qty ? Math.max(1, parseInt(qty.value, 10) || 1) : 1);
});

function openDrawer() { drawer.classList.add("open"); backdrop.hidden = false; }
function closeDrawer() { drawer.classList.remove("open"); backdrop.hidden = true; }
cartBtn.addEventListener("click", () => (user ? openDrawer() : openAuth("Sign in to see your cart.")));
cartClose.addEventListener("click", closeDrawer);
backdrop.addEventListener("click", closeDrawer);
