import { useEffect, useRef } from 'react';

/** Decorative fluid field only; never receives clinical data. */
export function AmbientLava() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas?.getContext('2d');
    if (!canvas || !context) return;
    const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const colors = getComputedStyle(canvas);
    const green = colors.getPropertyValue('--ambient-green-rgb').trim().split(' ').map(Number);
    const blue = colors.getPropertyValue('--ambient-blue-rgb').trim().split(' ').map(Number);
    const width = 192;
    const height = 144;
    canvas.width = width;
    canvas.height = height;
    const image = context.createImageData(width, height);
    let frame = 0;
    let lastPaint = -Infinity;
    let elapsed = 0;
    let previous = 0;

    function paint(time: number) {
      const t = time / 10000;
      for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
          const u = x / width;
          const v = y / height;
          // Domain-warped flowing ribbons, not floating circles or particles.
          const warp = Math.sin(v * 7 - t) * .7 + Math.cos(u * 5 + t * .7) * .45;
          const field = Math.sin(u * 10 + warp * 2.8 + t * .8) + Math.cos(v * 7 - warp * 1.5 - t);
          const intensity = Math.pow(Math.max(0, Math.min(1, (field + .15) / 1.55)), 1.4);
          const blend = (Math.sin(u * 5 + v * 3 - t * .4) + 1) / 2;
          const index = (y * width + x) * 4;
          for (let channel = 0; channel < 3; channel++) {
            image.data[index + channel] = (green[channel] ?? 0) * (1 - blend) + (blue[channel] ?? 0) * blend;
          }
          image.data[index + 3] = intensity * 255;
        }
      }
      context?.putImageData(image, 0, 0);
    }

    function animate(now: number) {
      if (previous && !document.hidden) elapsed += Math.min(now - previous, 100);
      previous = now;
      if (!document.hidden && now - lastPaint > 80) {
        paint(elapsed);
        lastPaint = now;
      }
      frame = requestAnimationFrame(animate);
    }

    function updateMotion() {
      cancelAnimationFrame(frame);
      previous = 0;
      if (motion.matches) paint(0);
      else frame = requestAnimationFrame(animate);
    }
    updateMotion();
    motion.addEventListener('change', updateMotion);
    return () => {
      cancelAnimationFrame(frame);
      motion.removeEventListener('change', updateMotion);
    };
  }, []);

  return <canvas ref={canvasRef} className="ambient-lava" aria-hidden="true" />;
}