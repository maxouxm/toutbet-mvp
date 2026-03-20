import { Download, FileText, X } from 'lucide-react';
import { useEffect, useRef } from 'react';
import { Button } from './Button';

export function PdfModal(props: { title: string; src: string; onClose: () => void }) {
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const onDown = (e: MouseEvent) => {
      if (!ref.current) return;
      if (e.target instanceof Node && !ref.current.contains(e.target)) props.onClose();
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') props.onClose();
    };
    window.addEventListener('mousedown', onDown);
    window.addEventListener('keydown', onKey);
    return () => {
      window.removeEventListener('mousedown', onDown);
      window.removeEventListener('keydown', onKey);
    };
  }, [props]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/70 tb-animate-in" />
      <div
        ref={ref}
        className="relative w-full max-w-2xl overflow-hidden rounded-3xl border border-white/10 bg-bg2/95 shadow-2xl backdrop-blur tb-animate-in"
      >
        <div className="flex items-center justify-between gap-3 border-b border-white/10 p-4">
          <div className="truncate text-sm font-extrabold text-white/90">{props.title}</div>
          <button
            className="rounded-xl p-2 text-white/60 hover:bg-white/5 hover:text-white"
            onClick={props.onClose}
            type="button"
            aria-label="Fermer"
          >
            <X />
          </button>
        </div>
        <div className="p-6">
          <div className="rounded-3xl border border-white/10 bg-black/20 p-6">
            <div className="flex items-start gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/15 text-primary">
                <FileText />
              </div>
              <div className="min-w-0">
                <div className="text-base font-extrabold">Document PDF</div>
                <div className="mt-1 text-sm text-white/60">
                  Télécharge les conditions d’utilisation pour les consulter, puis reviens terminer ton inscription.
                </div>
                <div className="mt-4">
                  <a href={props.src} download>
                    <Button>
                      <Download size={16} /> Télécharger
                    </Button>
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

