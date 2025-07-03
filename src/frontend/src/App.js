import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [viewports, setViewports] = useState([
    { id: 1, title: 'Viewport 1', file: null, currentFrame: 0, totalFrames: 0, dicomFilePath: '' },
    { id: 2, title: 'Viewport 2', file: null, currentFrame: 0, totalFrames: 0, dicomFilePath: '' }
  ]);
  const [bindSliders, setBindSliders] = useState(false);
  const [isE2EFile, setIsE2EFile] = useState(false);
  const [selectedE2EType, setSelectedE2EType] = useState(null);
  const [testMessage, setTestMessage] = useState('');




  const handleE2ETypeSelection = async (type) => {
    setSelectedE2EType(type);
    const formData = new FormData();
    formData.append('file', viewports[0].file);
    formData.append('type', type);
  
    try {
      const response = await fetch('/api/upload_e2e', {
        method: 'POST',
        body: formData,
      });
  
      if (response.ok) {
        const data = await response.json();
        setViewports(prevViewports => 
          prevViewports.map(viewport => 
            viewport.id === 1
              ? { ...viewport, totalFrames: data.number_of_frames, dicomFilePath: data.dicom_file_path }
              : viewport
          )
        );
        displayFrame(1, 0);
        setIsE2EFile(false);
      } else {
        const errorData = await response.json();
        alert('Error: ' + errorData.detail);
      }
    } catch (error) {
      console.error('Error:', error);
      alert('An error occurred during the E2E processing.');
    }
  };

  const testBackendConnection = async () => {
    try {
      console.log('Attempting to connect to /api/test');
      const response = await fetch('/api/test');
      console.log('Response received:', response);
      console.log('Response status:', response.status);
      console.log('Response headers:', response.headers);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      console.log('Response data:', data);
      setTestMessage(data.message);
    } catch (error) {
      console.error('Error:', error);
      setTestMessage(`Connection failed: ${error.message}`);
    }
  };

  const uploadDICOM = async (viewportNumber, file) => {
    const formData = new FormData();
    formData.append('file', file);
  
    if (file.name.toLowerCase().endsWith('.e2e')) {
      setIsE2EFile(true);
      console.log('E2E file detected:', file.name);
      setSelectedE2EType(null);
      return;
    }
  
    try {
      const response = await fetch('http://localhost:8000/api/upload_image', {
        method: 'POST',
        body: formData,
      });
  
      if (!response.ok) {
        const errorText = await response.text();
        console.log('Server response:', errorText);
        throw new Error(`HTTP error! status: ${response.status}`);
      }
  
      const data = await response.json();
      console.log('Upload response:', data);
  
      const { number_of_frames, dicom_file_path } = data;
  
      // Update the viewport state
      setViewports((prevViewports) =>
        prevViewports.map((viewport) =>
          viewport.id === viewportNumber
            ? {
                ...viewport,
                file: file,
                totalFrames: number_of_frames,
                dicomFilePath: dicom_file_path,
                currentFrame: 0,
              }
            : viewport
        )
      );
  
      // Display the first frame by passing dicomFilePath directly
      await displayFrame(viewportNumber, 0, dicom_file_path);
    } catch (error) {
      console.error('Error:', error);
      alert('An error occurred during the upload process. Check console for details.');
    }
  };
  
  const displayFrame = async (viewportNumber, frame, dicomFilePath) => {
    try {
      const response = await fetch(
        `/api/view_dicom_png?frame=${frame}&dicom_file_path=${encodeURIComponent(dicomFilePath)}`
      );
      if (response.ok) {
        const blob = await response.blob();
        const imageUrl = URL.createObjectURL(blob);
  
        // Update the viewport's imageUrl and currentFrame
        setViewports((prevViewports) =>
          prevViewports.map((viewport) =>
            viewport.id === viewportNumber
              ? { ...viewport, currentFrame: frame, imageUrl: imageUrl }
              : viewport
          )
        );
      } else {
        const errorData = await response.json();
        alert(`Error: ${errorData.detail}`);
      }
    } catch (error) {
      console.error('Error:', error);
      alert('An error occurred while displaying the frame.');
    }
  };

  const handleSliderChange = (viewportNumber, frame) => {
    const viewport = viewports.find((v) => v.id === viewportNumber);
    if (!viewport) return;
  
    displayFrame(viewportNumber, frame, viewport.dicomFilePath);
  
    if (bindSliders) {
      const otherViewportNumber = viewportNumber === 1 ? 2 : 1;
      const otherViewport = viewports.find((v) => v.id === otherViewportNumber);
      if (otherViewport && otherViewport.totalFrames === viewport.totalFrames) {
        displayFrame(otherViewportNumber, frame, otherViewport.dicomFilePath);
      }
    }
  };

  const handleE2EToDicomConvert = async () => {
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = '.e2e';

    fileInput.onchange = async (event) => {
      const file = event.target.files[0];
      if (!file) {
        alert('No file selected');
        return;
      }

      const formData = new FormData();
      formData.append('file', file);

      try {
        const response = await fetch('/api/convert', {
          method: 'POST',
          body: formData,
        });

        if (response.ok) {
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = 'converted_dicom_files.zip';
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);
          alert('E2E file converted successfully. The zip file containing DICOM files has been downloaded.');
        } else {
          const errorData = await response.json();
          alert('Error: ' + errorData.detail);
        }
      } catch (error) {
        console.error('Error:', error);
        alert('An error occurred during the conversion process.');
      }
    };

    fileInput.click();
  };

  const handleDicomMetadataExtract = async () => {
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.multiple = true;
    fileInput.accept = '.dcm';

    fileInput.onchange = async (event) => {
      const files = fileInput.files;
      if (files.length === 0) {
        alert('No file selected');
        return;
      }

      const formData = new FormData();
      for (let i = 0; i < files.length; i++) {
        formData.append('file', files[i]);
      }

      try {
        const response = await fetch('/api/dicom_to_mat_npy_zip', {
          method: 'POST',
          body: formData,
        });

        if (response.ok) {
          const zipBlob = await response.blob();
          const downloadUrl = URL.createObjectURL(zipBlob);
          const a = document.createElement('a');
          a.href = downloadUrl;
          a.download = 'dicom_metadata_and_pixels.zip';
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
        } else {
          const errorData = await response.json();
          alert('Error: ' + errorData.detail);
        }
      } catch (error) {
        console.error('Error:', error);
        alert('An error occurred during the metadata extraction process.');
      }
    };

    fileInput.click();
  };

  return (
    <div className="App">
      <div className="menu-bar">
        <nav>
          <a href="#">File</a>
          <a href="#">Edit</a>
          <div className="dropdown">
            <span className="dropbtn">Tools</span>
            <div className="dropdown-content">
              <a href="#">Lock Scroll</a>
              <a href="#" onClick={handleE2EToDicomConvert}>E2E to DICOM Converter</a>
              <a href="#" onClick={handleDicomMetadataExtract}>DICOM Metadata & Pixel Extractor</a>
              <a href="#">Other Tool 2</a>
            </div>
          </div>
          <a href="#">Help</a>
        </nav>
      </div>
      <header>Retinal Image Viewer and File Processor</header>
  
      <div className="main-content">
      <div className="test-connection">
            <button onClick={testBackendConnection}>Test Backend Connection</button>
              {testMessage && <p>{testMessage}</p>}
            </div>
      {viewports.map(viewport => (
        <div key={viewport.id} className="viewport-container">
          <h2 id={`viewportTitle${viewport.id}`}>{viewport.title}</h2>
          {!viewport.file ? (
            <div className="dicom-prompt" onClick={() => document.getElementById(`dicomFile${viewport.id}`).click()}>
              Click to upload a DICOM or E2E file for {viewport.title}
            </div>
          ) : isE2EFile && !selectedE2EType ? (
            <div className="e2e-selection">
              <button className="e2e-button" onClick={() => handleE2ETypeSelection('SLO')}>SLO</button>
              <button className="e2e-button" onClick={() => handleE2ETypeSelection('OCT')}>OCT</button>
            </div>
          ) : (
            <>
              <img 
                id={`viewportImage${viewport.id}`} 
                className="viewport-image" 
                src={viewport.imageUrl} 
                alt={`DICOM ${viewport.title}`} 
              />
              <div className="slider-section">
                <label htmlFor={`frameSlider${viewport.id}`}>Select Frame</label>
                <input
                  type="range"
                  id={`frameSlider${viewport.id}`}
                  min="0"
                  max={viewport.totalFrames - 1}
                  value={viewport.currentFrame}
                  onChange={(e) => handleSliderChange(viewport.id, parseInt(e.target.value))}
                />
                <p>Current Frame: {viewport.currentFrame + 1} of {viewport.totalFrames}</p>
              </div>
            </>
          )}
          <input
            type="file"
            id={`dicomFile${viewport.id}`}
            style={{ display: 'none' }}
            onChange={(e) => uploadDICOM(viewport.id, e.target.files[0])}
            accept=".dcm,.e2e"
          />
        </div>
      ))}
  
        <div id="bindSlidersContainer" style={{display: viewports.every(v => v.file) ? 'block' : 'none'}}>
          <input 
            type="checkbox" 
            id="bindSliders" 
            checked={bindSliders}
            onChange={(e) => setBindSliders(e.target.checked)}
          />
          <label htmlFor="bindSliders">Bind Sliders</label>
        </div>
      </div>
  
      <footer>
        © 2024 Kodiak Sciences Inc - All Rights Reserved.
      </footer>
    </div>
  );
}

export default App;