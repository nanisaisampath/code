import React from 'react';

function Toolbar({ onE2EToDicomConvert, onDicomMetadataExtract }) {
  return (
    <div className="toolbar">
      <h2><i className="fas fa-tools"></i></h2>
      <nav>
        <a href="#">Lock Scroll</a>
        <a href="#" onClick={onE2EToDicomConvert}>E2E to DICOM Converter</a>
        <a href="#" onClick={onDicomMetadataExtract}>DICOM Metadata & Pixel Extractor</a>
        <a href="#">Other Tool 2</a>
      </nav>
    </div>
  );
}

export default Toolbar;