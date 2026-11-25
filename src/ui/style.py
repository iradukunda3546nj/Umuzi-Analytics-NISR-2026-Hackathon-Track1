"""Page styles for Umuzi Analytics. One stylesheet, injected once per run.

Animations: cards rise in, the target arrow is drawn and its head flies to the
district's position, input bars grow, the "Why?" button pulses. All of it is
switched off for users who ask their system for reduced motion.
"""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&display=swap');
:root { --ever:#24493f; --ever-2:#2f6152; --ink:#1f2421; --ink-2:#55595a; --ink-3:#7b7f7f;
        --line:#dcdcd5; --card:#ffffff; --red:#9c3d24; --sun:#f2b632; --paper:#f6f5f0; }
[data-testid="stHeader"] {background: transparent;}
.block-container, [data-testid="stMainBlockContainer"] {padding-top: 3.2rem; padding-bottom: 2.5rem; max-width: 1320px;}

/* ---------- top bar */
.umz-brand {display:flex; align-items:center; gap:10px; font-weight:800; font-size:20px; color:var(--ever);
            letter-spacing:.2px; padding-top:4px;}
.umz-brand small {font-weight:500; color:var(--ink-2); font-size:12.5px;}
.st-key-nav button {border-radius:999px; padding:2px 14px; min-height:36px;}
.st-key-nav button p {font-size:14px;}

/* ---------- landing */
.umz-hero {text-align:center; padding: 4vh 0 1vh 0;}
.umz-hero h1 {font-family:'DM Serif Display', Georgia, serif; font-weight:400; font-size:clamp(44px, 7vw, 86px);
              line-height:1.0; margin:0; color:#13302a; letter-spacing:.5px;}
.umz-hero h1 span {color:var(--ever-2);}
.umz-hero .umz-q {font-size:clamp(20px, 2.4vw, 27px); font-weight:700; color:#13302a; margin:18px auto 0 auto;
              max-width:820px; line-height:1.3;}
.umz-hero p {font-size:clamp(16px, 1.8vw, 20px); color:#1f2421; margin:10px auto 0 auto; max-width:760px; line-height:1.45;}
.umz-hero p b {color:var(--ever);}
.umz-hooks {display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:16px; margin:28px 0 10px 0;}
.umz-hook {background:rgba(255,255,255,.93); border-radius:16px; padding:20px 18px; box-shadow:0 8px 28px rgba(16,40,32,.16);
           animation: umz-rise .7s cubic-bezier(.2,.7,.2,1) both; backdrop-filter: blur(4px);}
.umz-hook-top {display:flex; align-items:center; justify-content:space-between; margin-bottom:12px;}
.umz-hook-ic {width:52px; height:52px; border-radius:50%; background:#e7efe9; color:var(--ever);
              display:flex; align-items:center; justify-content:center;}
.umz-hook-k {font-size:12px; font-weight:800; letter-spacing:1.6px; background:var(--sun); color:#1f2421;
             border-radius:999px; padding:3px 11px;}
.umz-hook-t {font-size:19px; font-weight:700; color:var(--ink); line-height:1.25;}
.umz-hook-l {font-size:14.5px; color:var(--ink-2); margin-top:6px; line-height:1.4;}
.umz-stats {display:flex; flex-wrap:wrap; justify-content:center; gap:10px 34px; margin:18px auto 6px auto;
            background:rgba(19,48,42,.86); color:#fff; border-radius:999px; padding:10px 28px; width:fit-content;
            animation: umz-rise .7s .55s both;}
.umz-stats div {display:flex; align-items:baseline; gap:7px;}
.umz-stats b {font-size:22px;} .umz-stats span {font-size:13.5px; opacity:.9;}
.umz-flow {display:flex; flex-wrap:wrap; justify-content:center; align-items:center; gap:8px; margin:18px 0 4px 0;
           animation: umz-rise .7s .7s both;}
.umz-flow-step {display:inline-flex; align-items:center; gap:7px; background:#fff; border-radius:999px;
                padding:7px 14px; font-size:14.5px; font-weight:600; color:var(--ink); box-shadow:0 3px 12px rgba(16,40,32,.12);}
.umz-flow-step .umz-ic {color:var(--ever);}
.umz-flow-arrow {color:#fff; filter: drop-shadow(0 1px 2px rgba(0,0,0,.5));}
.umz-who {text-align:center; font-size:13.5px; color:#1f2421; margin-top:14px;}
.st-key-cta_explore button {background:var(--ever); color:#fff; border:none; border-radius:999px; font-size:18px;
           padding:12px 30px; box-shadow:0 8px 22px rgba(36,73,63,.35); animation: umz-pulse 2.6s 1.4s infinite;}
.st-key-cta_explore button:hover {background:var(--ever-2); color:#fff;}
.st-key-cta_explore button p {font-size:18px; font-weight:700;}
.st-key-cta_ask button p {font-size:16px; font-weight:600;}
.st-key-cta_ask button {border-radius:999px; font-size:16px; padding:11px 24px; background:rgba(255,255,255,.95);}

/* ---------- shared card pieces */
.umz-card {background:var(--card); border:1px solid var(--line); border-radius:16px; padding:18px 20px;
           box-shadow:0 4px 18px rgba(16,40,32,.07); animation: umz-rise .55s cubic-bezier(.2,.7,.2,1) both;}
.umz-kicker {font-size:12px; letter-spacing:.8px; text-transform:uppercase; color:var(--ink-3); font-weight:600;}
.umz-big {font-size:30px; font-weight:800; color:var(--ink); line-height:1.15; margin:4px 0 2px 0;}
.umz-sub {font-size:15px; color:var(--ink-2);}
.umz-chip {display:inline-block; padding:4px 12px; border-radius:999px; font-size:13px; font-weight:700;
           border:1px solid rgba(0,0,0,.18);}
.umz-step {display:flex; align-items:center; gap:10px; font-size:18px; font-weight:800; color:var(--ink); margin-bottom:10px;}
.umz-step-n {width:30px; height:30px; border-radius:50%; background:var(--ever); color:#fff; font-size:15px;
             display:flex; align-items:center; justify-content:center;}
.umz-line {font-size:15px; color:var(--ink); margin-top:10px;}
.umz-fine {font-size:12px; color:var(--ink-3); margin-top:8px;}
.umz-warn {font-size:13px; background:#fbf0dc; border:1px solid #e6c88f; padding:6px 10px; border-radius:8px; margin-bottom:8px;}

/* ---------- target arrow */
.umz-target-svg {display:block; max-width:640px; margin:0 auto;}
.umz-shaft {stroke-dasharray: var(--len); stroke-dashoffset: var(--len); animation: umz-draw 1.1s .2s ease-out forwards;}
.umz-head {animation: umz-fly 1.1s .2s ease-out both;}
.umz-bull {transform-box: fill-box; transform-origin: center; animation: umz-thud .5s 1.25s ease-out both;}

/* ---------- legend chips */
.umz-legs {display:flex; flex-wrap:wrap; gap:6px 14px; margin-top:4px;}
.umz-leg {display:inline-flex; align-items:center; gap:6px; font-size:12.5px; color:var(--ink-2);}
.umz-leg b {color:var(--ink);}
.umz-leg-sel {color:var(--ink); font-weight:700;}
.umz-sw {width:13px; height:13px; border-radius:3px; border:1px solid #6b6f6c; display:inline-block;}

/* ---------- survey tiles */
.umz-tiles {display:flex; gap:8px;}
.umz-tile {flex:1; border-radius:12px; padding:10px 6px; text-align:center; border:1px solid rgba(0,0,0,.1);
           animation: umz-pop .45s cubic-bezier(.2,.9,.3,1.3) both;}
.umz-tile-rel {font-size:12px; margin-top:2px;} .umz-tile-val {font-size:22px; font-weight:800; line-height:1.15;}
.umz-tile-lab {font-size:11.5px;}

/* ---------- why button */
.st-key-why_btn button {width:100%; border-radius:16px; border:2px dashed var(--ever); background:#eef4f0;
           color:var(--ever); font-size:19px; font-weight:800; padding:14px 10px; animation: umz-pulse 2.4s 1.6s infinite;}
.st-key-why_btn button:hover {background:var(--ever); color:#fff; border-style:solid;}
.st-key-why_btn button p {font-size:19px; font-weight:800;}
.st-key-why_btn button [data-testid="stIconMaterial"] {font-size:28px;}

/* ---------- inputs */
.umz-inp {display:flex; gap:14px; align-items:center; padding:10px 0; border-bottom:1px dashed var(--line);}
.umz-inp-ic {width:54px; height:54px; border-radius:14px; background:#f3f3ee; display:flex; align-items:center;
             justify-content:center; flex:0 0 54px;}
.umz-inp-body {flex:1;}
.umz-inp-name {font-size:16px; font-weight:700; color:var(--ink); margin-bottom:4px;}
.umz-inp-word {font-size:13px; font-weight:700; margin-left:6px;}
.umz-inp-note {font-size:13px; color:var(--ink-3);}
.umz-bar {display:flex; align-items:center; gap:8px; font-size:13px; margin:3px 0;}
.umz-bar-lab {width:118px; flex:0 0 118px; color:var(--ink-2); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;}
.umz-bar-track {flex:1; height:12px; background:#efefea; border-radius:6px; overflow:hidden;}
.umz-bar-fill {display:block; height:100%; border-radius:6px; transform-origin:left; animation: umz-grow 1s ease-out both;}
.umz-bar b {width:38px; text-align:right;}

/* ---------- verdict + action */
.umz-verdict {display:flex; gap:14px; align-items:center;}
.umz-verdict-ic {flex:0 0 64px; height:64px; border-radius:50%; background:#f3f3ee; display:flex; align-items:center; justify-content:center;}
.umz-verdict-t {font-size:19px; font-weight:800; color:var(--ink); line-height:1.25;}
.umz-verdict-l {font-size:15px; color:var(--ink-2); margin-top:4px;}
.umz-action {background:#fff7dd; border:2px solid var(--sun); border-radius:16px; padding:16px 20px;
             animation: umz-rise .55s .25s both;}
.umz-action-head {display:flex; gap:12px; align-items:center;}
.umz-action-ic {width:52px; height:52px; border-radius:50%; background:var(--sun); color:#1f2421; display:flex;
                align-items:center; justify-content:center; transform:rotate(-12deg);}
.umz-action-t {font-size:22px; font-weight:900; letter-spacing:.5px; text-transform:uppercase; color:#1f2421;}
.umz-action-s {font-size:14px; color:var(--ink-2);}
.umz-checks {list-style:none; padding:0; margin:12px 0 0 0;}
.umz-checks li {display:flex; gap:10px; align-items:center; font-size:15.5px; color:var(--ink); padding:7px 0;
                border-top:1px solid #f0e2b4; animation: umz-rise .4s both;}
.umz-checks li span {color:#8a6400; display:flex;}

/* ---------- assistant */
.umz-chat-note {text-align:center; font-size:12.5px; color:var(--ink-3); margin:10px 0; display:flex;
                 align-items:center; gap:10px;}
.umz-chat-note::before, .umz-chat-note::after {content:""; flex:1; border-top:1px solid var(--line);}
.umz-ask-head {display:flex; align-items:center; gap:10px; font-size:18px; font-weight:800; color:var(--ink);}
[class*="st-key-sugg_"] button {border-radius:999px; font-size:13px; padding:3px 12px; min-height:30px;
           background:#eef4f0; border:1px solid #cfe0d5; color:var(--ever);}

@keyframes umz-rise {from {opacity:0; transform: translateY(14px);} to {opacity:1; transform:none;}}
@keyframes umz-pop {from {opacity:0; transform: scale(.85);} to {opacity:1; transform:none;}}
@keyframes umz-draw {to {stroke-dashoffset: 0;}}
@keyframes umz-fly {from {transform: translateX(var(--from)); opacity:.2;} to {transform:none; opacity:1;}}
@keyframes umz-thud {0% {transform: scale(1);} 40% {transform: scale(1.12);} 100% {transform: scale(1);}}
@keyframes umz-grow {from {transform: scaleX(0);} to {transform: scaleX(1);}}
@keyframes umz-pulse {0%,100% {box-shadow:0 0 0 0 rgba(36,73,63,.35);} 50% {box-shadow:0 0 0 10px rgba(36,73,63,0);}}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {animation: none !important;}
  .umz-shaft {stroke-dashoffset: 0;}
}
</style>
"""


def background_css(b64_jpeg: str) -> str:
    """Landing-page photo behind a light veil, so white cards and dark text stay readable."""
    return (f"<style>.stApp {{background: linear-gradient(180deg, rgba(246,245,240,.80) 0%, rgba(246,245,240,.55) 45%, "
            f"rgba(246,245,240,.82) 100%), url('data:image/jpeg;base64,{b64_jpeg}') center/cover fixed;}}</style>")
