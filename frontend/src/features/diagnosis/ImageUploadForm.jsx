export const MAX_IMAGES = 5

export default function ImageUploadForm({ images, onImagesChange, onSubmit, disabled }) {
  function handleSubmit(event) {
    event.preventDefault()
    onSubmit()
  }

  function handleFileSelected(event) {
    const file = event.target.files?.[0]
    if (file && images.length < MAX_IMAGES) {
      onImagesChange([...images, file])
    }
    // Reset so selecting the same file again (after removing it) still fires onChange.
    event.target.value = ''
  }

  function handleRemove(index) {
    onImagesChange(images.filter((_, i) => i !== index))
  }

  return (
    <form onSubmit={handleSubmit} className="image-upload-form">
      <div>
        <p className="image-upload-form__label">
          <span aria-hidden="true">📷 </span>
          Or upload up to {MAX_IMAGES} photos instead
        </p>
        <div className="photo-tray">
          {Array.from({ length: MAX_IMAGES }, (_, index) => {
            const file = images[index]
            return file ? (
              <div key={index} className="photo-tray__slot photo-tray__slot--filled">
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
            ) : (
              <label key={index} className="photo-tray__slot photo-tray__slot--empty">
                <span aria-hidden="true">+</span>
                <input
                  type="file"
                  className="photo-tray__input"
                  aria-label={`Add photo ${index + 1}`}
                  accept="image/jpeg,image/png"
                  onChange={handleFileSelected}
                  disabled={disabled || images.length >= MAX_IMAGES}
                />
              </label>
            )
          })}
        </div>
        {images.length > 0 && (
          <p className="image-upload-form__count">
            {images.length} of {MAX_IMAGES} selected
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
