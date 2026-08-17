import json, re

with open('/home/claude/graded_listings.json') as f:
    data = json.load(f)

graded = data['graded']
ineligible = data['ineligible']

# Vertical-level constants — change these three lines to retarget the whole
# build at a different category (e.g. Self-Storage) without hunting for
# hardcoded strings elsewhere in the file.
CATEGORY_NAME = "HVAC"
CATEGORY_LABEL = "HVAC"  # display form with spacing
CATEGORY_SHORT = "HVAC"  # used in short-form copy contexts

# Single source of truth for the domain — update this one line once registered,
# and title tags, canonical links, JSON-LD urls, sitemap.xml, and robots.txt
# all pick it up automatically.
DOMAIN = "https://bizvetting.com"

# Same values embedded in SUPABASE_SCRIPT below (for deal pages) — kept as
# separate constants too so the landing page's lead-capture form can
# reference them without duplicating the literal strings a third time.
SUPABASE_PROJECT_URL = "https://zvzccgbzfmnjzjyqxaay.supabase.co"
SUPABASE_PUBLISHABLE_KEY = "sb_publishable_Rfp5FzznTrV9UFldAQCvrg_2bu6oVDT"

FONT_LINK = '''<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">'''

with open('/home/claude/site/assets/style.css') as f:
    CSS_INLINE = f.read()

SUPABASE_SCRIPT = '''<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
<script>
(function () {
  const SUPABASE_URL = "https://zvzccgbzfmnjzjyqxaay.supabase.co";
  const SUPABASE_ANON_KEY = "sb_publishable_Rfp5FzznTrV9UFldAQCvrg_2bu6oVDT";

  // Every deal page's own slug, so this same script works unmodified on
  // all 333+ pages — derived from the filename itself.
  const PAGE_SLUG = window.location.pathname
    .split('/').pop()
    .replace(/^deal-/, '')
    .replace(/\.html$/, '');

  const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

  async function init() {
    const { data: { session } } = await supabase.auth.getSession();
    const gateCard = document.querySelector('.gate-card');
    if (!gateCard) return; // page has no gate card, nothing to do

    if (!session) {
      renderLoggedOutState(gateCard);
      return;
    }

    // Logged in — check this specific deal's real gated data.
    const { data, error } = await supabase
      .from('deals_public')
      .select('exact_price, broker_name, broker_contact, target_price, annual_debt_service, source_url, member_content_unlocked')
      .eq('slug', PAGE_SLUG)
      .single();

    if (error || !data) {
      console.error('Bizvetting: could not load deal data', error);
      return; // fall back to the static gated placeholders already on the page
    }

    if (data.member_content_unlocked) {
      unlockGateCard(gateCard, data);
    } else {
      renderUpgradePrompt(gateCard);
    }
  }

  function renderLoggedOutState(gateCard) {
    const memberBtn = gateCard.querySelector('.btn-orange');
    if (!memberBtn) return;
    memberBtn.textContent = 'Log In to Continue';
    memberBtn.onclick = function (e) {
      e.preventDefault();
      const email = prompt('Enter your email to receive a login link:');
      if (!email) return;
      supabase.auth.signInWithOtp({ email }).then(function (res) {
        if (res.error) {
          alert('Something went wrong: ' + res.error.message);
        } else {
          alert('Check your email for a login link, then come back to this page.');
        }
      });
    };
  }

  function renderUpgradePrompt(gateCard) {
    const ctaText = gateCard.querySelector('.gate-cta-text');
    if (ctaText) {
      ctaText.textContent = "You're logged in — become a member to unlock this listing's exact price, broker contact, and target-offer price.";
    }
    const memberBtn = gateCard.querySelector('.btn-orange');
    if (memberBtn) {
      memberBtn.onclick = async function (e) {
        e.preventDefault();
        memberBtn.textContent = 'Redirecting...';
        const { data: { session } } = await supabase.auth.getSession();
        if (!session) return;
        try {
          const res = await fetch(SUPABASE_URL + '/functions/v1/create-checkout-session', {
            method: 'POST',
            headers: {
              'Authorization': 'Bearer ' + session.access_token,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ return_path: window.location.pathname }),
          });
          const data = await res.json();
          if (data.url) {
            window.location.href = data.url;
          } else {
            alert('Something went wrong starting checkout: ' + (data.error || 'unknown error'));
            memberBtn.textContent = 'Become a Member';
          }
        } catch (err) {
          console.error('Checkout error:', err);
          alert('Something went wrong. Please try again.');
          memberBtn.textContent = 'Become a Member';
        }
      };
    }
  }

  function unlockGateCard(gateCard, data) {
    const rows = gateCard.querySelectorAll('.gate-row');
    rows.forEach(function (row) {
      const label = row.querySelector('.label');
      const val = row.querySelector('.val');
      if (!label || !val) return;
      row.classList.remove('gate-blur');
      const labelText = label.textContent.trim();
      if (labelText === 'Exact asking price') {
        val.textContent = data.exact_price ? '$' + Number(data.exact_price).toLocaleString() : 'Not available';
      } else if (labelText === 'Est. annual debt service') {
        val.textContent = data.annual_debt_service ? '$' + Number(data.annual_debt_service).toLocaleString() : 'Not available';
      } else if (labelText === 'Broker contact') {
        val.textContent = data.broker_contact || 'Not yet available';
      } else if (labelText === 'Target offer price') {
        val.textContent = data.target_price ? '$' + Number(data.target_price).toLocaleString() : 'Not available';
      } else if (labelText === 'Original listing') {
        if (data.source_url) {
          val.innerHTML = '';
          const link = document.createElement('a');
          link.href = data.source_url;
          link.target = '_blank';
          link.rel = 'noopener noreferrer';
          link.textContent = 'View listing →';
          val.appendChild(link);
        } else {
          val.textContent = 'Not available';
        }
      }
    });
    const overlay = gateCard.querySelector('.gate-overlay');
    if (overlay) overlay.remove();
  }

  init();
})();
</script>'''

