export default function ImageUploadForm({ image, onImageChange, onSubmit, disabled }) {
  function handleSubmit(event) {
    event.preventDefault()
    onSubmit()
  }

  return (
    <form onSubmit={handleSubmit} className="image-upload-form">
      <div>
        <label htmlFor="diagnosisImage">
          <span aria-hidden="true">📷 </span>
          Or upload a photo instead
        </label>
        <input
          id="diagnosisImage"
          type="file"
          accept="image/jpeg,image/png"
          onChange={(event) => onImageChange(event.target.files?.[0] ?? null)}
          disabled={disabled}
        />
        {image && <p className="image-upload-form__filename">Selected: {image.name}</p>}
      </div>

      <button type="submit" disabled={disabled || !image}>
        {disabled ? '⏳ Submitting…' : '📷 Diagnose from photo'}
      </button>
    </form>
  )
}
