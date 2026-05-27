import type { PhotoRead } from '@/shared/api/types';

interface Props {
  photos: PhotoRead[];
  aspectRatio?: 'square' | 'video';
}

export function PhotoGallery({ photos, aspectRatio = 'square' }: Props) {
  if (photos.length === 0) {
    return (
      <div className="aspect-square w-full rounded-card bg-sand/40 flex items-center justify-center text-sienna-deep">
        <span>фото нет</span>
      </div>
    );
  }
  const ar = aspectRatio === 'video' ? 'aspect-video' : 'aspect-square';
  return (
    <div className="flex gap-2 overflow-x-auto snap-x snap-mandatory -mx-5 px-5 pb-1">
      {photos.map((p) => (
        <img
          key={p.id}
          src={p.url}
          alt=""
          loading="lazy"
          className={`snap-center shrink-0 w-72 ${ar} object-cover rounded-card border border-sand bg-sand/30`}
        />
      ))}
    </div>
  );
}