# Small header-nav widget: shows "Log In" when signed out, "Log Out" when
# signed in. Appended to every page via header(), so one definition here
# updates the whole site. Uses the same Supabase project/key as everything
# else — no new credentials, just a second small client instance scoped to
# this one widget.
AUTH_STATUS_SCRIPT = '''<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
<script>
(function () {
  const _sbAuth = window.supabase.createClient("''' + SUPABASE_PROJECT_URL + '''", "''' + SUPABASE_PUBLISHABLE_KEY + '''");
  const el = document.getElementById('authStatus');
  if (!el) return;
  _sbAuth.auth.getSession().then(function (res) {
    const session = res.data.session;
    if (session) {
      el.innerHTML = '<a href="#" id="logoutLink">Log Out</a>';
      document.getElementById('logoutLink').onclick = function (e) {
        e.preventDefault();
        _sbAuth.auth.signOut().then(function () { window.location.reload(); });
      };
    } else {
      el.innerHTML = '<a href="#" id="loginLink">Log In</a>';
      document.getElementById('loginLink').onclick = function (e) {
        e.preventDefault();
        const email = prompt('Enter your email to receive a login link:');
        if (!email) return;
        _sbAuth.auth.signInWithOtp({ email: email }).then(function (r) {
          alert(r.error ? ('Something went wrong: ' + r.error.message) : 'Check your email for a login link.');
        });
      };
    }
  });
})();
</script>'''

STATE_ABBR_TO_REGION = {
    'CT': 'New England', 'MA': 'New England', 'RI': 'New England', 'NH': 'New England',
    'ME': 'New England', 'VT': 'New England',
    'NJ': 'Mid-Atlantic', 'NY': 'Mid-Atlantic', 'PA': 'Mid-Atlantic', 'VA': 'Mid-Atlantic',
    'MD': 'Mid-Atlantic', 'DE': 'Mid-Atlantic', 'WV': 'Mid-Atlantic', 'DC': 'Mid-Atlantic',
    'CA': 'Pacific', 'WA': 'Pacific NW', 'OR': 'Pacific NW', 'HI': 'Pacific', 'AK': 'Pacific',
    'AZ': 'Southwest', 'UT': 'Southwest', 'NM': 'Southwest',
    'NC': 'Southeast', 'FL': 'Southeast', 'AL': 'Southeast', 'TN': 'Southeast',
    'GA': 'Southeast', 'SC': 'Southeast', 'KY': 'Southeast', 'MS': 'Southeast',
    'OK': 'South Central', 'TX': 'South Central', 'LA': 'South Central', 'AR': 'South Central',
    'WI': 'Midwest', 'IL': 'Midwest', 'MI': 'Midwest', 'IN': 'Midwest',
    'OH': 'Midwest', 'IA': 'Midwest', 'MO': 'Midwest', 'MN': 'Midwest',
    'KS': 'Midwest', 'NE': 'Midwest', 'SD': 'Midwest', 'ND': 'Midwest',
    'CO': 'Mountain West', 'NV': 'Mountain West', 'ID': 'Mountain West',
    'MT': 'Mountain West', 'WY': 'Mountain West',
    'ON': 'Canada — Ontario', 'NS': 'Canada — Nova Scotia', 'BC': 'Canada — British Columbia',
    'AB': 'Canada — Alberta', 'QC': 'Canada — Quebec', 'MB': 'Canada — Manitoba',
    'SK': 'Canada — Saskatchewan', 'NB': 'Canada — New Brunswick', 'NL': 'Canada — Newfoundland',
    'PE': 'Canada — Prince Edward Island',
}

GRADE_COLOR = {'A': '#4FB583', 'B': '#E0AC3F', 'C': '#D66650'}

def tag_svg(grade, w=64, h=82):
    color = GRADE_COLOR[grade]
    cx = w/2
    body_y = h*0.14
    body_h = h - body_y - 4
    hole_cy = body_y + 11
    letter_size = h*0.36
    return f'''<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg">
  <line x1="{cx}" y1="0" x2="{cx}" y2="{body_y+2}" stroke="#8CA0B3" stroke-width="1.4" stroke-dasharray="2 2"/>
  <rect x="4" y="{body_y}" width="{w-8}" height="{body_h}" rx="7" fill="#ECEEE7" stroke="{color}" stroke-width="2" stroke-dasharray="4 3"/>
  <circle cx="{cx}" cy="{hole_cy}" r="4.5" fill="none" stroke="#13202B" stroke-width="1.4"/>
  <circle cx="{cx}" cy="{hole_cy}" r="1.8" fill="#0F2A44"/>
  <text x="{cx}" y="{body_y+body_h*0.62}" text-anchor="middle" font-family="'Space Grotesk',sans-serif" font-weight="700" font-size="{letter_size:.0f}" fill="{color}">{grade}</text>
</svg>'''

STATE_NAME_TO_ABBR = {
    'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR', 'california': 'CA',
    'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE', 'florida': 'FL', 'georgia': 'GA',
    'hawaii': 'HI', 'idaho': 'ID', 'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA',
    'kansas': 'KS', 'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD',
    'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS',
    'missouri': 'MO', 'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV',
    'new hampshire': 'NH', 'new jersey': 'NJ', 'new mexico': 'NM', 'new york': 'NY',
    'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH', 'oklahoma': 'OK',
    'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI', 'south carolina': 'SC',
    'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT', 'vermont': 'VT',
    'virginia': 'VA', 'washington': 'WA', 'west virginia': 'WV', 'wisconsin': 'WI',
    'wyoming': 'WY', 'ontario': 'ON', 'nova scotia': 'NS', 'british columbia': 'BC',
    'alberta': 'AB', 'quebec': 'QC', 'manitoba': 'MB', 'saskatchewan': 'SK',
    'new brunswick': 'NB', 'newfoundland': 'NL', 'prince edward island': 'PE',
}

def general_location(loc):
    if not loc:
        return "Region withheld"
    m = re.search(r',\s*([A-Z]{2})$', loc)
    if m:
        st = m.group(1)
    elif re.fullmatch(r'[A-Z]{2}', loc.strip()):
        st = loc.strip()
    else:
        st = STATE_NAME_TO_ABBR.get(loc.strip().lower())
    if st:
        region = STATE_ABBR_TO_REGION.get(st)
        return f"{region} ({st})" if region else st
    return loc

