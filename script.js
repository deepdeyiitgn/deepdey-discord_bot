// =======================
// Device Detection & Vibe
// =======================
function isMobile() {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

document.body.classList.add(isMobile() ? 'mobile-vibe' : 'desktop-vibe');

// =======================
// Mobile Navbar Toggle
// =======================
const menuToggle = document.querySelector('.menu-toggle');
const navLinks = document.querySelector('.navbar ul');
if (menuToggle && navLinks) {
  menuToggle.addEventListener('click', () => {
    navLinks.classList.toggle('active');
  });
}

// =======================
// Smooth Scroll for Navigation
// =======================
document.querySelectorAll('.navbar ul li a').forEach(link => {
  link.addEventListener('click', (e) => {
    e.preventDefault();
    const targetId = link.getAttribute('href');
    const targetElement = document.querySelector(targetId);
    if(targetElement) {
      targetElement.scrollIntoView({ behavior: 'smooth', block: isMobile() ? 'start' : 'center' });
    } else {
      window.location.href = targetId;
    }
    if(navLinks.classList.contains('active')) navLinks.classList.remove('active');
  });
});

// =======================
// Button Hover & Tap Animation
// =======================
const buttons = document.querySelectorAll('.btn');
buttons.forEach(button => {
  if (isMobile()) {
    button.addEventListener('touchstart', () => {
      button.style.transform = 'scale(0.97)';
      button.style.boxShadow = '0 2px 12px #ffd60a';
    });
    button.addEventListener('touchend', () => {
      button.style.transform = 'scale(1)';
      button.style.boxShadow = '';
    });
  } else {
    button.addEventListener('mouseenter', () => {
      button.style.transform = 'scale(1.07)';
      button.style.boxShadow = '0 8px 32px #3a0ca3';
    });
    button.addEventListener('mouseleave', () => {
      button.style.transform = 'scale(1)';
      button.style.boxShadow = '';
    });
  }
});

// =======================
// Section Fade-in Animation
// =======================
const sections = document.querySelectorAll('.section, .hero, .about-hero, .blog-hero, .contact-hero, .portfolio-hero');
const fadeInOnScroll = new IntersectionObserver((entries, observer) => {
  entries.forEach(entry => {
    if(entry.isIntersecting) {
      entry.target.classList.add('fade-in');
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.15 });

sections.forEach(section => {
  section.classList.add('pre-fade');
  fadeInOnScroll.observe(section);
});

// =======================
// Desktop Parallax Blobs
// =======================
if (!isMobile()) {
  const blobs = document.querySelectorAll('.bg-blob');
  let mouseX = 0, mouseY = 0, animating = false;
  window.addEventListener('mousemove', throttle((e) => {
    mouseX = (e.clientX / window.innerWidth - 0.5) * 20;
    mouseY = (e.clientY / window.innerHeight - 0.5) * 20;
    if (!animating) {
      animating = true;
      requestAnimationFrame(() => {
        blobs.forEach((blob, i) => {
          blob.style.transform = `translate(${mouseX*(i+1)}px, ${mouseY*(i+1)}px)`;
        });
        animating = false;
      });
    }
  }, 16));
}

// =======================
// Reduce motion for accessibility
// =======================
if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
  document.body.classList.add('reduced-motion');
  const style = document.createElement('style');
  style.innerHTML = '* { transition: none !important; animation: none !important; }';
  document.head.appendChild(style);
}

// =======================
// Lazy load images
// =======================
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('img[loading="lazy"]').forEach(img => {
    if(img.dataset.src) img.src = img.dataset.src;
  });
});

// =======================
// Lag-free Preloader for Popup & Background
// =======================
(() => {
  const bg16by9 = 'https://i.postimg.cc/L5gHK74n/winter-wonderland-illustration-wallpaper-3840x2160.jpg';
  const bgDefault = 'https://i.postimg.cc/KvFM9ZvR/blue-maximalist-winter-wonderland-background-design-template-56b30f8eef163e2075a3407fca8bf413-screen.jpg';

  function chooseBg() {
    // choose high-res when display aspect is roughly 16:9 (tolerance)
    const ratio = window.innerWidth / window.innerHeight;
    if (Math.abs(ratio - (16/9)) < 0.06) return bg16by9;
    return bgDefault;
  }

  function setBodyBg(url) {
    try {
      document.documentElement.style.setProperty('--body-bg-url', `url(${url})`);
      // apply to body::before by adding a small style node
      let s = document.getElementById('body-bg-style');
      if (!s) {
        s = document.createElement('style');
        s.id = 'body-bg-style';
        document.head.appendChild(s);
      }
      s.innerHTML = `body::before { background-image: url(${JSON.stringify(url)}); }`;
    } catch (e) { /* ignore */ }
  }

  function preloadImage(url) {
    return new Promise((res) => {
      const img = new Image();
      img.src = url;
      img.onload = img.onerror = () => res();
    });
  }

  async function warmup() {
    const chosen = chooseBg();
    // set faded background immediately (will load progressively)
    setBodyBg(chosen);
    // preload both images (so swap is fast if needed)
    await Promise.all([preloadImage(bgDefault), preloadImage(bg16by9)]);

    // Warm popup elements by creating off-screen element and removing it
    try {
      const temp = document.createElement('div');
      temp.style.position = 'fixed';
      temp.style.left = '-9999px';
      temp.style.top = '-9999px';
      temp.style.width = '200px';
      temp.style.height = '200px';
      temp.innerHTML = document.querySelector('.diwali-popup-content') ? '' : `
        <div class="diwali-popup-content"><div class="diya-container"></div></div>`;
      document.body.appendChild(temp);
      // force style/layout read
      void temp.offsetHeight;
      setTimeout(() => temp.remove(), 80);
    } catch (e) { /* ignore */ }
  }

  window.addEventListener('load', () => {
    // run warmup shortly after load to avoid competing with critical paint
    setTimeout(warmup, 600);
  });
})();

// =======================
// Throttle & Debounce Utilities
// =======================
function throttle(fn, wait) {
  let lastTime = 0;
  return function(...args) {
    const now = Date.now();
    if(now - lastTime >= wait) {
      lastTime = now;
      fn.apply(this, args);
    }
  };
}

function debounce(fn, delay) {
  let timer = null;
  return function(...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

// =======================
// Blockers (Ctrl Keys & Right Click)
// =======================
document.addEventListener('keydown', (e) => {
  const blockedKeys = ['a','c','v','x','u'];
  if(e.ctrlKey && blockedKeys.includes(e.key.toLowerCase())) {
    e.preventDefault();
    const alertDiv = document.createElement('div');
    alertDiv.textContent = `🚫 Ctrl+${e.key.toUpperCase()} is blocked!`;
    Object.assign(alertDiv.style, {
      position: 'fixed', top: '20px', right: '20px', background: 'rgba(255,0,0,0.9)',
      color: '#fff', padding: '10px 15px', borderRadius: '5px', fontFamily: 'Arial, sans-serif',
      zIndex: 9999, boxShadow: '0 0 10px rgba(0,0,0,0.5)', transition: 'opacity 0.5s'
    });
    document.body.appendChild(alertDiv);
    setTimeout(() => { alertDiv.style.opacity = '0'; setTimeout(()=>alertDiv.remove(),500); }, 1500);
  }
});
document.addEventListener('contextmenu', e => e.preventDefault());

// =======================
// Favicon Setup
// =======================
(function() {
  let link = document.querySelector("link[rel~='icon']");
  if (!link) {
    link = document.createElement("link");
    link.rel = "icon";
    link.type = "image/png";
    document.head.appendChild(link);
  }
  link.href = "https://www.deepdeyiitk.com/web/image/website/1/favicon?unique=e5fe8cd";
})();


// =======================
// Typed Text Animation
// =======================
const typedText = ["JEE Aspirant 2027","Creator","Web Developer","Loyal"];
let index = 0, charIndex = 0;
const typedEl = document.querySelector('.typed');
function type() {
  if(!typedEl) return;
  typedEl.textContent = typedText[index].slice(0,charIndex++);
  if(charIndex>typedText[index].length){ charIndex=0; index=(index+1)%typedText.length; setTimeout(type,1000);}
  else setTimeout(type,150);
}
type();

// =======================
// Animated Counters
// =======================
document.querySelectorAll('.counter').forEach(counter=>{
  const updateCount=()=>{
    const target=+counter.dataset.target;
    const count=+counter.innerText;
    const increment=target/200;
    if(count<target){ counter.innerText=Math.ceil(count+increment); setTimeout(updateCount,20); }
    else counter.innerText=target;
  };
  updateCount();
});

// =======================
// Live Date & Clock (Navbar Desktop, Footer Mobile)
// =======================
(function(){
  const navbar = document.querySelector('.navbar');
  const clockFooter = document.getElementById('footerClock');

  const clockDesktop = document.createElement('div');
  clockDesktop.id = 'navbarClock';
  navbar?.appendChild(clockDesktop);

  function updateClock(){
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth()+1).padStart(2,'0');
    const date = String(now.getDate()).padStart(2,'0');
    const dayNames = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];
    const day = dayNames[now.getDay()];

    let hours = now.getHours();
    const minutes = String(now.getMinutes()).padStart(2,'0');
    const seconds = String(now.getSeconds()).padStart(2,'0');
    const ampm = hours>=12?'PM':'AM';
    hours = hours%12||12;
    hours = String(hours).padStart(2,'0');

    const clockStr = `${year}/${month}/${date} ${day} || ${hours}:${minutes}:${seconds} ${ampm}`;
    if(clockDesktop) clockDesktop.textContent = clockStr;
    if(clockFooter) clockFooter.textContent = clockStr;
  }

  function adjustClockDisplay(){
    if(window.innerWidth<=768){
      clockDesktop && (clockDesktop.style.display='none');
      clockFooter && (clockFooter.style.display='block');
    }else{
      clockDesktop && (clockDesktop.style.display='block');
      clockFooter && (clockFooter.style.display='none');
    }
  }

  updateClock();
  adjustClockDisplay();
  setInterval(updateClock,1000);
  window.addEventListener('resize', adjustClockDisplay);

  // Styling
  if(clockDesktop){
    Object.assign(clockDesktop.style,{
      fontSize:'1.3rem', fontWeight:'600', color:'#ffd60a', fontFamily:'monospace', marginLeft:'auto', whiteSpace:'nowrap'
    });
  }
  if(clockFooter){
    Object.assign(clockFooter.style,{
      fontSize:'1.2rem', fontWeight:'500', color:'#ffd60a', fontFamily:'monospace', textAlign:'center', marginTop:'12px'
    });
  }
})();

// =======================
// Dark / Light Mode Toggle
// =======================
const toggleBtn = document.createElement('button');
toggleBtn.textContent = '🌓 Beta';
toggleBtn.id = 'themeToggle';
Object.assign(toggleBtn.style,{
  position:'fixed', bottom:'20px', left:'20px', padding:'10px 16px',
  background:'#3a0ca3', color:'#ffd60a', border:'none', borderRadius:'8px',
  fontSize:'0.95rem', fontWeight:'600', cursor:'pointer', boxShadow:'0 4px 12px rgba(0,0,0,0.3)',
  transition:'all 0.3s ease'
});
toggleBtn.addEventListener('mouseenter', ()=>{ toggleBtn.style.transform='scale(1.05)'; toggleBtn.style.boxShadow='0 6px 16px rgba(0,0,0,0.4)'; });
toggleBtn.addEventListener('mouseleave', ()=>{ toggleBtn.style.transform='scale(1)'; toggleBtn.style.boxShadow='0 4px 12px rgba(0,0,0,0.3)'; });
document.body.appendChild(toggleBtn);

toggleBtn.addEventListener('click', () => {
  document.body.classList.toggle('dark-mode');
});

// =======================
// Navbar Logo + Deep Dey Centered
// =======================
(function(){
  const navbar = document.querySelector('.navbar');
  if(!navbar) return;

  // Remove old logo if exists
  navbar.querySelector('.logo-container')?.remove();

  const logoContainer = document.createElement('div');
  logoContainer.className = 'logo-container';
  Object.assign(logoContainer.style,{
    display:'flex', alignItems:'center', justifyContent:'center', gap:'12px', margin:'0 auto'
  });

  const logoImg = document.createElement('img');
  logoImg.src = "https://www.deepdeyiitk.com/web/image/website/1/favicon?unique=e5fe8cd";
  logoImg.alt = "Deep Dey Logo";
  logoImg.style.width = '36px';
  logoImg.style.height = '36px';

  const logoLink = document.createElement('a');
  logoLink.href = "https://apps.deepdeyiitk.com/";
  logoLink.textContent = "Deep Dey";
  Object.assign(logoLink.style,{
    textDecoration:'none', color:'#3a0ca3', fontWeight:'700', fontSize:'1.8rem'
  });

  logoContainer.appendChild(logoImg);
  logoContainer.appendChild(logoLink);
  navbar.insertBefore(logoContainer, navbar.firstChild);
})();

// =======================
// Persistent Background Music
// =======================

const MUSIC_FILE = "background.mp3"; // same folder as script
const MUSIC_KEY = "bg-music-time";

// Create audio element if not already created
if (!window.bgMusic) {
  window.bgMusic = new Audio(`./${MUSIC_FILE}`);
  window.bgMusic.volume = 0.7;
  window.bgMusic.loop = true;

  // Resume from saved time
  const savedTime = localStorage.getItem(MUSIC_KEY);
  if (savedTime) {
    window.bgMusic.currentTime = parseFloat(savedTime);
  }

  // Save current time before leaving page
  window.addEventListener("beforeunload", () => {
    localStorage.setItem(MUSIC_KEY, window.bgMusic.currentTime);
  });

  // Try autoplay after user interaction
  const startMusic = () => {
    window.bgMusic.play().catch(() => {
      console.log("Autoplay blocked, waiting for user action.");
    });
    document.removeEventListener("click", startMusic);
    document.removeEventListener("keydown", startMusic);
  };

  document.addEventListener("click", startMusic);
  document.addEventListener("keydown", startMusic);
}

// =======================
// ✅ Auto-inject Open Graph Meta Tags for StudyBot (Deep Dey)
// =======================
(function() {
  const head = document.querySelector("head");

  const metaTags = [
    { property: "og:type", content: "website" },
    { property: "og:title", content: "StudyBot — Your Study Companion • Deep Dey" },
    { property: "og:site_name", content: "Deep Dey - The FUTURE IITIAN 🎯" },
    { property: "og:url", content: "https://bots.deepdeyiitk.com/" },
    { property: "og:image", content: "https://i.postimg.cc/YSV9JqBD/Neon-Green-Circle-Frame-Fitness-You-Tube-Profile-Picturedurga-puja.png" },
    { property: "og:description", content: "📘 StudyBot — the AI-powered Discord companion built by Deep Dey to boost discipline, focus, and consistency for JEE 2027 aspirants. Track uptime, check productivity, and stay accountable 24×7. Made with 🩷 and vision for IIT Kanpur." }
  ];

  metaTags.forEach(tagData => {
    // Check if same OG tag already exists
    if (!document.querySelector(`meta[property="${tagData.property}"]`)) {
      const tag = document.createElement("meta");
      tag.setAttribute("property", tagData.property);
      tag.setAttribute("content", tagData.content);
      head.appendChild(tag);
    }
  });

  console.log("✅ OG meta tags injected for StudyBot — Deep Dey");
})();

