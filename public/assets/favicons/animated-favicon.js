/* Animated favicon loader for Chrome/modern browsers.
   Expects a frames-list JSON at /assets/favicons/frames-list.json
   which should be an array of absolute paths to PNG frames.
   The Python extraction script `scripts/extract_favicon_frames.py` will create it.
*/
(function(){
  async function init(){
    try{
      const res = await fetch('/assets/favicons/frames-list.json', {cache: 'no-store'});
      if(!res.ok) return;
      const frames = await res.json();
      if(!Array.isArray(frames) || frames.length === 0) return;

      // Preload images
      const imgs = await Promise.all(frames.map(src => new Promise((resolve) => {
        const im = new Image();
        im.onload = () => resolve(im);
        im.onerror = () => resolve(null);
        im.src = src + (src.includes('?') ? '&' : '?') + 'v=' + Date.now();
      })));

      const valid = imgs.filter(Boolean);
      if(valid.length === 0) return;

      let idx = 0;
      function setIcon(url){
        // remove any existing icon links to avoid multiple competing icons
        document.querySelectorAll("link[rel~='icon']").forEach(n => n.remove());
        const link = document.createElement('link');
        link.rel = 'icon';
        link.type = 'image/png';
        link.href = url;
        document.head.appendChild(link);
      }

      // initial
      setIcon(frames[0]);

      // animate: cycle through preloaded images using their original URLs
      const intervalMs = 3000; // adjust if you want faster/slower
      setInterval(() => {
        idx = (idx + 1) % frames.length;
        setIcon(frames[idx]);
      }, intervalMs);
    }catch(e){
      console.debug('animated-favicon error', e);
    }
  }
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