def band_price_range(price):
    if price < 500_000: step = 50_000
    elif price < 1_000_000: step = 100_000
    elif price < 2_000_000: step = 250_000
    else: step = 500_000
    lo = (price // step) * step
    hi = lo + step
    return lo, hi

def band_price(price):
    lo, hi = band_price_range(price)
    fmt = lambda v: f"${v/1000:.0f}K" if v < 1_000_000 else f"${v/1_000_000:.2f}M".replace('.00M','M').replace('.50M','.5M')
    return f"{fmt(lo)} – {fmt(hi)}"

def slugify(title):
    s = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
    return s[:50].strip('-')

def public_ref(url):
    # A stable, ONE-WAY reference shown publicly (in URLs, JSON-LD, and the
    # on-page badge). Deliberately never the real source-platform listing ID
    # (BizBuySell's trailing digits, BizQuest's "BW..." code) -- exposing the
    # real ID would let anyone reconstruct or guess the original listing URL
    # directly, bypassing the entire membership gate with zero effort. MD5
    # is one-way: this value is stable across rebuilds (same URL always
    # produces the same ref) but cannot be reversed back into the source URL.
    import hashlib
    return hashlib.md5(url.encode()).hexdigest()[:8]

def money(v): return f"${v:,.0f}"
def grade_word(g): return {'A': 'strong', 'B': 'moderate', 'C': 'tight'}[g]

def deal_meta_description(d, ref_id):
    return (f"{d['region']} {CATEGORY_NAME} business, Grade {d['grade']}: "
            f"{d['sde_multiple']}x SDE multiple, {d['dscr_as_stated']}x as-stated DSCR / "
            f"{d['dscr_stressed']}x stressed DSCR. Asking price band {d['price_band']}. "
            f"Free underwriting breakdown, no signup required. (Listing #{ref_id})")

def deal_h1(d):
    return (f"{d['region']} {CATEGORY_SHORT} Business: {d['sde_multiple']}x SDE Multiple, "
            f"{d['dscr_stressed']}x Stressed DSCR — Grade {d['grade']}")

def deal_short_label(d, region=None):
    # Used anywhere a compact link/row label is needed (the listings table,
    # hub pages) -- built from the same already-free, already-banded fields
    # as the H1, never the raw broker title. Adjacent table columns already
    # show price/SDE/DSCR, so this stays short rather than repeating them.
    # region is an explicit param, not read from d['region'], because
    # ineligible listings never get that key precomputed the way graded
    # ones do -- callers pass whichever region string they already have.
    return f"{region or d.get('region')} {CATEGORY_SHORT} Business"

def deal_json_ld(d, url, ref_id):
    price_lo, price_hi = band_price_range(d['price'])
    payload = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": f"{d['region']} {CATEGORY_NAME} Business — Grade {d['grade']}",
        "sku": ref_id,
        "category": f"{CATEGORY_NAME} Service Business",
        "description": deal_meta_description(d, ref_id),
        "url": url,
        "offers": {
            "@type": "Offer",
            "priceCurrency": "USD",
            "priceSpecification": {
                "@type": "PriceSpecification",
                "minPrice": price_lo,
                "maxPrice": price_hi,
                "priceCurrency": "USD"
            },
            "businessFunction": "http://purl.org/goodrelations/v1#Sell",
            "areaServed": d['region'],
            "availability": "https://schema.org/InStock"
        },
        "additionalProperty": [
            {"@type": "PropertyValue", "name": "SDE Multiple", "value": f"{d['sde_multiple']}x"},
            {"@type": "PropertyValue", "name": "DSCR (as-stated)", "value": str(d['dscr_as_stated'])},
            {"@type": "PropertyValue", "name": "DSCR (stressed)", "value": str(d['dscr_stressed'])},
            {"@type": "PropertyValue", "name": "Grade", "value": d['grade']}
        ]
    }
    return json.dumps(payload, indent=2)

