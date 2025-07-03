import React, { useState } from 'react';

function ViewportContainer({ viewport, onUpload, onFrameChange, bindSliders }) {
  const [currentFrame, setCurrentFrame] = useState(0);
  const [totalFrames, setTotalFrames] = useState(0);

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    onUpload(file);
  };

  const handleSliderChange = (event) => {
    const frame = parseInt(event.target.value);
    setCurrentFrame(frame);
    onFrameChange(frame);
  };

  return (
    <div className="viewport-container">
      <h2>{viewport.title}</h2>
      {!viewport.file ? (
        <div className="dicom-prompt" onClick={() => document.getElementById(`dicomFile${viewport.id}`).click()}>
          Click to upload a DICOM file for {viewport.title}
        </div>
      ) : (
        <>
          <img id={`viewportImage${viewport.id}`} className="viewport-image" alt={`DICOM ${viewport.title}`} />
          <div className="slider-section">
            <label htmlFor={`frameSlider${viewport.id}`}>Select Frame</label>
            <input
              type="range"
              id={`frameSlider${viewport.id}`}
              min="0"
              max={totalFrames - 1}
              value={currentFrame}
              onChange={handleSliderChange}
            />
            <p>Current Frame: {currentFrame + 1} of {totalFrames}</p>
          </div>
        </>
      )}
      <input
        type="file"
        id={`dicomFile${viewport.id}`}
        style={{ display: 'none' }}
        onChange={handleFileChange}
      />
    </div>
  );
}

export default ViewportContainer;