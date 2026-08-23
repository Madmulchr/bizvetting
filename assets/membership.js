// ============================================================================
// assets/membership.js
// ============================================================================
// Single shared module for login + Stripe checkout, used by every page on
// the site. Before this file existed, this logic was copy-pasted into each
// of 366 HTML files separately -- which is how "Become a Member" ended up
// opening a bare browser prompt() box instead of leading to payment, and why
// it took two full clicks (with an email round-trip in between) to actually
// reach Stripe. Fixed here once, not 366 times.
//
// What changed vs. the old per-page inline scripts:
//   1. No more window.prompt()/alert() for login -- a small inline dialog
//      instead, which actually looks like part of the site.
//   2. "Become a Member" while logged out no longer dead-ends after sending
//      the magic-link email. It remembers (in localStorage) that a checkout
//      was in progress; the moment the visitor clicks their email link and
//      lands back on the site (any page), checkout resumes automatically
//      and sends them straight to Stripe. One click total, not two.
//   3. The Stripe/Supabase wiring itself (create-checkout-session, session
//      handling) is untouched -- same backend, same security model.
// ============================================================================
(function (window) {
  const SUPABASE_URL = "https://zvzccgbzfmnjzjyqxaay.supabase.co";
  const SUPABASE_ANON_KEY = "sb_publishable_Rfp5FzznTrV9UFldAQCvrg_2bu6oVDT";
  const PENDING_KEY = 'bv_pending_checkout';
  const PENDING_TTL_MS = 30 * 60 * 1000; // ignore a checkout someone started >30 min ago

  const sb = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

  // ---- small inline UI helpers, replace window.prompt()/alert() ----------
  function askForEmail(message) {
    return new Promise(function (resolve) {
      const overlay = document.createElement('div');
      overlay.setAttribute('role', 'dialog');
      overlay.style.cssText = 'position:fixed;inset:0;background:rgba(10,14,20,0.65);z-index:9999;display:flex;align-items:center;justify-content:center;padding:16px;';
      overlay.innerHTML =
        '<div style="background:#0F1B26;border:1px solid #2A3A48;border-radius:10px;padding:24px;max-width:340px;width:100%;font-family:inherit;">' +
        '<p style="color:#ECEEE7;margin:0 0 12px;font-size:14px;line-height:1.4;">' + message + '</p>' +
        '<input type="email" placeholder="you@email.com" required style="width:100%;box-sizing:border-box;padding:10px;border-radius:6px;border:1px solid #2A3A48;background:#13202B;color:#ECEEE7;font-size:16px;margin-bottom:12px;">' +
        '<div style="display:flex;gap:8px;justify-content:flex-end;">' +
        '<button type="button" data-act="cancel" style="padding:8px 14px;border-radius:6px;border:1px solid #2A3A48;background:transparent;color:#ECEEE7;cursor:pointer;font-size:13.5px;">Cancel</button>' +
        '<button type="button" data-act="send" style="padding:8px 14px;border-radius:6px;border:none;background:#D66650;color:#fff;cursor:pointer;font-size:13.5px;">Send link</button>' +
        '</div></div>';
      document.body.appendChild(overlay);
      const input = overlay.querySelector('input');
      input.focus();
      function close(val) {
        if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
        resolve(val);
      }
      overlay.querySelector('[data-act="cancel"]').onclick = function () { close(null); };
      overlay.querySelector('[data-act="send"]').onclick = function () { close(input.value.trim() || null); };
      overlay.onclick = function (e) { if (e.target === overlay) close(null); };
      input.onkeydown = function (e) {
        if (e.key === 'Enter') { e.preventDefault(); close(input.value.trim() || null); }
        if (e.key === 'Escape') close(null);
      };
    });
  }

  function showToast(message) {
    const t = document.createElement('div');
    t.textContent = message;
    t.style.cssText = 'position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:#0F1B26;border:1px solid #2A3A48;color:#ECEEE7;padding:12px 20px;border-radius:8px;font-size:13.5px;z-index:9999;max-width:90vw;text-align:center;box-shadow:0 4px 16px rgba(0,0,0,0.3);';
    document.body.appendChild(t);
    setTimeout(function () { if (t.parentNode) t.parentNode.removeChild(t); }, 6000);
  }

  // ---- pending-checkout bookkeeping (survives the magic-link round trip) -
  function setPendingCheckout(path) {
    try {
      localStorage.setItem(PENDING_KEY, JSON.stringify({ path: path, ts: Date.now() }));
    } catch (e) { /* localStorage unavailable (private mode etc) -- not fatal */ }
  }
  function takePendingCheckout() {
    let raw;
    try { raw = localStorage.getItem(PENDING_KEY); } catch (e) { return null; }
    if (!raw) return null;
    try { localStorage.removeItem(PENDING_KEY); } catch (e) {}
    try {
      const parsed = JSON.parse(raw);
      if (Date.now() - parsed.ts > PENDING_TTL_MS) return null;
      return parsed.path;
    } catch (e) { return null; }
  }

  // ---- login ---------------------------------------------------------------
  // opts.resumeCheckout: if true, remembers returnPath so that once the
  // visitor clicks their magic link and lands back on the site (any page),
  // checkout resumes automatically -- no second "Become a Member" click.
  async function requestLogin(opts) {
    opts = opts || {};
    const email = await askForEmail('Enter your email to receive a login link:');
    if (!email) return false;
    if (opts.resumeCheckout) setPendingCheckout(opts.returnPath || window.location.pathname);
    const { error } = await sb.auth.signInWithOtp({ email: email });
    if (error) {
      showToast('Something went wrong: ' + error.message);
      return false;
    }
    showToast("Check your email for a login link — it'll bring you right back here.");
    return true;
  }

  // ---- checkout --------------------------------------------------------------
  async function startCheckout(btnEl, returnPath) {
    const { data: { session } } = await sb.auth.getSession();
    if (!session) return false;
    const originalText = btnEl ? btnEl.textContent : null;
    if (btnEl) btnEl.textContent = 'Redirecting...';
    try {
      const res = await fetch(SUPABASE_URL + '/functions/v1/create-checkout-session', {
        method: 'POST',
        headers: { 'Authorization': 'Bearer ' + session.access_token, 'Content-Type': 'application/json' },
        body: JSON.stringify({ return_path: returnPath || window.location.pathname }),
      });
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
        return true;
      }
      showToast('Something went wrong starting checkout: ' + (data.error || 'unknown error'));
    } catch (err) {
      console.error('Checkout error:', err);
      showToast('Something went wrong. Please try again.');
    }
    if (btnEl && originalText) btnEl.textContent = originalText;
    return false;
  }

  // The one function every "Become a Member" button should call.
  async function startOrDeferCheckout(btnEl, returnPath) {
    const path = returnPath || window.location.pathname;
    const { data: { session } } = await sb.auth.getSession();
    if (session) return startCheckout(btnEl, path);
    return requestLogin({ resumeCheckout: true, returnPath: path });
  }

  // Runs on every page load. If a checkout was started before login and the
  // visitor is now authenticated, skip straight to Stripe.
  async function resumePendingCheckout() {
    const pending = takePendingCheckout();
    if (!pending) return false;
    const { data: { session } } = await sb.auth.getSession();
    if (!session) return false;
    return startCheckout(null, pending);
  }

  // ---- header Log In / Log Out widget, present on every page -------------
  function initHeaderAuth() {
    const el = document.getElementById('authStatus');
    if (!el) return;
    sb.auth.getSession().then(function (res) {
      const session = res.data.session;
      if (session) {
        el.innerHTML = '<a href="#" id="logoutLink">Log Out</a>';
        document.getElementById('logoutLink').onclick = function (e) {
          e.preventDefault();
          sb.auth.signOut().then(function () { window.location.reload(); });
        };
      } else {
        el.innerHTML = '<a href="#" id="loginLink">Log In</a>';
        document.getElementById('loginLink').onclick = function (e) {
          e.preventDefault();
          requestLogin();
        };
      }
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initHeaderAuth();
    resumePendingCheckout();
  });

  window.BVMembership = {
    sb: sb,
    showToast: showToast,
    requestLogin: requestLogin,
    startCheckout: startCheckout,
    startOrDeferCheckout: startOrDeferCheckout,
  };
})(window);