def band_discount(pct):
    if pct <= 0: return "Clears at ask"
    banded = 5 * ((pct - 1) // 5 + 1)  # round up to next 5
    return f"~{banded}% off ask"

DOWN_PCT = 0.125
for d in graded:
    d['region'] = general_location(d['location'])
    d['price_band'] = band_price(d['price'])
    # Slug built entirely from already-free, already-banded fields (region,
    # category, grade, SDE multiple) plus a one-way hash for uniqueness --
    # never the raw broker title or the real source-platform listing ID.
    # Both of those would let a free user reverse-search or directly
    # reconstruct the original listing, defeating the membership gate.
    slug_base = slugify(f"{d['region']}-{CATEGORY_SHORT}-grade-{d['grade']}-{d['sde_multiple']}x-sde")
    d['slug'] = f"{slug_base}-{public_ref(d['url'])}"
    down_payment = d['price'] * DOWN_PCT
    post_debt_cash = d['sde'] - d['annual_debt_service']
    d['coc'] = round(100 * post_debt_cash / down_payment, 1) if down_payment else 0

    # Target-offer math: since debt service scales linearly with price at fixed
    # down%/rate/term, the price that hits a target stressed DSCR is a simple ratio.
    TARGET_DSCR = 1.25  # standard SBA lender comfort threshold
    if d['dscr_stressed'] >= TARGET_DSCR:
        d['discount_needed_pct'] = 0
        d['target_price'] = d['price']
    else:
        ratio = d['dscr_stressed'] / TARGET_DSCR
        d['target_price'] = round(d['price'] * ratio, -3)  # nearest $1,000
        d['discount_needed_pct'] = round(100 * (1 - ratio))

SPONSOR_MODULE = '''
<div class="sponsor-module">
  <div class="sponsor-label">Sponsored — SBA Lenders Active in This Category</div>
  <div class="sponsor-grid">
    <div class="sponsor-card"><h4>Live Oak Bank</h4><p>National SBA 7(a) volume leader for trades &amp; home-service acquisitions.</p></div>
    <div class="sponsor-card"><h4>Newtek / NSBF</h4><p>Non-bank SBA lender, fast pre-qualification for owner-operator deals.</p></div>
    <div class="sponsor-card"><h4>Ready Capital</h4><p>SBA 7(a) &amp; 504, strong in $750K–$3M service-business acquisitions.</p></div>
  </div>
  <div class="sponsor-disclosure">Placement is paid and does not affect grading or ranking. Grades are computed independently from stressed DSCR.</div>
</div>
'''

def header():
    return f'''<header class="site-header">
  <div class="site-header-inner">
    <a class="wordmark-block" href="index.html">
      <span class="wordmark">Biz<span>vetting</span></span>
      <span class="wordmark-tag">In-demand, on-market businesses — pre-underwritten &amp; ranked, accelerating your path to ownership</span>
    </a>
    <nav class="header-nav">
      <a class="current" href="listings.html">{CATEGORY_LABEL}</a>
      <a href="#">Self-Storage</a>
      <a href="#">Methodology</a>
      <a href="#">Membership</a>
      <span id="authStatus"></span>
    </nav>
  </div>
</header>''' + AUTH_STATUS_SCRIPT

def footer():
    return '''<footer class="site-footer"><div class="wrap">
  Bizvetting grades HVAC, plumbing, and electrical businesses for sale against standardized SBA 7(a) underwriting math. Deal figures are estimates for screening purposes only, derived from public listing data and standardized assumptions (12.5% down, 9.5% rate, 10-yr term, 20% SDE stress haircut). Not a substitute for lender underwriting or a CPA-reviewed quality-of-earnings review. Grades are relative to the current batch, not an absolute rating.
</div></footer>'''

# ============================================================
# Landing page (index.html)
# ============================================================
top5 = [d for d in graded if d['grade'] == 'A'][:5]
n_total_l = len(graded) + len(ineligible)

rack_items = []
for d in top5:
    rack_items.append(f'''<div class="rack-item">
      <div class="tag-wrap">{tag_svg(d['grade'], 78, 100)}</div>
      <div class="rack-cap"><b>{d['sde_multiple']}x SDE</b><span>{d['region']}</span></div>
    </div>''')

landing_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Bizvetting — SBA-Underwritten Deal Screening for HVAC, Plumbing &amp; Electrical Businesses</title>
<meta name="description" content="Every HVAC, plumbing, and electrical business for sale, underwritten through SBA 7(a) math and graded relative to the current batch — before you call the broker.">
<link rel="canonical" href="{DOMAIN}/">
<meta property="og:type" content="website">
<meta property="og:title" content="Bizvetting — SBA-Underwritten Deal Screening for HVAC, Plumbing &amp; Electrical Businesses">
<meta property="og:description" content="Every HVAC, plumbing, and electrical business for sale, underwritten through SBA 7(a) math and graded relative to the current batch — before you call the broker.">
<meta property="og:url" content="{DOMAIN}/">
{FONT_LINK}
<style>
{CSS_INLINE}
</style>
</head>
<body>
{header()}
<div class="hero wrap">
  <div class="hero-eyebrow">Batch No. 2026.08 — SBA 7(a) Underwriting Cycle</div>
  <h1 class="hero-title">Every HVAC, plumbing &amp; electrical listing, <span class="hl">tagged and inspected</span> before you call the broker.</h1>
  <p class="hero-sub">We evaluate HVAC, plumbing, and electrical businesses publicly listed for sale and run each one through standard SBA 7(a) underwriting math — same down payment, same rate, same stress test a lender applies. Then the whole batch gets graded against itself. Every listing leaves with a grade: A, B, or C.</p>
  <div class="hero-meta">
    <div><b>{n_total_l}</b>listings screened this cycle</div>
    <div><b>{len(graded)}</b>SBA-financeable &amp; tagged</div>
    <div><b>$500K–$3M</b>price band</div>
  </div>
  <div class="rack">
    <div class="rack-wire"></div>
    <div class="rack-items">
      {"".join(rack_items)}
    </div>
  </div>
</div>

<section class="method-strip wrap">
  <span class="hero-eyebrow" style="margin-bottom:0;">Method</span>
  <div class="method-grid">
    <div class="method-step">
      <div class="num">01</div>
      <h3>Screen</h3>
      <p>Every HVAC, plumbing, and electrical business publicly listed for sale is evaluated and filtered to the SBA sweet spot — $500K–$3M asking price, field-service businesses only.</p>
    </div>
    <div class="method-step">
      <div class="num">02</div>
      <h3>Inspect</h3>
      <p>Each deal runs through the same SBA 7(a) math a lender will — 12.5% down, current market rate, 10-year term, and a 20% stressed SDE haircut before DSCR is recalculated.</p>
    </div>
    <div class="method-step">
      <div class="num">03</div>
      <h3>Tag</h3>
      <p>Deals are graded A, B, or C relative to the batch, not an arbitrary cutoff — so the strongest financeable deals surface first, every cycle.</p>
    </div>
  </div>
  <div class="assumptions-box">
    <b>Financing case:</b> 12.5% down · 9.5% rate · 10-yr SBA 7(a) term<br>
    <b>Stress test:</b> stated SDE haircut 20% before the DSCR is recalculated<br>
    <b>Grading:</b> relative to this cycle's batch (Grade A = top third), not a lender pre-approval<br>
    <b>SDE multiple:</b> broker-stated cash flow ÷ asking price, shown plainly alongside the tag
  </div>
</section>

<section class="cta-section wrap">
  <div class="cta-inner">
    <div>
      <span class="hero-eyebrow">Full list</span>
      <h2>The full tagged list is free.</h2>
      <p class="desc">Every business, every tag, every DSCR — browse it all with no signup. Membership only unlocks the exact price, target-offer price, and a direct link to the original listing once you're ready to make a call.</p>
    </div>
    <div class="cta-card">
      <div class="amt">Free to browse</div>
      <div class="amt-desc">No email required to see grades, multiples, and DSCR for every listing.</div>
      <a class="btn-orange" href="listings.html">See the full list →</a>
      <div class="cta-divider"></div>
      <div class="amt">$39<span style="font-size:14px;color:var(--ink-dim);font-weight:400;">/month</span></div>
      <div class="amt-desc">Membership unlocks exact price, target-offer price, and a direct link to the original listing on any deal.</div>
      <a class="btn-orange" href="#" id="landingMemberBtn">Become a Member →</a>
      <div class="cta-divider"></div>
      <form class="leadgen" onsubmit="handleSubmit(event)">
        <input type="email" id="leadEmail" placeholder="you@email.com" required>
        <button type="submit">Email me new Grade A deals →</button>
      </form>
      <div class="confirm-msg" id="confirmMsg">✓ You're on the list — check your inbox.</div>
      <p class="fine-print" id="leadError" style="display:none;color:var(--flag);"></p>
      <p class="fine-print">No spam. Unsubscribe with one click.</p>
    </div>
  </div>
</section>
{footer()}
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
<script>
const _sb = window.supabase.createClient("{SUPABASE_PROJECT_URL}", "{SUPABASE_PUBLISHABLE_KEY}");

document.getElementById('landingMemberBtn').onclick = async function(e) {{
  e.preventDefault();
  const btn = e.target;
  const {{ data: {{ session }} }} = await _sb.auth.getSession();
  if (!session) {{
    const email = prompt('Enter your email to receive a login link:');
    if (!email) return;
    const {{ error }} = await _sb.auth.signInWithOtp({{ email }});
    if (error) {{
      alert('Something went wrong: ' + error.message);
    }} else {{
      alert('Check your email for a login link, then come back and click Become a Member again.');
    }}
    return;
  }}
  btn.textContent = 'Redirecting...';
  try {{
    const res = await fetch("{SUPABASE_PROJECT_URL}" + '/functions/v1/create-checkout-session', {{
      method: 'POST',
      headers: {{ 'Authorization': 'Bearer ' + session.access_token, 'Content-Type': 'application/json' }},
      body: JSON.stringify({{ return_path: '/listings.html' }}),
    }});
    const data = await res.json();
    if (data.url) {{
      window.location.href = data.url;
    }} else {{
      alert('Something went wrong starting checkout: ' + (data.error || 'unknown error'));
      btn.textContent = 'Become a Member →';
    }}
  }} catch (err) {{
    console.error('Checkout error:', err);
    alert('Something went wrong. Please try again.');
    btn.textContent = 'Become a Member →';
  }}
}};
async function handleSubmit(e){{
  e.preventDefault();
  const emailInput = document.getElementById('leadEmail');
  const errorMsg = document.getElementById('leadError');
  const button = e.target.querySelector('button');
  errorMsg.style.display = 'none';
  button.textContent = 'Submitting...';
  try {{
    const {{ error }} = await _sb.from('email_leads').insert({{ email: emailInput.value, source: 'landing_page' }});
    if (error) throw error;
    document.getElementById('confirmMsg').style.display='block';
    e.target.reset();
    button.textContent = 'Email me new Grade A deals →';
  }} catch (err) {{
    console.error('Lead capture error:', err);
    errorMsg.textContent = 'Something went wrong — please try again.';
    errorMsg.style.display = 'block';
    button.textContent = 'Email me new Grade A deals →';
  }}
}}
</script>
</body>
</html>'''

with open('/home/claude/site/index.html', 'w') as f:
    f.write(landing_html)

# ============================================================
# Listings / ledger page
# ============================================================
n_a = sum(1 for d in graded if d['grade']=='A')
n_b = sum(1 for d in graded if d['grade']=='B')
n_c = sum(1 for d in graded if d['grade']=='C')

rows = []
for d in graded:
    price_lo, _ = band_price_range(d['price'])
    super_region = d['region'].split(' (')[0]
    rows.append(f'''<tr data-region="{super_region}" data-grade="{d['grade']}" data-price-lo="{price_lo}" data-dscr-stressed="{d['dscr_stressed']}" data-sde-multiple="{d['sde_multiple']}">
  <td style="width:52px;">{tag_svg(d['grade'], 40, 52)}</td>
  <td class="deal-title-cell"><a href="deal-{d['slug']}.html">{deal_short_label(d)}</a><span class="deal-meta">{d['region']}</span></td>
  <td class="num-cell">{d['price_band']}</td>
  <td class="num-cell">{d['sde_multiple']}x</td>
  <td class="dscr-pair">{d['dscr_as_stated']} <span class="arrow">→</span> <span class="stressed">{d['dscr_stressed']}</span></td>
  <td class="num-cell">{band_discount(d['discount_needed_pct'])}</td>
</tr>''')

ineligible_rows = []
for d in ineligible:
    ineligible_rows.append(f'''<tr class="ineligible-row">
  <td><span class="ineligible-tag">—</span></td>
  <td class="deal-title-cell"><a href="#">{deal_short_label(d, general_location(d['location']))}</a><span class="deal-meta">{general_location(d['location'])}</span></td>
  <td class="num-cell">{band_price(d['price'])}</td>
  <td class="num-cell">—</td>
  <td class="dscr-pair"><span class="ineligible-tag">Exceeds SBA $5M loan cap</span></td>
  <td class="num-cell">—</td>
</tr>''')

# Distinct super-regions present in this cycle's data, for the filter dropdown.
# Computed from the actual dataset rather than hardcoded, so it stays correct
# as more listings get added in future cycles.
_region_counts = {}
for d in graded:
    sr = d['region'].split(' (')[0]
    _region_counts[sr] = _region_counts.get(sr, 0) + 1
region_options = "".join(
    f'<option value="{sr}">{sr} ({c})</option>'
    for sr, c in sorted(_region_counts.items(), key=lambda x: -x[1])
)

listings_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HVAC, Plumbing &amp; Electrical Businesses for Sale — Tagged for SBA Financing | Bizvetting</title>
<meta name="description" content="Bizvetting screens HVAC, plumbing, and electrical service businesses for sale, tagged by stressed DSCR against standardized SBA 7(a) financing assumptions.">
<link rel="canonical" href="{DOMAIN}/listings.html">
<meta property="og:type" content="website">
<meta property="og:title" content="HVAC, Plumbing &amp; Electrical Businesses for Sale — Tagged for SBA Financing">
<meta property="og:description" content="Bizvetting screens HVAC, plumbing, and electrical service businesses for sale, tagged by stressed DSCR against standardized SBA 7(a) financing assumptions.">
<meta property="og:url" content="{DOMAIN}/listings.html">
{FONT_LINK}
<style>
{CSS_INLINE}
</style>
</head>
<body>
{header()}
<div class="batch-banner wrap">
  <div class="hero-eyebrow">Current Batch — Cycle 2026.08</div>
  <h1 class="batch-title">HVAC, Plumbing &amp; Electrical Businesses, Tagged for SBA Financing</h1>
  <p class="batch-sub">Every listing is run through the same SBA 7(a) underwriting math and graded against the rest of this batch by stressed DSCR. No listing pays for a better grade. {n_a} Grade A · {n_b} Grade B · {n_c} Grade C · {len(ineligible)} over SBA loan cap.</p>
</div>
<div class="ledger wrap">
  <div class="filter-bar" id="filterBar">
    <div class="filter-bar-locked" id="filterBarLocked">
      <span class="filter-lock-icon">&#128274;</span>
      <span class="filter-lock-text">Filtering &amp; sorting is a membership feature.</span>
      <a href="#" class="btn-orange" id="filterUpsellBtn" style="padding:8px 16px;font-size:12.5px;">Become a Member — $39/month</a>
    </div>
    <div class="filter-bar-controls" id="filterBarControls" style="display:none;">
      <div class="filter-group">
        <label for="filterRegion">Region</label>
        <select id="filterRegion"><option value="">All regions</option>{region_options}</select>
      </div>
      <div class="filter-group">
        <label>Grade</label>
        <div class="filter-checks">
          <label><input type="checkbox" class="filterGrade" value="A" checked> A</label>
          <label><input type="checkbox" class="filterGrade" value="B" checked> B</label>
          <label><input type="checkbox" class="filterGrade" value="C" checked> C</label>
        </div>
      </div>
      <div class="filter-group">
        <label for="filterMinDscr">Min stressed DSCR</label>
        <input type="number" id="filterMinDscr" step="0.05" placeholder="e.g. 1.25">
      </div>
      <div class="filter-group">
        <label for="filterMaxPrice">Max asking price</label>
        <select id="filterMaxPrice">
          <option value="">No limit</option>
          <option value="500000">Under $500K</option>
          <option value="1000000">Under $1M</option>
          <option value="2000000">Under $2M</option>
          <option value="5000000">Under $5M</option>
        </select>
      </div>
      <button class="btn-orange" id="filterResetBtn" style="padding:8px 16px;font-size:12.5px;">Reset</button>
      <span class="filter-count" id="filterCount"></span>
    </div>
  </div>
  <div class="ledger-panel">
  <table class="ledger-table" id="ledgerTable">
    <thead><tr>
      <th></th>
      <th class="sortable" data-sort="title">Business</th>
      <th class="sortable" data-sort="price-lo">Asking price</th>
      <th class="sortable" data-sort="sde-multiple">SDE multiple</th>
      <th class="sortable" data-sort="dscr-stressed">DSCR — stated → stressed</th>
      <th>To hit 1.25x</th>
    </tr></thead>
    <tbody>
      {"".join(rows)}
      {"".join(ineligible_rows)}
    </tbody>
  </table>
  </div>
  {SPONSOR_MODULE}
</div>
{footer()}
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
<script>
(function () {{
  const _sb = window.supabase.createClient("{SUPABASE_PROJECT_URL}", "{SUPABASE_PUBLISHABLE_KEY}");

  async function checkMembership() {{
    const {{ data: {{ session }} }} = await _sb.auth.getSession();
    if (!session) return false;
    // member_content_unlocked is derived purely from the session, not from
    // which row is queried -- any single row tells us the same answer, so
    // this doesn't need to touch gated data to check membership status.
    const {{ data }} = await _sb.from('deals_public').select('member_content_unlocked').limit(1).single();
    return data ? data.member_content_unlocked : false;
  }}

  function initFilters() {{
    const table = document.getElementById('ledgerTable');
    const allRows = Array.from(table.querySelectorAll('tbody tr:not(.ineligible-row)'));
    const regionSel = document.getElementById('filterRegion');
    const gradeChecks = document.querySelectorAll('.filterGrade');
    const minDscr = document.getElementById('filterMinDscr');
    const maxPrice = document.getElementById('filterMaxPrice');
    const countEl = document.getElementById('filterCount');
    let sortState = {{ key: null, dir: 1 }};

    function applyFilters() {{
      const region = regionSel.value;
      const grades = Array.from(gradeChecks).filter(c => c.checked).map(c => c.value);
      const minD = parseFloat(minDscr.value) || null;
      const maxP = parseFloat(maxPrice.value) || null;
      let visible = 0;
      allRows.forEach(function (row) {{
        let show = true;
        if (region && row.dataset.region !== region) show = false;
        if (!grades.includes(row.dataset.grade)) show = false;
        if (minD !== null && parseFloat(row.dataset.dscrStressed) < minD) show = false;
        if (maxP !== null && parseFloat(row.dataset.priceLo) > maxP) show = false;
        row.style.display = show ? '' : 'none';
        if (show) visible++;
      }});
      countEl.textContent = `Showing ${{visible}} of ${{allRows.length}} graded deals`;
    }}

    regionSel.onchange = applyFilters;
    minDscr.oninput = applyFilters;
    maxPrice.onchange = applyFilters;
    gradeChecks.forEach(c => c.onchange = applyFilters);
    document.getElementById('filterResetBtn').onclick = function () {{
      regionSel.value = '';
      gradeChecks.forEach(c => c.checked = true);
      minDscr.value = '';
      maxPrice.value = '';
      applyFilters();
    }};

    document.querySelectorAll('.sortable').forEach(function (th) {{
      th.onclick = function () {{
        const key = th.dataset.sort;
        sortState.dir = (sortState.key === key) ? -sortState.dir : 1;
        sortState.key = key;
        document.querySelectorAll('.sortable').forEach(h => h.classList.remove('sort-asc', 'sort-desc'));
        th.classList.add(sortState.dir === 1 ? 'sort-asc' : 'sort-desc');
        const tbody = table.querySelector('tbody');
        const sorted = allRows.slice().sort(function (a, b) {{
          let av, bv;
          if (key === 'title') {{
            av = a.querySelector('.deal-title-cell a').textContent;
            bv = b.querySelector('.deal-title-cell a').textContent;
            return sortState.dir * av.localeCompare(bv);
          }} else {{
            const dataKey = key === 'price-lo' ? 'priceLo' : key === 'sde-multiple' ? 'sdeMultiple' : 'dscrStressed';
            av = parseFloat(a.dataset[dataKey]);
            bv = parseFloat(b.dataset[dataKey]);
            return sortState.dir * (av - bv);
          }}
        }});
        sorted.forEach(row => tbody.appendChild(row));
      }};
    }});

    applyFilters();
  }}

  async function init() {{
    const isMember = await checkMembership();
    if (isMember) {{
      document.getElementById('filterBarLocked').style.display = 'none';
      document.getElementById('filterBarControls').style.display = 'flex';
      initFilters();
    }} else {{
      document.getElementById('filterUpsellBtn').onclick = async function (e) {{
        e.preventDefault();
        const {{ data: {{ session }} }} = await _sb.auth.getSession();
        if (!session) {{
          const email = prompt('Enter your email to receive a login link:');
          if (!email) return;
          const {{ error }} = await _sb.auth.signInWithOtp({{ email }});
          alert(error ? ('Something went wrong: ' + error.message) : 'Check your email for a login link, then come back and try again.');
          return;
        }}
        e.target.textContent = 'Redirecting...';
        try {{
          const res = await fetch("{SUPABASE_PROJECT_URL}" + '/functions/v1/create-checkout-session', {{
            method: 'POST',
            headers: {{ 'Authorization': 'Bearer ' + session.access_token, 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ return_path: '/listings.html' }}),
          }});
          const data = await res.json();
          if (data.url) window.location.href = data.url;
          else alert('Something went wrong: ' + (data.error || 'unknown error'));
        }} catch (err) {{
          console.error('Checkout error:', err);
          alert('Something went wrong. Please try again.');
        }}
      }};
    }}
  }}
  init();
}})();
</script>
</body>
</html>'''

with open('/home/claude/site/listings.html', 'w') as f:
    f.write(listings_html)

# ============================================================
# Deal permalink pages
# ============================================================
DEAL_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{h1} | Bizvetting</title>
<meta name="description" content="{meta_description}">
<link rel="canonical" href="{canonical_url}">
<meta property="og:type" content="product">
<meta property="og:title" content="{h1}">
<meta property="og:description" content="{meta_description}">
<meta property="og:url" content="{canonical_url}">
{font_link}
<style>
{css}
</style>
<script type="application/ld+json">
{json_ld}
</script>
</head>
<body>
{header}
<div class="deal-header wrap">
  <div class="breadcrumb"><a href="listings.html">{category_label}</a> / {region}</div>
  <div class="deal-header-row">
    <div>
      <h1 class="deal-h1">{h1}<span class="deal-ref">#{ref_id}</span></h1>
      <div class="deal-location">{region} · {category_label} Services</div>
    </div>
    {tag_big}
  </div>
</div>

<div class="deal-body wrap">
  <main>
    <p class="section-label">Financing Snapshot</p>
    <table class="figures-table">
      <tr><th>Asking price band</th><td>{price_band}</td></tr>
      <tr><th>SDE multiple</th><td>{sde_multiple}x</td></tr>
      <tr><th>DSCR — as stated</th><td>{dscr_as_stated}</td></tr>
      <tr><th>DSCR — stressed<span class="sub-note">SDE haircut 20%, per SBA lender stress-test convention</span></th><td>{dscr_stressed}</td></tr>
      <tr><th>Price move to hit 1.25x stressed<span class="sub-note">Standard SBA lender comfort threshold</span></th><td>{discount_band}</td></tr>
    </table>

    <p class="section-label">About This Listing</p>
    <div class="prose">
      <p>This is a {category} service business currently listed for sale in {region}. It has been screened against this cycle's batch of comparable listings and graded {grade} — {grade_word_lower} relative to the current market, based on how much cushion remains in its cash flow after a standardized SBA stress test, not an absolute rating of the business itself.</p>
      <p>Full listing details, including the exact asking price, target-offer price, and a direct link to the original listing, are available to members.</p>
    </div>
  </main>

  <aside>
    <div class="rail-block gate-card">
      <div class="gate-row gate-blur"><span class="label">Exact asking price</span><span class="val">$████,███</span></div>
      <div class="gate-row gate-blur"><span class="label">Est. annual debt service</span><span class="val">$██,███</span></div>
      <div class="gate-row gate-blur"><span class="label">Broker contact</span><span class="val">██████████</span></div>
      <div class="gate-row gate-blur"><span class="label">Target offer price</span><span class="val">$████,███</span></div>
      <div class="gate-row gate-blur"><span class="label">Original listing</span><span class="val">██████████</span></div>
      <div class="gate-overlay">
        <div class="gate-lock">&#128274;</div>
        <p class="gate-cta-text">Unlock the exact price, target-offer price, and a direct link to the original listing.</p>
        <div class="gate-price">$39<span>/month</span></div>
        <a class="btn-orange" href="#">Become a Member</a>
      </div>
    </div>
  </aside>
</div>

{sponsor_module}
{footer}
{supabase_script}
</body>
</html>'''

for d in graded:
    ref_id = public_ref(d['url']).upper()
    deal_url = f"{DOMAIN}/deal-{d['slug']}.html"
    html = DEAL_TEMPLATE.format(
        grade=d['grade'], grade_word=grade_word(d['grade']),
        grade_word_lower=grade_word(d['grade']).lower(),
        region=d['region'], price_band=d['price_band'], sde_multiple=d['sde_multiple'],
        annual_debt_service=money(d['annual_debt_service']),
        dscr_as_stated=d['dscr_as_stated'], dscr_stressed=d['dscr_stressed'],
        discount_band=band_discount(d['discount_needed_pct']),
        category=CATEGORY_NAME, category_label=CATEGORY_LABEL,
        h1=deal_h1(d), ref_id=ref_id, meta_description=deal_meta_description(d, ref_id),
        json_ld=deal_json_ld(d, deal_url, ref_id), canonical_url=deal_url,
        font_link=FONT_LINK, header=header(), footer=footer(), css=CSS_INLINE,
        tag_big=tag_svg(d['grade'], 88, 112),
        sponsor_module=f'<div class="wrap">{SPONSOR_MODULE}</div>',
        supabase_script=SUPABASE_SCRIPT
    )
    with open(f"/home/claude/site/deal-{d['slug']}.html", 'w') as f:
        f.write(html)

print(f"Built index.html + listings.html + {len(graded)} deal pages")

# ============================================================
# sitemap.xml + robots.txt — generated from the same data every
# other page pulls from, so they can never drift out of sync with
# what deal pages actually exist. Swap DOMAIN at the top once
# registered and every URL below updates automatically.
# ============================================================
import datetime
today = datetime.date.today().isoformat()

sitemap_urls = [
    (f"{DOMAIN}/", "daily", "1.0"),
    (f"{DOMAIN}/listings.html", "daily", "0.9"),
]
for d in graded:
    sitemap_urls.append((f"{DOMAIN}/deal-{d['slug']}.html", "weekly", "0.7"))

sitemap_entries = "\n".join(
    f"  <url>\n    <loc>{url}</loc>\n    <lastmod>{today}</lastmod>\n"
    f"    <changefreq>{freq}</changefreq>\n    <priority>{pri}</priority>\n  </url>"
    for url, freq, pri in sitemap_urls
)
sitemap_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{sitemap_entries}
</urlset>'''
with open('/home/claude/site/sitemap.xml', 'w') as f:
    f.write(sitemap_xml)

robots_txt = f'''User-agent: *
Allow: /

Sitemap: {DOMAIN}/sitemap.xml
'''
with open('/home/claude/site/robots.txt', 'w') as f:
    f.write(robots_txt)

print(f"Built sitemap.xml ({len(sitemap_urls)} URLs) + robots.txt")

# ============================================================
# Hub / region pages — density-gated. Only super-regions with
# enough real volume get a page; thin regions stay folded into
# the full listings table rather than publishing a near-empty
# page. Threshold and grouping both come from the live data, not
# a hand-picked list, so this stays correct as the dataset grows.
# ============================================================
HUB_MIN_DEALS = 15

hub_groups = {}
for d in graded:
    super_region = d['region'].split(' (')[0]
    hub_groups.setdefault(super_region, []).append(d)

hub_pages = []  # (name, slug, deals) for qualifying regions
for name, deals in hub_groups.items():
    if name == 'Region withheld':
        continue  # not a real region — don't build a hub page for "unknown"
    if len(deals) >= HUB_MIN_DEALS:
        slug = slugify(name)
        hub_pages.append((name, slug, deals))
hub_pages.sort(key=lambda x: -len(x[2]))

def hub_json_ld(name, slug, deals, url):
    payload = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": f"{name} {CATEGORY_NAME} Businesses for Sale",
        "description": f"{len(deals)} {CATEGORY_NAME} businesses for sale in {name}, graded by stressed DSCR against standardized SBA 7(a) underwriting.",
        "url": url,
        "mainEntity": {
            "@type": "ItemList",
            "numberOfItems": len(deals),
            "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "url": f"{DOMAIN}/deal-{d['slug']}.html"}
                for i, d in enumerate(deals)
            ]
        }
    }
    return json.dumps(payload, indent=2)

