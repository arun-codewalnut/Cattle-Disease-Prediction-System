import { useState } from 'react'

export const MAX_IMAGES = 5

export default function ImageUploadForm({ images, onImagesChange, onSubmit, disabled }) {
  // Set when a selection was larger than the remaining room. The alternative — silently
  // keeping the first few — loses photos the user thought they'd attached.
  const [skippedNotice, setSkippedNotice] = useState(null)

  function handleSubmit(event) {
    event.preventDefault()
    onSubmit()
  }

  // One `multiple` input replaces the five single-file slots this form used to render: the
  // browser's own picker already takes several files at once, so the slots were five ways to
  // do one thing. Selections append rather than replace, so adding more in a second pick
  // still works, as does removing one and picking it again.
  function handleFilesSelected(event) {
    const selected = Array.from(event.target.files ?? [])
    const room = MAX_IMAGES - images.length
    const accepted = selected.slice(0, room)
    const skipped = selected.length - accepted.length

    if (accepted.length > 0) {
      onImagesChange([...images, ...accepted])
    }
    setSkippedNotice(
      skipped > 0
        ? `${skipped} photo${skipped > 1 ? 's' : ''} not added — ${MAX_IMAGES} per diagnosis is the limit.`
        : null
    )

    // Reset so selecting the same file again (after removing it) still fires onChange.
    event.target.value = ''
  }

  function handleRemove(index) {
    onImagesChange(images.filter((_, i) => i !== index))
    setSkippedNotice(null)
  }

  const isFull = images.length >= MAX_IMAGES

  return (
    <form onSubmit={handleSubmit} className="image-upload-form">
      <div>
        <p className="image-upload-form__label">
          <span aria-hidden="true">📷 </span>
          Or upload photos instead — up to {MAX_IMAGES}, selectable in one go
        </p>

        <label className={`photo-picker${isFull ? ' photo-picker--full' : ''}`}>
          <span className="photo-picker__icon" aria-hidden="true">
            {isFull ? '✓' : '+'}
          </span>
          <span className="photo-picker__text">
            {isFull
              ? `Maximum ${MAX_IMAGES} photos selected`
              : images.length === 0
                ? 'Choose photos'
                : 'Add more photos'}
          </span>
          <input
            type="file"
            className="photo-tray__input"
            aria-label="Add photos"
            accept="image/jpeg,image/png"
            multiple
            onChange={handleFilesSelected}
            disabled={disabled || isFull}
          />
        </label>

        {images.length > 0 && (
          <div className="photo-tray">
            {images.map((file, index) => (
              <div key={`${file.name}-${index}`} className="photo-tray__slot photo-tray__slot--filled">
                <span className="photo-tray__icon" aria-hidden="true">
                  📷
                </span>
                <span className="photo-tray__filename">{file.name}</span>
                <button
                  type="button"
                  className="photo-tray__remove"
                  aria-label={`Remove ${file.name}`}
                  onClick={() => handleRemove(index)}
                  disabled={disabled}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}

        {images.length > 0 && (
          <p className="image-upload-form__count">
            {images.length} of {MAX_IMAGES} selected
          </p>
        )}

        {skippedNotice && (
          <p role="status" className="image-upload-form__notice">
            <span aria-hidden="true">⚠️</span> {skippedNotice}
          </p>
        )}
      </div>

      <button type="submit" disabled={disabled || images.length === 0}>
        {disabled ? (
          <>
            <span className="btn-spinner" aria-hidden="true" /> Submitting…
          </>
        ) : (
          `📷 Diagnose from ${images.length > 1 ? 'photos' : 'photo'}`
        )}
      </button>
    </form>
  )
}
