# Optical Fiber Splicing Loss Simulator

An educational Python/Streamlit web application for exploring an optical fibre link power budget.

## Features
- Fibre attenuation, splice loss, and connector loss calculations
- Total link loss, received power, and link margin
- PASS/FAIL based on receiver sensitivity
- Component-wise charts and fibre-length sweep
- Scenario comparison (Excellent, Good, Average, Poor)
- CSV exports and Markdown simulation report
- Theory and methodology section

## Requirements
- Python 3.9 or newer
- Packages listed in `requirements.txt`

## Run locally

1. Extract the ZIP file.
2. Open a terminal in the extracted project folder.
3. (Recommended) Create and activate a virtual environment.
4. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

5. Start the app:

   ```bash
   streamlit run app.py
   ```

6. Open the local URL shown in the terminal, usually `http://localhost:8501`.

## Default example
- Fibre length: 10 km
- Attenuation: 0.2 dB/km
- Splices: 5 at 0.1 dB each
- Connectors: 2 at 0.5 dB each
- Transmitter power: 0 dBm
- Receiver sensitivity: -20 dBm

Expected calculated results:
- Fibre loss: 2.0 dB
- Splice loss: 0.5 dB
- Connector loss: 1.0 dB
- Total loss: 3.5 dB
- Received power: -3.5 dBm
- Link margin: 16.5 dB
- Status: PASS

## Model limitations
This is a simplified theoretical power-budget model. It does not simulate dispersion, nonlinear effects, wavelength-dependent attenuation, environmental variations, or a BER target. It is not a replacement for real fibre measurements.

## Note about source
This is a reconstructed implementation based on the project screenshots and report context provided in the conversation. It is a runnable code version of the described features, not a recovered copy of any original source repository.