HUB_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{name} {category} Businesses for Sale — Graded for SBA Financing | Bizvetting</title>
<meta name="description" content="{meta_description}">
<link rel="canonical" href="{canonical_url}">
<meta property="og:type" content="website">
<meta property="og:title" content="{name} {category} Businesses for Sale — Graded for SBA Financing">
<meta property="og:description" content="{meta_description}">
<meta property="og:url" content="{canonical_url}">
{font_link}
<style>
{css}
</style>
<script type="application/ld+json">
{json_ld}
</script>
</head>
<body>
{header}
<div class="batch-banner wrap">
  <div class="hero-eyebrow">Region — Cycle 2026.08</div>
  <h1 class="batch-title">{name} {category} Businesses, Graded for SBA Financing</h1>
  <p class="batch-sub">{n_deals} {category} businesses for sale in {name}, run through the same SBA 7(a) underwriting math as every other listing and graded against the full current batch — not just against each other. {n_a} Grade A · {n_b} Grade B · {n_c} Grade C.</p>
</div>
<div class="ledger wrap">
  <div class="ledger-panel">
  <table class="ledger-table">
    <thead><tr><th></th><th>Business</th><th>Asking price</th><th>SDE multiple</th><th>DSCR — stated → stressed</th><th>To hit 1.25x</th></tr></thead>
    <tbody>
      {rows}
    </tbody>
  </table>
  </div>
  <p class="fine-print" style="margin-top:20px;"><a href="listings.html">See the full national list →</a></p>
  {sponsor_module}
</div>
{footer}
</body>
</html>'''

hub_nav_links = []
for name, slug, deals in hub_pages:
    n_a = sum(1 for d in deals if d['grade'] == 'A')
    n_b = sum(1 for d in deals if d['grade'] == 'B')
    n_c = sum(1 for d in deals if d['grade'] == 'C')
    rows = []
    for d in sorted(deals, key=lambda x: -x['dscr_stressed']):
        rows.append(f'''<tr>
  <td style="width:52px;">{tag_svg(d['grade'], 40, 52)}</td>
  <td class="deal-title-cell"><a href="deal-{d['slug']}.html">{deal_short_label(d)}</a><span class="deal-meta">{d['region']}</span></td>
  <td class="num-cell">{d['price_band']}</td>
  <td class="num-cell">{d['sde_multiple']}x</td>
  <td class="dscr-pair">{d['dscr_as_stated']} <span class="arrow">→</span> <span class="stressed">{d['dscr_stressed']}</span></td>
  <td class="num-cell">{band_discount(d['discount_needed_pct'])}</td>
</tr>''')
    hub_url = f"{DOMAIN}/hub-{slug}.html"
    meta_desc = (f"{len(deals)} {CATEGORY_NAME} businesses for sale in {name}, Grade A/B/C "
                 f"({n_a}/{n_b}/{n_c}), graded by stressed DSCR against standardized SBA 7(a) "
                 f"underwriting. Free, no signup required.")
    html = HUB_TEMPLATE.format(
        name=name, category=CATEGORY_NAME, n_deals=len(deals),
        n_a=n_a, n_b=n_b, n_c=n_c, rows="".join(rows),
        meta_description=meta_desc, canonical_url=hub_url,
        json_ld=hub_json_ld(name, slug, deals, hub_url),
        font_link=FONT_LINK, header=header(), footer=footer(), css=CSS_INLINE,
        sponsor_module=SPONSOR_MODULE
    )
    with open(f"/home/claude/site/hub-{slug}.html", 'w') as f:
        f.write(html)
    hub_nav_links.append((name, slug, len(deals)))

# Wire hub pages into the full listings page so they're discoverable,
# not orphaned pages nothing links to.
browse_by_region = "".join(
    f'<a href="hub-{slug}.html" class="region-chip">{name} <span>({n})</span></a>'
    for name, slug, n in hub_nav_links
)
with open('/home/claude/site/listings.html') as f:
    listings_content = f.read()
region_block = f'<div class="region-browse wrap"><span class="hero-eyebrow" style="margin-bottom:10px;">Browse by Region</span><div class="region-chips">{browse_by_region}</div></div>'
listings_content = listings_content.replace('<div class="ledger wrap">', region_block + '\n<div class="ledger wrap">', 1)
with open('/home/claude/site/listings.html', 'w') as f:
    f.write(listings_content)

# Add hub pages to the sitemap (regenerate it including these new URLs)
sitemap_urls += [(f"{DOMAIN}/hub-{slug}.html", "weekly", "0.8") for _, slug, _ in hub_pages]
sitemap_entries = "\n".join(
    f"  <url>\n    <loc>{url}</loc>\n    <lastmod>{today}</lastmod>\n"
    f"    <changefreq>{freq}</changefreq>\n    <priority>{pri}</priority>\n  </url>"
    for url, freq, pri in sitemap_urls
)
sitemap_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{sitemap_entries}
</urlset>'''
with open('/home/claude/site/sitemap.xml', 'w') as f:
    f.write(sitemap_xml)

print(f"Built {len(hub_pages)} hub pages: {[f'{n} ({c})' for n, s, c in hub_nav_links]}")
print(f"Sitemap updated to {len(sitemap_urls)} URLs")
